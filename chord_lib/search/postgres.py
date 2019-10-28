import re

from psycopg2 import sql
from typing import Callable, Dict, Optional, Tuple

# Search Rules:
#  - If an object or query doesn't match the schema, it's an error.
#  - If an optional property isn't present, it's "False".


__all__ = ["search_ast_to_psycopg2_sql"]


TEST_SCHEMA = {
    "type": "object",
    "properties": {
        "biosamples": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "procedure": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "label": {"type": "string"}
                                },
                                "search": {
                                    "database": {
                                        "relation": "patients_ontology",
                                        "primary_key": "id",
                                        "relationship": {
                                            "type": "MANY_TO_ONE",
                                            "foreign_key": "code_id"
                                        }
                                    }
                                }
                            }
                        },
                        "search": {
                            "database": {
                                "relation": "patients_procedure",
                                "primary_key": "id",
                                "relationship": {
                                    "type": "MANY_TO_ONE",
                                    "foreign_key": "procedure_id"  # TODO: Wrong name?
                                }
                            }
                        }
                    }
                },
                "search": {
                    "database": {
                        "relation": "patients_biosample",
                        "primary_key": "biosample_id",
                        "relationship": {
                            "type": "MANY_TO_ONE",
                            "foreign_key": "biosample_id"  # M2M child key
                        }
                    }
                }
            },
            "search": {
                "database": {
                    "relation": "patients_phenopacket_biosamples",
                    "relationship": {
                        "type": "MANY_TO_MANY",
                        "parent_foreign_key": "phenopacket_id",
                        "parent_primary_key": "phenopacket_id"
                    }
                }
            }
        },
        "subject": {
            "type": "object",
            "properties": {
                "karyotypic_sex": {"type": "string", "search": {}}
            },
            "search": {
                "database": {
                    "relation": "patients_individual",
                    "primary_key": "individual_id",
                    "relationship": {
                        "type": "MANY_TO_ONE",
                        "foreign_key": "subject_id"
                    }
                }
            }
        }
        # TODO: Metadata (one-to-one) example
    },
    "search": {
        "database": {
            "relation": "patients_phenopacket",
            "primary_key": "phenopacket_id"
        }
    }
}


TEST_AST = [
    "#and",
    ["#co",
     ["#resolve", "biosamples", "[item]", "procedure", "code", "label"],
     "biopsy"],
    ["#eq", ["#resolve", "subject", "karyotypic_sex"], "XO"]
]


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

    if len(resolve) == 0 or schema["type"] not in ("array", "object"):
        return ()

    relations = (parent_relation[0] if parent_relation is not None else None,
                 schema.get("search", {}).get("database", {}).get("relation", None))
    aliases = (resolve_path if resolve_path is not None else None,
               re.sub(r"[$\[\]]+", "", "{}_{}".format(resolve_path if resolve_path is not None else "", resolve[0])))
    key_link = None

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

    join_table_data = (relations, aliases, key_link)

    if schema["type"] == "array":
        if len(resolve) == 1:  # End result is array
            return join_table_data,  # Return single tuple of relation

        elif resolve[1] != "[item]":
            raise SyntaxError("Cannot get property of array in #resolve")

        else:
            return (join_table_data,) + collect_resolve_join_tables(resolve[1:], schema["items"],
                                                                    (relations[1], aliases[1]), aliases[1])

    elif schema["type"] == "object":
        if len(resolve) == 1:
            return join_table_data,

        return (join_table_data,) + collect_resolve_join_tables(resolve[1:], schema["properties"][resolve[1]],
                                                                (relations[1], aliases[1]), aliases[1])


def collect_join_tables(ast, terms: tuple, schema: dict):
    if not isinstance(ast, list):
        return terms

    if ast[0] == "#resolve":
        return terms + tuple(t for t in collect_resolve_join_tables(["$root"] + ast[1:], schema) if t not in terms)

    new_terms = terms

    for item in ast:
        if isinstance(item, list):
            new_terms = collect_join_tables(item, new_terms, schema)

    return new_terms


