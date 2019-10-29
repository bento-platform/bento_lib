import re

from psycopg2 import sql
from typing import Callable, Dict, Optional, Tuple

from .custom_types import Query


# Search Rules:
#  - If an object or query doesn't match the schema, it's an error.
#  - If an optional property isn't present, it's "False".


__all__ = ["search_query_to_psycopg2_sql"]


SQLComposableWithParams = Tuple[sql.Composable, tuple]


def collect_resolve_join_tables(
    resolve: list,
    schema: dict,
    parent_relation: Optional[Tuple[Optional[str], Optional[str]]] = None,
    resolve_path: Optional[str] = None
) -> tuple:
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
               re.sub(r"[$\[\]]+", "", "{}_{}".format(resolve_path if resolve_path is not None else "", resolve[0]))
               if relations[1] is not None else None)

    key_link = None
    field_alias = None

    if schema["type"] not in ("array", "object"):
        if len(resolve) > 1:
            raise TypeError("Cannot get property of literal")
        field_alias = schema.get("search", {}).get("database", {}).get("field",
                                                                       resolve[0] if resolve[0] != "$root" else None)
        return (relations, aliases, key_link, field_alias),

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

    join_table_data = (relations, aliases, key_link, field_alias)

    if schema["type"] == "array":
        if len(resolve) == 1:  # End result is array
            return join_table_data,  # Return single tuple of relation

        elif resolve[1] != "[item]":
            raise TypeError("Cannot get property of array in #resolve")

        else:
            return (join_table_data,) + collect_resolve_join_tables(resolve[1:], schema["items"],
                                                                    (relations[1], aliases[1]), aliases[1])

    # Otherwise, type is object

    if len(resolve) == 1:
        return join_table_data,

    try:
        return (join_table_data,) + collect_resolve_join_tables(resolve[1:], schema["properties"][resolve[1]],
                                                                (relations[1], aliases[1]), aliases[1])
    except KeyError:
        raise ValueError("Property {} not found in object".format(resolve[1]))


def collect_join_tables(ast: Query, terms: tuple, schema: dict) -> tuple:
    if not isinstance(ast, list):
        return terms

    if ast[0] == "#resolve":
        return terms + tuple(t for t in collect_resolve_join_tables(["$root"] + ast[1:], schema) if t not in terms)

    new_terms = terms

    for item in ast:
        if isinstance(item, list):
            new_terms = collect_join_tables(item, new_terms, schema)

    return new_terms


def join_fragment(ast: Query, schema: dict) -> sql.Composable:
    terms = collect_join_tables(ast, (), schema)
    if len(terms) == 0:
        return sql.SQL("")

    return sql.SQL(" LEFT JOIN ").join(
        [sql.SQL("{} AS {}").format(sql.Identifier(terms[0][0][1]), sql.Identifier(terms[0][1][1]))] +
        [sql.SQL("{r1} AS {a1} ON {a0}.{f0} = {a1}.{f1}").format(
            r1=sql.Identifier(term[0][1]),
            a0=sql.Identifier(term[1][0]),
            a1=sql.Identifier(term[1][1]),
            f0=sql.Identifier(term[2][0]),
            f1=sql.Identifier(term[2][1])
        ) for term in terms[1:] if term[2] is not None]  # Exclude terms without key-links
    )


def search_ast_to_psycopg2_expr(ast: Query, params: tuple, schema: dict) -> SQLComposableWithParams:
    if isinstance(ast, dict):  # Error: dict has no meaning yet
        raise NotImplementedError("Cannot use objects as literals")

    if not isinstance(ast, list):
        # Literal (string/number/boolean)
        return sql.Placeholder(), (*params, ast)

    if len(ast) == 0:
        raise SyntaxError("Invalid expression: []")

    if not isinstance(ast[0], str):
        raise SyntaxError("Invalid function: {}".format(ast[0]))

    fn = ast[0]
    args = ast[1:]

    if fn not in POSTGRES_SEARCH_LANGUAGE_FUNCTIONS:
        raise SyntaxError("Non-existent function: {}".format(fn))

    return POSTGRES_SEARCH_LANGUAGE_FUNCTIONS[fn](args, params, schema)


