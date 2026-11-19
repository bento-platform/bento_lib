__all__ = [
    "NC_NAME_PATTERN",
    "CURIE_PATTERN",
]

# see (very roughly):
#  - https://www.w3.org/TR/2010/NOTE-curie-20101216/#s_syntax
#  - https://www.w3.org/TR/1999/REC-xml-names-19990114/#NT-NCName
NC_NAME_PATTERN = r"^[a-zA-Z_][a-zA-Z0-9.\-_]*$"
CURIE_PATTERN = r"^[a-zA-Z_][a-zA-Z0-9.\-_]*:[a-zA-Z0-9.\-_]+$"
