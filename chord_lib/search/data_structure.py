import jsonschema
from collections.abc import Iterable
from itertools import chain
from operator import and_, or_, not_, lt, le, eq, gt, ge, contains
from typing import Callable, Dict, List, Tuple, Union

from .queries import *


__all__ = ["check_ast_against_data_structure"]


BaseQueryableStructure = Union[dict, list, str, int, float, bool]
QueryableStructure = Union[BaseQueryableStructure, Tuple["QueryableStructure"]]
BBOperator = Callable[[BaseQueryableStructure, BaseQueryableStructure], bool]


def _is_gen_flatten_compatible(t):
    try:
        iter(t)
        return not isinstance(t, str) and not isinstance(t, list) and not isinstance(t, dict)
    except TypeError:
        return False


def generator_flatten(t) -> Iterable:
    """
    Flattens a possibly nested tuple or base queryable structure into a 1-dimensional generator.
    :param t: The value to flatten and or expand into a 1-dimensional generator.
    :return: A generator of flattened values.
    """
    return chain.from_iterable(generator_flatten(v) for v in t) if _is_gen_flatten_compatible(t) else (t,)


def evaluate(ast: AST, data_structure: QueryableStructure, schema: dict, internal: bool = False,
             validate: bool = True) -> QueryableStructure:
    """
    Evaluates a query expression into a value, populated by a passed data structure.
    :param ast: A query expression.
    :param data_structure: A data structure from which to resolve values.
    :param schema: The JSON schema for data objects being queried.
    :param internal: Whether internal-only fields are allowed to be resolved.
    :param validate: Whether to validate the structure against the schema. Typically called only once per evaluate.
    :return: A value (string, int, float, bool, array, or dict.)
    """

    if validate:
        try:
            jsonschema.validate(data_structure, schema)
        except jsonschema.ValidationError:
            raise ValueError("Invalid data structure: \n{}\nFor Schema: \n{}".format(data_structure, schema))

    if isinstance(ast, Literal):
        return ast.value

    if ast.fn == FUNCTION_HELPER_WC:
        raise NotImplementedError("Cannot use wildcard helper here")

    check_operation_permissions(
        ast,
        schema,
        search_getter=lambda rl, s: _resolve_with_search(rl, data_structure, s, internal)[1],
        internal=internal)

    return QUERY_CHECK_SWITCH[ast.fn](ast.args, data_structure, schema, internal)


# TODO: More rigorous / defined rules
def check_ast_against_data_structure(
    ast: AST,
    data_structure: QueryableStructure,
    schema: dict,
    internal: bool = False
) -> bool:
    """
    Checks a query against a data structure, returning True if the
    :param ast: A query to evaluate against the data object.
    :param data_structure: The data object to evaluate the query against.
    :param schema: A JSON schema representing valid data objects.
    :param internal: Whether internal-only fields are allowed to be resolved.
    :return: A boolean representing whether or not the query matches the data object.
    """

    # TODO: What to do here? Should be standardized, esp. w/r/t False returns
    return any(isinstance(e, bool) and e for e in generator_flatten(evaluate(ast, data_structure, schema, internal)))


def _binary_op(op: BBOperator) -> Callable[[List[AST], QueryableStructure, dict, bool], bool]:
    """
    Returns a lambda which will evaluate a boolean-returning binary operator on a pair of arguments against a
    data structure/object of some type and return a Boolean result.
    :param op: The operator the lambda is representing.
    :return: Operator lambda for use in evaluating expressions.
    """

    def uncurried_binary_op(args: List[AST], ds: QueryableStructure, schema: dict, internal: bool) -> bool:
        # TODO: Standardize type safety / behaviour!!!
        try:
            # Either LHS or RHS could be a tuple of [item]
            return any(
                op(li, ri)
                for li in generator_flatten(evaluate(args[0], ds, schema, internal, validate=False))  # LHS, Outer loop
                for ri in generator_flatten(evaluate(args[1], ds, schema, internal, validate=False))  # RHS, Inner loop
            )

        except TypeError:
            raise TypeError("Type-invalid use of binary operator {}".format(op))

    return lambda args, ds, schema, internal: uncurried_binary_op(args, ds, schema, internal)


def preserved_tuple_apply(
    v: QueryableStructure,
    fn: Callable[[BaseQueryableStructure], QueryableStructure]
) -> QueryableStructure:
    # TODO: Should generator_flatten be used here?
    return fn(v) if not isinstance(v, tuple) else tuple(fn(d) for d in generator_flatten(v))


def curried_get(k) -> Callable:
    return lambda v: v[k]


def _resolve_with_search(
    resolve: List[Literal],
    resolving_ds: QueryableStructure,
    schema: dict,
    internal: bool = False
) -> Tuple[QueryableStructure, dict]:
    """
    Resolves / evaluates a path (either object or array) into a value and its search properties. Assumes the
    data structure has already been checked against its schema.
    :param resolve: The current path to resolve, not including the current data structure.
    :param resolving_ds: The data structure being resolved upon.
    :param schema: The JSON schema representing the resolving data structure.
    :param internal: Whether internal-only fields are allowed to be resolved.
    :return: The resolved value after exploring the resolve path, and the search operations that can be performed on it.
    """

    if len(resolve) == 0:
        # Resolve the root if it's an empty list
        return resolving_ds, schema.get("search", {})

    if schema["type"] not in ("object", "array"):
        raise TypeError("Cannot get property of literal")

    elif schema["type"] == "object" and resolve[0].value not in schema["properties"]:
        raise ValueError("Property {} not found in object, {}".format(resolve[0].value, [x.value for x in resolve]))

    elif schema["type"] == "array" and resolve[0].value != "[item]":
        raise TypeError("Cannot get property of array")

    return _resolve_with_search(
        resolve[1:],
        preserved_tuple_apply(resolving_ds, curried_get(resolve[0].value) if schema["type"] == "object" else tuple),
        schema["properties"][resolve[0].value] if schema["type"] == "object" else schema["items"],
        internal)


def _resolve(resolve: List[Literal], resolving_ds: QueryableStructure, schema: dict, internal: bool):
    """
    Does the same thing as _resolve_with_ops, but discards the search operations.
    """
    return _resolve_with_search(resolve, resolving_ds, schema, internal)[0]


QUERY_CHECK_SWITCH: Dict[FunctionName, Callable[[List[AST], QueryableStructure, dict, bool], QueryableStructure]] = {
    FUNCTION_AND: _binary_op(and_),
    FUNCTION_OR: _binary_op(or_),
    FUNCTION_NOT: lambda args, ds, schema, internal: not_(evaluate(args[0], ds, schema, internal, validate=False)),

    FUNCTION_LT: _binary_op(lt),
    FUNCTION_LE: _binary_op(le),
    FUNCTION_EQ: _binary_op(eq),
    FUNCTION_GT: _binary_op(gt),
    FUNCTION_GE: _binary_op(ge),

    FUNCTION_CO: _binary_op(contains),

    FUNCTION_RESOLVE: _resolve
}
