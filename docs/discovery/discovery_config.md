# Discovery configuration: structure and validation

The Bento discovery configuration format is used for Bento implementers to specify which fields of their instance (or a
project or dataset) are viewable as charts or searchable, and the rules for count search result censorship, i.e.,
how many filters can be queried for counts queries, and what the minimum count is before counts are censored to 0.

For more information on the goals of discovery configuration files and how to upload them to Bento, see the
[public data discovery configuration](https://github.com/bento-platform/bento/blob/main/docs/public_discovery.md)
document in the main Bento repository.


## Validating a discovery configuration JSON with `bento_lib`

Here is some sample code for loading and validating a discovery configuration JSON file, yielding a Pydantic object 
containing the configuration and a tuple of warnings, each of which is a tuple of:

* a path (tuple of strings/integers) to the part of the JSON where the error occurred
* a message string

```python
from bento_lib.discovery.helpers import load_discovery_config
from bento_lib.discovery.models.config import DiscoveryConfig

my_cfg: DiscoveryConfig
my_cfg, warnings = load_discovery_config("my_config.json")
print(f"my configuration has {len(warnings)} warnings:", warnings)
```

The `load_discovery_config` function may raise for any number of reasons (see sections below).

### ERROR: The structure is incorrect

If the structure of the file is incorrect versus the Pydantic model definition, a Pydantic 
[`ValidationError`](https://docs.pydantic.dev/latest/api/pydantic_core/#pydantic_core.ValidationError) will be raised.

### ERROR: A field is referenced without being defined

If a field (via a chart or a search field) is referenced without being defined in the configuration `"fields": {...}` 
JSON block, a `DiscoveryValidationError` will be raised with a message containing the location of where the error 
occurred and the phrase "field definition not found".

Examples of invalid discovery configurations can be found at:

* [`/tests/data/discovery_config_invalid_2.json`](../../tests/data/discovery_config_invalid_2.json)
* [`/tests/data/discovery_config_invalid_3.json`](../../tests/data/discovery_config_invalid_3.json)

### ERROR: If duplicate charts or search fields are defined

A field may only be used once as a chart, and once as a search field. Any more than that will produce a 
`DiscoveryValidationError` with a message containing the location of where the error occurred and the phrase
"field already seen".

Examples of invalid discovery configurations can be found at:

* [`/tests/data/discovery_config_invalid_4.json`](../../tests/data/discovery_config_invalid_4.json)
* [`/tests/data/discovery_config_invalid_5.json`](../../tests/data/discovery_config_invalid_5.json)

### WARNING: A field is defined without being used anywhere in the configuration

If a field is defined in the configuration `"fields": {...}` block, but not used anywhere, a warning will be emitted,
which will look something like the following:

```
2025-04-08 10:53:18 [warning  ] field not referenced           field=lab_test_result_value field_idx=0
```

An example of a discovery configuration which will produce this warning can be found at:

* [`/tests/data/discovery_config_warning.json`](../../tests/data/discovery_config_warning.json)
