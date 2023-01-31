import functools
import re

from psycopg2 import sql
from typing import Callable, Dict, Optional, Tuple

from . import queries as q
from ._types import JSONSchema


# Search Rules:
#  - If an object or query doesn't match the schema, it's an error.
#  - If an optional property isn't present, it's "False".


__all__ = ["search_query_to_psycopg2_sql"]


SQLComposableWithParams = Tuple[sql.Composable, tuple]

QUERY_ROOT = q.Literal("$root")
SQL_ROOT = sql.Identifier("_root")


# TODO: Python 3.7: Data Class
class OptionalComposablePair:
    def __init__(self, parent: Optional[sql.Composable], current: Optional[sql.Composable]):
        self.parent: Optional[sql.Composable] = parent
        self.current: Optional[sql.Composable] = current

    def __repr__(self):  # pragma: no cover
        return f"<OptionalComposablePair parent={self.parent} current={self.current}>"


# TODO: Python 3.7: Data Class
class JoinAndSelectData:
    def __init__(
        self,
        relations: OptionalComposablePair,
        aliases: OptionalComposablePair,
        current_alias_str: Optional[str],
        key_link: Optional[Tuple[str, str]],
        field_alias: Optional[str],
        search_properties: dict,
        unresolved: Tuple[q.Literal, ...]
    ):
        self.relations: OptionalComposablePair = relations
        self.aliases: OptionalComposablePair = aliases
        self.current_alias_str: Optional[str] = current_alias_str
        self.key_link: Optional[Tuple[str, str]] = key_link
        self.field_alias: Optional[str] = field_alias
        self.search_properties: dict = search_properties
        self.unresolved: Tuple[q.Literal, ...] = unresolved

    def __repr__(self):  # pragma: no cover
        return f"<JoinAndSelectData relations={self.relations} aliases={self.aliases}>"


def json_schema_to_postgres_type(schema: JSONSchema) -> str:
    """
    Maps a JSON schema to a Postgres type for on the fly mapping.
    :param schema: JSON schema to map.
    """
    if schema["type"] == "string":
        return "TEXT"
    elif schema["type"] == "integer":
        return "INTEGER"
    elif schema["type"] == "number":
        return "DOUBLE PRECISION"
    elif schema["type"] == "object":
        return "JSON"  # TODO: JSON or JSONB
    elif schema["type"] == "array":
        return "JSON"  # TODO: JSON or JSONB
    elif schema["type"] == "boolean":
        return "BOOLEAN"
    else:
        # null
        return "TEXT"  # TODO


def json_schema_to_postgres_schema(name: str, schema: JSONSchema) -> Tuple[Optional[sql.Composable], Optional[str]]:
    """
    Maps a JSON object schema to a Postgres schema for on-the-fly mapping.
    :param name: the name to give the fake table.
    :param schema: JSON schema to map.
    """

    if schema["type"] != "object":
        return None, None

    return (
        sql.SQL("{}({})").format(
            sql.Identifier(name),
            sql.SQL(", ").join(sql.SQL("{} {}").format(sql.Identifier(p), sql.SQL(json_schema_to_postgres_type(s)))
                               for p, s in schema["properties"].items())),
        "{}({})".format(name, ", ".join("{} {}".format(p, json_schema_to_postgres_type(s))
                                        for p, s in schema["properties"].items()))
    )


def _get_search_and_database_properties(schema: JSONSchema) -> Tuple[dict, dict]:
    search_properties = schema.get("search", {})
    return search_properties, search_properties.get("database", {})


