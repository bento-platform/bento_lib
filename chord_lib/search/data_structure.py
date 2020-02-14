import jsonschema
from operator import and_, or_, not_, lt, le, eq, gt, ge, contains
from typing import Callable, Dict, List, Optional, Tuple, Union

from .queries import *


__all__ = ["check_ast_against_data_structure"]


QueryableStructure = Union[dict, list, str, int, float, bool]
BBOperator = Callable[[QueryableStructure, QueryableStructure], bool]

ResolveDict = Dict[str, Tuple[int, "ResolveDict"]]
IndexCombination = Dict[str, int]


def _validate_data_structure_against_schema(data_structure: QueryableStructure, schema: dict):
    """
    Validates a queryable data structure of some type against a JSON schema. This is an important validation step,
    because (assuming the schema is correct) it allows methods to make more assumptions about the integrity of the
    data structure while traversing it.
    :param data_structure: The data structure to validate
    :param schema: The JSON schema to validate the data structure against
    """
    try:
        jsonschema.validate(data_structure, schema)
    except jsonschema.ValidationError:
        raise ValueError("Invalid data structure: \n{}\nFor Schema: \n{}".format(data_structure, schema))


def _validate_not_wc(e: Expression):
    """
    The #_wc expression function is a helper for converting the queries into the Postgres IR. If we encounter this
    function in a query being evaluated against a data structure, it's meaningless and should raise an error.
    :param e: The expression (function) to check
    """
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

    # The validate flag is used to avoid redundantly validating the integrity of child data structures
    if validate:
        _validate_data_structure_against_schema(data_structure, schema)

    # A literal (e.g. <Literal value=5>) evaluates to its own value (5)
    if isinstance(ast, Literal):
        return ast.value

    # Prevents the Postgres internal-only #_wc function from being used in expressions being evaluated against Python
    # data structures. See the documentation for _validate_not_wc.
    _validate_not_wc(ast)

    # Check that the current permissions (internal or not) allow us to perform the current operation on any resolved
    # fields. Internal queries are used for joins, etc. by services, or are performed by someone with unrestricted
    # access to the data.
    # TODO: This could be made more granular (some people could be given access to specific objects / tables)
    check_operation_permissions(
        ast,
        schema,
        search_getter=lambda rl, s: _resolve_with_properties(rl, data_structure, s, index_combination, internal)[1],
        internal=internal)

    # Evaluate the non-literal expression recursively.
    return QUERY_CHECK_SWITCH[ast.fn](ast.args, data_structure, schema, index_combination, internal)


def _collect_array_lengths(ast: AST, data_structure: QueryableStructure, schema: dict) -> Dict[str, Tuple[int, dict]]:
    """
    To evaluate a query in a manner consistent with the Postgres evaluator (and facilitate richer queries), each array
    item needs to be fixed in a particular evaluation of a query that involves array accesses. This helper function
    collects the lengths of arrays for each different array used in the field; it does this by traversing the data
    structure. These can be later used by _create_all_index_combinations to create all possible combinations of accesses
    to fix them in an evaluation run.
    :param ast: The AST-ified query
    :param data_structure: The FULL data structure the query is being evaluated against
    :param schema: The JSON schema of the full data structure
    :return: A recursive dictionary with keys being array paths and values being a tuple of (length, children dict)
    """

    # Literals are not arrays (currently), so they will not have any specified lengths
    if isinstance(ast, Literal):
        return {}

    # Standard validation to prevent Postgres internal-style queries from being passed in (see _validate_not_wc docs)
    _validate_not_wc(ast)

    # Resolves are where the magic happens w/r/t array access. Capture any array accesses with their lengths and child
    # array accesses and store them in the recursive dictionary.
    if ast.fn == FUNCTION_RESOLVE:
        r = _resolve_array_lengths(ast.args, data_structure, schema)
        return {r[0]: r[1:]} if r is not None else {}

    # If the current expression is a non-resolve function, recurse into its arguments and collect any additional array
    # accesses; then, store them in the recursive dictionary.

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
    if len(array_data) == 0:
        # Add in the finished list of indexes as the base case
        yield parent_template

    # Otherwise, loop through and recurse
    for c_path, c_resolve in array_data.items():
        for i in range(c_resolve[0]):
            item_template = {**parent_template, c_path: i}
            yield from _create_all_index_combinations(c_resolve[1], item_template)


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
