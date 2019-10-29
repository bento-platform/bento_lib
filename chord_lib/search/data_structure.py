from jsonschema import validate, ValidationError
from operator import and_, or_, not_, lt, le, eq, gt, ge, contains
from typing import Callable, Dict, Tuple, Union

__all__ = ["check_query_against_data_structure"]


Query = Union[list, str, int, float, bool]
BaseQueryableStructure = Union[dict, list, str, int, float, bool]
QueryableStructure = Union[BaseQueryableStructure, Tuple['QueryableStructure']]
BBOperator = Callable[[BaseQueryableStructure, BaseQueryableStructure], bool]


def tuple_flatten(t) -> tuple:
    if isinstance(t, tuple):
        flattened = ()
        for v in t:
            flattened += tuple_flatten(v)

        return flattened

    return t,


def evaluate(query: Query, ds: QueryableStructure, schema: dict) -> QueryableStructure:
    """
    Evaluates a query expression into a value, populated by a passed data structure.
    :param query: A query expression.
    :param ds: A data structure from which to resolve values.
    :param schema:
    :return: A value (string, int, float, bool, array, or dict.)
    """

    if not isinstance(query, list):
        return query  # Literal

    if len(query) == 0:
        raise SyntaxError("Invalid expression: []")

    if not isinstance(query[0], str):
        raise SyntaxError("Invalid function: {}".format(query[0]))

    fn: str = query[0]
    args = query[1:]

    return QUERY_CHECK_SWITCH[fn](args, ds, schema)


# TODO: More rigorous / defined rules
def check_query_against_data_structure(query: Query, ds: QueryableStructure, schema: dict) -> bool:
    try:
        validate(ds, schema)
    except ValidationError:
        raise ValueError("Invalid data structure")

    # TODO: What to do here? Should be standardized, esp. w/r/t False returns
    return any(isinstance(e, bool) and e for e in tuple_flatten(evaluate(query, ds, schema)))


def _binary_op(op: BBOperator) -> Callable[[list, QueryableStructure, dict], bool]:
    def uncurried_binary_op(args: list, ds: QueryableStructure, schema: dict) -> bool:
        # TODO: Standardize type safety / behaviour!!!
        try:
            lhs = tuple_flatten(evaluate(args[0], ds, schema))
            rhs = tuple_flatten(evaluate(args[1], ds, schema))

            # Either LHS or RHS could be a tuple of [item]

            return any(op(li, ri) for li in lhs for ri in rhs)  # TODO: Type safety checks ahead-of-time

        except IndexError:
            raise SyntaxError("Cannot use binary operator {} on less than two values".format(op))

        except TypeError:
            raise TypeError("Type-invalid use of binary operator {}".format(op))

    return lambda args, ds, schema: uncurried_binary_op(args, ds, schema)


def _resolve(resolve: list, resolving_ds: QueryableStructure, schema: dict) -> QueryableStructure:
    # Assume data structure has already been checked against schema

    if len(resolve) == 0:
        # Resolve the root if it's an empty list
        return resolving_ds

    if schema["type"] == "object":
        if resolve[0] not in schema["properties"]:
            raise SyntaxError("Property {} not found in object".format(resolve[0]))

        # TODO: Should tuple_flatten be used here?
        return _resolve(
            resolve[1:],
            (resolving_ds[resolve[0]] if not isinstance(resolving_ds, tuple)
             else tuple(d[resolve[0]] for d in tuple_flatten(resolving_ds))),
            schema["properties"][resolve[0]])

    elif schema["type"] == "array":
        if resolve[0] != "[item]":
            raise SyntaxError("Cannot get property of array")

        # TODO: Should tuple_flatten be used here?
        return _resolve(
            resolve[1:],
            (tuple(resolving_ds) if not isinstance(resolving_ds, tuple)
             else tuple(tuple(d) for d in tuple_flatten(resolving_ds))),
            schema["items"])

    raise SyntaxError("Cannot get property of literal")


QUERY_CHECK_SWITCH: Dict[str, Callable[[list, QueryableStructure, dict], QueryableStructure]] = {
    "#and": _binary_op(and_),
    "#or": _binary_op(or_),
    "#not": lambda args, ds, schema: not_(check_query_against_data_structure(args[0], ds, schema)),

    "#lt": _binary_op(lt),
    "#le": _binary_op(le),
    "#eq": _binary_op(eq),
    "#gt": _binary_op(gt),
    "#ge": _binary_op(ge),

    "#co": _binary_op(contains),

    "#resolve": _resolve
}

# print(evaluate(["#and",
#                 ["#eq", ["#resolve", "subject", "karyotypic_sex"], "XO"],
#                 ["#co", ["#resolve", "biosamples", "[item]", "procedure", "code", "id"], "TE"]],
#                {
#                    "subject": {"karyotypic_sex": "XO"},
#                    "biosamples": [{"procedure": {"code": {"id": "TEST", "label": "TEST LABEL"}}}]
#                }, TEST_SCHEMA))
