from typing import Callable, List, Optional, Tuple, Union

from .operations import (
    SEARCH_OP_LT,
    SEARCH_OP_LE,
    SEARCH_OP_EQ,
    SEARCH_OP_GT,
    SEARCH_OP_GE,
    SEARCH_OP_CO
)


__all__ = [
    "FUNCTION_AND",
    "FUNCTION_OR",
    "FUNCTION_NOT",
    "FUNCTION_LT",
    "FUNCTION_LE",
    "FUNCTION_EQ",
    "FUNCTION_GT",
    "FUNCTION_GE",
    "FUNCTION_CO",
    "FUNCTION_RESOLVE",
    "FUNCTION_HELPER_WC",

    "VALID_FUNCTIONS",

    "FUNCTION_SEARCH_OP_MAP",

    "LiteralValue",
    "FunctionName",
    "Query",
    "AST",

    "Expression",
    "Literal",

    "convert_query_to_ast",
    "convert_query_to_ast_and_preprocess",
    "ast_to_and_asts",
    "and_asts_to_ast",
    "check_operation_permissions",
]


FUNCTION_AND = "#and"
FUNCTION_OR = "#or"
FUNCTION_NOT = "#not"

FUNCTION_LT = "#lt"
FUNCTION_LE = "#le"
FUNCTION_EQ = "#eq"
FUNCTION_GT = "#gt"
FUNCTION_GE = "#ge"

FUNCTION_CO = "#co"

FUNCTION_RESOLVE = "#resolve"

FUNCTION_HELPER_WC = "#_wc"

VALID_FUNCTIONS = (
    FUNCTION_AND,
    FUNCTION_OR,
    FUNCTION_NOT,
    FUNCTION_LT,
    FUNCTION_LE,
    FUNCTION_EQ,
    FUNCTION_GT,
    FUNCTION_GE,
    FUNCTION_CO,
    FUNCTION_RESOLVE,
    FUNCTION_HELPER_WC,
)

BINARY_RANGE = (2, 2)

FUNCTION_ARGUMENTS = {
    FUNCTION_AND: BINARY_RANGE,
    FUNCTION_OR: BINARY_RANGE,
    FUNCTION_NOT: (1, 1),
    FUNCTION_LT: BINARY_RANGE,
    FUNCTION_LE: BINARY_RANGE,
    FUNCTION_EQ: BINARY_RANGE,
    FUNCTION_GT: BINARY_RANGE,
    FUNCTION_GE: BINARY_RANGE,
    FUNCTION_CO: BINARY_RANGE,
    FUNCTION_RESOLVE: (0, None),
    FUNCTION_HELPER_WC: (1, 1),
}


FUNCTION_SEARCH_OP_MAP = {
    FUNCTION_LT: SEARCH_OP_LT,
    FUNCTION_LE: SEARCH_OP_LE,
    FUNCTION_EQ: SEARCH_OP_EQ,
    FUNCTION_GT: SEARCH_OP_GT,
    FUNCTION_GE: SEARCH_OP_GE,

    FUNCTION_CO: SEARCH_OP_CO,
}


literal_types = str, int, float, bool    # TODO: How to handle dict in practical cases?
LiteralValue = Union[literal_types]

FunctionName = str


Query = Union[list, LiteralValue]


# TODO: Prevent nested resolves
# TODO: Argument types...


AST = Union["Expression", "Literal"]


class Expression:
    type = "e"

    def __init__(self, fn: str, args: List[AST]):
        assert fn in VALID_FUNCTIONS
        self.fn = fn

        arg_range = FUNCTION_ARGUMENTS[fn]
        assert len(args) >= arg_range[0] and (arg_range[1] is None or len(args) <= arg_range[1])
        self.args = args

    def __eq__(self, other):
        return (isinstance(other, Expression) and self.fn == other.fn and
                all(a == b for a, b in zip(self.args, other.args)))

    def __str__(self):
        return "[{}, {}]".format(self.fn, ", ".join(str(a) for a in self.args))

    def __repr__(self):  # pragma: no cover
        return f"<Expression {self.fn} [{', '.join(repr(a) for a in self.args)}]>"


