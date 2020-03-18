import jsonschema
from functools import partial
from itertools import chain, product, starmap
from operator import and_, or_, not_, lt, le, eq, gt, ge, contains, is_not
from typing import Callable, Dict, List, Iterable, Optional, Tuple, Union

from chord_lib.search import queries as q


__all__ = ["check_ast_against_data_structure"]


QueryableStructure = Union[dict, list, str, int, float, bool]
BBOperator = Callable[[QueryableStructure, QueryableStructure], bool]

FunctionArgs = List[q.AST]

IndexCombination = Dict[str, int]
ArrayLengthData = Tuple[str, int, Tuple["ArrayLengthData", ...]]


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


def _validate_not_wc(e: q.Expression):
    """
    The #_wc expression function is a helper for converting the queries into the Postgres IR. If we encounter this
    function in a query being evaluated against a data structure, it's meaningless and should raise an error.
    :param e: The expression (function) to check
    """
    if e.fn == q.FUNCTION_HELPER_WC:
        raise NotImplementedError("Cannot use wildcard helper here")


def evaluate_no_validate(
    ast: q.AST,
    data_structure: QueryableStructure,
    schema: dict,
    index_combination: Optional[IndexCombination],
    internal: bool = False,
    resolve_checks: bool = True,
    check_permissions: bool = True,
) -> QueryableStructure:
    """
    Evaluates a query expression into a value, populated by a passed data structure.
    :param ast: A query expression.
    :param data_structure: A data structure from which to resolve values.
    :param schema: The JSON schema for data objects being queried.
    :param index_combination: The combination of array indices being evaluated upon.
    :param internal: Whether internal-only fields are allowed to be resolved.
    :param resolve_checks: Whether to run resolve checks. Should only be run once per query/ds/schema combo
    :param check_permissions: Whether to check the operation permissions. Typically called once per AST/DS combo.
    :return: A value (string, int, float, bool, array, or dict.)
    """

    # A literal (e.g. <Literal value=5>) evaluates to its own value (5)
    if ast.type == "l":
        return ast.value

    if resolve_checks:  # TODO: Separate setting
        # Prevents the Postgres internal-only #_wc function from being used in expressions being evaluated against
        # Python data structures. See the documentation for _validate_not_wc. Should only be run once per AST.
        _validate_not_wc(ast)

    if check_permissions:
        # Check that the current permissions (internal or not) allow us to perform the current operation on any resolved
        # fields. Internal queries are used for joins, etc. by services, or are performed by someone with unrestricted
        # access to the data.
        # TODO: This could be made more granular (some people could be given access to specific objects / tables)
        q.check_operation_permissions(
            ast,
            schema,
            lambda rl, s: _resolve_properties_and_check(rl, s, index_combination),
            internal)

    # Evaluate the non-literal expression recursively.
    return QUERY_CHECK_SWITCH[ast.fn](ast.args, data_structure, schema, index_combination, internal, resolve_checks,
                                      check_permissions)


def evaluate(
    ast: q.AST,
    data_structure: QueryableStructure,
    schema: dict,
    index_combination: Optional[IndexCombination],
    internal: bool = False,
    resolve_checks: bool = True,
    check_permissions: bool = True,
):
    # The validate flag is used to avoid redundantly validating the integrity of child data structures
    _validate_data_structure_against_schema(data_structure, schema)
    return evaluate_no_validate(ast, data_structure, schema, index_combination, internal, resolve_checks,
                                check_permissions)


