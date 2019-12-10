from chord_lib.search import *
from datetime import datetime
from pytest import raises


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
                                    "type": "MANY_TO_MANY",
                                    "parent_foreign_key": "biosample_id",
                                    "parent_primary_key": "biosample_id"
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
                "queryable": "all",
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
        }
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
            "type": "object"
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
    "subject": {"id": "S1", "karyotypic_sex": "XO", "sex": "MALE"},
    "biosamples": [
        {
            "procedure": {"code": {"id": "TEST", "label": "TEST LABEL"}},
            "tumor_grade": [{"id": "TG1", "label": "TG1 LABEL"}, {"id": "TG2", "label": "TG2 LABEL"}]
        },
        {
            "procedure": {"code": {"id": "DUMMY", "label": "DUMMY LABEL"}},
            "tumor_grade": [{"id": "TG3", "label": "TG3 LABEL"}, {"id": "TG4", "label": "TG4 LABEL"}]
        }
    ],
}

INVALID_DATA = [{True, False}]


# Expression, Internal, Result
DS_VALID_EXPRESSIONS = (
    (TEST_EXPR_1, False, TEST_EXPR_1),
    (TEST_EXPR_2, False, TEST_EXPR_2),
    (TEST_EXPR_3, False, ("TEST", "DUMMY")),
    (TEST_EXPR_4, False, "XO"),
    (TEST_EXPR_5, False, TEST_DATA_1),
    (TEST_EXPR_6, False, False),
    (TEST_EXPR_7, False, ("TG1", "TG2", "TG3", "TG4")),
    (TEST_EXPR_8, False, TEST_DATA_1["biosamples"])
)

# Query, Internal, Result
DS_VALID_QUERIES = (
    (TEST_QUERY_1, False, True),
    (TEST_QUERY_2, False, True),
    (TEST_QUERY_3, False, True),
    (TEST_QUERY_4, False, True),
    (TEST_QUERY_5, False, False),
    (TEST_QUERY_6, False, False),
    (TEST_QUERY_7, True, True),
    (TEST_QUERY_8, False, True)
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
)

DS_INVALID_EXPRESSIONS = (
    *COMMON_INVALID_EXPRESSIONS,
    (["#_wc", "v1"], False, NotImplementedError)
)


# Query, Internal, Parameters
PG_VALID_QUERIES = (
    (TEST_QUERY_1, False, ("XO",)),
    (TEST_QUERY_2, False, ("%TE%",)),
    (TEST_QUERY_3, False, ("XO", "%TE%")),
    (TEST_QUERY_4, False, ("XO", "%TE%", False)),
    (TEST_QUERY_5, False, ("XO", "%TE%", False)),
    (TEST_QUERY_6, False, ("some_non_bool_value",)),
    (TEST_QUERY_7, True, ("1ac54805-4145-4829-93e2-f362de55f28f",)),
    (TEST_QUERY_8, False, ("MALE",))
)

PG_INVALID_EXPRESSIONS = (
    *COMMON_INVALID_EXPRESSIONS,
    (["#_wc", "v1", "v2"], False, SyntaxError),
    (["#_wc", ["#resolve", "biosamples"]], False, NotImplementedError),
    ({"dict": True}, False, ValueError),
)


def test_build_search_response():
    test_response = build_search_response({"some": "result"}, datetime.now())

    assert isinstance(test_response, dict)
    assert tuple(sorted(test_response.keys())) == ("results", "time")
    assert any((isinstance(test_response["results"], dict),
                isinstance(test_response["results"], list),
                isinstance(test_response["results"], tuple)))

    t = float(test_response["time"])
    assert t >= 0


def test_queries_and_ast():
    assert queries.Literal(5) == queries.Literal(5)
    assert queries.Literal("5") == queries.Literal("5")
    assert queries.Literal(True) == queries.Literal(True)
    assert queries.Literal(1.0) == queries.Literal(1.0)

    for f in TEST_FUNCTIONS:
        e = queries.Expression(fn=f[0], args=f[1:])
        assert e.fn == f[0]
        assert str(e.args) == str(f[1:])

    for f in TEST_INVALID_FUNCTIONS:
        with raises(AssertionError):
            queries.Expression(fn=f[0], args=[queries.Literal(a) for a in f[1:]])

    for f in TEST_INVALID_EXPRESSION_SYNTAX:
        with raises(SyntaxError):
            queries.convert_query_to_ast(f)

    for v in TEST_INVALID_LITERALS:
        with raises(AssertionError):
            queries.Literal(value=v)

        with raises(ValueError):
            queries.convert_query_to_ast(v)

    for b, a in TEST_REDUCE_NOTS:
        assert queries.convert_query_to_ast_and_preprocess(b) == \
            queries.convert_query_to_ast_and_preprocess(a)

    for q, s in TEST_QUERY_STR:
        assert str(queries.convert_query_to_ast_and_preprocess(q)) == s

    for b, a, in TEST_LIST_ANDS:
        assert all(bi == ai for bi, ai in
                   zip(queries.ast_to_and_asts(queries.convert_query_to_ast_and_preprocess(b)), a))

    assert queries.and_asts_to_ast(()) is None

    for b, a in TEST_UNLIST_ANDS:
        assert queries.and_asts_to_ast(queries.ast_to_and_asts(queries.convert_query_to_ast_and_preprocess(b))) == \
            queries.convert_query_to_ast_and_preprocess(a)


def test_postgres():
    # TODO: This is sort of artificial; does this case actually arise?
    assert postgres.collect_resolve_join_tables([], {}, None, None) == ()

    with raises(SyntaxError):
        postgres.search_query_to_psycopg2_sql(TEST_EXPR_8, TEST_INVALID_SCHEMA)

    for e, i, p in PG_VALID_QUERIES:
        _, params = postgres.search_query_to_psycopg2_sql(e, TEST_SCHEMA, i)
        assert params == p

    for e, i, _v in DS_VALID_EXPRESSIONS:
        postgres.search_query_to_psycopg2_sql(e, TEST_SCHEMA, i)

    for e, i, ex in PG_INVALID_EXPRESSIONS:
        with raises(ex):
            postgres.search_query_to_psycopg2_sql(e, TEST_SCHEMA, i)


def test_data_structure_search():
    for e, i, v in DS_VALID_EXPRESSIONS:
        assert data_structure.evaluate(queries.convert_query_to_ast(e), TEST_DATA_1, TEST_SCHEMA) == v

    for q, i, v in DS_VALID_QUERIES:
        assert data_structure.check_ast_against_data_structure(queries.convert_query_to_ast(q), TEST_DATA_1,
                                                               TEST_SCHEMA, i) == v

    for e, i, ex in DS_INVALID_EXPRESSIONS:
        with raises(ex):
            data_structure.evaluate(queries.convert_query_to_ast(e), TEST_DATA_1, TEST_SCHEMA, i)

    # Invalid data
    with raises(ValueError):
        data_structure.evaluate(queries.convert_query_to_ast(TEST_EXPR_1), INVALID_DATA, TEST_SCHEMA)


# noinspection PyProtectedMember
def test_check_operation_permissions():
    for e, i, _v in DS_VALID_EXPRESSIONS:
        queries.check_operation_permissions(
            queries.convert_query_to_ast(e),
            TEST_SCHEMA, search_getter=lambda rl, s: data_structure._resolve_with_search(rl, TEST_DATA_1, s)[1])
