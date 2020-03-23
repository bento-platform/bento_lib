from chord_lib.search import build_search_response, data_structure, operations, postgres, queries
from datetime import datetime
from pytest import raises


NUMBER_SEARCH = {
    "operations": [
        operations.SEARCH_OP_LT,
        operations.SEARCH_OP_LE,
        operations.SEARCH_OP_GT,
        operations.SEARCH_OP_GE,
        operations.SEARCH_OP_EQ,
    ],
    "queryable": "all"
}

JSONB_DB_SEARCH = {
    "database": {
        "type": "jsonb"
    }
}


TEST_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {
            "type": "string",
            "search": {
                "operations": [operations.SEARCH_OP_EQ],
                "queryable": "internal",
                "database": {"field": "phenopacket_id"}
            }
        },
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
                                    "id": {
                                        "type": "string",
                                        "search": {
                                            "operations": [operations.SEARCH_OP_CO],
                                            "queryable": "all"
                                        }
                                    },
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
                    },
                    "tumor_grade": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "search": {
                                        "operations": [operations.SEARCH_OP_EQ],
                                        "queryable": "all"
                                    }
                                },
                                "label": {"type": "string"}
                            },
                            "search": {
                                "database": {
                                    "relation": "patients_ontology",
                                    "primary_key": "id",   # Ontology primary key
                                    "relationship": {
                                        "type": "MANY_TO_ONE",
                                        "foreign_key": "code_id"  # M2M child key
                                    }
                                }
                            }
                        },
                        "search": {
                            "database": {
                                "relation": "patients_biosample_tumor_grades",
                                "relationship": {
                                    "type": "ONE_TO_MANY",
                                    "parent_foreign_key": "biosample_id",
                                    "parent_primary_key": "biosample_id"
                                }
                            }
                        }
                    },

                    # lazy
                    "test_postgres_array": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "test": {
                                    "type": "string",
                                    "search": {
                                        "operations": [operations.SEARCH_OP_EQ],
                                        "queryable": "all"
                                    }
                                }
                            },
                            "search": {
                                "database": {
                                    "type": "json"
                                }
                            }
                        },
                        "search": {
                            "database": {
                                "type": "array"
                            }
                        }
                    },

                    # lazy
                    "test_json_array": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "test": {
                                    "type": "string",
                                    "search": {
                                        "operations": [operations.SEARCH_OP_EQ],
                                        "queryable": "all"
                                    }
                                }
                            },
                            "search": {
                                "database": {
                                    "type": "json"
                                }
                            }
                        },
                        "search": {
                            "database": {
                                "type": "json"
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
                "queryable": "all",
                "database": {
                    "relation": "patients_phenopacket_biosamples",
                    "relationship": {
                        "type": "ONE_TO_MANY",
                        "parent_foreign_key": "phenopacket_id",
                        "parent_primary_key": "phenopacket_id"
                    }
                }
            }
        },
        "subject": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "search": {
                        "operations": [operations.SEARCH_OP_EQ],
                        "queryable": "internal"
                    }
                },
                "karyotypic_sex": {
                    "type": "string",
                    "search": {
                        "operations": [operations.SEARCH_OP_EQ],
                        "queryable": "all"
                    }
                },
                "sex": {
                    "type": "string",
                    "enum": ["UNKNOWN_SEX", "FEMALE", "MALE", "OTHER_SEX"],
                    "search": {
                        "operations": [operations.SEARCH_OP_EQ],
                        "queryable": "all"
                    }
                },
                "taxonomy": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "search": {
                                "operations": [operations.SEARCH_OP_EQ],
                                "queryable": "all"
                            }
                        },
                        "label": {"type": "string"}
                    },
                    "required": ["id", "label"],
                    "search": JSONB_DB_SEARCH
                }
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
        },
        "test_op_1": {
            "type": "array",
            "items": {
                "type": "number",
                "search": NUMBER_SEARCH,
            },
            "search": JSONB_DB_SEARCH
        },
        "test_op_2": {
            "type": "array",
            "items": {
                "type": "number",
                "search": NUMBER_SEARCH,
            },
            "search": JSONB_DB_SEARCH
        },
        "test_op_3": {
            "type": "array",
            "items": {
                "type": "array",
                "items": {
                    "type": "number",
                    "search": NUMBER_SEARCH
                },
                "search": JSONB_DB_SEARCH
            },
            "search": JSONB_DB_SEARCH
        },
        # TODO: Metadata (one-to-one) example
    },
    "search": {
        "operations": [],
        "queryable": "all",
        "database": {
            "relation": "patients_phenopacket",
            "primary_key": "phenopacket_id"
        }
    }
}

