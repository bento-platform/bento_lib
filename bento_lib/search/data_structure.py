import json
import re

import jsonschema

from functools import partial
from itertools import chain, product, starmap
from operator import and_, or_, not_, lt, le, eq, gt, ge, contains, is_not
from typing import Callable, Dict, List, Iterable, Optional, Tuple, Union

from . import queries as q
from ._types import JSONSchema


__all__ = ["check_ast_against_data_structure"]


QueryableStructure = Union[dict, list, set, str, int, float, bool]
BBOperator = Callable[[QueryableStructure, QueryableStructure], bool]

IndexCombination = Dict[str, int]
ArrayLengthData = Tuple[str, int, Tuple["ArrayLengthData", ...]]


def _icontains(lhs: str, rhs: str) -> bool:
    """
    Same as the "contains" operator, except with case-folded (i.e. case
    insensitive) arguments.
    :param lhs: The LHS for the operation.
    :param rhs: The RHS for the operation.
    :return: The result of the icontains operation.
    """
    return contains(lhs.casefold(), rhs.casefold())


def _in(lhs: Union[str, int, float], rhs: QueryableStructure) -> bool:
    """
    Same as `contains`, except order of arguments is inverted and second
    argument is a set.
    Note: set is preferred over list as it makes `contains` complexity O(1) vs O(n).
    As this is intended to be used in a loop over dataset results, it makes the
    implementation's complexity linear instead of quadratic.
    """
    return contains(rhs, lhs)


def _i_starts_with(lhs: str, rhs: str) -> bool:
    """
    Checks whether a string starts with a particular prefix, in a case-insensitive fashion.
    :param lhs: The full string to assess.
    :param rhs: The prefix to test against LHS.
    :return: Whether the string starts with the prefix.
    """
    if not isinstance(lhs, str) or not isinstance(rhs, str):
        raise TypeError(f"{q.FUNCTION_ISW} can only be used with strings")
    return lhs.casefold().startswith(rhs.casefold())


def _i_ends_with(lhs: str, rhs: str) -> bool:
    """
    Checks whether a string ends with a particular suffix, in a case-insensitive fashion.
    :param lhs: The full string to assess.
    :param rhs: The prefix to test against LHS.
    :return: Whether the string ends with the prefix.
    """
    if not isinstance(lhs, str) or not isinstance(rhs, str):
        raise TypeError(f"{q.FUNCTION_IEW} can only be used with strings")
    return lhs.casefold().endswith(rhs.casefold())


# See, e.g., https://stackoverflow.com/questions/399078/what-special-characters-must-be-escaped-in-regular-expressions
REGEX_CHARS_TO_ESCAPE = frozenset({"[", "]", "(", ")", "{", "}", "\\", ".", "^", "$", "*", "+", "-", "?", "|"})


def regex_from_like_pattern(pattern: str, case_insensitive: bool) -> re.Pattern:
    """
    Converts an SQL-style match pattern with %/_ wildcards into a Python Regex object.
    :param pattern: The SQL-style match pattern to convert.
    :param case_insensitive: Whether the generated Regex should be case-insensitive.
    :return: The converted Regex object.
    """

    # - Replace % with (.*) if % is not preceded by a \
    # - Wrap with ^$ to replicate whole-string behaviour
    # - Escape any special Regex characters

    regex_form: List[str] = ["^"]
    escape_mode: bool = False
    for char in pattern:
        # Put us into escape mode, so that the next character is escaped if needed
        if char == "\\":
            escape_mode = True
            continue

        if char == "%":  # Matches any number of characters
            # If we're in escape mode, append the literal %. Otherwise, replace it with a wildcard pattern.
            regex_form.append("%" if escape_mode else "(.*)")
        elif char == "_":  # Match a single character
            regex_form.append("_" if escape_mode else ".")
        elif char in REGEX_CHARS_TO_ESCAPE:
            # Escape special Regex characters with a backslash while building pattern
            regex_form.append(rf"\{char}")
        else:
            regex_form.append(char)  # Unmodified if not special

        escape_mode = False  # Turn off escape mode after one iteration; it only applies to the character in front of it

    regex_form.append("$")

    return re.compile("".join(regex_form), *((re.IGNORECASE,) if case_insensitive else ()))


def _like_op(case_insensitive: bool):
    def like_inner(lhs, rhs) -> bool:
        if not isinstance(lhs, str) or not isinstance(rhs, str):
            raise TypeError(f"{q.FUNCTION_LIKE} can only be used with strings")

        return regex_from_like_pattern(rhs, case_insensitive).match(lhs) is not None

    return like_inner


