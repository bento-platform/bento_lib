import pytest
from pydantic import ValidationError

from bento_lib.ontologies import common_resources as cr, common_classes as ct, models as m


def test_ontology_resources():
    assert (
        cr.NCIT.as_versioned("https://purl.obolibrary.org/obo/ncit/releases/2024-05-07/ncit.owl", "2024-05-07")
        == cr.NCIT_2024_05_07
    )
    assert cr.NCIT_2024_05_07.to_phenopackets_repr() == {
        "id": "ncit",
        "name": "NCI Thesaurus OBO Edition",
        "namespace_prefix": "NCIT",
        "iri_prefix": "http://purl.obolibrary.org/obo/NCIT_",
        "url": "https://purl.obolibrary.org/obo/ncit/releases/2024-05-07/ncit.owl",
        "version": "2024-05-07",
    }


def test_make_class():
    assert cr.NCBI_TAXON.make_class("NCBITaxon:9606", "Homo sapiens") == m.ResourceOntologyClass(
        id="NCBITaxon:9606",
        label="Homo sapiens",
        ontology=cr.NCBI_TAXON,
    )
    assert cr.NCBI_TAXON_2025_12_03.make_class("NCBITaxon:9606", "Homo sapiens") == m.ResourceOntologyClass(
        id="NCBITaxon:9606",
        label="Homo sapiens",
        ontology=cr.NCBI_TAXON_2025_12_03,
    )


def test_ontology_classes():
    assert ct.NCBI_TAXON_HOMO_SAPIENS.ontology == cr.NCBI_TAXON
    assert ct.NCBI_TAXON_HOMO_SAPIENS.to_phenopackets_repr() == {
        "id": "NCBITaxon:9606",
        "label": "Homo sapiens",
    }


def test_ontology_class_validation():
    with pytest.raises(ValidationError) as e:
        cr.NCIT_2024_05_07.make_class("NCBITaxon:9606", "Homo sapiens")

    assert "Value error, class CURIE must start with ontology resource namespace prefix" in str(e.value)
