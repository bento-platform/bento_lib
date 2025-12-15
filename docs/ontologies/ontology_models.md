# `bento_lib` ontology resource and ontology class models

## Defining ontology classes and resources

Models and Python typed dictionary definitions for ontology classes (modeled aftert the Phenopackets V2 
[`OntologyClass`](https://phenopacket-schema.readthedocs.io/en/latest/ontologyclass.html) element) and ontology resources
(modeled after the Phenopackets V2 [`Resource`](https://phenopacket-schema.readthedocs.io/en/latest/resource.html)) 
element.

An ontology class has two properties: a CURIE ID (`id`) and a human-readable label (`label`). The CURIE ID contains a 
prefix which uniquely identifies an ontology resource in the scope of a particular dataset, although ontology resources
can have multiple versions, and a class may only be valid in a subset of these versions. Here's an example of an 
ontology class defined using the `OntologyClass` Pydantic model, representing *Homo sapiens* 
using the [OBO version of the `NCBITaxon` ontology](https://github.com/obophenotype/ncbitaxon):

```python
from bento_lib.ontologies import models

models.OntologyClass(id="NCBITaxon:9606", label="Homo sapiens")
```

The library also includes a model for representing ontology resources themselves (both unversioned and versioned forms);
for example, we can represent the NCBITaxon ontology and generate the above *Homo sapiens* class via method:


```python
from bento_lib.ontologies import models
from pydantic import HttpUrl

NCBI_TAXON = models.OntologyResource(
    id="ncbitaxon",
    name="NCBI organismal classification",
    namespace_prefix="NCBITaxon",
    iri_prefix=HttpUrl("http://purl.obolibrary.org/obo/NCBITaxon_"),
    url=HttpUrl("https://purl.obolibrary.org/obo/ncbitaxon.owl"),
    repository_url=HttpUrl("https://github.com/obophenotype/ncbitaxon"),
) 

NCBI_TAXON.make_class("NCBITaxon:9606", "Homo sapiens")

# The above is generated as a models.ResourceOntologyClass, as it is linked to a specific resource.
```

We can optionally version an ontology resource using the `<resource>.as_versioned(<url>, <version>)` method to attach
a specific version to a resource, which is useful for generating Katsu-compatible resource records and in general for
keeping datasets properly "frozen" and avoiding references becoming broken:

```python
NCBI_TAXON_2025_12_03 = NCBI_TAXON.as_versioned(
    url="https://purl.obolibrary.org/obo/ncbitaxon/2025-12-03/ncbitaxon.owl",
    version="2025-12-03",
)

NCBI_TAXON_2025_12_03.make_class("NCBITaxon:9606", "Homo sapiens")
```

Note that none of these `make_class` methods **validate what is inside the .owl file**; this is left to the person 
producing the file these classes are used in.


##  Common ontology resources and classes

Many ontologies are reused across datasets in Bento; these have been predefined in 
[`bento_lib.ontologies.common_resources`](../../bento_lib/ontologies/common_resources.py), with commonly-used classes 
from these resources defined in [`bento_lib.ontologies.common_classes`](../../bento_lib/ontologies/common_classes.py).
