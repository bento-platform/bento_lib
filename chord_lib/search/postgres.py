import re

from collections import namedtuple
from psycopg2 import sql
from typing import Callable, Dict, List, Optional, Tuple

from .queries import *


# Search Rules:
#  - If an object or query doesn't match the schema, it's an error.
#  - If an optional property isn't present, it's "False".


__all__ = ["search_query_to_psycopg2_sql"]


SQLComposableWithParams = Tuple[sql.Composable, tuple]

JoinAndSelectData = namedtuple("JoinAndSelectData", ("relations", "aliases", "key_link", "field_alias"))


def collect_resolve_join_tables(
    resolve: List[Literal],
    schema: dict,
    parent_relation: Optional[Tuple[Optional[str], Optional[str]]] = None,
    resolve_path: Optional[str] = None
) -> Tuple[JoinAndSelectData, ...]:
    """
    Recursively collects tables to join for compiling the query.
    :param resolve: The current resolve list, minus the command. Starts with $root to keep schema proper.
    :param schema: The schema of the current element (first property.)
    :param parent_relation: The tuple representing the parent relation, format: (relation name, alias).
    :param resolve_path: Underscore-delimited list of parent property names in the case of nested objects/arrays.
    :return: Tuple of tables with joining properties.
    """

    # Many to one: child_key -> primary_key
    # Many to many: primary_key -> parent_key (treat as just another through)

    if len(resolve) == 0:
        return ()

    relations = (parent_relation[0] if parent_relation is not None else None,
                 schema.get("search", {}).get("database", {}).get("relation", None))

    aliases = (resolve_path if resolve_path is not None else None,
               re.sub(r"[$\[\]]+", "", "{}_{}".format(resolve_path if resolve_path is not None else "",
                                                      resolve[0].value))
               if relations[1] is not None else None)

    key_link = None

    if schema["type"] not in ("array", "object"):
        if len(resolve) > 1:
            raise TypeError("Cannot get property of literal")
        return JoinAndSelectData(relations=relations, aliases=aliases, key_link=key_link, field_alias=(
            schema.get("search", {})
                  .get("database", {})
                  .get("field", resolve[0].value if resolve[0].value != "$root" else None)
        )),

    if "search" in schema and "database" in schema["search"] and "relationship" in schema["search"]["database"]:
        rel_type = schema["search"]["database"]["relationship"]["type"]
        if rel_type == "MANY_TO_ONE":
            key_link = (schema["search"]["database"]["relationship"]["foreign_key"],
                        schema["search"]["database"]["primary_key"])
        elif rel_type in ("MANY_TO_MANY", "ONE_TO_MANY"):
            key_link = (schema["search"]["database"]["relationship"]["parent_primary_key"],
                        schema["search"]["database"]["relationship"]["parent_foreign_key"])
        else:
            raise SyntaxError("Invalid relationship type: {}".format(rel_type))

    # relations, aliases, key_link, field_alias
    join_table_data = JoinAndSelectData(relations=relations, aliases=aliases, key_link=key_link, field_alias=None)

    if schema["type"] == "array":
        if len(resolve) == 1:  # End result is array
            return join_table_data,  # Return single tuple of relation

        elif resolve[1].value != "[item]":
            raise TypeError("Cannot get property of array in #resolve")

        else:
            return (join_table_data,) + collect_resolve_join_tables(resolve[1:], schema["items"],
                                                                    (relations[1], aliases[1]), aliases[1])

    # Otherwise, type is object

    if len(resolve) == 1:
        return join_table_data,

    try:
        return (join_table_data,) + collect_resolve_join_tables(resolve[1:], schema["properties"][resolve[1].value],
                                                                (relations[1], aliases[1]), aliases[1])
    except KeyError:
        raise ValueError("Property {} not found in object".format(resolve[1]))


def collect_join_tables(ast: AST, terms: tuple, schema: dict) -> Tuple[JoinAndSelectData, ...]:
    if isinstance(ast, Literal):
        return terms

    if ast.fn == FUNCTION_RESOLVE:
        return terms + tuple(t for t in collect_resolve_join_tables([Literal("$root")] + ast.args, schema)
                             if t not in terms)

    new_terms = terms

    for item in (a for a in ast.args if isinstance(a, Expression)):
        new_terms = collect_join_tables(item, new_terms, schema)

    return new_terms


