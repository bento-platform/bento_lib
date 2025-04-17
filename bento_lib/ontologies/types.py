from typing import TypedDict

__all__ = [
    "PhenoV2Resource",
    "PhenoV2OntologyClassDict",
]


class PhenoV2Resource(TypedDict):
    id: str
    name: str
    url: str
    version: str
    namespace_prefix: str
    iri_prefix: str


class PhenoV2OntologyClassDict(TypedDict):
    id: str
    label: str
