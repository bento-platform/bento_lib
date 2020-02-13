import jsonschema
from operator import and_, or_, not_, lt, le, eq, gt, ge, contains
from typing import Callable, Dict, List, Tuple, Union, Optional

from .queries import *


__all__ = ["check_ast_against_data_structure"]


BaseQueryableStructure = Union[dict, list, str, int, float, bool]
QueryableStructure = Union[BaseQueryableStructure, Tuple["QueryableStructure"]]
BBOperator = Callable[[BaseQueryableStructure, BaseQueryableStructure], bool]

ResolveDict = Dict[str, Tuple[int, "ResolveDict"]]
IndexCombination = Dict[str, int]


def _validate_data_structure_against_schema(data_structure: QueryableStructure, schema: dict):
    try:
        jsonschema.validate(data_structure, schema)
    except jsonschema.ValidationError:
        raise ValueError("Invalid data structure: \n{}\nFor Schema: \n{}".format(data_structure, schema))


def _validate_not_wc(e: Expression):
    if e.fn == FUNCTION_HELPER_WC:
        raise NotImplementedError("Cannot use wildcard helper here")


def evaluate(ast: AST, data_structure: QueryableStructure, schema: dict,
             index_combination: Optional[IndexCombination], internal: bool = False, validate: bool = True)\
        -> QueryableStructure:
    """
    Evaluates a query expression into a value, populated by a passed data structure.
    :param ast: A query expression.
    :param data_structure: A data structure from which to resolve values.
    :param schema: The JSON schema for data objects being queried.
    :param index_combination: The combination of array indices being evaluated upon.
    :param internal: Whether internal-only fields are allowed to be resolved.
    :param validate: Whether to validate the structure against the schema. Typically called only once per evaluate.
    :return: A value (string, int, float, bool, array, or dict.)
    """

    if validate:
        _validate_data_structure_against_schema(data_structure, schema)

    if isinstance(ast, Literal):
        return ast.value

    _validate_not_wc(ast)

    check_operation_permissions(
        ast,
        schema,
        search_getter=lambda rl, s: _resolve_with_properties(rl, data_structure, s, index_combination, internal)[1],
        internal=internal)

    return QUERY_CHECK_SWITCH[ast.fn](ast.args, data_structure, schema, index_combination, internal)


def _collect_array_lengths(ast: AST, data_structure: QueryableStructure, schema: dict) -> Dict[str, Tuple[int, dict]]:
    if isinstance(ast, Literal):
        return {}

    _validate_not_wc(ast)

    if ast.fn == FUNCTION_RESOLVE:
        r = _resolve_array_lengths(ast.args, data_structure, schema)
        return {r[0]: r[1:]} if r is not None else {}

    array_lengths = {}
    for e in ast.args:
        al = _collect_array_lengths(e, data_structure, schema)
        for k, v in al.items():
            if k not in array_lengths:
                array_lengths[k] = v
            else:
                array_lengths[k] = (array_lengths[k][0], {**array_lengths[k][1], **v[1]})

    return array_lengths


def _create_all_index_combinations(array_data: Dict[str, Tuple[int, Dict]], parent_template):
    combinations = []

    if len(array_data) == 0:
        # Add in the finished list of indexes as the base case
        combinations.append(parent_template)

    # Otherwise, loop through and recurse
    for c_path, c_resolve in array_data.items():
        for i in range(c_resolve[0]):
            item_template = {**parent_template, c_path: i}
            combinations.extend(_create_all_index_combinations(c_resolve[1], item_template))

    return tuple(combinations)


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

    _validate_data_structure_against_schema(data_structure, schema)

    # Collect all array resolves and their lengths in order to properly cross-product arrays
    array_lengths = _collect_array_lengths(ast, data_structure, schema)

    # Create all combinations of indexes into arrays
    index_combinations = _create_all_index_combinations(array_lengths, {})

    # TODO: What to do here? Should be standardized, esp. w/r/t False returns
    # Loop through all combinations of array indices to freeze "[item]"s at particular indices across the whole query.
    for ic in index_combinations:
        # Don't need to re-validate data structure
        e = evaluate(ast, data_structure, schema, ic, internal, validate=False)
        if isinstance(e, bool) and e:
            return True

    return False


