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
                                            "child_key": "code_id"
                                        }
                                    }
                                }
                            }
                        },
                        "search": {
                            "relation": "procedures",
                            "primary_key": "id",
                            "relationship": {
                                "type": "MANY_TO_ONE",
                                "child_key": "procedure_id"  # TODO: Wrong name?
                            }
                        }
                    }
                },
                "search": {
                    "database": {
                        "relation": "biosamples",
                        "primary_key": "biosample_id",
                        "relationship": {
                            "type": "MANY_TO_MANY",
                            "relation": "phenopacket_biosamples",
                            "parent_key": "phenopacket_id",
                            "child_key": "biosample_id"
                        }
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
                        "child_key": "subject_id"
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


class SearchSchema:
    def __init__(self, data, parent):
        self.data = data
        self.parent = parent

    def __getitem__(self, item):
        return self.data[item]

    def __contains__(self, item):
        return item in self.data

    def __str__(self):
        return "SearchSchema"

    def __repr__(self):
        return "<SearchSchema>"


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

    print(ast)

    if len(ast) == 0 or ast[0][0] != "#":
        raise SyntaxError("AST Error: Invalid Expression: {}".format(ast))

    fn = ast[0]
    args = ast[1:]

    return POSTGRES_SEARCH_LANGUAGE_FUNCTIONS[fn](args, params)


def _wildcard(args, params):
    if len(args) != 1:
        raise SyntaxError("Invalid number of arguments for #_wc")

    if isinstance(args[0], list):
        raise NotImplementedError("Cannot currently use #co on an expression")  # TODO

    return "%s", (*params, "%{}%".format(args[0]))


def _get_schema(path, schema, parent):
    if len(path) <= 1:
        return SearchSchema(schema, parent)
    elif schema["type"] == "array" and len(path) >= 2 and path[1] == "[item]":
        return _get_schema(path[2:], schema["items"], parent)
    else:
        return _get_schema(path[1:], schema["properties"][path[0]], schema)

    # TODO: More error states


def _resolve(args, params):
    if len(args) == 0:
        return "$root"
    elif args[-1] == "[item]":
        return ["#_item", _resolve(args[:-1], params), _get_schema(args, TEST_SCHEMA, None)]
    else:
        return ["#_prop", _resolve(args[:-1], params), args[-1], _get_schema(args, TEST_SCHEMA, None)]


# noinspection SqlDialectInspection,SqlNoDataSourceInspection
def _prop(args, params):  # TODO
    if len(args) != 3:
        raise SyntaxError("Invalid number of arguments for #_prop")

    obj, prop, schema = args
    # TODO: Prevent SQL injection on obj and prop explicitly instead of relying on schema

    print(prop)

    if not isinstance(prop, str):
        raise NotImplementedError("Cannot currently use expressions as property values")  # TODO

    if schema["type"] not in ("object", "array"):
        # TODO: This will break since it should not be %s parameterized
        return "{}.{}".format(search_ast_to_postgres(obj, params)[0], prop), params

    if schema["type"] == "object" and "search" in schema and "database" in schema["search"]:
        # Another table (presumably), possibly with a connector table

        tbl_name = schema["search"]["database"]["relation"]
        rel_type = schema["search"]["database"]["relationship"]["type"]
        primary_key = schema["search"]["database"]["primary_key"]
        c_key = schema["search"]["database"]["relationship"]["child_key"]

        parent = schema.parent
        if parent is None:
            # TODO
            return "", params

        parent_relation = parent["search"]["database"]["relation"]
        parent_primary_key = parent["search"]["database"]["primary_key"]

        if rel_type == "MANY_TO_ONE":
            return f"SELECT {prop} FROM {tbl_name} WHERE {parent_relation}.{c_key} = {tbl_name}.{primary_key}", params

        elif rel_type == "MANY_TO_MANY":
            mm_rel = schema["search"]["database"]["relationship"]["relation"]
            pc_key = schema["search"]["database"]["relationship"]["parent_key"]  # TODO: Rename these...

            # TODO: This is broken...

            return f"SELECT {prop} FROM {tbl_name} WHERE {tbl_name}.{primary_key} IN (" \
                   f"SELECT {mm_rel}.{c_key} FROM {mm_rel} " \
                   f"WHERE {mm_rel}.{pc_key} = {parent_relation}.{parent_primary_key})", params

        # TODO

    # TODO

    print(schema["type"], schema.data)

    return "", params


def _item(args, params):  # TODO
    return "", params


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

    "#resolve": lambda args, params: search_ast_to_postgres(_resolve(args, params), params),

    "#_prop": _prop,
    "#_item": _item,

    "#_wc": _wildcard
}


# [#resolve "$root" "hello"] -> [#_prop $root hello]


TEST_AST = [
    "#and",
    ["#co",
     ["#resolve", "biosamples", "procedure", "[item]", "label"],
     "biopsy"],
    ["#eq", ["#resolve", "subject", "karyotypic_sex"], "XO"]
]

# TEST_AST = [
#     "#and",
#     ["#co",
#      ["#_prop", ["#_prop", ["#_item", ["#_prop", "$root", "biosamples"]], "procedure"], "label"],
#      "biopsy"],
#     ["#eq", ["#_prop", ["#_prop", "$root", "individual"], "karyotypic_sex"], "XO"]
# ]

print(search_ast_to_postgres(TEST_AST, ())[0])