def _collect_array_lengths(ast: q.AST, data_structure: QueryableStructure, schema: dict,
                           resolve_checks: bool) -> Iterable[ArrayLengthData]:
    """
    To evaluate a query in a manner consistent with the Postgres evaluator (and facilitate richer queries), each array
    item needs to be fixed in a particular evaluation of a query that involves array accesses. This helper function
    collects the lengths of arrays for each different array used in the field; it does this by traversing the data
    structure. These can be later used by _create_all_index_combinations to create all possible combinations of accesses
    to fix them in an evaluation run.
    :param ast: The AST-ified query
    :param data_structure: The FULL data structure the query is being evaluated against
    :param schema: The JSON schema of the full data structure
    :param resolve_checks: Whether to run resolve checks. Should only be run once per query/ds/schema combo
    :return: A recursive dictionary with keys being array paths and values being a tuple of (length, children dict)
    """

    # Literals are not arrays (currently), so they will not have any specified lengths
    if ast.type == "l":
        return

    # Standard validation to prevent Postgres internal-style queries from being passed in (see _validate_not_wc docs)
    _validate_not_wc(ast)

    # Resolves are where the magic happens w/r/t array access. Capture any array accesses with their lengths and child
    # array accesses.
    if ast.fn == q.FUNCTION_RESOLVE:
        r = _resolve_array_lengths(ast.args, data_structure, schema, "_root", resolve_checks)
        if r is not None:
            yield r
        return

    # If the current expression is a non-resolve function, recurse into its arguments and collect any additional array
    # accesses; construct a list of possibly redundant array accesses with the arrays' lengths.
    als = tuple(chain.from_iterable(_collect_array_lengths(e, data_structure, schema, resolve_checks)
                                    for e in ast.args))
    yield from (
        a1 for i1, a1 in enumerate(als)
        if not any(
            a1[0] == a2[0] and len(a1[2]) <= len(a2[2]) and i1 < i2  # Deduplicate identical or subset items
            for i2, a2 in enumerate(als)
        )
    )


def _dict_combine(dicts: Iterable[dict]):
    """
    Utility function to combine an iterable of dictionaries into a single dictionary via d.update(d2)
    :param dicts: Iterable of dictionaries
    :return: A single, combined dictionary
    """
    c = {}
    for d in dicts:
        c.update(d)
    return c


def _create_index_combinations(array_data: ArrayLengthData, parent_template: IndexCombination) \
        -> Iterable[IndexCombination]:
    """
    Creates combinations of array indices from a particular array (including children, NOT including siblings.)
    :param array_data: Information about an array's length and its children's lengths
    :param parent_template: A dictionary with information about the array's parent's current fixed indexed configuration
    :return: An iterable of different combinations of fixed indices for the array and it's children (for later search)
    """

    for i in range(array_data[1]):
        item_template = {**parent_template, array_data[0]: i}

        if len(array_data[2]) == 0:  # TODO: Don't like this logic...
            yield item_template  # What if this is overridden elsewhere?
            continue

        # TODO: Don't like the mono-tuple-ing stuff
        yield from _create_all_index_combinations((array_data[2][i],), item_template)


def _create_all_index_combinations(arrays_data: Iterable[ArrayLengthData], parent_template: IndexCombination) \
        -> Iterable[IndexCombination]:
    """
    Creates combinations of array indexes for all siblings in an iterable of arrays' length data.
    :param arrays_data: An iterable of arrays' length data
    :param parent_template: A dictionary with information about the arrays' parent's current fixed indexed configuration
    :return: An iterable of different combinations of fixed indices for the arrays and their children (for later search)
    """

    # Loop through and recurse
    combination_sets = (_create_index_combinations(array_data, parent_template) for array_data in arrays_data)

    # Combine index mappings from different combination sets into a final list of array index combinations
    # Takes the cross product of the combination sets, since they're parallel fixations and there may be inter-item
    # comparisons between the two sets.
    # TODO: Do we need the combination superset replacement logic still?
    #  combinations = [c for c in combinations if not any(c.items() < c2.items() for c2 in combinations)]
    yield from map(_dict_combine, product(*combination_sets))


# TODO: More rigorous / defined rules
def check_ast_against_data_structure(
    ast: q.AST,
    data_structure: QueryableStructure,
    schema: dict,
    internal: bool = False,
    return_all_index_combinations: bool = False,
) -> Union[bool, Iterable[IndexCombination]]:
    """
    Checks a query against a data structure, returning True if the
    :param ast: A query to evaluate against the data object.
    :param data_structure: The data object to evaluate the query against.
    :param schema: A JSON schema representing valid data objects.
    :param internal: Whether internal-only fields are allowed to be resolved.
    :param return_all_index_combinations: Whether internal-only fields are allowed to be resolved.
    :return: Determined by return_all_index_combinations; either
               1) A boolean representing whether or not the query matches the data object; or
               2) An iterable of all index combinations where the query matches the data object
    """

    # Validate data structure against JSON schema here to avoid having to repetitively do it later
    _validate_data_structure_against_schema(data_structure, schema)

    # Collect all array resolves and their lengths in order to properly cross-product arrays
    array_lengths = _collect_array_lengths(ast, data_structure, schema, True)

    # Create all combinations of indexes into arrays and enumerate them; to be used to loop through all combinations of
    # array indices to freeze "[item]"s at particular indices across the whole query.
    index_combinations = enumerate(_create_all_index_combinations(array_lengths, {}))

    # TODO: What to do here? Should be standardized, esp. w/r/t False returns

    def _evaluate(i: int, ic: IndexCombination) -> bool:
        e = evaluate_no_validate(ast, data_structure, schema, ic, internal, False, (i == 0))
        return isinstance(e, bool) and e

    if return_all_index_combinations:
        return (ic for i, ic in index_combinations if _evaluate(i, ic))

    return any(starmap(_evaluate, index_combinations))