def _binary_op(op: BBOperator)\
        -> Callable[[List[AST], QueryableStructure, dict, bool, Optional[IndexCombination]], bool]:
    """
    Returns a lambda which will evaluate a boolean-returning binary operator on a pair of arguments against a
    data structure/object of some type and return a Boolean result.
    :param op: The operator the lambda is representing.
    :return: Operator lambda for use in evaluating expressions.
    """

    def uncurried_binary_op(args: List[AST], ds: QueryableStructure, schema: dict, ic: Optional[IndexCombination],
                            internal: bool) -> bool:
        # TODO: Standardize type safety / behaviour!!!

        lhs = evaluate(args[0], ds, schema, ic, internal, validate=False)
        rhs = evaluate(args[1], ds, schema, ic, internal, validate=False)

        try:
            return op(lhs, rhs)
        except TypeError:
            raise TypeError(f"Type-invalid use of binary operator {op} ({lhs}, {rhs})")

    return lambda args, ds, schema, ic, internal: uncurried_binary_op(args, ds, schema, ic, internal)


def _resolve_checks(resolve, schema):
    if schema["type"] not in ("object", "array"):
        raise TypeError("Cannot get property of literal")

    elif schema["type"] == "object" and resolve[0].value not in schema["properties"]:
        raise ValueError("Property {} not found in object, {}".format(resolve[0].value, [x.value for x in resolve]))

    elif schema["type"] == "array" and resolve[0].value != "[item]":
        raise TypeError("Cannot get property of array")


def _resolve_array_lengths(
    resolve: List[Literal],
    resolving_ds: QueryableStructure,
    schema: dict,
    path="_root",
) -> Tuple[str, int, ResolveDict]:
    if len(resolve) == 0:
        # Resolve the root if it's an empty list
        return (path, len(resolving_ds), {}) if schema["type"] == "array" else None

    _resolve_checks(resolve, schema)

    if resolve[0].value == "[item]":
        resolves = {}
        for i in range(len(resolving_ds)):
            r = _resolve_array_lengths(resolve[1:], resolving_ds[i], schema["items"], f"{path}.{resolve[0].value}")
            if r is not None and r[0] not in resolves:
                resolves[r[0]] = r[1:]

        return path, len(resolving_ds), resolves

    return _resolve_array_lengths(resolve[1:], resolving_ds[resolve[0].value], schema["properties"][resolve[0].value],
                                  f"{path}.{resolve[0].value}")


def _resolve_with_properties(
    resolve: List[Literal],
    resolving_ds: QueryableStructure,
    schema: dict,
    index_combination: Optional[IndexCombination],
    internal: bool = False,
    path="_root",
) -> Tuple[QueryableStructure, dict]:
    """
    Resolves / evaluates a path (either object or array) into a value and its search properties. Assumes the
    data structure has already been checked against its schema.
    :param resolve: The current path to resolve, not including the current data structure.
    :param resolving_ds: The data structure being resolved upon.
    :param schema: The JSON schema representing the resolving data structure.
    :param index_combination: The combination of array indices being evaluated upon
    :param internal: Whether internal-only fields are allowed to be resolved.
    :param path: A string representation of the path to the currently-resolved data structure.
    :return: The resolved value after exploring the resolve path, and the search operations that can be performed on it.
    """

    if len(resolve) == 0:
        # Resolve the root if it's an empty list
        return resolving_ds, schema.get("search", {}),

    _resolve_checks(resolve, schema)

    if resolve[0].value == "[item]" and (index_combination is None or path not in index_combination):
        # TODO: Specific exception class
        raise Exception(f"Index combination not provided for path {path}")

    return _resolve_with_properties(
        resolve[1:],
        resolving_ds[resolve[0].value] if schema["type"] == "object" else resolving_ds[index_combination[path]],
        schema["properties"][resolve[0].value] if schema["type"] == "object" else schema["items"],
        index_combination,
        internal,
        path=f"{path}.{resolve[0]}")


def _resolve(resolve: List[Literal], resolving_ds: QueryableStructure, schema: dict,
             index_combination: Optional[Dict[str, int]], internal: bool = False):
    """
    Does the same thing as _resolve_with_properties, but discards the search properties.
    """
    return _resolve_with_properties(resolve, resolving_ds, schema, index_combination, internal)[0]


QUERY_CHECK_SWITCH: Dict[
    FunctionName,
    Callable[[List[AST], QueryableStructure, dict, bool, Optional[IndexCombination]], QueryableStructure]
] = {
    FUNCTION_AND: _binary_op(and_),
    FUNCTION_OR: _binary_op(or_),
    FUNCTION_NOT: lambda args, ds, schema, internal, ic: not_(evaluate(args[0], ds, schema, internal, ic,
                                                                       validate=False)),

    FUNCTION_LT: _binary_op(lt),
    FUNCTION_LE: _binary_op(le),
    FUNCTION_EQ: _binary_op(eq),
    FUNCTION_GT: _binary_op(gt),
    FUNCTION_GE: _binary_op(ge),

    FUNCTION_CO: _binary_op(contains),

    FUNCTION_RESOLVE: _resolve
}