def _validate_data_structure_against_schema(
    data_structure: QueryableStructure, schema: JSONSchema, secure_errors: bool = True
) -> None:
    """
    Validates a queryable data structure of some type against a JSON schema. This is an important validation step,
    because (assuming the schema is correct) it allows methods to make more assumptions about the integrity of the
    data structure while traversing it.
    :param data_structure: The data structure to validate
    :param schema: The JSON schema to validate the data structure against
    """
    schema_validator = jsonschema.Draft7Validator(schema)
    if not schema_validator.is_valid(data_structure):
        # There is a mismatch between the data structure and the corresponding
        # search schema. This probably means either the schema is incorrect or
        # the service is returning data that doesn't conform to what it says it
        # should conform to. If secure_errors is False, the data structure,
        # schema, and validation errors will all be returned in the giant
        # error string.

        errors = tuple(err.message for err in schema_validator.iter_errors(data_structure))
        errors_str = "\n".join(errors)

        if secure_errors:
            raise ValueError(
                f"Invalid data structure for schema (schema ID: {schema.get('$id', 'N/A')});"
                f"encountered {len(errors)} validation errors (masked for privacy)"
            )

        raise ValueError(
            f"Invalid data structure: \n"
            f"{data_structure}\n"
            f"For schema: \n"
            f"{json.dumps(schema)} \n"
            f"Validation Errors: \n"
            f"{errors_str}"
        )


def _validate_not_wc(e: q.AST) -> None:
    """
    The #_wc (wildcard) expression function is a helper for converting the queries into the Postgres IR. If we encounter
    this function in a query being evaluated against a data structure, it's meaningless and should raise an error.
    :param e: The expression (function) to check
    """
    if e.fn == q.FUNCTION_HELPER_WC:
        raise NotImplementedError("Cannot use wildcard helper here")


def evaluate_no_validate(
    ast: q.AST,
    data_structure: QueryableStructure,
    schema: JSONSchema,
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
            ast, schema, lambda rl, s: _resolve_properties_and_check(rl, s, index_combination), internal
        )

    # Evaluate the non-literal expression recursively.
    return QUERY_CHECK_SWITCH[ast.fn](
        ast.args, data_structure, schema, index_combination, internal, resolve_checks, check_permissions
    )


def evaluate(
    ast: q.AST,
    data_structure: QueryableStructure,
    schema: JSONSchema,
    index_combination: Optional[IndexCombination],
    internal: bool = False,
    resolve_checks: bool = True,
    check_permissions: bool = True,
    secure_errors: bool = True,
):
    # The 'validate' flag is used to avoid redundantly validating the integrity of child data structures
    _validate_data_structure_against_schema(data_structure, schema, secure_errors=secure_errors)
    return evaluate_no_validate(
        ast, data_structure, schema, index_combination, internal, resolve_checks, check_permissions
    )