def join_fragment(ast: AST, schema: dict) -> sql.Composable:
    terms = collect_join_tables(ast, (), schema)
    if len(terms) == 0:
        return sql.SQL("")

    return sql.SQL(" LEFT JOIN ").join(
        [sql.SQL("{} AS {}").format(sql.Identifier(terms[0].relations[1]), sql.Identifier(terms[0].aliases[1]))] +
        [sql.SQL("{r1} AS {a1} ON {a0}.{f0} = {a1}.{f1}").format(
            r1=sql.Identifier(term.relations[1]),
            a0=sql.Identifier(term.aliases[0]),
            a1=sql.Identifier(term.aliases[1]),
            f0=sql.Identifier(term.key_link[0]),
            f1=sql.Identifier(term.key_link[1])
        ) for term in terms[1:] if term.key_link is not None]  # Exclude terms without key-links
    )


def search_ast_to_psycopg2_expr(ast: AST, params: tuple, schema: dict) -> SQLComposableWithParams:
    if isinstance(ast, Literal):
        return sql.Placeholder(), (*params, ast.value)

    return POSTGRES_SEARCH_LANGUAGE_FUNCTIONS[ast.fn](ast.args, params, schema)


def search_query_to_psycopg2_sql(query, schema: dict) -> SQLComposableWithParams:
    # TODO: Shift recursion to not have to add in the extra SELECT for the root?
    ast = convert_query_to_ast_and_preprocess(query)
    sql_obj, params = search_ast_to_psycopg2_expr(ast, (), schema)
    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    return sql.SQL("SELECT \"_root\".* FROM {} WHERE {}").format(join_fragment(ast, schema), sql_obj), params


def uncurried_binary_op(op: str, args: List[AST], params: tuple, schema: dict) -> SQLComposableWithParams:
    # TODO: Need to fix params!! Use named params
    lhs_sql, lhs_params = search_ast_to_psycopg2_expr(args[0], params, schema)
    rhs_sql, rhs_params = search_ast_to_psycopg2_expr(args[1], params, schema)
    return sql.SQL("({}) {} ({})").format(lhs_sql, sql.SQL(op), rhs_sql), params + lhs_params + rhs_params


def _binary_op(op) -> Callable[[list, tuple, dict], SQLComposableWithParams]:
    return lambda args, params, schema: uncurried_binary_op(op, args, params, schema)


def _not(args: list, params: tuple, schema: dict) -> SQLComposableWithParams:
    child_sql, child_params = search_ast_to_psycopg2_expr(args[0], params, schema)
    return sql.SQL("NOT ({})").format(child_sql), params + child_params


def _wildcard(args: List[AST], params: tuple, _schema: dict) -> SQLComposableWithParams:
    if isinstance(args[0], Expression):
        raise NotImplementedError("Cannot currently use #co on an expression")  # TODO

    try:
        return sql.Placeholder(), (*params, "%{}%".format(args[0].value.replace("%", r"\%")))
    except AttributeError:  # Cast
        raise TypeError("Type-invalid use of binary function #co")


def get_relation(resolve: List[Literal], schema: dict):
    aliases = collect_resolve_join_tables(resolve, schema)[-1].aliases
    return aliases[1] if aliases[1] is not None else aliases[0]


def get_field(resolve: List[Literal], schema: dict) -> Optional[str]:
    return collect_resolve_join_tables(resolve, schema)[-1].field_alias


def _resolve(args: List[AST], params: tuple, schema: dict) -> SQLComposableWithParams:
    r_id = get_relation([Literal("$root")] + args, schema)
    f_id = get_field([Literal("$root")] + args, schema)
    return sql.SQL("{}.{}").format(sql.Identifier(r_id),
                                   sql.Identifier(f_id) if f_id is not None else sql.SQL("*")), params


def _contains(args: List[AST], params: tuple, schema: dict) -> SQLComposableWithParams:
    lhs_sql, lhs_params = search_ast_to_psycopg2_expr(args[0], params, schema)
    rhs_sql, rhs_params = search_ast_to_psycopg2_expr(Expression(fn=FUNCTION_HELPER_WC, args=[args[1]]), params, schema)
    return sql.SQL("({}) LIKE ({})").format(lhs_sql, rhs_sql), params + lhs_params + rhs_params


POSTGRES_SEARCH_LANGUAGE_FUNCTIONS: Dict[str, Callable[[List[AST], tuple, dict], SQLComposableWithParams]] = {
    FUNCTION_AND: _binary_op("AND"),
    FUNCTION_OR: _binary_op("OR"),
    FUNCTION_NOT: _not,

    FUNCTION_LT: _binary_op("<"),
    FUNCTION_LE: _binary_op("<="),
    FUNCTION_EQ: _binary_op("="),
    FUNCTION_GT: _binary_op(">"),
    FUNCTION_GE: _binary_op(">="),

    FUNCTION_CO: _contains,

    FUNCTION_RESOLVE: _resolve,

    FUNCTION_HELPER_WC: _wildcard
}