class Literal:
    type = "l"

    def __init__(self, value: LiteralValue):
        assert any(isinstance(value, t) for t in literal_types)
        self.value = value

    def __eq__(self, other):
        return isinstance(other, Literal) and self.value == other.value

    def __str__(self):
        return str(self.value)

    def __repr__(self):  # pragma: no cover
        return f"<Literal {self.value}>"


def convert_query_to_ast(query: Query) -> AST:
    if isinstance(query, list):
        if len(query) == 0 or not isinstance(query[0], str) or query[0] not in VALID_FUNCTIONS:
            raise SyntaxError("Invalid expression: {}".format(query))

        try:
            return Expression(query[0], [convert_query_to_ast(q) for q in query[1:]])
        except AssertionError:
            raise SyntaxError("Invalid number of arguments for function {}: {}".format(query[0], len(query[1:])))

    elif any(isinstance(query, t) for t in literal_types):
        return Literal(query)

    raise ValueError("Invalid literal: {}".format(query))


def simplify_nots(ast: AST) -> AST:
    # not (not a) => a

    if ast.type == "l":
        return ast

    if ast.fn == FUNCTION_NOT and ast.args[0].type == "e" and ast.args[0].fn == FUNCTION_NOT:
        return simplify_nots(ast.args[0].args[0])

    return Expression(fn=ast.fn, args=[simplify_nots(a) for a in ast.args])


def convert_query_to_ast_and_preprocess(query: Query) -> AST:
    ast = convert_query_to_ast(query)
    return simplify_nots(ast)


def ast_to_and_asts(ast: AST) -> Tuple[AST, ...]:
    # (and e1 e2) => <e1, e2>
    # (and (and e1 e2) e3) => <e1, e2, e3>
    # (and e1 (and e2 e3)) => <e1, e2, e3>
    # (and (and e1 e2) (and e3 e4)) => <e1, e2, e3, e4>
    # etc.

    if not ast.type == "e" or ast.fn != FUNCTION_AND:
        return ast,

    return (*ast_to_and_asts(ast.args[0]), *ast_to_and_asts(ast.args[1]))


def and_asts_to_ast(asts: Tuple[AST, ...]) -> Optional[AST]:
    # (e1, e2, e3, e4) => (and e1 (and e2 (and e3 e4)))

    if len(asts) == 0:
        return None

    if len(asts) == 1:
        return asts[0]

    return Expression(FUNCTION_AND, [asts[0], and_asts_to_ast(asts[1:])])


def check_operation_permissions(ast: AST, schema: dict, search_getter: Callable[[List[Literal], dict], dict],
                                internal: bool = False):
    if ast.type == "l":
        return

    if ast.fn == FUNCTION_RESOLVE:
        search_properties = search_getter(ast.args, schema)

        query_modes = ("internal", "all") if internal else ("all",)
        query_mode = search_properties.get("queryable", "none")

        # If resolving any field, make sure at least some operation is permitted
        if query_mode not in query_modes:
            # TODO: Custom exception?
            raise ValueError("Cannot access field using {} (queryable: {}, allowed are {})".format(ast, query_mode,
                                                                                                   query_modes))

    # Check to make sure the function's execution is permitted

    if ast.fn not in FUNCTION_SEARCH_OP_MAP:
        return

    # TODO: Make this check recursive (#11) or somehow deal with boolean values
    if any(FUNCTION_SEARCH_OP_MAP[ast.fn] not in search_getter(a.args, schema).get("operations", [])
           for a in ast.args if a.type == "e" and a.fn == FUNCTION_RESOLVE):
        # TODO: Custom exception?
        raise ValueError("Schema forbids using function: {}\nAST: {}\nSchema: \n{}".format(ast.fn, ast, schema))
