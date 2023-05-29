from typing import List, Union

__all__ = [
    "get_field_schema_from_base_schema",
]


def get_field_schema_from_base_schema(field: List[str], search_schema: dict) -> Union[dict, None]:
    """
    Retrieves the schema for a particular field inside a base search schema.
    :param field: A list of strings representing the path to the field in the schema.
    :param search_schema: The schema to traverse.
    :return: The Bento search schema for the field, if available. None otherwise.
    """
    pass