def collect_resolve_join_tables(
    resolve: Tuple[q.Literal, ...],
    schema: JSONSchema,
    parent_relation: Optional[Tuple[Optional[sql.Composable], Optional[sql.Composable]]] = None,
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

    search_properties, search_database_properties = _get_search_and_database_properties(schema)

    # TODO: might be able to inject .value under some circumstances here
    schema_field = resolve[0].value
    db_field = search_database_properties.get("field", schema_field if schema_field != QUERY_ROOT.value else None)
    current_relation = search_database_properties.get("relation")

    new_resolve_path = re.sub(r"[$\[\]]+", "", "{}_{}".format(resolve_path if resolve_path is not None else "",
                                                              schema_field))
    current_alias = None
    current_alias_str = None

    if current_relation is None and schema["type"] in ("array", "object"):
        if db_field is None:
            raise SyntaxError("Cannot determine or synthesize current relation")

        # TODO: Additional conditions to check if it's actually JSON
        # TODO: HStore support?
        structure_type = search_database_properties.get("type")
        if structure_type in ("json", "jsonb"):
            if schema["type"] == "array":  # JSON(B) array or object
                relation_template = "{}_array_elements({})"
                current_alias = sql.Identifier(new_resolve_path)
                current_alias_str = new_resolve_path
            else:  # object
                relation_template = "{}_to_record({})"
                current_alias, current_alias_str = json_schema_to_postgres_schema(new_resolve_path, schema)

            current_relation = sql.SQL(relation_template).format(
                sql.SQL(structure_type),
                sql.SQL(".").join((parent_relation[1], sql.Identifier(db_field))
                                  if db_field != "[item]" else (parent_relation[1],)))

        elif structure_type == "array" and schema["type"] == "array":  # Postgres array
            current_relation = sql.SQL("unnest({}.{})").format(parent_relation[1], sql.Identifier(db_field))
            current_alias = sql.Identifier(new_resolve_path)
            current_alias_str = new_resolve_path

        else:
            raise ValueError(f"Structure type / schema type mismatch: {structure_type} / {schema['type']}\n"
                             f"    Search properties: {search_properties}\n"
                             f"    Search database properties: {search_database_properties}\n"
                             f"    Resolve path: {new_resolve_path}")

    elif current_relation is not None:
        current_relation = sql.Identifier(current_relation)
        current_alias = sql.Identifier(new_resolve_path)
        current_alias_str = new_resolve_path

    relations = OptionalComposablePair(parent_relation[0] if parent_relation is not None else None, current_relation)

    # Parent, Current
    aliases = OptionalComposablePair(parent=sql.Identifier(resolve_path) if resolve_path is not None else None,
                                     current=current_alias)

    key_link = None
    if "relationship" in search_database_properties:
        relationship = search_database_properties["relationship"]
        relationship_type = relationship["type"]
        if relationship_type == "MANY_TO_ONE":
            key_link = (relationship["foreign_key"], search_database_properties["primary_key"])
        elif relationship_type == "ONE_TO_MANY":
            key_link = (relationship["parent_primary_key"], relationship["parent_foreign_key"])
        else:
            raise SyntaxError("Invalid relationship type: {}".format(relationship_type))

    join_table_data = JoinAndSelectData(relations=relations, aliases=aliases, current_alias_str=current_alias_str,
                                        key_link=key_link, field_alias=db_field, search_properties=search_properties,
                                        unresolved=resolve[1:])

    if len(resolve) == 1:
        # We're at the end of the resolve list
        return join_table_data,  # Return single tuple of relation

    if schema["type"] not in ("array", "object"):
        # Primitive type, len(resolve) > 1
        # TODO: Handle invalid schema types?
        raise TypeError("Cannot get property of primitive")

    if schema["type"] == "array" and resolve[1].value != "[item]":
        raise TypeError("Cannot get property of array in #resolve")
    elif schema["type"] == "object":  # Object
        if "properties" not in schema:
            raise SyntaxError("Searchable objects in schemas must have all properties described")
        if resolve[1].value not in schema["properties"]:
            raise ValueError("Property {} not found in object".format(resolve[1]))

    return (join_table_data,) + collect_resolve_join_tables(
        resolve=resolve[1:],
        schema=schema["items"] if schema["type"] == "array" else schema["properties"][resolve[1].value],
        parent_relation=(relations.current, aliases.current),
        resolve_path=new_resolve_path if current_relation is not None else None)


def collect_join_tables(ast: q.AST, terms: tuple, schema: JSONSchema) -> Tuple[JoinAndSelectData, ...]:
    if isinstance(ast, q.Literal):
        return terms

    if ast.fn == q.FUNCTION_RESOLVE:
        terms_list = list(terms)
        collected_joins = collect_resolve_join_tables((QUERY_ROOT, *ast.args), schema)

        for j in collected_joins:
            existing_aliases = set(t.current_alias_str for t in terms_list if t is not None)
            if j.current_alias_str is not None and j.current_alias_str not in existing_aliases:
                terms_list.append(j)

        return tuple(terms_list)

    new_terms = terms

    for item in (a for a in ast.args if isinstance(a, q.Expression)):
        new_terms = collect_join_tables(item, new_terms, schema)

    return new_terms


def join_fragment(ast: q.AST, schema: JSONSchema) -> sql.Composable:
    terms = collect_join_tables(ast, (), schema)
    if not terms:  # Query was probably just a literal
        # TODO: Don't hard-code _root?
        search_database_properties = _get_search_and_database_properties(schema)[1]
        relation = search_database_properties.get("relation")
        return sql.SQL("{} AS {}").format(sql.Identifier(relation) if relation else sql.SQL("(SELECT NULL)"), SQL_ROOT)

    return sql.SQL(", ").join((
        sql.SQL(" LEFT JOIN ").join((
            sql.SQL("{} AS {}").format(terms[0].relations.current, terms[0].aliases.current),
            *(sql.SQL("{r1} AS {a1} ON {a0}.{f0} = {a1}.{f1}").format(
                r1=term.relations.current,
                a0=term.aliases.parent,
                a1=term.aliases.current,
                f0=sql.Identifier(term.key_link[0]),
                f1=sql.Identifier(term.key_link[1])
            ) for term in terms[1:] if term.key_link is not None),  # Exclude terms without key-links
        )),
        *(sql.SQL("{r1} AS {a1}").format(r1=term.relations.current, a1=term.aliases.current)
          for term in terms[1:] if term.key_link is None and term.relations.current is not None),
    ))


def search_ast_to_psycopg2_expr(ast: q.AST, params: tuple, schema: JSONSchema, internal: bool = False) \
        -> SQLComposableWithParams:
    if isinstance(ast, q.Literal):
        return sql.Placeholder(), (*params, ast.value)

    q.check_operation_permissions(ast, schema, search_getter=get_search_properties, internal=internal)

    return POSTGRES_SEARCH_LANGUAGE_FUNCTIONS[ast.fn](ast.args, params, schema, internal)


def search_query_to_psycopg2_sql(query, schema: JSONSchema, internal: bool = False) -> SQLComposableWithParams:
    # TODO: Shift recursion to not have to add in the extra SELECT for the root?
    ast = q.convert_query_to_ast_and_preprocess(query)
    sql_obj, params = search_ast_to_psycopg2_expr(ast, (), schema, internal)
    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    return sql.SQL("SELECT {}.* FROM {} WHERE {}").format(SQL_ROOT, join_fragment(ast, schema), sql_obj), params


def uncurried_binary_op(op: str, args: q.Args, params: tuple, schema: JSONSchema, internal: bool = False) \
        -> SQLComposableWithParams:
    # TODO: Need to fix params!! Use named params
    lhs_sql, lhs_params = search_ast_to_psycopg2_expr(args[0], params, schema, internal)
    rhs_sql, rhs_params = search_ast_to_psycopg2_expr(args[1], params, schema, internal)
    return sql.SQL("({}) {} ({})").format(lhs_sql, sql.SQL(op), rhs_sql), params + lhs_params + rhs_params


def _binary_op(op) -> Callable[[q.Args, tuple, JSONSchema, bool], SQLComposableWithParams]:
    return lambda args, params, schema, internal: uncurried_binary_op(op, args, params, schema, internal)


def _in(args: q.Args, params: tuple, schema: JSONSchema, internal: bool = False) -> SQLComposableWithParams:
    lhs_sql, lhs_params = search_ast_to_psycopg2_expr(args[0], params, schema, internal)
    rhs_sql, rhs_params = search_ast_to_psycopg2_expr(args[1], params, schema, internal)
    return sql.SQL("({}) IN {}").format(lhs_sql, rhs_sql), params + lhs_params + rhs_params


def _not(args: q.Args, params: tuple, schema: JSONSchema, internal: bool = False) -> SQLComposableWithParams:
    child_sql, child_params = search_ast_to_psycopg2_expr(args[0], params, schema, internal)
    return sql.SQL("NOT ({})").format(child_sql), params + child_params


# TODO rename the function ?
def _contains(op: str, wc_loc: str, args: q.Args, params: tuple, schema: JSONSchema, internal: bool = False)\
        -> SQLComposableWithParams:
    lhs_sql, lhs_params = search_ast_to_psycopg2_expr(args[0], params, schema, internal)
    rhs_sql, rhs_params = search_ast_to_psycopg2_expr(
        q.Expression(fn=q.FUNCTION_HELPER_WC, args=[args[1], q.Literal(wc_loc)]), params, schema, internal)
    return sql.SQL("({}) {} ({})").format(lhs_sql, sql.SQL(op), rhs_sql), params + lhs_params + rhs_params


def _contains_op(op: str) -> Callable[[q.Args, tuple, JSONSchema, bool], SQLComposableWithParams]:
    def _inner(*args):
        return _contains(op, "anywhere", *args)
    return _inner


_i_starts_with = functools.partial(_contains, "ILIKE", "start")
_i_ends_with = functools.partial(_contains, "ILIKE", "end")


def _wildcard(args: Tuple[q.AST, q.AST], params: tuple, _schema: JSONSchema, _internal: bool = False) \
        -> SQLComposableWithParams:
    if isinstance(args[0], q.Expression):
        raise NotImplementedError("Cannot currently use #co on an expression")  # TODO

    if args[1].value == "start":
        wcs = "{}%"
    elif args[1].value == "end":
        wcs = "%{}"
    else:  # anywhere
        wcs = "%{}%"

    try:
        return sql.Placeholder(), (*params, wcs.format(args[0].value.replace("%", r"\%")))
    except AttributeError:  # Cast
        raise TypeError("Type-invalid use of binary function #co")


def get_relation(resolve: Tuple[q.Literal, ...], schema: JSONSchema):
    aliases = collect_resolve_join_tables((QUERY_ROOT, *resolve), schema)[-1].aliases
    return aliases.current if aliases.current is not None else aliases.parent


def get_field(resolve: Tuple[q.Literal, ...], schema: JSONSchema) -> Optional[str]:
    return collect_resolve_join_tables((QUERY_ROOT, *resolve), schema)[-1].field_alias


def get_search_properties(resolve: Tuple[q.Literal, ...], schema: JSONSchema) -> dict:
    return collect_resolve_join_tables((QUERY_ROOT, *resolve), schema)[-1].search_properties


def _resolve(args: q.Args, params: tuple, schema: JSONSchema, _internal: bool = False) -> SQLComposableWithParams:
    f_id = get_field(args, schema)
    return sql.SQL("{}.{}").format(get_relation(args, schema),
                                   sql.Identifier(f_id) if f_id is not None else sql.SQL("*")), params


def _list(args: q.Args, params: tuple, _schema: JSONSchema, _internal: bool = False) -> SQLComposableWithParams:
    # :param args: a tuple of query.Literal objects to be used in an IN clause.
    # with psycopg2, it must be passed as a tuple of tuples, hence the enclosing
    # parentheses in the following statement.
    # TODO: for large lists, the syntax IN (VALUES ("patient1"), ("patient2")) which creates
    #  a table construct on the fly is recommended performance-wise (better indexing)
    # FUTURE: psycopg3 won't allow the "tuples adaptation" syntax anymore:
    # https://www.psycopg.org/psycopg3/docs/basic/from_pg2.html#you-cannot-use-in-s-with-a-tuple
    values = tuple(a.value for a in args)
    return sql.Placeholder(), (*params, values)


POSTGRES_SEARCH_LANGUAGE_FUNCTIONS: Dict[
    str,
    Callable[[q.Args, tuple, JSONSchema, bool], SQLComposableWithParams]
] = {
    q.FUNCTION_AND: _binary_op("AND"),
    q.FUNCTION_OR: _binary_op("OR"),
    q.FUNCTION_NOT: _not,

    q.FUNCTION_LT: _binary_op("<"),
    q.FUNCTION_LE: _binary_op("<="),
    q.FUNCTION_EQ: _binary_op("="),
    q.FUNCTION_GT: _binary_op(">"),
    q.FUNCTION_GE: _binary_op(">="),
    q.FUNCTION_IN: _in,

    q.FUNCTION_CO: _contains_op("LIKE"),
    q.FUNCTION_ICO: _contains_op("ILIKE"),

    q.FUNCTION_ISW: _i_starts_with,
    q.FUNCTION_IEW: _i_ends_with,

    q.FUNCTION_RESOLVE: _resolve,
    q.FUNCTION_LIST: _list,

    q.FUNCTION_HELPER_WC: _wildcard
}
