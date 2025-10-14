# `bento_lib` ontology resource and ontology term models

Models and Python typed dictionary definitions for ontology terms (modeled after the Phenopackets V2 
[`OntologyClass`](https://phenopacket-schema.readthedocs.io/en/latest/ontologyclass.html) element) and ontology resources
(modeled after the Phenopackets V2 [`Resource`](https://phenopacket-schema.readthedocs.io/en/latest/resource.html)) 
element.

An ontology term has two properties: a CURIE ID (`id`) and a human-readable label (`label`). The CURIE ID contains a 
prefix which uniquely identifies an ontology resource in the scope of a particular dataset, although ontology resources
can have multiple versions, and a term may only be valid in a subset of these versions. Here's an example of an ontology
term (class, in Phenopacket terminology) defined using the `OntologyTerm` Pydantic model, representing *Homo sapiens* 
using the [OBO version of the `NCBITaxon` ontology](https://github.com/obophenotype/ncbitaxon):

```python
from bento_lib.ontologies import models

models.OntologyTerm(id="NCBITaxon:9606", label="Homo sapiens")
```

TODO
