from datetime import datetime
from typing import Dict, List, Tuple, Union

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
                                        "relation": "ontologies",
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
                                "relation": "procedures",
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
                        "relation": "biosamples",
                        "primary_key": "biosample_id",
                        "relationship": {
                            "type": "MANY_TO_ONE",
                            "relation": "phenopacket_biosamples",
                            "foreign_key": "biosample_id"  # M2M child key
                        }
                    }
                }
            },
            "search": {
                "database": {
                    "relation": "phenopacket_biosamples",
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
                    "relation": "individuals",
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
            "relation": "phenopackets",
            "primary_key": "phenopacket_id"
        }
    }
}


def _binary_op(op):
    return lambda args, params: (
        "({}) {} ({})".format(search_ast_to_postgres(args[0], params)[0], op,
                              search_ast_to_postgres(args[1], params)[0]),
        params
    )


def _not(args, params):
    return "NOT ({})".format(search_ast_to_postgres(args[0], params)[0]), params


def search_ast_to_postgres(ast, params):
    if not isinstance(ast, list):
        return "%s", (*params, ast)

    print("AST:", ast)

    if len(ast) == 0 or ast[0][0] != "#":
        raise SyntaxError("AST Error: Invalid Expression: {}".format(ast))

    fn = ast[0]
    args = ast[1:]

    # TODO: Somehow need to push down array access

    return POSTGRES_SEARCH_LANGUAGE_FUNCTIONS[fn](args, params)


def _wildcard(args, params):
    if len(args) != 1:
        raise SyntaxError("Invalid number of arguments for #_wc")

    if isinstance(args[0], list):
        raise NotImplementedError("Cannot currently use #co on an expression")  # TODO

    return "%s", (*params, "%{}%".format(args[0]))


def _get_relation(resolve):
    return _collect_resolve_join_tables(resolve, TEST_SCHEMA)[-1][0][1]  # TODO: Schema


def _resolve(args, params):
    return "{}.{}".format(_get_relation(["$root"] + args), args[-1]), params


def _collect_resolve_join_tables(resolve, schema, parent_relation=None) -> tuple:
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

    relations = ((parent_relation, schema["search"]["database"]["relation"]
                  if "search" in schema and "database" in schema["search"] else None))
    key_link = None

    if "search" in schema and "database" in schema["search"] and "relationship" in schema["search"]["database"]:
        rel_type = schema["search"]["database"]["relationship"]["type"]
        if rel_type == "MANY_TO_ONE":
            key_link = (schema["search"]["database"]["relationship"]["foreign_key"],
                        schema["search"]["database"]["primary_key"])
        elif rel_type == "MANY_TO_MANY":
            key_link = (schema["search"]["database"]["relationship"]["parent_primary_key"],
                        schema["search"]["database"]["relationship"]["parent_foreign_key"])

    if schema["type"] == "array":
        if len(resolve) == 1:  # End result is array
            return (relations, key_link),  # Return single tuple of relation

        elif resolve[1] != "[item]":
            # print(resolve)
            raise SyntaxError("Cannot get property of array in #resolve")

        else:
            return ((relations, key_link),) + _collect_resolve_join_tables(resolve[1:], schema["items"], relations[1])

    elif schema["type"] == "object":
        if len(resolve) == 1:
            return (relations, key_link),

        return ((relations, key_link),) + _collect_resolve_join_tables(resolve[1:], schema["properties"][resolve[1]],
                                                                       relations[1])


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


def join_fragment(ast):
    terms = _collect_join_tables(ast, ())
    if len(terms) == 0:
        return ""

    fragment = terms[0][0][1]

    for term in terms[1:]:
        # TODO: Sanitize
        # TODO: Need to rename queries, maybe use sub-queries with joins
        # TODO: Need to make sure ex. ontologies can be used in different situations
        fragment += " LEFT JOIN {} ON {}.{} = {}.{}".format(term[0][1], term[0][0], term[1][0], term[0][1], term[1][1])

    return fragment


POSTGRES_SEARCH_LANGUAGE_FUNCTIONS = {
    "#and": _binary_op("AND"),
    "#or": _binary_op("OR"),
    "#not": _not,

    "#lt": _binary_op("<"),
    "#le": _binary_op("<="),
    "#eq": _binary_op("="),
    "#gt": _binary_op(">"),
    "#ge": _binary_op(">="),

    "#co": lambda args, params: ("({}) LIKE ({})".format(search_ast_to_postgres(args[0], params)[0],
                                                         search_ast_to_postgres(["#_wc", args[1]], params)[0]), params),

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

# noinspection SqlDialectInspection,SqlNoDataSourceInspection
print("SELECT * FROM {} WHERE {}".format(join_fragment(TEST_AST), search_ast_to_postgres(TEST_AST, ())[0]))
