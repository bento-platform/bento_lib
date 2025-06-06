# Bento Library (for Python Bento microservices)

![Test Status](https://github.com/bento-platform/bento_lib/workflows/Test/badge.svg)
![Lint Status](https://github.com/bento-platform/bento_lib/workflows/Lint/badge.svg)
[![codecov](https://codecov.io/gh/bento-platform/bento_lib/branch/master/graph/badge.svg)](https://codecov.io/gh/bento-platform/bento_lib)
[![PyPI version](https://badge.fury.io/py/bento-lib.svg)](https://badge.fury.io/py/bento-lib)

Common utilities and helpers for Bento platform services.


## Installing

`bento_lib` can be added to a new service through normal installation, with any extras 
that may be needed:

```bash
# Add to a project using Poetry for dependencies
poetry add bento_lib

# Install using pip with the FastAPI extra
pip install bento_lib[fastapi]

# etc...
```


## Developing

Clone the repository and set up the Poetry environment using the following commands:

```bash
git clone git@github.com:bento-platform/bento_lib.git
poetry install --all-extras
```


### Running Tests

For tests to complete successfully, the following external servers must be running:

* A Redis server at `localhost:6379`
* A Postgres server at `localhost:5432` with `peer` access for the `postgres` 
  role/database 

Then, tests and linting can be run with the following command:

```bash
poetry run tox
```


### Releasing


#### 1. Release Checklist

  * [ ] All tests pass and test coverage has not been reduced

  * [ ] Package version has been updated (following semver) in `pyproject.toml`
    
  * [ ] The latest changes have been merged into the `master` branch
    
  * [ ] A release has been created, tagged in the format of `v#.#.#` and named
    in the format of `Version #.#.#`, listing any changes made, in the GitHub 
    releases page **tagged from the master branch!**
    

##### 1A. Note on Versioning

The `bento_lib` project uses [semantic versioning](https://semver.org/) for
releasing. If the API is broken in any way, including minor differences in the
way a function behaves given an identical set of parameters (excluding bugfixes
for unintentional behaviour), the MAJOR version must be incremented. In this 
way, we guarantee that projects relying on this API do not accidentally break
upon upgrading.


#### 2. Releasing automatically

When a version is tagged on GitHub, a build + release CI pipeline is automatically triggered.
Make sure that the tagged version is a valid semantic versioning translation of the version in
`pyproject.toml`, and that the versions otherwise match.


## Modules

### `apps`

`apps` provides Python classes for setting up applications, wrapping a framework's base class with
additional code to set up error handling and basic Bento service boilerplate.

### `auth`

`auth` provides Python service middleware for dealing with the Bento authorization service.

### `db`

`db` contains common base classes for setting up database managers.

### `discovery`

`discovery` contains models and helper functions for the Bento Discovery Configuration specification, used
in [Katsu](https://github.com/bento-platform/katsu).

#### Guides

* [Discovery configuration: structure and validation](./docs/discovery/discovery_config.md)

### `drs`

`drs` provides utilities for fetching data and record metadata from 
GA4GH-compatible DRS services, and Bento's own implementation (which has some 
non-standard extensions.)

### `events`

`events` facilitates JSON-serialized message-passing between Bento
microservices. Serialized objects can be at most 512 MB.

Events should have a lower-case type which is type-insensitively unique and
adequately describes the associated data.

All Bento channels are prefixed with `bento.`.

### `logging`

`logging` contains helper functions and types for standardized Bento logging 
configuration and formatting, including structured logging using 
[`structlog`](https://www.structlog.org/en/stable/).

#### Guides

* [setting up structured logging in FastAPI](./docs/logging/fastapi_structlog.md)

### `responses`

`responses` contains standardized error message-generating functions 
and exception handling functions for different Python web frameworks.

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

### `service_info`

`service_info` contains Python typed dictionaries, Pydantic models, and helpers
for common structures and operations related to GA4GH's `/service-info` 
specification.

#### Guides

* [Bento's use of the GA4GH `/service-info` specification](./docs/service_info/bento_service_info.md)

### `streaming`

`streaming` contains helper code for streaming bytes via HTTP from files, and 
proxied HTTP resources, including exception definitions and HTTP `Range` header 
parsing. 

### `utils`

Small common-use utilities for Bento services and other libraries.

### `workflows`

`workflows` contains common code used for handling workflow metadata processing
and response generation, as well as code associated with Bento's ingestion
routines across the different data services.
