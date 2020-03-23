# CHORD Library (for Python CHORD microservices)

![Build Status](https://api.travis-ci.org/c3g/chord_lib.svg?branch=master)
[![codecov](https://codecov.io/gh/c3g/chord_lib/branch/master/graph/badge.svg)](https://codecov.io/gh/c3g/chord_lib)
[![PyPI version](https://badge.fury.io/py/chord-lib.svg)](https://badge.fury.io/py/chord-lib)

Common utilities and helpers for CHORD services.


## Running Tests

```bash
python3 -m tox
```


## Releasing


### 1. Release Checklist

  * [ ] All tests pass and test coverage has not been reduced

  * [ ] Package version has been updated (following semver) in 
    `chord_lib/package.cfg`
    
  * [ ] The latest changes have been merged from the `develop` branch into the
    `master` branch
    
  * [ ] A release has been created, tagged in the format of `v#.#.#` and named
    in the format of `Version #.#.#`, listing any changes made, in the GitHub 
    releases page **tagged from the master branch!**


### 2. Releasing from the Command Line

```bash
# IF NECESSARY: Install twine OUTSIDE of the virtual environment
python3 -m pip install twine

# Switch to the correct branch and make sure it's up to date
git checkout master
git pull

# If needed, enter the project virtual environment
source env/bin/activate

# Remove existing build files
rm -rf build/ dist/ chord_lib.egg-info/

# Build the new package
python3 setup.py sdist bdist_wheel

# In between these steps - test out the package... make sure everyhting works
# before uploading it to production PyPI.

# Upload it to PyPI
python3 -m twine upload dist/*
```


## Modules

### `auth`

`auth` provides Python service decorators and Django / DRF backends for dealing
with the CHORD container authentication headers (derived from
`lua-resty-openidc`, set by the internal container NGINX instance.)

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

The query syntax for CHORD takes advantage of JSON schemas augmented with
additional properties about the field's accessibility and, in the case of
Postgres, how the field maps to a table column (or JSON column sub-field.)

`search.data_structure` contains code for evaluating a CHORD query against a
Python data structure.

`search.operations` contains constants representing valid search operations one
can allow against particular fields from within an augmented JSON schema.

`search.postgres` contains a "transpiler" from the CHORD query syntax to the
`psycopg2`-provided
[intermediate representation (IR)](https://www.psycopg.org/docs/sql.html) for
PostgreSQL, allowing safe queries against a Postgres database.

`search.queries` provides definitions for the CHORD query AST and some helper
methods for creating and processing ASTs.

### `utils`

`utils` contains miscellaneous utilities commonly required by CHORD services.

### `workflows`

`workflows` contains common code used for handling workflow metadata processing
and response generation.
