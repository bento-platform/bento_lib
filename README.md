# Bento Library (for Python Bento microservices)

![Build Status](https://api.travis-ci.org/bento-platform/bento_lib.svg?branch=master)
[![codecov](https://codecov.io/gh/bento-platform/bento_lib/branch/master/graph/badge.svg)](https://codecov.io/gh/bento-platform/bento_lib)
[![PyPI version](https://badge.fury.io/py/bento-lib.svg)](https://badge.fury.io/py/bento-lib)

Common utilities and helpers for Bento platform services.


## Running Tests

```bash
python3 -m tox
```


## Releasing


### 1. Release Checklist

  * [ ] All tests pass and test coverage has not been reduced

  * [ ] Package version has been updated (following semver) in 
    `bento_lib/package.cfg`
    
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
rm -rf build/ dist/ bento_lib.egg-info/

# Build the new package
python3 setup.py sdist bdist_wheel

# In between these steps - test out the package... make sure everyhting works
# before uploading it to production PyPI.

# Upload it to PyPI
twine upload dist/*
```


## Modules

### `auth`

`auth` provides Python service decorators and Django / DRF backends for dealing
with the Bento container authentication headers (derived from
`lua-resty-openidc`, set by the internal container NGINX instance.)

### `events`

`events` facilitates JSON-serialized message-passing between Bento
microservices. Serialized objects can be at most 512 MB.

Events should have a lower-case type which is type-insensitively unique and
adequately describes the associated data.

All Bento channels are prefixed with `bento.`.

### `ingestion`

`ingestion` contains common code used for handling ingestion routines in
different Bento data services.

### `schemas`

`schemas` contains common JSON schemas which may be useful to a variety of
different Bento services.

`schemas.bento` contains Bento-specific schemas, and `schemas.ga4gh` contains
GA4GH-standardized schemas (possibly not exactly to spec.)

### `search`

`search` contains definitions, validators, and transformations for the query
syntax for Bento, as well as a transpiler to the `psycopg2` PostgreSQL IR.

The query syntax for Bento takes advantage of JSON schemas augmented with
additional properties about the field's accessibility and, in the case of
Postgres, how the field maps to a table column (or JSON column sub-field.)

`search.data_structure` contains code for evaluating a Bento query against a
Python data structure.

`search.operations` contains constants representing valid search operations one
can allow against particular fields from within an augmented JSON schema.

`search.postgres` contains a "transpiler" from the Bento query syntax to the
`psycopg2`-provided
[intermediate representation (IR)](https://www.psycopg.org/docs/sql.html) for
PostgreSQL, allowing safe queries against a Postgres database.

`search.queries` provides definitions for the Bento query AST and some helper
methods for creating and processing ASTs.

### `utils`

`utils` contains miscellaneous utilities commonly required by Bento services.

### `workflows`

`workflows` contains common code used for handling workflow metadata processing
and response generation.
