import psycopg2.sql
from bento_lib.search import build_search_response, data_structure, operations, postgres, queries
from datetime import datetime
from pytest import mark, raises

NUMBER_SEARCH = {
    "operations": [
        operations.SEARCH_OP_LT,
        operations.SEARCH_OP_LE,
        operations.SEARCH_OP_GT,
        operations.SEARCH_OP_GE,
        operations.SEARCH_OP_EQ,
        operations.SEARCH_OP_IN,
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
                "operations": [operations.SEARCH_OP_EQ, operations.SEARCH_OP_IN],
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
                                            "operations": [
                                                operations.SEARCH_OP_CO,
                                                operations.SEARCH_OP_ICO,
                                                operations.SEARCH_OP_ISW,
                                                operations.SEARCH_OP_IEW,
                                                operations.SEARCH_OP_LIKE,
                                                operations.SEARCH_OP_ILIKE,
                                            ],
                                            "queryable": "all"
                                        }
                                    },
                                    "label": {
                                        "type": "string",
                                        "search": {
                                            "operations": [
                                                operations.SEARCH_OP_ICO,
                                                operations.SEARCH_OP_ISW,
                                                operations.SEARCH_OP_IEW,
                                                operations.SEARCH_OP_LIKE,
                                                operations.SEARCH_OP_ILIKE,
                                            ],
                                            "queryable": "all"
                                        }
                                    }
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
                                        "operations": [operations.SEARCH_OP_EQ, operations.SEARCH_OP_IN],
                                        "queryable": "all"
                                    }
                                },
                                "label": {"type": "string"}
                            },
                            "search": {
                                "database": {
                                    "relation": "patients_ontology",
                                    "primary_key": "id",  # Ontology primary key
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
                                },
                                "test2": {
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
                        "operations": [operations.SEARCH_OP_EQ, operations.SEARCH_OP_IN],
                        "queryable": "internal"
                    }
                },
                "karyotypic_sex": {
                    "type": "string",
                    "search": {
                        "operations": [operations.SEARCH_OP_EQ, operations.SEARCH_OP_IN],
                        "queryable": "all"
                    }
                },
                "sex": {
                    "type": "string",
                    "enum": ["UNKNOWN_SEX", "FEMALE", "MALE", "OTHER_SEX"],
                    "search": {
                        "operations": [operations.SEARCH_OP_EQ, operations.SEARCH_OP_IN],
                        "queryable": "all"
                    }
                },
                "taxonomy": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "search": {
                                "operations": [operations.SEARCH_OP_EQ, operations.SEARCH_OP_IN],
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
                "operations": [operations.SEARCH_OP_EQ, operations.SEARCH_OP_IN],
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
                            "operations": [operations.SEARCH_OP_EQ, operations.SEARCH_OP_IN],
                            "queryable": "all"
                        }
                    },
                    "prop": {
                        "type": "string",
                        "search": {
                            "operations": [operations.SEARCH_OP_EQ, operations.SEARCH_OP_IN],
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
    [queries.FUNCTION_ICO, "LABEL", "label"],
    [queries.FUNCTION_RESOLVE, "biosamples", "[item]", "procedure", "code", "id"],
    [queries.FUNCTION_IN, 5, {1, 2, 3, 4, 5}],
    [queries.FUNCTION_LIST, 1, 2, 3, 4, 5]
)

TEST_INVALID_FUNCTIONS = (
    ["eq", 5, 6],
    ["#bad", 6, 7],
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
    [queries.FUNCTION_ICO, "LABEL"],
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
TEST_QUERY_5 = ["#and", TEST_QUERY_3, False]
TEST_QUERY_6 = "some_non_bool_value"
TEST_QUERY_13 = [
    "#and",
    ["#co", ["#resolve", "biosamples", "[item]", "procedure", "code", "id"], "TEST"],
    ["#eq", ["#resolve", "biosamples", "[item]", "tumor_grade", "[item]", "id"], "TG2"]
]  # True with TEST_DATA_1 - same [item]s!
TEST_QUERY_16 = ["#lt", ["#resolve", "test_op_1", "[item]"], ["#resolve", "test_op_2", "[item]"]]
TEST_QUERY_17 = ["#and", TEST_QUERY_16, ["#eq", ["#resolve", "test_op_2", "[item]"], 11]]
TEST_QUERY_18 = ["#and", TEST_QUERY_16, ["#eq", ["#resolve", "test_op_1", "[item]"], 7]]

TEST_QUERIES = [
    # query: the search query expression
    # ds: columns for data_structure querying
    #  - Query
    #  - Internal
    #  - Result
    #  - Number of Index Combinations (against TEST_DATA_1)
    #  - Number of Matching Index Combinations (against TEST_DATA_1)
    # ps: (internal: bool, postgres params: tuple)

    {"query": TEST_QUERY_1,  # 1
     "ds": (False, True, 1, 1),  # No index accesses
     "ps": (False, ("XO",))},
    {"query": TEST_QUERY_2,  # 2
     "ds": (False, True, 2, 1),  # Accessing 2 biosamples
     "ps": (False, ("%TE%",))},
    {"query": ["#and", TEST_QUERY_1, TEST_QUERY_2],  # 3
     "ds": (False, True, 2, 1),  # Accessing 2 biosamples
     "ps": (False, ("XO", "%TE%"))},
    {"query": ["#or", TEST_QUERY_3, False],  # 4
     "ds": (False, True, 2, 1),  # Accessing 2 biosamples
     "ps": (False, ("XO", "%TE%", False))},
    {"query": TEST_QUERY_5,  # 5
     "ds": (False, False, 2, 0),  # Accessing 2 biosamples
     "ps": (False, ("XO", "%TE%", False))},
    {"query": TEST_QUERY_6,  # 6
     "ds": (False, False, 1, 0),  # No index accesses
     "ps": (False, ("some_non_bool_value",))},
    {"query": ["#eq", ["#resolve", "id"], "1ac54805-4145-4829-93e2-f362de55f28f"],  # 7
     "ds": (True, True, 1, 1),  # No index accesses
     "ps": (True, ("1ac54805-4145-4829-93e2-f362de55f28f",))},
    {"query": ["#eq", ["#resolve", "subject", "sex"], "MALE"],  # 8
     "ds": (False, True, 1, 1),  # No index accesses
     "ps": (False, ("MALE",))},
    {"query": ["#eq", ["#resolve", "subject", "taxonomy", "id"], "NCBITaxon:9606"],  # 9
     "ds": (False, True, 1, 1),
     "ps": (False, ("NCBITaxon:9606",))},
    # 10
    {"query": ["#eq", ["#resolve", "biosamples", "[item]", "test_postgres_array", "[item]", "test"], "test_value"],
     "ds": (False, True, 2, 2),  # Accessing 2 biosamples, each with 1 test_postgres_array item
     "ps": (False, ("test_value",))},
    # 11
    {"query": ["#eq", ["#resolve", "biosamples", "[item]", "test_json_array", "[item]", "test"], "test_value"],
     "ds": (False, True, 2, 2),  # Accessing 2 biosamples, each with 1 test_json_array item
     "ps": (False, ("test_value",))},
    {
        # Test array item access - [item] at a certain path point should mean the same object across the whole query.
        "query": [  # 12
            "#and",
            ["#co", ["#resolve", "biosamples", "[item]", "procedure", "code", "id"], "TEST"],
            ["#eq", ["#resolve", "biosamples", "[item]", "tumor_grade", "[item]", "id"], "TG4"]
        ],  # False with TEST_DATA_1 - different [item]s!
        "ds": (False, False, 5, 0),  # Accessing 2 biosamples, one with 2 tumor grades, the other with 3
        "ps": (False, ("%TEST%", "TG4")),
    },
    {"query": TEST_QUERY_13,  # True with TEST_DATA_1 - same [item]s!
     "ds": (False, True, 5, 1),  # Accessing 2 biosamples, one with 2 tumor grades, the other with 3
     "ps": (False, ("%TEST%", "TG2"))},
    {
        # True with TEST_DATA_1 - different [item]s but one of them is correct in both
        "query": [
            "#or",
            ["#co", ["#resolve", "biosamples", "[item]", "procedure", "code", "id"], "DUMMY"],
            ["#eq", ["#resolve", "biosamples", "[item]", "tumor_grade", "[item]", "id"], "TG2"]
        ],
        "ds": (False, True, 5, 4),  # Accessing 2 biosamples, one with 2 tumor grades, the other with 3
        "ps": (False, ("%DUMMY%", "TG2")),
    },
    {"query": ["#gt", ["#resolve", "test_op_1", "[item]"], ["#resolve", "test_op_2", "[item]"]],  # 15
     "ds": (False, False, 9, 0),  # Accessing 3 elements in test_op_n array
     "ps": (False, ())},
    {"query": TEST_QUERY_16,  # 16
     "ds": (False, True, 9, 9),  # Accessing 3 elements in test_op_n array
     "ps": (False, ())},
    {"query": TEST_QUERY_17,  # 17
     "ds": (False, True, 9, 3),  # Accessing 3 elements in test_op_n array
     "ps": (False, (11,))},
    {"query": TEST_QUERY_18,  # 18
     "ds": (False, True, 9, 3),  # Accessing 3 elements in test_op_n array
     "ps": (False, (7,))},
    {"query": ["#and", TEST_QUERY_13, TEST_QUERY_17],  # 19
     "ds": (False, True, 45, 3),  # Accessing 2 biosamples, one with 2 tumor grades, the other with 3 +PLUS+ "
     "ps": (False, ("%TEST%", "TG2", 11))},
    {"query": ["#and", TEST_QUERY_13, TEST_QUERY_18],  # 20
     "ds": (False, True, 45, 3),  # Accessing 2 biosamples, one with 2 tumor grades, the other with 3 +PLUS+ "
     "ps": (False, ("%TEST%", "TG2", 7))},
    {"query": ["#eq", ["#resolve", "test_op_2", "[item]"], ["#resolve", "test_op_3", "[item]", "[item]"]],  # 21
     "ds": (False, True, 27, 1),  # Accessing 3 elements in test_op_2, plus 9 in test_op_3 (non-flattened)
     "ps": (False, ())},
    {
        # 22
        "query": ["#eq", ["#resolve", "test_op_3", "[item]", "[item]"], ["#resolve", "test_op_3", "[item]", "[item]"]],
        "ds": (False, True, 9, 9),  # Accessing 9 in test_op_3 and checking them against itself
        "ps": (False, ()),
    },
    {
        # 23
        "query": [
            "#and",
            ["#eq", ["#resolve", "test_op_1", "[item]"], 6],
            ["#eq", ["#resolve", "test_op_3", "[item]", "[item]"], 8]
        ],
        "ds": (False, True, 27, 1),  # test_op_3: 9, test_op_1: 3
        "ps": (False, (6, 8)),
    },
    {"query": ["#ico", ["#resolve", "biosamples", "[item]", "procedure", "code", "label"], "label"],  # 24
     "ds": (False, True, 2, 2),  # Case-insensitive contains; accessing two biosamples' procedure code labels
     "ps": (True, ("%label%",))},
    {"query": ["#in", ["#resolve", "subject", "karyotypic_sex"], ["#list", "XO", "XX"]],  # 25
     "ds": (False, True, 1, 1),  # in statement, search in list of string values
     "ps": (True, (("XO", "XX"),))},
    # Starts with 'label' - no matches since both end with 'label' instead:
    {"query": ["#isw", ["#resolve", "biosamples", "[item]", "procedure", "code", "label"], "label"],  # 26
     "ds": (False, False, 2, 0),  # Starts with 'label' - no matches since both end with 'label' instead
     "ps": (True, ("label%",))},
    # Ends with 'label' + case-insensitive - 2 matches
    {"query": ["#iew", ["#resolve", "biosamples", "[item]", "procedure", "code", "label"], "Label"],  # 27
     "ds": (False, True, 2, 2),  # Ends with 'label' + case-insensitive - 2 matches
     "ps": (True, ("%Label",))},
    # Starts with 'dummy' - only 1 of 2 match; case-insensitive
    {"query": ["#isw", ["#resolve", "biosamples", "[item]", "procedure", "code", "label"], "duMmy"],  # 28
     "ds": (False, True, 2, 1),  # Starts with 'dummy' - only 1 of 2 match; case-insensitive
     "ps": (True, ("duMmy%",))},

    # One hundred million I?LIKE query tests !!!

    # 26 but using #like
    {"query": ["#like", ["#resolve", "biosamples", "[item]", "procedure", "code", "label"], "LABEL%"],  # 29
     "ds": (False, False, 2, 0),
     "ps": (False, ("LABEL%",))},
    # 26 but using #ilike
    {"query": ["#ilike", ["#resolve", "biosamples", "[item]", "procedure", "code", "label"], "LaBeL%"],  # 30
     "ds": (False, False, 2, 0),
     "ps": (False, ("LaBeL%",))},

    # 27 but with #like - 2 matches (correct case)
    {"query": ["#like", ["#resolve", "biosamples", "[item]", "procedure", "code", "label"], "%LABEL"],  # 31
     "ds": (False, True, 2, 2),
     "ps": (True, ("%LABEL",))},
    #  - no matches since it is case-sensitive
    {"query": ["#like", ["#resolve", "biosamples", "[item]", "procedure", "code", "label"], "%L_BeL"],  # 32
     "ds": (False, False, 2, 0),
     "ps": (False, ("%L_BeL",))},
    #  - 2 matches; case-insensitive
    {"query": ["#ilike", ["#resolve", "biosamples", "[item]", "procedure", "code", "label"], "%LaBE_"],  # 33
     "ds": (False, True, 2, 2),
     "ps": (True, ("%LaBE_",))},

    # 28 but with like - only 1 of 2 match for both
    {"query": ["#like", ["#resolve", "biosamples", "[item]", "procedure", "code", "label"], "%DUMM_%"],  # 34
     "ds": (False, True, 2, 1),
     "ps": (True, ("%DUMM_%",))},
    {"query": ["#like", ["#resolve", "biosamples", "[item]", "procedure", "code", "label"], "DU_MY%"],  # 35
     "ds": (False, True, 2, 1),
     "ps": (True, ("DU_MY%",))},

    #  - 0 matches (bad case)
    {"query": ["#like", ["#resolve", "biosamples", "[item]", "procedure", "code", "label"], "DUmmY%"],  # 36
     "ds": (False, False, 2, 0),
     "ps": (False, ("DUmmY%",))},

    # 28 but with ilike - only 1 of 2 match
    {"query": ["#ilike", ["#resolve", "biosamples", "[item]", "procedure", "code", "label"], "duMmy%"],  # 37
     "ds": (False, True, 2, 1),
     "ps": (True, ("duMmy%",))},
    {"query": ["#ilike", ["#resolve", "biosamples", "[item]", "procedure", "code", "label"], "%duM%my%"],  # 38
     "ds": (False, True, 2, 1),
     "ps": (True, ("%duM%my%",))},

    #  - no matches (bad pattern)
    {"query": ["#ilike", ["#resolve", "biosamples", "[item]", "procedure", "code", "label"], "%duM%my"],  # 39
     "ds": (False, False, 2, 0),
     "ps": (False, ("%duM%my",))},

    #  - no matches (bad pattern); testing escaped % and Regex escapes
    {"query": ["#ilike", ["#resolve", "biosamples", "[item]", "procedure", "code", "label"], "[%duM\\%\\_my]"],  # 40
     "ds": (False, False, 2, 0),
     "ps": (False, ("[%duM\\%\\_my]",))},

    # Testing nested Postgres JSON schema-creation
    {"query": ["#eq", ["#resolve", "biosamples", "[item]", "test_postgres_array", "[item]", "test2", "test"], "a"],
     "ds": (False, True, 2, 2),  # Accessing 2 biosamples, each with 1 test_postgres_array item
     "ps": (False, ("a",))},
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
INVALID_EXPR_12 = ["#resolve", "subject", ["#gt", 7, 5]]  # Invalid with expression inside resolve

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
            "test_postgres_array": [{"test": "test_value", "test2": {"test": "a"}}],
            "test_json_array": [{"test": "test_value"}],
        },
        {
            "procedure": {"code": {"id": "DUMMY", "label": "DUMMY LABEL"}},
            "tumor_grade": [
                {"id": "TG3", "label": "TG3 LABEL"},
                {"id": "TG4", "label": "TG4 LABEL"},
                {"id": "TG5", "label": "TG5 LABEL"},
            ],
            "test_postgres_array": [{"test": "test_value", "test2": {"test": "a"}}],
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

# Query, Internal, Exception
COMMON_INVALID_EXPRESSIONS = (
    (INVALID_EXPR_1, False, SyntaxError),
    (INVALID_EXPR_2, False, SyntaxError),
    (INVALID_EXPR_3, False, TypeError),
    (INVALID_EXPR_4, False, ValueError),
    (INVALID_EXPR_5, False, TypeError),
    (INVALID_EXPR_6, False, TypeError),
    (INVALID_EXPR_7, False, SyntaxError),
    (INVALID_EXPR_8, False, SyntaxError),
    (INVALID_EXPR_9, False, ValueError),
    (INVALID_EXPR_10, False, ValueError),
    (INVALID_EXPR_11, True, ValueError),
    (INVALID_EXPR_12, False, TypeError),
)

# Expression, Internal, Exception Raised, Index Combination
DS_INVALID_EXPRESSIONS = (
    *((*i, None) for i in COMMON_INVALID_EXPRESSIONS),
    # Missing index combinations:
    (TEST_EXPR_7, False, Exception, {"_root.biosamples": 0}),
    (TEST_EXPR_7, False, Exception, {}),
    (TEST_EXPR_7, False, Exception, None),
    (["#_wc", "v1", "anywhere"], False, NotImplementedError, None),
    (["#co", ["#resolve", "biosamples", "[item]", "procedure", "code", "id"],
      ["#_wc", "v1", "anywhere"]], False, NotImplementedError, {"_root.biosamples": 0}),
    (["#isw", 5, 3], False, TypeError, None),  # Invalid with wrong types (DS only)
    (["#iew", 5, 3], False, TypeError, None),  # Invalid with wrong types (DS only)
    (["#like", 5, 3], False, TypeError, None),  # Invalid with wrong types (DS only)
    (["#ilike", 5, 3], False, TypeError, None),  # Invalid with wrong types (DS only)
)

PG_INVALID_EXPRESSIONS = (
    *COMMON_INVALID_EXPRESSIONS,
    (["#_wc", "v1"], False, SyntaxError),
    (["#_wc", "v1", "v2", "v3"], False, SyntaxError),
    (["#_wc", ["#resolve", "biosamples"], "anywhere"], False, NotImplementedError),
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


def test_literal_hashing():
    assert hash(queries.Literal(5)) == hash(5)
    assert hash(queries.Literal(5.0)) == hash(5.0)
    assert hash(queries.Literal("abc")) == hash("abc")
    assert hash(queries.Literal(True)) == hash(True)


@mark.parametrize("f", TEST_FUNCTIONS)
def test_valid_function_construction(f):
    e = queries.Expression(fn=f[0], args=f[1:])
    assert e.fn == f[0]
    assert e.value == e
    assert str(e.args) == str(tuple(f[1:]))


@mark.parametrize("f", TEST_INVALID_FUNCTIONS)
def test_invalid_function_construction(f):
    with raises(AssertionError):
        queries.Expression(fn=f[0], args=[queries.Literal(a) for a in f[1:]])


@mark.parametrize("f", TEST_INVALID_EXPRESSION_SYNTAX)
def test_invalid_expression_syntax(f):
    with raises(SyntaxError):
        queries.convert_query_to_ast(f)


@mark.parametrize("v", TEST_INVALID_LITERALS)
def test_invalid_literals(v):
    with raises(AssertionError):
        # noinspection PyTypeChecker
        queries.Literal(value=v)

    with raises(ValueError):
        # noinspection PyTypeChecker
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
    null_schema = postgres.json_schema_to_postgres_schema("test", {"type": "integer"}, "json")
    assert null_schema[0] is None and null_schema[1] is None and null_schema[2] is None

    for s, p in zip(JSON_SCHEMA_TYPES, POSTGRES_TYPES):
        res = postgres.json_schema_to_postgres_schema("test", {
            "type": "object",
            "properties": {
                "test2": {"type": s}
            }
        }, "json")
        assert res[1] == "test"
        assert res[2] == psycopg2.sql.Composed([
            psycopg2.sql.SQL("("),
            psycopg2.sql.Composed([
                psycopg2.sql.Composed([
                    psycopg2.sql.Identifier("test2"),
                    psycopg2.sql.SQL(" "),
                    psycopg2.sql.SQL(p)
                ])
            ]),
            psycopg2.sql.SQL(")"),
        ])


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


@mark.parametrize("query", TEST_QUERIES)
def test_postgres_valid_queries(query):
    e = query["query"]
    i, p = query["ps"]
    _, params = postgres.search_query_to_psycopg2_sql(e, TEST_SCHEMA, i)
    assert params == p


@mark.parametrize("e, i, _v, _ic", DS_VALID_EXPRESSIONS)
def test_postgres_valid_expressions(e, i, _v, _ic):
    postgres.search_query_to_psycopg2_sql(e, TEST_SCHEMA, i)


@mark.parametrize("e, i, ex", PG_INVALID_EXPRESSIONS)
def test_postgres_invalid_expressions(e, i, ex):
    with raises(ex):
        postgres.search_query_to_psycopg2_sql(e, TEST_SCHEMA, i)


@mark.parametrize("e, i, v, ic", DS_VALID_EXPRESSIONS)
def test_data_structure_search_1(e, i, v, ic):
    assert data_structure.evaluate(
        queries.convert_query_to_ast(e), TEST_DATA_1, TEST_SCHEMA, ic, secure_errors=False) == v
    assert data_structure.evaluate(
        queries.convert_query_to_ast(e), TEST_DATA_1, TEST_SCHEMA, ic, secure_errors=True) == v


# noinspection PyProtectedMember
@mark.parametrize("query", TEST_QUERIES)
def test_data_structure_search_2(query):
    q = query["query"]
    i, v, ni, nm = query["ds"]

    # These are all valid, so we should be able to try out the different options with no negative effects
    assert data_structure.check_ast_against_data_structure(
        queries.convert_query_to_ast(q), TEST_DATA_1, TEST_SCHEMA, i, secure_errors=False) == v

    assert data_structure.check_ast_against_data_structure(
        queries.convert_query_to_ast(q), TEST_DATA_1, TEST_SCHEMA, i, secure_errors=False,
        skip_schema_validation=True) == v

    assert data_structure.check_ast_against_data_structure(
        queries.convert_query_to_ast(q), TEST_DATA_1, TEST_SCHEMA, i, secure_errors=True) == v

    assert data_structure.check_ast_against_data_structure(
        queries.convert_query_to_ast(q), TEST_DATA_1, TEST_SCHEMA, i, secure_errors=True,
        skip_schema_validation=True) == v

    ics = tuple(data_structure.check_ast_against_data_structure(
        queries.convert_query_to_ast(q), TEST_DATA_1, TEST_SCHEMA, i, return_all_index_combinations=True))

    assert len(ics) == nm


@mark.parametrize("query", TEST_QUERIES)
def test_data_structure_search_3(query):
    q = query["query"]
    i, v, ni, nm = query["ds"]

    als = data_structure._collect_array_lengths(queries.convert_query_to_ast(q), TEST_DATA_1, TEST_SCHEMA,
                                                resolve_checks=True)
    ics = tuple(data_structure._create_all_index_combinations({}, als))
    assert len(ics) == ni
    assert nm <= len(ics)


@mark.parametrize("e, i, ex, ic", DS_INVALID_EXPRESSIONS)
def test_data_structure_search_4(e, i, ex, ic):
    with raises(ex):
        data_structure.evaluate(
            queries.convert_query_to_ast(e), TEST_DATA_1, TEST_SCHEMA, ic, i, secure_errors=False)
    with raises(ex):
        data_structure.evaluate(
            queries.convert_query_to_ast(e), TEST_DATA_1, TEST_SCHEMA, ic, i, secure_errors=True)


def test_data_structure_search_5():
    # Invalid data

    with raises(ValueError):
        data_structure.evaluate(
            queries.convert_query_to_ast(TEST_EXPR_1), INVALID_DATA, TEST_SCHEMA, {}, secure_errors=False)

    with raises(ValueError):
        data_structure.evaluate(
            queries.convert_query_to_ast(TEST_EXPR_1), INVALID_DATA, TEST_SCHEMA, {}, secure_errors=True)


def test_large_data_structure_query():
    def large_query():
        assert data_structure.check_ast_against_data_structure(
            queries.convert_query_to_ast(TEST_LARGE_QUERY_1), TEST_DATA_2, TEST_SCHEMA_2, False)

    # Test large query
    import cProfile
    cProfile.runctx("large_query()", {}, locals(), sort="tottime")


# noinspection PyProtectedMember
@mark.parametrize("e, i, _v, ic", DS_VALID_EXPRESSIONS)
def test_check_operation_permissions(e, i, _v, ic):
    queries.check_operation_permissions(
        queries.convert_query_to_ast(e),
        TEST_SCHEMA,
        search_getter=lambda rl, s: data_structure._resolve_properties_and_check(rl, s, ic))