def _binary_op(op: BBOperator)\
        -> Callable[[FunctionArgs, QueryableStructure, dict, Optional[IndexCombination], bool, bool], bool]:
    """
    Returns a boolean-returning binary operator on a pair of arguments against a data structure/object of some type and
    return a Boolean result.
    :param op: The operator the lambda is representing
    :return: Operator lambda for use in evaluating expressions
    """

    is_and = op == and_
    is_or = op == or_

    def uncurried_binary_op(args: FunctionArgs, ds: QueryableStructure, schema: dict, ic: Optional[IndexCombination],
                            internal: bool, resolve_checks: bool, check_permissions: bool) -> bool:
        # TODO: Standardize type safety / behaviour!!!

        # Evaluate both sides of the binary expression. If there's a type error while trying to use a Python built-in,
        # override it with a custom-message type error.

        lhs = evaluate_no_validate(args[0], ds, schema, ic, internal, resolve_checks, check_permissions)

        # TODO: These shortcuts don't type-check the RHS, is that OK?

        # Shortcut #and
        if is_and and not lhs:
            return False

        # Shortcut #or
        if is_or and lhs:
            return True

        rhs = evaluate_no_validate(args[1], ds, schema, ic, internal, resolve_checks, check_permissions)

        try:
            return op(lhs, rhs)
        except TypeError:
            raise TypeError(f"Type-invalid use of binary operator {op} ({lhs}, {rhs})")

    return uncurried_binary_op


def _resolve_checks(resolve_value: str, schema: dict):
    """
    Performs standard checks while going through any type of "resolve"-based function (where a #resolve call is being
    processed) to prevent access errors.
    :param resolve_value: The value of the current resolve term being processed
    :param schema: The JSON schema of the data sub-structure currently being processed
    """
    if schema["type"] not in ("object", "array"):
        raise TypeError("Cannot get property of literal")

    elif schema["type"] == "object" and resolve_value not in schema["properties"]:
        raise ValueError("Property {} not found in object".format(resolve_value))

    elif schema["type"] == "array" and resolve_value != "[item]":
        raise TypeError("Cannot get property of array")


_is_not_none = partial(is_not, None)


def _get_child_resolve_array_lengths(
    new_resolve: List[q.Literal],
    resolving_ds: List,
    item_schema: dict,
    new_path: str,
    resolve_checks: bool,
) -> Iterable[ArrayLengthData]:
    """
    Recursively resolve array lengths for all children of elements of an array using the _resolve_array_length function.
    :param new_resolve: The resolve path starting after the item access of the array being processed
    :param resolving_ds: The array data structure whose elements we're resolving child array accesses of
    :param item_schema: The JSON schema of the array's items
    :param new_path: The string representation of the path followed so far, including the most recent item access
    :param resolve_checks: Whether to run resolve checks. Should only be run once per query/ds/schema combo
    :return: A tuple of the current array's element-wise array length data
    """
    return filter(_is_not_none, (
        _resolve_array_lengths(new_resolve, array_item_ds, item_schema, new_path, resolve_checks)
        for array_item_ds in resolving_ds
    ))


