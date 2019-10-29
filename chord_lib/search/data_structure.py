from jsonschema import validate, ValidationError
from operator import and_, or_, not_, lt, le, eq, gt, ge
from typing import Union

__all__ = ["check_query_against_data_structure"]


Query = Union[list, str, int, float, bool]
QueryableStructure = Union[dict, list, str, int, float, bool]


def evaluate(query: Query, ds, schema):
    if not isinstance(query, list):
        return query  # Literal

    if len(query) == 0:
        raise SyntaxError("Invalid expression: []")

    fn = query[0]
    args = query[1:]

    return QUERY_CHECK_SWITCH[fn](args, ds, schema)


# TODO: More rigorous / defined rules
def check_query_against_data_structure(query: Query, ds: QueryableStructure, schema: dict) -> bool:
    try:
        validate(ds, schema)
    except ValidationError:
        raise ValueError("Invalid data structure")

    ev = evaluate(query, ds, schema)

    if not isinstance(ev, tuple):
        ev = ev,

    for e in ev:
        if isinstance(ev, bool) and e:
            return True

    # TODO: What to do here? Should be standardized
    return False


def uncurried_binary_op(op, args, ds, schema):
    lhs = evaluate(args[0], ds, schema)
    rhs = evaluate(args[1], ds, schema)

    # Either LHS or RHS could be a tuple of [item]

    # TODO: Multiple levels of tuples!!

    if not isinstance(lhs, tuple):
        lhs = lhs,

    if not isinstance(rhs, tuple):
        rhs = rhs,

    return any(op(li, ri) for li in lhs for ri in rhs)


def _binary_op(op):
    return lambda args, ds, schema: uncurried_binary_op(op, args, ds, schema)


def _contains(args, ds, schema):
    # TODO: Standardize type safety / behaviour!!!
    lhs = evaluate(args[0], ds, schema)
    rhs = evaluate(args[1], ds, schema)

    # Either LHS or RHS could be a tuple of [item]

    # TODO: Multiple levels of tuples!!

    if not isinstance(lhs, tuple):
        lhs = lhs,

    if not isinstance(rhs, tuple):
        rhs = rhs,

    return any(ri in li for li in lhs for ri in rhs)  # TODO: Very not type safe!!!


def resolve_rec(resolve, ds, schema):
    # Assume data structure has already been checked against schema

    if len(resolve) == 0:
        return ds

    if schema["type"] == "object":
        if resolve[0] not in schema["properties"]:
            raise SyntaxError("Property {} not found in object".format(resolve[0]))

        return resolve_rec(resolve[1:],
                           ds[resolve[0]] if not isinstance(ds, tuple) else tuple(d[resolve[0]] for d in ds),
                           schema["properties"][resolve[0]])

    elif schema["type"] == "array":
        if resolve[0] != "[item]":
            raise SyntaxError("Cannot get property of array")

        # TODO: Multiple levels of tuple

        return resolve_rec(resolve[1:], tuple(ds) if not isinstance(ds, tuple) else tuple(tuple(d) for d in ds),
                           schema["items"])

    raise SyntaxError("Cannot get property of literal")


def _resolve(args, ds, schema):
    return resolve_rec(args, ds, schema)


QUERY_CHECK_SWITCH = {
    "#and": _binary_op(and_),
    "#or": _binary_op(or_),
    "#not": lambda args, ds, schema: not_(check_query_against_data_structure(args[0], ds, schema)),

    "#lt": _binary_op(lt),
    "#le": _binary_op(le),
    "#eq": _binary_op(eq),
    "#gt": _binary_op(gt),
    "#ge": _binary_op(ge),

    "#co": _contains,

    "#resolve": _resolve
}

# print(evaluate(["#and",
#                 ["#eq", ["#resolve", "subject", "karyotypic_sex"], "XO"],
#                 ["#co", ["#resolve", "biosamples", "[item]", "procedure", "code", "id"], "TE"]],
#                {
#                    "subject": {"karyotypic_sex": "XO"},
#                    "biosamples": [{"procedure": {"code": {"id": "TEST", "label": "TEST LABEL"}}}]
#                }, TEST_SCHEMA))
