import functools
import re

from psycopg2 import sql
from typing import Callable, Dict, Literal, Optional, Tuple

from . import queries as q
from ._types import JSONSchema


# Search Rules:
#  - If an object or query doesn't match the schema, it's an error.
#  - If an optional property isn't present, it's "False".


__all__ = ["search_query_to_psycopg2_sql"]


SQLComposableWithParams = Tuple[sql.Composable, tuple]

QUERY_ROOT = q.Literal("$root")
SQL_ROOT = sql.Identifier("_root")
SQL_NOTHING = sql.SQL("")


# TODO: Python 3.7: Data Class
class OptionalComposablePair:
    def __init__(self, parent: Optional[sql.Composable], current: Optional[sql.Composable]):
        # A 'Composable' here is an abstract base class from PsycoPG2's Postgres IR which can represent anything
        # in the PostgreSQL language which can be composed together to create a query.
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
        current_alias_sql_schema: Optional[sql.SQL],
        key_link: Optional[Tuple[str, str]],
        field_alias: Optional[str],
        search_properties: dict,
        unresolved: Tuple[q.Literal, ...],
    ):
        self.relations: OptionalComposablePair = relations
        self.aliases: OptionalComposablePair = aliases
        self.current_alias_str: Optional[str] = current_alias_str
        self.current_alias_sql_schema: Optional[sql.SQL] = current_alias_sql_schema
        self.key_link: Optional[Tuple[str, str]] = key_link
        self.field_alias: Optional[str] = field_alias
        self.search_properties: dict = search_properties
        self.unresolved: Tuple[q.Literal, ...] = unresolved

    def __repr__(self):  # pragma: no cover
        return f"<JoinAndSelectData relations={self.relations} aliases={self.aliases}>"


def json_schema_to_postgres_type(schema: JSONSchema, structure_type: Literal["json", "jsonb"]) -> str:
    """
    Maps a JSON schema to a Postgres type for on the fly mapping.
    :param schema: JSON schema to map.
    :param structure_type: Whether we are deconstructing a JSON or JSONB field.
    """
    if schema["type"] == "string":
        return "TEXT"
    elif schema["type"] == "integer":
        return "INTEGER"
    elif schema["type"] == "number":
        return "DOUBLE PRECISION"
    elif schema["type"] == "object":
        return structure_type.upper()
    elif schema["type"] == "array":
        return structure_type.upper()
    elif schema["type"] == "boolean":
        return "BOOLEAN"
    else:
        # null
        return "TEXT"  # TODO


def json_schema_to_postgres_schema(
    name: str,
    schema: JSONSchema,
    structure_type: Literal["json", "jsonb"],
) -> Tuple[Optional[sql.Composable], Optional[str], Optional[sql.Composable]]:
    """
    Maps a JSON object schema to a Postgres schema for on-the-fly mapping.
    :param name: the name to give the fake table.
    :param schema: JSON schema to map.
    :param structure_type: Whether we are deconstructing a JSON or JSONB field.
    """

    if schema["type"] != "object":
        return None, None, None

    return (
        sql.Identifier(name),
        name,
        sql.SQL("({})").format(
            sql.SQL(", ").join(
                sql.SQL("{} {}").format(
                    sql.Identifier(p),
                    sql.SQL(json_schema_to_postgres_type(s, structure_type)),
                )
                for p, s in schema["properties"].items()
            )
        ),
    )


def _get_search_and_database_properties(schema: JSONSchema) -> Tuple[dict, dict]:
    search_properties = schema.get("search", {})
    return search_properties, search_properties.get("database", {})


