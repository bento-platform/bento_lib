from chord_lib.search import *
from datetime import datetime
from pytest import raises


TEST_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {
            "type": "string",
            "search": {
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
                    },
                    "tumor_grade": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
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


TEST_QUERY_1 = ["#eq", ["#resolve", "subject", "karyotypic_sex"], "XO"]
TEST_QUERY_2 = ["#co", ["#resolve", "biosamples", "[item]", "procedure", "code", "id"], "TE"]
TEST_QUERY_3 = ["#and", TEST_QUERY_1, TEST_QUERY_2]
TEST_QUERY_4 = ["#or", TEST_QUERY_3, False]
TEST_QUERY_5 = ["#and", TEST_QUERY_3, False]
TEST_QUERY_6 = "some_non_bool_value"
TEST_QUERY_7 = ["#eq", ["#resolve", "id"], "1ac54805-4145-4829-93e2-f362de55f28f"]

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


TEST_DATA_1 = {
    "id": "1ac54805-4145-4829-93e2-f362de55f28f",
    "subject": {"karyotypic_sex": "XO"},
    "biosamples": [
        {
            "procedure": {"code": {"id": "TEST", "label": "TEST LABEL"}},
            "tumor_grade": [{"id": "TG1", "label": "TG1 LABEL"}, {"id": "TG2", "label": "TG2 LABEL"}]
        },
        {
            "procedure": {"code": {"id": "DUMMY", "label": "DUMMY LABEL"}},
            "tumor_grade": [{"id": "TG3", "label": "TG3 LABEL"}, {"id": "TG4", "label": "TG4 LABEL"}]
        }
    ]
}

INVALID_DATA = [{True, False}]


DS_VALID_EXPRESSIONS = (
    (TEST_EXPR_1, TEST_EXPR_1),
    (TEST_EXPR_2, TEST_EXPR_2),
    (TEST_EXPR_3, ("TEST", "DUMMY")),
    (TEST_EXPR_4, "XO"),
    (TEST_EXPR_5, TEST_DATA_1),
    (TEST_EXPR_6, False),
    (TEST_EXPR_7, ("TG1", "TG2", "TG3", "TG4")),
    (TEST_EXPR_8, TEST_DATA_1["biosamples"])
)

DS_VALID_QUERIES = (
    (TEST_QUERY_1, True),
    (TEST_QUERY_2, True),
    (TEST_QUERY_3, True),
    (TEST_QUERY_4, True),
    (TEST_QUERY_5, False),
    (TEST_QUERY_6, False),
    (TEST_QUERY_7, True),
)

DS_INVALID_EXPRESSIONS = (
    (INVALID_EXPR_1, SyntaxError),
    (INVALID_EXPR_2, SyntaxError),
    (INVALID_EXPR_3, TypeError),
    (INVALID_EXPR_4, ValueError),
    (INVALID_EXPR_5, TypeError),
    (INVALID_EXPR_6, TypeError),
    (INVALID_EXPR_7, SyntaxError),
    (INVALID_EXPR_8, SyntaxError),
)


PG_VALID_QUERIES = (
    (TEST_QUERY_1, ("XO",)),
    (TEST_QUERY_2, ("%TE%",)),
    (TEST_QUERY_3, ("XO", "%TE%")),
    (TEST_QUERY_4, ("XO", "%TE%", False)),
    (TEST_QUERY_5, ("XO", "%TE%", False)),
    (TEST_QUERY_6, ("some_non_bool_value",)),
    (TEST_QUERY_7, ("1ac54805-4145-4829-93e2-f362de55f28f",)),
)

PG_INVALID_EXPRESSIONS = (
    *DS_INVALID_EXPRESSIONS,
    (["#_wc", "v1", "v2"], SyntaxError),
    (["#_wc", ["#resolve", "biosamples"]], NotImplementedError),
    ({"dict": True}, NotImplementedError),
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


def test_postgres():
    # TODO: This is sort of artificial; does this case actually arise?
    assert postgres.collect_resolve_join_tables([], {}, None, None) == ()

    with raises(SyntaxError):
        postgres.search_query_to_psycopg2_sql(TEST_EXPR_8, TEST_INVALID_SCHEMA)

    for e, p in PG_VALID_QUERIES:
        _, params = postgres.search_query_to_psycopg2_sql(e, TEST_SCHEMA)
        assert params == p

    for e, _v in DS_VALID_EXPRESSIONS:
        postgres.search_query_to_psycopg2_sql(e, TEST_SCHEMA)

    for e, ex in PG_INVALID_EXPRESSIONS:
        with raises(ex):
            postgres.search_query_to_psycopg2_sql(e, TEST_SCHEMA)


def test_data_structure_search():
    for e, v in DS_VALID_EXPRESSIONS:
        assert data_structure.evaluate(e, TEST_DATA_1, TEST_SCHEMA) == v

    for q, v in DS_VALID_QUERIES:
        assert data_structure.check_query_against_data_structure(q, TEST_DATA_1, TEST_SCHEMA) == v

    for e, ex in DS_INVALID_EXPRESSIONS:
        with raises(ex):
            data_structure.evaluate(e, TEST_DATA_1, TEST_SCHEMA)

    # Invalid data
    with raises(ValueError):
        data_structure.evaluate(TEST_EXPR_1, INVALID_DATA, TEST_SCHEMA)
