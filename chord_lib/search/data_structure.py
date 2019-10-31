from jsonschema import validate, ValidationError
from operator import and_, or_, not_, lt, le, eq, gt, ge, contains
from typing import Callable, Dict, Tuple, Union

from .queries import *


__all__ = ["check_query_against_data_structure"]


BaseQueryableStructure = Union[dict, list, str, int, float, bool]
QueryableStructure = Union[BaseQueryableStructure, Tuple['QueryableStructure']]
BBOperator = Callable[[BaseQueryableStructure, BaseQueryableStructure], bool]


def tuple_flatten(t) -> tuple:
    """
    Flattens a possibly nested tuple or non-tuple into a 1-dimensional tuple.
    :param t: The value to flatten and or expand into a 1-dimensional tuple.
    :return: The flattened tuple.
    """

    if isinstance(t, tuple):
        flattened = ()
        for v in t:
            flattened += tuple_flatten(v)

        return flattened

    return t,


def evaluate(query: Query, data_structure: QueryableStructure, schema: dict) -> QueryableStructure:
    """
    Evaluates a query expression into a value, populated by a passed data structure.
    :param query: A query expression.
    :param data_structure: A data structure from which to resolve values.
    :param schema: The JSON schema for data objects being queried.
    :return: A value (string, int, float, bool, array, or dict.)
    """

    # Try converting to AST for validation reasons, although this doesn't use the AST directly (for now)
    convert_query_to_ast_and_preprocess(query)

    try:
        validate(data_structure, schema)
    except ValidationError:
        raise ValueError("Invalid data structure")

    if not isinstance(query, list):
        return query  # Literal

    fn: str = query[0]
    args = query[1:]

    if fn == FUNCTION_HELPER_WC:
        raise NotImplementedError("Cannot use wildcard helper here")

    return QUERY_CHECK_SWITCH[fn](args, data_structure, schema)


# TODO: More rigorous / defined rules
def check_query_against_data_structure(query: Query, data_structure: QueryableStructure, schema: dict) -> bool:
    """
    Checks a query against a data structure, returning True if the
    :param query: A query to evaluate against the data object.
    :param data_structure: The data object to evaluate the query against.
    :param schema: A JSON schema representing valid data objects.
    :return: A boolean representing whether or not the query matches the data object.
    """
    # TODO: What to do here? Should be standardized, esp. w/r/t False returns
    return any(isinstance(e, bool) and e for e in tuple_flatten(evaluate(query, data_structure, schema)))


def _binary_op(op: BBOperator) -> Callable[[list, QueryableStructure, dict], bool]:
    """
    Returns a lambda which will evaluate a boolean-returning binary operator on a pair of arguments against a
    data structure/object of some type and return a Boolean result.
    :param op: The operator the lambda is representing.
    :return: Operator lambda for use in evaluating expressions.
    """

    def uncurried_binary_op(args: list, ds: QueryableStructure, schema: dict) -> bool:
        # TODO: Standardize type safety / behaviour!!!
        try:
            lhs = tuple_flatten(evaluate(args[0], ds, schema))
            rhs = tuple_flatten(evaluate(args[1], ds, schema))

            # Either LHS or RHS could be a tuple of [item]

            return any(op(li, ri) for li in lhs for ri in rhs)  # TODO: Type safety checks ahead-of-time

        except TypeError:
            raise TypeError("Type-invalid use of binary operator {}".format(op))

    return lambda args, ds, schema: uncurried_binary_op(args, ds, schema)


def _resolve(resolve: list, resolving_ds: QueryableStructure, schema: dict) -> QueryableStructure:
    """
    Resolves / evaluates a path (either object or array) into a value. Assumes the data structure has already been
    checked against its schema.
    :param resolve: The current path to resolve, not including the current data structure.
    :param resolving_ds: The data structure being resolved upon.
    :param schema: The JSON schema representing the resolving data structure.
    :return: The resolved value after exploring the resolve path.
    """

    if len(resolve) == 0:
        # Resolve the root if it's an empty list
        return resolving_ds

    if schema["type"] == "object":
        if resolve[0] not in schema["properties"]:
            raise ValueError("Property {} not found in object".format(resolve[0]))

        # TODO: Should tuple_flatten be used here?
        return _resolve(
            resolve[1:],
            (resolving_ds[resolve[0]] if not isinstance(resolving_ds, tuple)
             else tuple(d[resolve[0]] for d in tuple_flatten(resolving_ds))),
            schema["properties"][resolve[0]])

    elif schema["type"] == "array":
        if resolve[0] != "[item]":
            raise TypeError("Cannot get property of array")

        # TODO: Should tuple_flatten be used here?
        return _resolve(
            resolve[1:],
            (tuple(resolving_ds) if not isinstance(resolving_ds, tuple)
             else tuple(tuple(d) for d in tuple_flatten(resolving_ds))),
            schema["items"])

    raise TypeError("Cannot get property of literal")


QUERY_CHECK_SWITCH: Dict[FunctionName, Callable[[list, QueryableStructure, dict], QueryableStructure]] = {
    FUNCTION_AND: _binary_op(and_),
    FUNCTION_OR: _binary_op(or_),
    FUNCTION_NOT: lambda args, ds, schema: not_(check_query_against_data_structure(args[0], ds, schema)),

    FUNCTION_LT: _binary_op(lt),
    FUNCTION_LE: _binary_op(le),
    FUNCTION_EQ: _binary_op(eq),
    FUNCTION_GT: _binary_op(gt),
    FUNCTION_GE: _binary_op(ge),

    FUNCTION_CO: _binary_op(contains),

    FUNCTION_RESOLVE: _resolve
}