def collect_resolve_join_tables(
    resolve: Tuple[q.Literal, ...],
    schema: JSONSchema,
    parent_relation: Optional[Tuple[Optional[sql.Composable], Optional[sql.Composable]]] = None,
    aliased_resolve_path: Optional[str] = None,
) -> Tuple[JoinAndSelectData, ...]:
    """
    Recursively collects tables to join for compiling the query.
    :param resolve: The current resolve list, minus the command. Starts with $root to keep schema proper.
    :param schema: The schema of the current element (first property.)
    :param parent_relation: The tuple representing the parent relation, format: (relation name, alias).
    :param aliased_resolve_path: Underscore-delimited string 'list' of parent property names in the case of nested
                                 objects/arrays, for building aliases for the nested fields in question.
                                 If it is None, we are at the root.
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

    # Gradually (recursively) build up an alias for this resolve statement at the field we're currently working on.
    # For example, if we are accessing $root.biosamples.[item].id, this would get the alias:
    #  _root_biosamples_item_id
    # by the process of:
    #  - replacing the $ in $root with _
    #  - recursing down and combining the path with the field as it is encountered using '_'
    aliased_resolve_path_str: str = aliased_resolve_path or ""
    new_aliased_resolve_path = re.sub(r"[$\[\]]+", "", f"{aliased_resolve_path_str}_{schema_field}")
    current_alias = None
    current_alias_str = None
    current_alias_sql_schema = None

    if current_relation is None and schema["type"] in ("array", "object"):
        if db_field is None:
            raise SyntaxError("Cannot determine or synthesize current relation")

        # TODO: Additional conditions to check if it's actually JSON
        # TODO: HStore support?
        structure_type = search_database_properties.get("type")

        if structure_type in ("json", "jsonb"):
            # For drilling into Postgres JSON objects, we have to be a bit more clever about how we access/alias
            # the fields in question...
            if schema["type"] == "array":  # JSON(B) array or object
                # will be used to call either json_array_elements(...) or jsonb_array_elements(...):
                relation_sql_template = "{structure_type}_array_elements({field})"
                current_alias = sql.Identifier(new_aliased_resolve_path)
                current_alias_str = new_aliased_resolve_path
            else:  # object
                # will be used to call either json_to_record(...) or jsonb_to_record(...):
                relation_sql_template = "{structure_type}_to_record({field})"
                current_alias, current_alias_str, current_alias_sql_schema = json_schema_to_postgres_schema(
                    new_aliased_resolve_path, schema, structure_type
                )

            current_relation = sql.SQL(relation_sql_template).format(
                structure_type=sql.SQL(structure_type),  # json or jsonb here
                field=sql.SQL(".").join(
                    # TODO: Write comment about logic here - array vs obj
                    (parent_relation[1], sql.Identifier(db_field)) if db_field != "[item]" else (parent_relation[1],)
                ),
            )

        elif structure_type == "array" and schema["type"] == "array":  # Postgres array
            # TODO: document what unnest is up to
            current_relation = sql.SQL("unnest({relation}.{field})").format(
                relation=parent_relation[1],
                field=sql.Identifier(db_field),
            )
            current_alias = sql.Identifier(new_aliased_resolve_path)
            current_alias_str = new_aliased_resolve_path

        else:
            raise ValueError(
                f"Structure type / schema type mismatch: {structure_type} / {schema['type']}\n"
                f"    Search properties: {search_properties}\n"
                f"    Search database properties: {search_database_properties}\n"
                f"    Aliased resolve path: {new_aliased_resolve_path}"
            )

    elif current_relation is not None:
        current_relation = sql.Identifier(current_relation)
        current_alias = sql.Identifier(new_aliased_resolve_path)
        current_alias_str = new_aliased_resolve_path

    relations = OptionalComposablePair(parent_relation[0] if parent_relation is not None else None, current_relation)

    # Parent, Current
    aliases = OptionalComposablePair(
        parent=sql.Identifier(aliased_resolve_path) if aliased_resolve_path is not None else None, current=current_alias
    )

    key_link = None
    if "relationship" in search_database_properties:
        relationship = search_database_properties["relationship"]
        relationship_type = relationship["type"]
        # TODO: py3.10: match
        if relationship_type == "MANY_TO_ONE":
            # For a many-to-one relationship, the outer/higher element in the nesting has the foreign key,
            # so that many outer elements can map to the same inner element.
            key_link = (relationship["foreign_key"], search_database_properties["primary_key"])
        elif relationship_type == "ONE_TO_MANY":
            # For a one-to-many relationship, the inner/nested element in the relationship has the foreign key,
            # so that many inner elements can map to the same outer element.
            key_link = (relationship["parent_primary_key"], relationship["parent_foreign_key"])
        else:
            raise SyntaxError(f"Invalid relationship type: {relationship_type}")

    join_table_data = JoinAndSelectData(
        relations=relations,
        aliases=aliases,
        current_alias_str=current_alias_str,
        current_alias_sql_schema=current_alias_sql_schema,
        key_link=key_link,
        field_alias=db_field,
        search_properties=search_properties,
        unresolved=resolve[1:],
    )

    if len(resolve) == 1:
        # We're at the end of the resolve list - this is the last part of the 'drill-down' for the field
        return (join_table_data,)  # Return single tuple of relation

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
            raise ValueError(f"Property {resolve[1]} not found in object")

    return (join_table_data,) + collect_resolve_join_tables(
        resolve=resolve[1:],
        schema=schema["items"] if schema["type"] == "array" else schema["properties"][resolve[1].value],
        parent_relation=(relations.current, aliases.current),
        aliased_resolve_path=new_aliased_resolve_path if current_relation is not None else None,
    )


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
    """
    When we query using our Bento search syntax, we don't have a concept of 'tables' in the relational DB sense.
    So, when we build the SELECT ... FROM ... WHERE query, we need to join a bunch of tables together, as specified
    in the search schema. This function builds that X JOIN Y JOIN Z ... fragment for the final select query.
    :param ast: The AST representation of the query being executed.
    :param schema: The JSON schema + extra Bento search properties for
    :return: The SQL fragment with all the aliased joins.
    """

    terms = collect_join_tables(ast, (), schema)
    if not terms:  # Query was probably just a literal
        # TODO: Don't hard-code _root?
        search_database_properties = _get_search_and_database_properties(schema)[1]
        relation = search_database_properties.get("relation")
        return sql.SQL("{r1} AS {a1}").format(
            r1=sql.Identifier(relation) if relation else sql.SQL("(SELECT NULL)"), a1=SQL_ROOT
        )

    return sql.SQL(
        ", "
    ).join(
        (
            # Alias each table/relation to a re-usable name, joining the relations on their linked keys
            # specified in the search schema.
            # First, join any relation pairs which are connected together via foreign keys
            # (e.g., nested objects stored in their own relations).
            # If there is just 1 entry in terms, no join will occur, and it'll just be set to its alias.
            sql.SQL(" LEFT JOIN ").join(
                (
                    sql.SQL("{r1} AS {a1}{s1}").format(
                        r1=terms[0].relations.current,
                        a1=terms[0].aliases.current,
                        s1=terms[0].current_alias_sql_schema or SQL_NOTHING,
                    ),
                    *(
                        sql.SQL("{r1} AS {a1}{s1} ON {a0}.{f0} = {a1}.{f1}").format(
                            r1=term.relations.current,
                            a0=term.aliases.parent,
                            a1=term.aliases.current,
                            f0=sql.Identifier(term.key_link[0]),
                            f1=sql.Identifier(term.key_link[1]),
                            s1=term.current_alias_sql_schema or SQL_NOTHING,
                        )
                        for term in terms[1:]
                        if term.key_link is not None
                    ),  # Exclude terms without key-links - they will be selected separately below
                )
            ),
            # Then, include any additional (non-terms[0]) non-joined relations.
            *(
                sql.SQL("{r1} AS {a1}{s1}").format(
                    r1=term.relations.current,
                    a1=term.aliases.current,
                    s1=term.current_alias_sql_schema or SQL_NOTHING,
                )
                for term in terms[1:]
                if term.key_link is None and term.relations.current is not None
            ),
        )
    )


def search_ast_to_psycopg2_expr(
    ast: q.AST, params: tuple, schema: JSONSchema, internal: bool = False
) -> SQLComposableWithParams:
    if isinstance(ast, q.Literal):
        return sql.Placeholder(), (*params, ast.value)

    # Before doing anything, check that the permissions are correct given the AST and the search schema.
    #  TODO: use OIDC to maybe dynamically inject permissions/access levels somehow - either into schema or as a param
    q.check_operation_permissions(ast, schema, search_getter=get_search_properties, internal=internal)

    # Begin recursively constructing the SQL expression, starting with the top-most expression in our query
    return POSTGRES_SEARCH_LANGUAGE_FUNCTIONS[ast.fn](ast.args, params, schema, internal)


def search_query_to_psycopg2_sql(query, schema: JSONSchema, internal: bool = False) -> SQLComposableWithParams:
    # TODO: Shift recursion to not have to add in the extra SELECT for the root?
    ast = q.convert_query_to_ast_and_preprocess(query)
    sql_obj, params = search_ast_to_psycopg2_expr(ast, (), schema, internal)
    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    return sql.SQL("SELECT {root}.* FROM {relations_with_joins} WHERE {query_expr}").format(
        root=SQL_ROOT, relations_with_joins=join_fragment(ast, schema), query_expr=sql_obj
    ), params


def uncurried_binary_op(
    op: str, args: q.Args, params: tuple, schema: JSONSchema, internal: bool = False
) -> SQLComposableWithParams:
    # TODO: Need to fix params!! Use named params
    lhs_sql, lhs_params = search_ast_to_psycopg2_expr(args[0], params, schema, internal)
    rhs_sql, rhs_params = search_ast_to_psycopg2_expr(args[1], params, schema, internal)
    return (
        sql.SQL("({lhs}) {op} ({rhs})").format(lhs=lhs_sql, op=sql.SQL(op), rhs=rhs_sql),
        params + lhs_params + rhs_params,  # Collect all params together from elsewhere + both sides of the expression
    )


def _binary_op(op) -> Callable[[q.Args, tuple, JSONSchema, bool], SQLComposableWithParams]:
    return lambda args, params, schema, internal: uncurried_binary_op(op, args, params, schema, internal)


def _in(args: q.Args, params: tuple, schema: JSONSchema, internal: bool = False) -> SQLComposableWithParams:
    lhs_sql, lhs_params = search_ast_to_psycopg2_expr(args[0], params, schema, internal)
    rhs_sql, rhs_params = search_ast_to_psycopg2_expr(args[1], params, schema, internal)
    return sql.SQL("({lhs}) IN {rhs}").format(lhs=lhs_sql, rhs=rhs_sql), params + lhs_params + rhs_params


def _not(args: q.Args, params: tuple, schema: JSONSchema, internal: bool = False) -> SQLComposableWithParams:
    child_sql, child_params = search_ast_to_psycopg2_expr(args[0], params, schema, internal)
    return sql.SQL("NOT ({child})").format(child=child_sql), params + child_params


def _like_op(op: str) -> Callable[[Tuple[q.AST, q.AST], tuple, JSONSchema, bool], SQLComposableWithParams]:
    def inner(
        args: Tuple[q.AST, q.AST], params: tuple, schema: JSONSchema, internal: bool = False
    ) -> SQLComposableWithParams:
        lhs_sql, lhs_params = search_ast_to_psycopg2_expr(args[0], params, schema, internal)
        rhs_sql, rhs_params = search_ast_to_psycopg2_expr(args[1], params, schema, internal)

        return (
            sql.SQL("{lhs} {op} {rhs}").format(lhs=lhs_sql, op=sql.SQL(op), rhs=rhs_sql),
            params + lhs_params + rhs_params,
        )

    return inner


# TODO rename the function ?
def _contains(
    op: str, wc_loc: str, args: q.Args, params: tuple, schema: JSONSchema, internal: bool = False
) -> SQLComposableWithParams:
    return _like_op(op)(
        (args[0], q.Expression(fn=q.FUNCTION_HELPER_WC, args=[args[1], q.Literal(wc_loc)])), params, schema, internal
    )


def _contains_op(op: str) -> Callable[[q.Args, tuple, JSONSchema, bool], SQLComposableWithParams]:
    def _inner(*args):
        return _contains(op, "anywhere", *args)

    return _inner


_i_starts_with = functools.partial(_contains, "ILIKE", "start")
_i_ends_with = functools.partial(_contains, "ILIKE", "end")


def _wildcard(
    args: Tuple[q.AST, q.AST], params: tuple, _schema: JSONSchema, _internal: bool = False
) -> SQLComposableWithParams:
    if isinstance(args[0], q.Expression):
        raise NotImplementedError(f"Cannot currently use {q.FUNCTION_HELPER_WC} on an expression")  # TODO

    # TODO: py3.10: match
    if args[1].value == "start":
        wcs = "{}%"
    elif args[1].value == "end":
        wcs = "%{}"
    else:  # anywhere
        wcs = "%{}%"

    try:
        return sql.Placeholder(), (*params, wcs.format(args[0].value.replace("%", r"\%").replace("_", r"\_")))
    except AttributeError:
        # Can happen with non-string argument to #_wc, which will throw on .replace(...)
        raise TypeError(f"Type-invalid use of function {q.FUNCTION_HELPER_WC}")


def get_relation(resolve: Tuple[q.Literal, ...], schema: JSONSchema):
    aliases = collect_resolve_join_tables((QUERY_ROOT, *resolve), schema)[-1].aliases
    return aliases.current if aliases.current is not None else aliases.parent


def get_field(resolve: Tuple[q.Literal, ...], schema: JSONSchema) -> Optional[str]:
    return collect_resolve_join_tables((QUERY_ROOT, *resolve), schema)[-1].field_alias


def get_search_properties(resolve: Tuple[q.Literal, ...], schema: JSONSchema) -> dict:
    return collect_resolve_join_tables((QUERY_ROOT, *resolve), schema)[-1].search_properties


def _resolve(args: q.Args, params: tuple, schema: JSONSchema, _internal: bool = False) -> SQLComposableWithParams:
    """
    Compiles arguments for a #resolve call (an operation which accesses a field on a Bento searchable object)
    into SQL.
    :param args: Arguments representing the path to the field being resolved.
    :param params: Any existing SQL parameters (i.e, values to insert into the SQL without introducing injections).
    :param schema: The schema for the Bento searchable object.
    :param _internal: (unused here) whether we are querying from a global-access context, or a permissioned one.
    :return: A tuple of the SQL representation for the field access, and the params tuple (unchanged here).
    """
    f_id = get_field(args, schema)
    return sql.SQL("{relation}.{field}").format(
        relation=get_relation(args, schema), field=sql.Identifier(f_id) if f_id is not None else sql.SQL("*")
    ), params


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


POSTGRES_SEARCH_LANGUAGE_FUNCTIONS: Dict[str, Callable[[q.Args, tuple, JSONSchema, bool], SQLComposableWithParams]] = {
    q.FUNCTION_AND: _binary_op("AND"),
    q.FUNCTION_OR: _binary_op("OR"),
    q.FUNCTION_NOT: _not,
    # -------------------------------------------
    q.FUNCTION_LT: _binary_op("<"),
    q.FUNCTION_LE: _binary_op("<="),
    q.FUNCTION_EQ: _binary_op("="),
    q.FUNCTION_GT: _binary_op(">"),
    q.FUNCTION_GE: _binary_op(">="),
    q.FUNCTION_IN: _in,
    # -------------------------------------------
    q.FUNCTION_CO: _contains_op("LIKE"),
    q.FUNCTION_ICO: _contains_op("ILIKE"),
    # -------------------------------------------
    q.FUNCTION_ISW: _i_starts_with,
    q.FUNCTION_IEW: _i_ends_with,
    q.FUNCTION_LIKE: _like_op("LIKE"),
    q.FUNCTION_ILIKE: _like_op("ILIKE"),
    # -------------------------------------------
    q.FUNCTION_RESOLVE: _resolve,
    q.FUNCTION_LIST: _list,
    # -------------------------------------------
    q.FUNCTION_HELPER_WC: _wildcard,
}
