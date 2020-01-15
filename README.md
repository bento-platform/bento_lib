# CHORD Library (for Python CHORD microservices)

![Build Status](https://api.travis-ci.org/c3g/chord_lib.svg?branch=master)
[![codecov](https://codecov.io/gh/c3g/chord_lib/branch/master/graph/badge.svg)](https://codecov.io/gh/c3g/chord_lib)
[![PyPI version](https://badge.fury.io/py/chord-lib.svg)](https://badge.fury.io/py/chord-lib)

Common utilities and helpers for CHORD services.


## Running Tests

```bash
python3 -m pytest --cov=chord_lib --cov-branch
```


## Modules

### `events`

`events` facilitates JSON-serialized message-passing between CHORD
microservices. Serialized objects can be at most 512 MB.

Events should have a lower-case type which is type-insensitively unique and
adequately describes the associated data.

All CHORD channels are prefixed with `chord.`.

### `ingestion`

`ingestion` contains common code used for handling ingestion routines in
different CHORD data services.

### `schemas`

`schemas` contains common JSON schemas which may be useful to a variety of
different CHORD services.

`schemas.chord` contains CHORD-specific schemas, and `schemas.ga4gh` contains
GA4GH-standardized schemas (possibly not exactly to spec.)

### `search`

`search` contains definitions, validators, and transformations for the query
syntax for CHORD, as well as a transpiler to the `psycopg2` PostgreSQL IR.

### `utils`

`utils` contains miscellaneous utilities commonly required by CHORD services.

### `workflows`

`workflows` contains common code used for handling workflow metadata processing
and response generation.
