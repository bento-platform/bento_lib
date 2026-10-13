"""
Advanced functions for discovery using Bento data dictionaries.
"""

from bento_lib.data_dictionary import DataDictionary

__all__ = ["field_intersection", "field_intersection_n"]


def field_intersection(dd1: DataDictionary, dd2: DataDictionary) -> frozenset[str]:
    """
    Calculates the intersection of compatible fields for querying across two data dictionaries.
    :param dd1: First data dictionary
    :param dd2: Second data dictionary
    :return: List of label CURIE IDs which are present and share units in both.
    """

    pass


def field_intersection_n(*args: tuple[DataDictionary, ...]) -> frozenset[str]:
    pass
