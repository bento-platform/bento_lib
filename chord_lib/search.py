from datetime import datetime
from psycopg2 import sql
from typing import Callable, Dict, List, Tuple, Union

__all__ = ["SEARCH_OPERATIONS", "SQL_SEARCH_OPERATORS", "build_search_response"]


SEARCH_OPERATIONS = ("eq", "lt", "le", "gt", "ge", "co")
SQL_SEARCH_OPERATORS = {
    "eq": "=",
    "lt": "<",
    "le": "<=",
    "gt": ">",
    "ge": ">=",
    "co": "LIKE"
}


def build_search_response(results: Union[Dict, List, Tuple], start_time: datetime) -> Dict:
    return {
        "results": results,
        "time": (datetime.now() - start_time).total_seconds()
    }


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


def _binary_op(op) -> Callable[[list, tuple], Tuple[sql.Composable, tuple]]:
    # TODO: Sanitize op?
    # TODO: Need to fix params!! Use named params
    return lambda args, params: (
        sql.SQL("({}) " + op + " ({})").format(search_ast_to_postgres(args[0], params)[0],
                                               search_ast_to_postgres(args[1], params)[0]),
        params + search_ast_to_postgres(args[0], params)[1] + search_ast_to_postgres(args[1], params)[1]
    )


def _not(args: list, params: tuple) -> Tuple[sql.Composable, tuple]:
    return sql.SQL("NOT ({})").format(search_ast_to_postgres(args[0], params)[0]), \
           params + search_ast_to_postgres(args[0], params)[1]


def search_ast_to_postgres(ast: list, params: tuple) -> Tuple[sql.Composable, tuple]:
    if not isinstance(ast, list):
        return sql.Placeholder(), (*params, ast)

    if len(ast) == 0 or ast[0][0] != "#":
        raise SyntaxError("AST Error: Invalid Expression: {}".format(ast))

    fn = ast[0]
    args = ast[1:]

    return POSTGRES_SEARCH_LANGUAGE_FUNCTIONS[fn](args, params)


def _wildcard(args: list, params: tuple) -> Tuple[sql.Composable, tuple]:
    if len(args) != 1:
        raise SyntaxError("Invalid number of arguments for #_wc")

    if isinstance(args[0], list):
        raise NotImplementedError("Cannot currently use #co on an expression")  # TODO

    return sql.Placeholder(), (*params, "%{}%".format(args[0].replace("%", r"\%")))


def _get_relation(resolve: list):
    return _collect_resolve_join_tables(resolve, TEST_SCHEMA)[-1][1][1]  # TODO: Schema


def _resolve(args: list, params: tuple) -> Tuple[sql.Composable, tuple]:
    return sql.SQL("{}.{}").format(sql.Identifier(_get_relation(["$root"] + args)), sql.Identifier(args[-1])), params


def _collect_resolve_join_tables(resolve: list, schema, parent_relation=None, resolve_path=None) -> tuple:
    """
    Recursively collects tables to join for compiling the query.
    :param resolve: The current resolve list, minus the command. Starts with $root to keep schema proper.
    :param schema: The schema of the current element (first property.)
    :return: Tuple of tables with joining properties.
    """

    # Many to one: child_key -> primary_key
    # Many to many: primary_key -> parent_key (treat as just another through)

    if len(resolve) == 0 or schema["type"] not in ("array", "object"):
        return ()

    relations = (
        parent_relation[0] if parent_relation is not None else None,
        schema["search"]["database"]["relation"] if "search" in schema and "database" in schema["search"] else None
    )
    aliases = (
        resolve_path if resolve_path is not None else None,
        "{}_{}".format(resolve_path if resolve_path is not None else "",
                       resolve[0]).replace("$", "").replace("[", "").replace("]", "")
    )
    key_link = None,

    if "search" in schema and "database" in schema["search"] and "relationship" in schema["search"]["database"]:
        rel_type = schema["search"]["database"]["relationship"]["type"]
        if rel_type == "MANY_TO_ONE":
            key_link = (schema["search"]["database"]["relationship"]["foreign_key"],
                        schema["search"]["database"]["primary_key"])
        elif rel_type == "MANY_TO_MANY":
            key_link = (schema["search"]["database"]["relationship"]["parent_primary_key"],
                        schema["search"]["database"]["relationship"]["parent_foreign_key"])

        # TODO: ONE TO MANY

    join_table_data = (relations, aliases, key_link)

    if schema["type"] == "array":
        if len(resolve) == 1:  # End result is array
            return join_table_data,  # Return single tuple of relation

        elif resolve[1] != "[item]":
            raise SyntaxError("Cannot get property of array in #resolve")

        else:
            return (join_table_data,) + _collect_resolve_join_tables(resolve[1:], schema["items"],
                                                                                    (relations[1], aliases[1]),
                                                                                    aliases[1])

    elif schema["type"] == "object":
        if len(resolve) == 1:
            return join_table_data,

        return (join_table_data,) + _collect_resolve_join_tables(resolve[1:], schema["properties"][resolve[1]],
                                                                 (relations[1], aliases[1]), aliases[1])


def _collect_join_tables(ast, terms: tuple):
    if not isinstance(ast, list):
        return terms

    if ast[0] == "#resolve":
        return terms + tuple(t for t in _collect_resolve_join_tables(["$root"] + ast[1:], TEST_SCHEMA)
                             if t not in terms)  # TODO: Schema

    new_terms = terms

    for item in ast:
        if isinstance(item, list):
            new_terms = _collect_join_tables(item, new_terms)

    return new_terms


def join_fragment(ast) -> sql.Composable:
    terms = _collect_join_tables(ast, ())
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


POSTGRES_SEARCH_LANGUAGE_FUNCTIONS: Dict[str, Callable[[list, tuple], Tuple[sql.Composable, tuple]]] = {
    "#and": _binary_op("AND"),
    "#or": _binary_op("OR"),
    "#not": _not,

    "#lt": _binary_op("<"),
    "#le": _binary_op("<="),
    "#eq": _binary_op("="),
    "#gt": _binary_op(">"),
    "#ge": _binary_op(">="),

    "#co": lambda args, params: (sql.SQL("({}) LIKE ({})").format(
        search_ast_to_postgres(args[0], params)[0], search_ast_to_postgres(["#_wc", args[1]], params)[0]),
                                 params + search_ast_to_postgres(args[0], params)[1] +
                                 search_ast_to_postgres(["#_wc", args[1]], params)[1]),

    "#resolve": _resolve,

    "#_wc": _wildcard
}


TEST_AST = [
    "#and",
    ["#co",
     ["#resolve", "biosamples", "[item]", "procedure", "code", "label"],
     "biopsy"],
    ["#eq", ["#resolve", "subject", "karyotypic_sex"], "XO"]
]

# from psycopg2 import connect
# conn = connect("dbname=metadata user=admin password=admin host=127.0.0.1 port=5432")
#
# # noinspection SqlDialectInspection,SqlNoDataSourceInspection
# print(sql.SQL("SELECT * FROM {} WHERE {}")
#       .format(join_fragment(TEST_AST), search_ast_to_postgres(TEST_AST, ())[0])
#       .as_string(conn))