def search_query_to_psycopg2_sql(query, schema: dict) -> SQLComposableWithParams:
    # TODO: Shift recursion to not have to add in the extra SELECT for the root?
    sql_obj, params = search_ast_to_psycopg2_expr(query, (), schema)
    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    return sql.SQL("SELECT \"_root\".* FROM {} WHERE {}").format(join_fragment(query, schema), sql_obj), params


def uncurried_binary_op(op: str, args: list, params: tuple, schema: dict) -> SQLComposableWithParams:
    # TODO: Need to fix params!! Use named params
    try:
        lhs_sql, lhs_params = search_ast_to_psycopg2_expr(args[0], params, schema)
        rhs_sql, rhs_params = search_ast_to_psycopg2_expr(args[1], params, schema)
        return sql.SQL("({}) {} ({})").format(lhs_sql, sql.SQL(op), rhs_sql), params + lhs_params + rhs_params
    except IndexError:
        raise SyntaxError("Cannot use binary operator {} on less than two values".format(op))


def _binary_op(op) -> Callable[[list, tuple, dict], SQLComposableWithParams]:
    return lambda args, params, schema: uncurried_binary_op(op, args, params, schema)


def _not(args: list, params: tuple, schema: dict) -> SQLComposableWithParams:
    child_sql, child_params = search_ast_to_psycopg2_expr(args[0], params, schema)
    return sql.SQL("NOT ({})").format(child_sql), params + child_params


def _wildcard(args: list, params: tuple, _schema: dict) -> SQLComposableWithParams:
    if len(args) != 1:
        raise SyntaxError("Invalid number of arguments for #_wc")

    if isinstance(args[0], list):
        raise NotImplementedError("Cannot currently use #co on an expression")  # TODO

    try:
        return sql.Placeholder(), (*params, "%{}%".format(args[0].replace("%", r"\%")))
    except AttributeError:  # Cast
        raise TypeError("Type-invalid use of binary function #co")


def get_relation(resolve: list, schema: dict):
    aliases = collect_resolve_join_tables(resolve, schema)[-1][1]
    return aliases[1] if aliases[1] is not None else aliases[0]


def get_field(resolve: list, schema: dict) -> Optional[str]:
    return collect_resolve_join_tables(resolve, schema)[-1][3]


def _resolve(args: list, params: tuple, schema: dict) -> SQLComposableWithParams:
    r_id = get_relation(["$root"] + args, schema)
    f_id = get_field(["$root"] + args, schema)
    return sql.SQL("{}.{}").format(sql.Identifier(r_id),
                                   sql.Identifier(f_id) if f_id is not None else sql.SQL("*")), params


def _contains(args: list, params: tuple, schema: dict) -> SQLComposableWithParams:
    lhs_sql, lhs_params = search_ast_to_psycopg2_expr(args[0], params, schema)
    rhs_sql, rhs_params = search_ast_to_psycopg2_expr(["#_wc", args[1]], params, schema)
    return sql.SQL("({}) LIKE ({})").format(lhs_sql, rhs_sql), params + lhs_params + rhs_params


POSTGRES_SEARCH_LANGUAGE_FUNCTIONS: Dict[str, Callable[[list, tuple, dict], SQLComposableWithParams]] = {
    "#and": _binary_op("AND"),
    "#or": _binary_op("OR"),
    "#not": _not,

    "#lt": _binary_op("<"),
    "#le": _binary_op("<="),
    "#eq": _binary_op("="),
    "#gt": _binary_op(">"),
    "#ge": _binary_op(">="),

    "#co": _contains,

    "#resolve": _resolve,

    "#_wc": _wildcard
}