def join_fragment(ast, schema: dict) -> sql.Composable:
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
        ) for term in terms[1:]]
    )


def search_ast_to_psycopg2_expr(ast: list, params: tuple, schema: dict) -> Tuple[sql.Composable, tuple]:
    if isinstance(ast, dict):  # Error: dict has no meaning yet
        raise NotImplementedError("Cannot use objects as literals")

    if not isinstance(ast, list):
        # Literal (string/number/boolean)
        return sql.Placeholder(), (*params, ast)

    if len(ast) == 0 or ast[0][0] != "#":
        raise SyntaxError("AST Error: Invalid Expression: {}".format(ast))

    fn = ast[0]
    args = ast[1:]

    return POSTGRES_SEARCH_LANGUAGE_FUNCTIONS[fn](args, params, schema)


def search_ast_to_psycopg2_sql(ast, schema: dict, connection) -> Tuple[sql.Composable, tuple]:
    # TODO: Shift recursion to not have to add in the extra SELECT for the root?
    sql_obj, params = search_ast_to_psycopg2_expr(ast, (), schema)
    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    return (sql.SQL("SELECT * FROM {} WHERE {}").format(join_fragment(ast, schema), sql_obj).as_string(connection),
            params)


def uncurried_binary_op(op, args, params, schema):
    # TODO: Need to fix params!! Use named params
    lhs_sql, lhs_params = search_ast_to_psycopg2_expr(args[0], params, schema)
    rhs_sql, rhs_params = search_ast_to_psycopg2_expr(args[1], params, schema)
    return sql.SQL("({}) {} ({})").format(lhs_sql, sql.SQL(op), rhs_sql), params + lhs_params + rhs_params


def _binary_op(op) -> Callable[[list, tuple, dict], Tuple[sql.Composable, tuple]]:
    return lambda args, params, schema: uncurried_binary_op(op, args, params, schema)


def _not(args: list, params: tuple, schema: dict) -> Tuple[sql.Composable, tuple]:
    child_sql, child_params = search_ast_to_psycopg2_expr(args[0], params, schema)
    return sql.SQL("NOT ({})").format(child_sql), params + child_params


def _wildcard(args: list, params: tuple, _schema: dict) -> Tuple[sql.Composable, tuple]:
    if len(args) != 1:
        raise SyntaxError("Invalid number of arguments for #_wc")

    if isinstance(args[0], list):
        raise NotImplementedError("Cannot currently use #co on an expression")  # TODO

    return sql.Placeholder(), (*params, "%{}%".format(args[0].replace("%", r"\%")))


def get_relation(resolve: list, schema: dict):
    return collect_resolve_join_tables(resolve, schema)[-1][1][1]  # TODO: Schema


def _resolve(args: list, params: tuple, schema: dict) -> Tuple[sql.Composable, tuple]:
    return sql.SQL("{}.{}").format(sql.Identifier(get_relation(["$root"] + args, schema)),
                                   sql.Identifier(args[-1])), params


def _contains(args, params, schema):
    lhs_sql, lhs_params = search_ast_to_psycopg2_expr(args[0], params, schema)
    rhs_sql, rhs_params = search_ast_to_psycopg2_expr(["#_wc", args[1]], params, schema)
    return sql.SQL("({}) LIKE ({})").format(lhs_sql, rhs_sql), params + lhs_params + rhs_params


POSTGRES_SEARCH_LANGUAGE_FUNCTIONS: Dict[str, Callable[[list, tuple, dict], Tuple[sql.Composable, tuple]]] = {
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

# from psycopg2 import connect
# conn = connect("dbname=metadata user=admin password=admin host=127.0.0.1 port=5432")
#
# print(search_ast_to_psycopg2_sql(TEST_AST, TEST_SCHEMA, conn))
