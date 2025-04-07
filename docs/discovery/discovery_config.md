# Discovery configuration: structure and validation

The Bento discovery configuration format is used for Bento implementers to specify which fields of their instance (or a
project or dataset) are viewable as charts or searchable, and the rules for count search result censorship, i.e.,
how many filters can be queried for counts queries, and what the minimum count is before counts are censored to 0.


## Validating a discovery configuration JSON with `bento_lib`

Here is some sample code for loading and validating a discovery configuration JSON file, yielding a Pydantic object 
containing the configuration:

```python
from bento_lib.discovery.helpers import load_discovery_config
from bento_lib.discovery.models.config import DiscoveryConfig

my_cfg: DiscoveryConfig = load_discovery_config("my_config.json")
```

The `load_discovery_config` function may raise for any number of reasons (see sections below).

### If the structure is incorrect

If the structure of the file is incorrect versus the Pydantic model definition, a Pydantic 
[`ValidationError`](https://docs.pydantic.dev/latest/api/pydantic_core/#pydantic_core.ValidationError) will be raised.

### If a field is referenced without being defined

If a field (via a chart or a search field) is referenced without being defined in the configuration `"fields": {...}` 
JSON block, a `DiscoveryValidationError` will be raised with a message containing the location of where the error 
occurred and the phrase "field definition not found".

Examples of invalid discovery configurations can be found at:

* [`/tests/data/discovery_config_invalid_2.json`](../../tests/data/discovery_config_invalid_2.json)
* [`/tests/data/discovery_config_invalid_3.json`](../../tests/data/discovery_config_invalid_3.json)

### If duplicate charts or search fields are defined

A field may only be used once as a chart, and once as a search field. TODO