def _collect_array_lengths(
    ast: q.AST, data_structure: QueryableStructure, schema: JSONSchema, resolve_checks: bool
) -> Iterable[ArrayLengthData]:
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
        return ()

    # Standard validation to prevent Postgres internal-style queries from being passed in (see _validate_not_wc docs)
    _validate_not_wc(ast)

    # Resolves are where the magic happens w/r/t array access. Capture any array accesses with their lengths and child
    # array accesses.
    if ast.fn == q.FUNCTION_RESOLVE:
        r = _resolve_array_lengths(ast.args, data_structure, schema, "_root", resolve_checks)
        return () if r is None else (r,)

    # If the current expression is a non-resolve function, recurse into its arguments and collect any additional array
    # accesses; construct a list of possibly redundant array accesses with the arrays' lengths.
    als = tuple(
        chain.from_iterable(_collect_array_lengths(e, data_structure, schema, resolve_checks) for e in ast.args)
    )
    return (
        a1
        for i1, a1 in enumerate(als)
        if not any(
            a1[0] == a2[0] and len(a1[2]) <= len(a2[2])  # Deduplicate identical or subset items
            for a2 in als[i1 + 1 :]
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


def _create_index_combinations(
    parent_template: IndexCombination, array_data: ArrayLengthData
) -> Iterable[IndexCombination]:
    """
    Creates combinations of array indices from a particular array (including children, NOT including siblings.)
    :param parent_template: A dictionary with information about the array's parent's current fixed indexed configuration
    :param array_data: Information about an array's length and its children's lengths
    :return: An iterable of different combinations of fixed indices for the array and it's children (for later search)
    """

    # array_data is a tuple of (path, length, (tuple of child array lengths,))

    for i in range(array_data[1]):
        item_template = {**parent_template, array_data[0]: i}

        if len(array_data[2]) == 0:  # TODO: Don't like this logic...
            yield item_template  # What if this is overridden elsewhere?
            continue

        # TODO: Don't like the mono-tuple-ing stuff
        yield from _create_all_index_combinations(item_template, (array_data[2][i],))


def _create_all_index_combinations(
    parent_template: IndexCombination, arrays_data: Iterable[ArrayLengthData]
) -> Iterable[IndexCombination]:
    """
    Creates combinations of array indexes for all siblings in an iterable of arrays' length data.
    :param parent_template: A dictionary with information about the arrays' parent's current fixed indexed configuration
    :param arrays_data: An iterable of arrays' length data
    :return: An iterable of different combinations of fixed indices for the arrays and their children (for later search)
    """

    # Combine index mappings from different combination sets into a final list of array index combinations
    # Takes the cross product of the combination sets, since they're parallel fixations and there may be inter-item
    # comparisons between the two sets.
    # TODO: Do we need the combination superset replacement logic still?
    #  combinations = [c for c in combinations if not any(c.items() < c2.items() for c2 in combinations)]
    return map(
        _dict_combine,
        # Loop through and recurse
        product(*map(partial(_create_index_combinations, parent_template), arrays_data)),
    )


# TODO: More rigorous / defined rules
def check_ast_against_data_structure(
    ast: q.AST,
    data_structure: QueryableStructure,
    schema: JSONSchema,
    internal: bool = False,
    return_all_index_combinations: bool = False,
    secure_errors: bool = True,
    skip_schema_validation: bool = False,
) -> Union[bool, Iterable[IndexCombination]]:
    """
    Checks a query against a data structure, returning True if the
    :param ast: A query to evaluate against the data object.
    :param data_structure: The data object to evaluate the query against.
    :param schema: A JSON schema representing valid data objects.
    :param internal: Whether internal-only fields are allowed to be resolved.
    :param return_all_index_combinations: Whether to return all index combinations that the query resolves to True on.
    :param secure_errors: Whether to not expose any data in error messaevaluateges. Impairs debugging.
    :param skip_schema_validation: Whether to skip schema validation on the data structure. Improves performance but can
                                   lead to wonky errors.
    :return: Determined by return_all_index_combinations; either
               1) A boolean representing whether or not the query matches the data object; or
               2) An iterable of all index combinations where the query matches the data object
    """

    if not skip_schema_validation:
        # Validate data structure against JSON schema here to avoid having to repetitively do it later
        _validate_data_structure_against_schema(data_structure, schema, secure_errors=secure_errors)

    # Collect all array resolves and their lengths in order to properly cross-product arrays
    array_lengths = _collect_array_lengths(ast, data_structure, schema, True)

    # Create all combinations of indexes into arrays and enumerate them; to be used to loop through all combinations of
    # array indices to freeze "[item]"s at particular indices across the whole query.
    index_combinations = enumerate(_create_all_index_combinations({}, array_lengths))

    # TODO: What to do here? Should be standardized, esp. w/r/t False returns

    def _evaluate(i: int, ic: IndexCombination) -> bool:
        return evaluate_no_validate(ast, data_structure, schema, ic, internal, False, (i == 0)) is True

    if return_all_index_combinations:
        return (ic for i, ic in index_combinations if _evaluate(i, ic))

    return any(starmap(_evaluate, index_combinations))


def _binary_op(
    op: BBOperator,
) -> Callable[[q.Args, QueryableStructure, JSONSchema, Optional[IndexCombination], bool, bool, bool], bool]:
    """
    Returns a boolean-returning binary operator on a pair of arguments against a data structure/object of some type and
    return a Boolean result.
    :param op: The operator the lambda is representing
    :return: Operator lambda for use in evaluating expressions
    """

    # needed for shortcutting assessment of boolean operators
    is_and = op == and_
    is_or = op == or_

    def uncurried_binary_op(
        args: q.Args,
        ds: QueryableStructure,
        schema: JSONSchema,
        ic: Optional[IndexCombination],
        internal: bool,
        resolve_checks: bool,
        check_permissions: bool,
    ) -> bool:
        # TODO: Standardize type safety / behaviour!!!

        # Evaluate both sides of the binary expression. If there's a type error while trying to use a Python built-in,
        # override it with a custom-message type error.

        lhs = evaluate_no_validate(args[0], ds, schema, ic, internal, resolve_checks, check_permissions)

        # These shortcuts mean that the RHS does NOT get type-checked!

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


def _resolve_checks(resolve_value: str, schema: JSONSchema):
    """
    Performs standard checks while going through any type of "resolve"-based function (where a #resolve call is being
    processed) to prevent access errors.
    :param resolve_value: The value of the current resolve term being processed
    :param schema: The JSON schema of the data sub-structure currently being processed
    """
    if schema["type"] not in ("object", "array"):
        raise TypeError("Cannot get property of literal")

    elif schema["type"] == "object" and resolve_value not in schema["properties"]:
        raise ValueError(f"Property {resolve_value} not found in object")

    elif schema["type"] == "array" and resolve_value != "[item]":
        raise TypeError("Cannot get property of array")


_is_not_none = partial(is_not, None)


def _get_child_resolve_array_lengths(
    new_resolve: Tuple[q.AST, ...],
    resolving_ds: list,
    item_schema: JSONSchema,
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
    return filter(
        _is_not_none,
        (
            _resolve_array_lengths(new_resolve, array_item_ds, item_schema, new_path, resolve_checks)
            for array_item_ds in resolving_ds
        ),
    )


def _resolve_array_lengths(
    resolve: Tuple[q.AST, ...],
    resolving_ds: QueryableStructure,
    schema: JSONSchema,
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
        #  - Python typing is awkward here (relying on schema correctness), so we don't process this line.
        return (path, len(resolving_ds), ()) if schema["type"] == "array" else None  # type: ignore

    resolve_value: str = str(resolve[0].value)

    if resolve_checks:  # pragma: no cover  TODO: Do we need this at all? right now we always check here
        _resolve_checks(resolve_value, schema)

    new_path = f"{path}.{resolve_value}"

    # The current data structure is an array, so return its length and recurse on its (potential) child arrays.
    if resolve[0].value == "[item]":
        return (
            path,
            len(resolving_ds),
            tuple(
                _get_child_resolve_array_lengths(resolve[1:], resolving_ds, schema["items"], new_path, resolve_checks)
            ),
        )

    # Otherwise, it's an object, so keep traversing without doing anything
    return _resolve_array_lengths(
        resolve[1:], resolving_ds[resolve_value], schema["properties"][resolve_value], new_path, resolve_checks
    )


def _resolve_properties_and_check(
    resolve: Tuple[q.Literal, ...],
    schema: JSONSchema,
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


def _resolve(
    resolve: Tuple[q.Literal, ...],
    resolving_ds: QueryableStructure,
    _schema: JSONSchema,
    index_combination: Optional[IndexCombination],
    _internal: bool,
    _resolve_checks: bool,
    _check_permissions: bool,
) -> QueryableStructure:
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
        resolving_ds = (
            resolving_ds[index_combination[path]]
            if current_resolve_value == "[item]"
            else resolving_ds[current_resolve_value]
        )
        path = f"{path}.{current_resolve_value}"

    return resolving_ds


def _list(
    literals: Tuple[q.Literal, ...],
    _resolving_ds: QueryableStructure,
    _schema: JSONSchema,
    _index_combination: Optional[IndexCombination],
    _internal: bool,
    _resolve_checks: bool,
    _check_permissions: bool,
) -> QueryableStructure:
    """
    This function is to be used in conjonction with the #in operator to check
    for matches in a set of literals. (e.g. individual.karyotypic_sex in {"XX", "X0", "XXX"})
    :param literals: an iterable containing all the literals to check upon.
    :return: a set containing all the values
    """
    return set(literal.value for literal in literals)


QUERY_CHECK_SWITCH: Dict[
    q.FunctionName,
    Callable[
        [q.Args, QueryableStructure, JSONSchema, Optional[IndexCombination], bool, bool, bool], QueryableStructure
    ],
] = {
    q.FUNCTION_AND: _binary_op(and_),
    q.FUNCTION_OR: _binary_op(or_),
    q.FUNCTION_NOT: lambda args, *rest: not_(evaluate_no_validate(args[0], *rest)),
    # ---------------------------------------------------------------
    q.FUNCTION_LT: _binary_op(lt),
    q.FUNCTION_LE: _binary_op(le),
    q.FUNCTION_EQ: _binary_op(eq),
    q.FUNCTION_GT: _binary_op(gt),
    q.FUNCTION_GE: _binary_op(ge),
    # ---------------------------------------------------------------
    q.FUNCTION_CO: _binary_op(contains),
    q.FUNCTION_ICO: _binary_op(_icontains),
    q.FUNCTION_IN: _binary_op(_in),
    # ---------------------------------------------------------------
    q.FUNCTION_ISW: _binary_op(_i_starts_with),
    q.FUNCTION_IEW: _binary_op(_i_ends_with),
    q.FUNCTION_LIKE: _binary_op(_like_op(case_insensitive=False)),
    q.FUNCTION_ILIKE: _binary_op(_like_op(case_insensitive=True)),
    # ---------------------------------------------------------------
    q.FUNCTION_RESOLVE: _resolve,
    q.FUNCTION_LIST: _list,
}