TEST_SCHEMA_2_DATA_TYPE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {
            "type": "string",
            "search": {
                "operations": [operations.SEARCH_OP_EQ],
                "queryable": "all"
            }
        },
        "children": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "search": {
                            "operations": [operations.SEARCH_OP_EQ],
                            "queryable": "all"
                        }
                    },
                    "prop": {
                        "type": "string",
                        "search": {
                            "operations": [operations.SEARCH_OP_EQ],
                            "queryable": "all"
                        }
                    }
                }
            }
        }
    }
}

TEST_SCHEMA_2 = {
    "type": "object",
    "properties": {
        "data_type_1": {
            "type": "array",
            "items": TEST_SCHEMA_2_DATA_TYPE_SCHEMA
        },
        "data_type_2": {
            "type": "array",
            "items": TEST_SCHEMA_2_DATA_TYPE_SCHEMA
        }
    }
}


# TODO: Postgres module should validate instead of throwing errors...
TEST_INVALID_SCHEMA = {
    "type": "object",
    "properties": {
        "biosamples": {
            "type": "array",
            "items": {
                "type": "object"
            },
            "search": {
                "database": {
                    "relation": "patients_phenopacket_biosamples",
                    "relationship": {
                        "type": "INVALID_RELATION_TYPE",
                        "parent_foreign_key": "phenopacket_id",
                        "parent_primary_key": "phenopacket_id"
                    }
                }
            }
        },
        "subject": {
            "type": "object",
            "search": {
                "database": {
                    "relation": "patients_individual"
                }
            }
        },
        "bad_array": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "search": {
        "database": {
            "relation": "patients_phenopacket",
            "primary_key": "phenopacket_id"
        }
    }
}

TEST_INVALID_SCHEMA_2 = {
    "type": "array",
    "items": {
        "type": "string"
    }
}


TEST_FUNCTIONS = (
    [queries.FUNCTION_AND, True, False],
    [queries.FUNCTION_OR, False, True],
    [queries.FUNCTION_NOT, False],
    [queries.FUNCTION_LT, 5, 6],
    [queries.FUNCTION_LE, 5, 6],
    [queries.FUNCTION_EQ, 5, 6],
    [queries.FUNCTION_GT, 5, 6],
    [queries.FUNCTION_GE, 5, 6],
    [queries.FUNCTION_CO, "hello", "h"],
    [queries.FUNCTION_RESOLVE, "biosamples", "[item]", "procedure", "code", "id"],
)

TEST_INVALID_FUNCTIONS = (
    ["eq", 5, 6],
    ["#bad", 6, 7]
)

TEST_INVALID_EXPRESSION_SYNTAX = (
    [],
    [5, 6],
    [True, False],
    [queries.FUNCTION_AND, True],
    [queries.FUNCTION_OR, True],
    [queries.FUNCTION_NOT, True, False],
    [queries.FUNCTION_LT, 5],
    [queries.FUNCTION_LE, 5],
    [queries.FUNCTION_EQ, 5],
    [queries.FUNCTION_GT, 5],
    [queries.FUNCTION_GE, 5],
    [queries.FUNCTION_CO, "hello"],
    *TEST_INVALID_FUNCTIONS
)

TEST_INVALID_LITERALS = (
    dict(),
    tuple(),
    set(),
    lambda x: x
)

REDUCE_NOT_1 = [queries.FUNCTION_NOT, [queries.FUNCTION_NOT, True]]
REDUCE_NOT_2 = [queries.FUNCTION_NOT, REDUCE_NOT_1]
REDUCE_NOT_3 = [queries.FUNCTION_AND, REDUCE_NOT_1, REDUCE_NOT_2]

TEST_REDUCE_NOTS = (
    (REDUCE_NOT_1, True),
    (REDUCE_NOT_2, [queries.FUNCTION_NOT, True]),
    (REDUCE_NOT_3, [queries.FUNCTION_AND, True, [queries.FUNCTION_NOT, True]])
)


TEST_QUERY_1 = ["#eq", ["#resolve", "subject", "karyotypic_sex"], "XO"]
TEST_QUERY_2 = ["#co", ["#resolve", "biosamples", "[item]", "procedure", "code", "id"], "TE"]
TEST_QUERY_3 = ["#and", TEST_QUERY_1, TEST_QUERY_2]
TEST_QUERY_4 = ["#or", TEST_QUERY_3, False]
TEST_QUERY_5 = ["#and", TEST_QUERY_3, False]
TEST_QUERY_6 = "some_non_bool_value"
TEST_QUERY_7 = ["#eq", ["#resolve", "id"], "1ac54805-4145-4829-93e2-f362de55f28f"]
TEST_QUERY_8 = ["#eq", ["#resolve", "subject", "sex"], "MALE"]
TEST_QUERY_9 = ["#eq", ["#resolve", "subject", "taxonomy", "id"], "NCBITaxon:9606"]
TEST_QUERY_10 = ["#eq", ["#resolve", "biosamples", "[item]", "test_postgres_array", "[item]", "test"], "test_value"]
TEST_QUERY_11 = ["#eq", ["#resolve", "biosamples", "[item]", "test_json_array", "[item]", "test"], "test_value"]

# Test array item access - [item] at a certain path point should mean the same object across the whole query.
TEST_QUERY_12 = [
    "#and",
    ["#co", ["#resolve", "biosamples", "[item]", "procedure", "code", "id"], "TEST"],
    ["#eq", ["#resolve", "biosamples", "[item]", "tumor_grade", "[item]", "id"], "TG4"]
]  # False with TEST_DATA_1 - different [item]s!
TEST_QUERY_13 = [
    "#and",
    ["#co", ["#resolve", "biosamples", "[item]", "procedure", "code", "id"], "TEST"],
    ["#eq", ["#resolve", "biosamples", "[item]", "tumor_grade", "[item]", "id"], "TG2"]
]  # True with TEST_DATA_1 - same [item]s!
TEST_QUERY_14 = [
    "#or",
    ["#co", ["#resolve", "biosamples", "[item]", "procedure", "code", "id"], "DUMMY"],
    ["#eq", ["#resolve", "biosamples", "[item]", "tumor_grade", "[item]", "id"], "TG2"]
]  # True with TEST_DATA_1 - different [item]s but one of them is correct in both
TEST_QUERY_15 = ["#gt", ["#resolve", "test_op_1", "[item]"], ["#resolve", "test_op_2", "[item]"]]
TEST_QUERY_16 = ["#lt", ["#resolve", "test_op_1", "[item]"], ["#resolve", "test_op_2", "[item]"]]
TEST_QUERY_17 = ["#and", TEST_QUERY_16, ["#eq", ["#resolve", "test_op_2", "[item]"], 11]]
TEST_QUERY_18 = ["#and", TEST_QUERY_16, ["#eq", ["#resolve", "test_op_1", "[item]"], 7]]
TEST_QUERY_19 = ["#and", TEST_QUERY_13, TEST_QUERY_17]
TEST_QUERY_20 = ["#and", TEST_QUERY_13, TEST_QUERY_18]
TEST_QUERY_21 = ["#eq", ["#resolve", "test_op_2", "[item]"], ["#resolve", "test_op_3", "[item]", "[item]"]]
TEST_QUERY_22 = ["#eq", ["#resolve", "test_op_3", "[item]", "[item]"], ["#resolve", "test_op_3", "[item]", "[item]"]]
TEST_QUERY_23 = [
    "#and",
    ["#eq", ["#resolve", "test_op_1", "[item]"], 6],
    ["#eq", ["#resolve", "test_op_3", "[item]", "[item]"], 8]
]

TEST_LARGE_QUERY_1 = [
    "#and",
    ["#eq",
     ["#resolve", "data_type_1", "[item]", "children", "[item]", "id"],
     ["#resolve", "data_type_2", "[item]", "children", "[item]", "id"]],
    ["#and",
     ["#eq", ["#resolve", "data_type_1", "[item]", "children", "[item]", "prop"], "prop500"],
     ["#eq", ["#resolve", "data_type_2", "[item]", "children", "[item]", "prop"], "prop500"]]
]

TEST_EXPR_1 = TEST_QUERY_6
TEST_EXPR_2 = True  # TODO: What to do in this case when it's a query?
TEST_EXPR_3 = ["#resolve", "biosamples", "[item]", "procedure", "code", "id"]
TEST_EXPR_4 = ["#resolve", "subject", "karyotypic_sex"]
TEST_EXPR_5 = ["#resolve"]
TEST_EXPR_6 = ["#not", True]
TEST_EXPR_7 = ["#resolve", "biosamples", "[item]", "tumor_grade", "[item]", "id"]
TEST_EXPR_8 = ["#resolve", "biosamples"]

INVALID_EXPR_1 = []
INVALID_EXPR_2 = ["#and", True]
INVALID_EXPR_3 = ["#co", 5, 6]
INVALID_EXPR_4 = ["#resolve", "invalid_property"]
INVALID_EXPR_5 = ["#resolve", "biosamples", "array_property"]
INVALID_EXPR_6 = ["#resolve", "subject", "karyotypic_sex", "literal_property"]
INVALID_EXPR_7 = ["#fake_fn", 5]
INVALID_EXPR_8 = [5, 5]
INVALID_EXPR_9 = ["#gt", ["#resolve", "subject", "sex"], "MALE"]
INVALID_EXPR_10 = ["#resolve", "subject", "id"]  # Invalid with bad permissions
INVALID_EXPR_11 = ["#resolve", "subject"]  # Invalid with bad permissions


TEST_QUERY_STR = (
    (TEST_QUERY_1, "[#eq, [#resolve, subject, karyotypic_sex], XO]"),
    (TEST_QUERY_2, "[#co, [#resolve, biosamples, [item], procedure, code, id], TE]"),
)


TEST_LIST_ANDS = (
    (TEST_QUERY_1, (queries.convert_query_to_ast_and_preprocess(TEST_QUERY_1),)),
    (TEST_QUERY_2, (queries.convert_query_to_ast_and_preprocess(TEST_QUERY_2),)),
    (TEST_QUERY_3, (queries.convert_query_to_ast_and_preprocess(TEST_QUERY_1),
                    queries.convert_query_to_ast_and_preprocess(TEST_QUERY_2))),
    (TEST_QUERY_5, (queries.convert_query_to_ast_and_preprocess(TEST_QUERY_1),
                    queries.convert_query_to_ast_and_preprocess(TEST_QUERY_2),
                    queries.convert_query_to_ast_and_preprocess(False))),
)

TEST_UNLIST_ANDS = (
    (TEST_QUERY_1, TEST_QUERY_1),
    (TEST_QUERY_2, TEST_QUERY_2),
    (TEST_QUERY_3, TEST_QUERY_3),
    (TEST_QUERY_5, ["#and", TEST_QUERY_1, ["#and", TEST_QUERY_2, False]])
)


TEST_DATA_1 = {
    "id": "1ac54805-4145-4829-93e2-f362de55f28f",
    "subject": {
        "id": "S1",
        "karyotypic_sex": "XO",
        "sex": "MALE",
        "taxonomy": {
            "id": "NCBITaxon:9606",
            "label": "Homo sapiens"
        }
    },
    "test_op_1": [5, 6, 7],
    "test_op_2": [9, 10, 11],
    "test_op_3": [[1, 2, 3], [4, 5], [], [6, 7, 8, 9]],
    "biosamples": [
        {
            "procedure": {"code": {"id": "TEST", "label": "TEST LABEL"}},
            "tumor_grade": [{"id": "TG1", "label": "TG1 LABEL"}, {"id": "TG2", "label": "TG2 LABEL"}],
            "test_postgres_array": [{"test": "test_value"}],
            "test_json_array": [{"test": "test_value"}],
        },
        {
            "procedure": {"code": {"id": "DUMMY", "label": "DUMMY LABEL"}},
            "tumor_grade": [
                {"id": "TG3", "label": "TG3 LABEL"},
                {"id": "TG4", "label": "TG4 LABEL"},
                {"id": "TG5", "label": "TG5 LABEL"},
            ],
            "test_postgres_array": [{"test": "test_value"}],
            "test_json_array": [{"test": "test_value"}],
        }
    ],
}

TEST_DATA_2 = {
    "data_type_1": [{
        "id": "test1",
        "children": [{"id": f"child{i}", "prop": f"prop{i}"} for i in range(1000)]
    }],
    "data_type_2": [{
        "id": "test2",
        "children": [{"id": f"child{i}", "prop": f"prop{i}"} for i in range(999, -1, -1)]
    }]
}

INVALID_DATA = [{True, False}]


# Expression, Internal, Result, Index Combination
DS_VALID_EXPRESSIONS = (
    (TEST_EXPR_1, False, TEST_EXPR_1, None),
    (TEST_EXPR_2, False, TEST_EXPR_2, None),
    (TEST_EXPR_3, False, "TEST", {"_root.biosamples": 0}),
    (TEST_EXPR_3, False, "DUMMY", {"_root.biosamples": 1}),
    (TEST_EXPR_4, False, "XO", None),
    (TEST_EXPR_5, False, TEST_DATA_1, None),
    (TEST_EXPR_6, False, False, None),
    (TEST_EXPR_7, False, "TG1", {"_root.biosamples": 0, "_root.biosamples.[item].tumor_grade": 0}),
    (TEST_EXPR_7, False, "TG2", {"_root.biosamples": 0, "_root.biosamples.[item].tumor_grade": 1}),
    (TEST_EXPR_7, False, "TG3", {"_root.biosamples": 1, "_root.biosamples.[item].tumor_grade": 0}),
    (TEST_EXPR_7, False, "TG4", {"_root.biosamples": 1, "_root.biosamples.[item].tumor_grade": 1}),
    (TEST_EXPR_7, False, "TG5", {"_root.biosamples": 1, "_root.biosamples.[item].tumor_grade": 2}),
    (TEST_EXPR_8, False, TEST_DATA_1["biosamples"], None),
)

# Columns:
#  - Query
#  - Internal
#  - Result
#  - Number of Index Combinations (against TEST_DATA_1)
#  - Number of Matching Index Combinations (against TEST_DATA_1)
DS_VALID_QUERIES = (
    (TEST_QUERY_1,  False, True,  1, 1),  # No index accesses
    (TEST_QUERY_2,  False, True,  2, 1),  # Accessing 2 biosamples
    (TEST_QUERY_3,  False, True,  2, 1),  # "
    (TEST_QUERY_4,  False, True,  2, 1),  # "
    (TEST_QUERY_5,  False, False, 2, 0),  # "
    (TEST_QUERY_6,  False, False, 1, 0),  # No index accesses
    (TEST_QUERY_7,  True,  True,  1, 1),  # "
    (TEST_QUERY_8,  False, True,  1, 1),  # "
    (TEST_QUERY_9,  False, True,  1, 1),  # "
    (TEST_QUERY_10, False, True,  2, 2),  # Accessing 2 biosamples, each with 1 test_postgres_array item
    (TEST_QUERY_11, False, True,  2, 2),  # Accessing 2 biosamples, each with 1 test_json_array item
    (TEST_QUERY_12, False, False, 5, 0),  # Accessing 2 biosamples, one with 2 tumor grades, the other with 3
    (TEST_QUERY_13, False, True,  5, 1),  # "
    (TEST_QUERY_14, False, True,  5, 4),  # "
    (TEST_QUERY_15, False, False, 9, 0),  # Accessing 3 elements in test_op_n array
    (TEST_QUERY_16, False, True,  9, 9),  # "
    (TEST_QUERY_17, False, True,  9, 3),  # "
    (TEST_QUERY_18, False, True,  9, 3),  # "
    (TEST_QUERY_19, False, True, 45, 3),  # Accessing 2 biosamples, one with 2 tumor grades, the other with 3 +PLUS+ "
    (TEST_QUERY_20, False, True, 45, 3),  # "
    (TEST_QUERY_21, False, True, 27, 1),  # Accessing 3 elements in test_op_2, plus 9 in test_op_3 (non-flattened)
    (TEST_QUERY_22, False, True,  9, 9),  # Accessing 9 in test_op_3 and checking them against itself
    (TEST_QUERY_23, False, True, 27, 1),  # test_op_3: 9, test_op_1: 3
)

# Query, Internal, Exception
COMMON_INVALID_EXPRESSIONS = (
    (INVALID_EXPR_1,  False, SyntaxError),
    (INVALID_EXPR_2,  False, SyntaxError),
    (INVALID_EXPR_3,  False, TypeError),
    (INVALID_EXPR_4,  False, ValueError),
    (INVALID_EXPR_5,  False, TypeError),
    (INVALID_EXPR_6,  False, TypeError),
    (INVALID_EXPR_7,  False, SyntaxError),
    (INVALID_EXPR_8,  False, SyntaxError),
    (INVALID_EXPR_9,  False, ValueError),
    (INVALID_EXPR_10, False, ValueError),
    (INVALID_EXPR_11, True,  ValueError),
)

# Expression, Internal, Exception Raised, Index Combination
DS_INVALID_EXPRESSIONS = (
    *((*i, None) for i in COMMON_INVALID_EXPRESSIONS),
    # Missing index combinations:
    (TEST_EXPR_7, False, Exception, {"_root.biosamples": 0}),
    (TEST_EXPR_7, False, Exception, {}),
    (TEST_EXPR_7, False, Exception, None),
    (["#_wc", "v1"], False, NotImplementedError, None),
    (["#co", ["#resolve", "biosamples", "[item]", "procedure", "code", "id"],
      ["#_wc", "v1"]], False, NotImplementedError, {"_root.biosamples": 0})
)


# Query, Internal, Parameters
PG_VALID_QUERIES = (
    (TEST_QUERY_1,  False, ("XO",)),
    (TEST_QUERY_2,  False, ("%TE%",)),
    (TEST_QUERY_3,  False, ("XO", "%TE%")),
    (TEST_QUERY_4,  False, ("XO", "%TE%", False)),
    (TEST_QUERY_5,  False, ("XO", "%TE%", False)),
    (TEST_QUERY_6,  False, ("some_non_bool_value",)),
    (TEST_QUERY_7,  True,  ("1ac54805-4145-4829-93e2-f362de55f28f",)),
    (TEST_QUERY_8,  False, ("MALE",)),
    (TEST_QUERY_9,  False, ("NCBITaxon:9606",)),
    (TEST_QUERY_10, False, ("test_value",)),
    (TEST_QUERY_11, False, ("test_value",)),
    (TEST_QUERY_12, False, ("%TEST%", "TG4")),
    (TEST_QUERY_13, False, ("%TEST%", "TG2")),
    (TEST_QUERY_14, False, ("%DUMMY%", "TG2")),
    (TEST_QUERY_15, False, ()),
    (TEST_QUERY_17, False, (11,)),
    (TEST_QUERY_18, False, (7,)),
    (TEST_QUERY_19, False, ("%TEST%", "TG2", 11)),
    (TEST_QUERY_20, False, ("%TEST%", "TG2", 7)),
    (TEST_QUERY_21, False, ()),
    (TEST_QUERY_22, False, ()),
    (TEST_QUERY_23, False, (6, 8)),
)

PG_INVALID_EXPRESSIONS = (
    *COMMON_INVALID_EXPRESSIONS,
    (["#_wc", "v1", "v2"], False, SyntaxError),
    (["#_wc", ["#resolve", "biosamples"]], False, NotImplementedError),
    ({"dict": True}, False, ValueError),
)

JSON_SCHEMA_TYPES = ("string", "integer", "number", "object", "array", "boolean", "null")
POSTGRES_TYPES = ("TEXT", "INTEGER", "DOUBLE PRECISION", "JSON", "JSON", "BOOLEAN", "TEXT")


def test_build_search_response():
    test_response = build_search_response({"some": "result"}, datetime.now())

    assert isinstance(test_response, dict)
    assert tuple(sorted(test_response.keys())) == ("results", "time")
    assert any((isinstance(test_response["results"], dict),
                isinstance(test_response["results"], list),
                isinstance(test_response["results"], tuple)))

    t = float(test_response["time"])
    assert t >= 0


def test_literal_equality():
    assert queries.Literal(5) == queries.Literal(5)
    assert queries.Literal("5") == queries.Literal("5")
    assert queries.Literal(True) == queries.Literal(True)
    assert queries.Literal(1.0) == queries.Literal(1.0)


def test_valid_function_construction():
    for f in TEST_FUNCTIONS:
        e = queries.Expression(fn=f[0], args=f[1:])
        assert e.fn == f[0]
        assert str(e.args) == str(f[1:])


def test_invalid_function_construction():
    for f in TEST_INVALID_FUNCTIONS:
        with raises(AssertionError):
            queries.Expression(fn=f[0], args=[queries.Literal(a) for a in f[1:]])


def test_invalid_expression_syntax():
    for f in TEST_INVALID_EXPRESSION_SYNTAX:
        with raises(SyntaxError):
            queries.convert_query_to_ast(f)


def test_invalid_literals():
    for v in TEST_INVALID_LITERALS:
        with raises(AssertionError):
            queries.Literal(value=v)

        with raises(ValueError):
            queries.convert_query_to_ast(v)


def test_query_not_preprocessing():
    for b, a in TEST_REDUCE_NOTS:
        assert queries.convert_query_to_ast_and_preprocess(b) == \
            queries.convert_query_to_ast_and_preprocess(a)


def test_queries_and_ast():
    for q, s in TEST_QUERY_STR:
        assert str(queries.convert_query_to_ast_and_preprocess(q)) == s

    for b, a, in TEST_LIST_ANDS:
        assert all(bi == ai for bi, ai in
                   zip(queries.ast_to_and_asts(queries.convert_query_to_ast_and_preprocess(b)), a))

    assert queries.and_asts_to_ast(()) is None

    for b, a in TEST_UNLIST_ANDS:
        assert queries.and_asts_to_ast(queries.ast_to_and_asts(queries.convert_query_to_ast_and_preprocess(b))) == \
            queries.convert_query_to_ast_and_preprocess(a)


def test_postgres_schemas():
    null_schema = postgres.json_schema_to_postgres_schema("test", {"type": "integer"})
    assert null_schema[0] is None and null_schema[1] is None

    for s, p in zip(JSON_SCHEMA_TYPES, POSTGRES_TYPES):
        assert postgres.json_schema_to_postgres_schema("test", {
            "type": "object",
            "properties": {
                "test2": {"type": s}
            }
        })[1] == f"test(test2 {p})"


def test_postgres_collect_resolve_join_tables():
    # TODO: This is sort of artificial; does this case actually arise?
    assert postgres.collect_resolve_join_tables((), {}, None, None) == ()


def test_postgres_invalid_schemas():
    with raises(SyntaxError):
        postgres.search_query_to_psycopg2_sql(TEST_EXPR_4, TEST_INVALID_SCHEMA)

    with raises(SyntaxError):
        postgres.search_query_to_psycopg2_sql(TEST_EXPR_8, TEST_INVALID_SCHEMA)

    with raises(ValueError):
        postgres.search_query_to_psycopg2_sql(["#resolve", "bad_array", "[item]"], TEST_INVALID_SCHEMA)

    with raises(SyntaxError):
        postgres.search_query_to_psycopg2_sql(["#resolve", "[item]"], TEST_INVALID_SCHEMA_2)


def test_postgres_valid_queries():
    for e, i, p in PG_VALID_QUERIES:
        _, params = postgres.search_query_to_psycopg2_sql(e, TEST_SCHEMA, i)
        assert params == p


def test_postgres_valid_expressions():
    for e, i, _v, _ic in DS_VALID_EXPRESSIONS:
        postgres.search_query_to_psycopg2_sql(e, TEST_SCHEMA, i)


def test_postgres_invalid_expressions():
    for e, i, ex in PG_INVALID_EXPRESSIONS:
        with raises(ex):
            postgres.search_query_to_psycopg2_sql(e, TEST_SCHEMA, i)


# noinspection PyProtectedMember
def test_data_structure_search():
    for e, i, v, ic in DS_VALID_EXPRESSIONS:
        assert data_structure.evaluate(queries.convert_query_to_ast(e), TEST_DATA_1, TEST_SCHEMA, ic) == v

    for q, i, v, _ni, nm in DS_VALID_QUERIES:
        assert data_structure.check_ast_against_data_structure(queries.convert_query_to_ast(q), TEST_DATA_1,
                                                               TEST_SCHEMA, i) == v

        ics = tuple(data_structure.check_ast_against_data_structure(
            queries.convert_query_to_ast(q), TEST_DATA_1, TEST_SCHEMA, i, return_all_index_combinations=True))

        assert len(ics) == nm

    for q, i, _v, ni, nm in DS_VALID_QUERIES:
        als = data_structure._collect_array_lengths(queries.convert_query_to_ast(q), TEST_DATA_1, TEST_SCHEMA,
                                                    resolve_checks=True)
        ics = tuple(data_structure._create_all_index_combinations(als, {}))
        assert len(ics) == ni
        assert nm <= len(ics)

    for e, i, ex, ic in DS_INVALID_EXPRESSIONS:
        with raises(ex):
            data_structure.evaluate(queries.convert_query_to_ast(e), TEST_DATA_1, TEST_SCHEMA, ic, i)

    # Invalid data
    with raises(ValueError):
        data_structure.evaluate(queries.convert_query_to_ast(TEST_EXPR_1), INVALID_DATA, TEST_SCHEMA, {})


def test_large_data_structure_query():
    def large_query():
        assert data_structure.check_ast_against_data_structure(queries.convert_query_to_ast(TEST_LARGE_QUERY_1),
                                                               TEST_DATA_2, TEST_SCHEMA_2, False)

    # Test large query
    import cProfile
    cProfile.runctx("large_query()", None, locals(), sort="tottime")


# noinspection PyProtectedMember
def test_check_operation_permissions():
    for e, i, _v, ic in DS_VALID_EXPRESSIONS:
        queries.check_operation_permissions(
            queries.convert_query_to_ast(e),
            TEST_SCHEMA,
            search_getter=lambda rl, s: data_structure._resolve_properties_and_check(rl, s, ic))
