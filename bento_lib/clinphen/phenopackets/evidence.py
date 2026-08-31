from bento_lib.ontologies.models import OntologyClass

from .._fields import FIELD_NULLABLE
from .._models import BentoClinPhenModel
from .external_reference import ExternalReference

__all__ = ["Evidence"]


class Evidence(BentoClinPhenModel):
    """
    https://phenopacket-schema.readthedocs.io/en/latest/evidence.html
    """

    evidence_code: OntologyClass
    reference: ExternalReference | None = FIELD_NULLABLE