def _resolve_array_lengths(
    resolve: List[q.Literal],
    resolving_ds: QueryableStructure,
    schema: dict,
    path: str = "_root",
    resolve_checks: bool = True,
) -> Optional[ArrayLengthData]:
    """
    Given a resolve path and a data structure, find lengths of any arrays in the current data structure and any
    descendents it may have.
    :param resolve: The current resolve path, where the first element is the next thing to resolve on the data structure
    :param resolving_ds: The data structure we're resolving on
    :param schema: A JSON schema modeling the current data structure
    :param path: A string representation of the path followed so far, including the most recent access
    :param resolve_checks: Whether to run resolve checks. Should only be run once per query/ds/schema combo
    :return: Either none (if no arrays were accessed) or a tuple of the current array's path, its length, and the
             lengths of any child array accesses
    """

    # TODO: yield multiple for children instead of having child tuple?

    if len(resolve) == 0:
        # Resolve the root if it's an empty list
        return (path, len(resolving_ds), ()) if schema["type"] == "array" else None

    resolve_value = resolve[0].value

    if resolve_checks:  # pragma: no cover  TODO: Do we need this at all? right now we always check here
        _resolve_checks(resolve_value, schema)

    new_path = f"{path}.{resolve_value}"

    # The current data structure is an array, so return its length and recurse on its (potential) child arrays.
    if resolve[0].value == "[item]":
        return (path,
                len(resolving_ds),
                tuple(_get_child_resolve_array_lengths(resolve[1:], resolving_ds, schema["items"], new_path,
                                                       resolve_checks)))

    # Otherwise, it's an object, so keep traversing without doing anything
    return _resolve_array_lengths(resolve[1:], resolving_ds[resolve_value], schema["properties"][resolve_value],
                                  new_path, resolve_checks)


def _resolve_properties_and_check(
    resolve: List[q.Literal],
    schema: dict,
    index_combination: Optional[IndexCombination],
) -> dict:
    """
    Resolves / evaluates a path (either object or array) into a value and its search properties. Assumes the
    data structure has already been checked against its schema.
    :param resolve: The current path to resolve, not including the current data structure
    :param schema: The JSON schema representing the resolving data structure
    :param index_combination: The combination of array indices being evaluated upon
    :return: The resolved value after exploring the resolve path, and the search operations that can be performed on it
    """

    path = "_root"
    r_schema = schema

    for current_resolve in resolve:
        current_resolve_value = current_resolve.value

        _resolve_checks(current_resolve_value, r_schema)
        if current_resolve_value == "[item]" and (index_combination is None or path not in index_combination):
            # TODO: Specific exception class
            raise Exception(f"Index combination not provided for path {path}")

        r_schema = r_schema["items"] if r_schema["type"] == "array" else r_schema["properties"][current_resolve_value]
        path = f"{path}.{current_resolve_value}"

    # Resolve the root if resolve list is empty
    return r_schema.get("search", {})


def _resolve(resolve: List[q.Literal], resolving_ds: QueryableStructure, _schema: dict,
             index_combination: Optional[IndexCombination], _internal, _resolve_checks, _check_permissions):
    """
    Resolves / evaluates a path (either object or array) into a value. Assumes the data structure has already been
    checked against its schema.
    :param resolve: The current path to resolve, not including the current data structure
    :param resolving_ds: The data structure being resolved upon
    :param index_combination: The combination of array indices being evaluated upon
    :return: The resolved value after exploring the resolve path, and the search operations that can be performed on it
    """

    path = "_root"

    for current_resolve in resolve:
        current_resolve_value = current_resolve.value
        resolving_ds = (resolving_ds[index_combination[path]] if current_resolve_value == "[item]"
                        else resolving_ds[current_resolve_value])
        path = f"{path}.{current_resolve_value}"

    return resolving_ds


QUERY_CHECK_SWITCH: Dict[
    q.FunctionName,
    Callable[[FunctionArgs, QueryableStructure, dict, Optional[IndexCombination], bool, bool], QueryableStructure]
] = {
    q.FUNCTION_AND: _binary_op(and_),
    q.FUNCTION_OR: _binary_op(or_),
    q.FUNCTION_NOT: lambda args, ds, schema, internal, ic, r_chk, p_chk:
        not_(evaluate_no_validate(args[0], ds, schema, internal, ic, r_chk, p_chk)),

    q.FUNCTION_LT: _binary_op(lt),
    q.FUNCTION_LE: _binary_op(le),
    q.FUNCTION_EQ: _binary_op(eq),
    q.FUNCTION_GT: _binary_op(gt),
    q.FUNCTION_GE: _binary_op(ge),

    q.FUNCTION_CO: _binary_op(contains),

    q.FUNCTION_RESOLVE: _resolve
}
