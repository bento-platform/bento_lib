from pydantic import BaseModel


class OntologyTerm(BaseModel):
    id: str
    label: str
