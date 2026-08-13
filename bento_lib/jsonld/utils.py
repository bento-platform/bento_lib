__all__ = ["first_if_only_else_all"]


def first_if_only_else_all[T](x: list[T]) -> T | list[T]:
    return x[0] if len(x) == 1 else x
