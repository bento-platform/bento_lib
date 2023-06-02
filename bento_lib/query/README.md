# Bento querying system

## Goals

* Simpler to work with than the old `bento_lib.search` methods
* Separate `and`/`or`, Boolean querying (<=, ==, !=, etc.) vs. expressions returning typed values 
  which exist in schema-land (numbers/strings/etc.)
* **Flow:** 
   * request 
   * -> compiled request object (for number of term counts for censorship, AST generation, etc.) 
   * -> passed to executor (Postgres or Python DS or ElasticSearch) class 
   * -> generated result structure


## Request format

TODO

`POST /data-types/phenopacket/search`

```json
{
  "query": [
    {
      "or": [
        {
          "field": ["biosamples", "[item]", "id"],
          "negated": false,
          "operator": "<",
          "expr": 2
        },
        {
          "field": ["biosamples", "[item]", "id"],
          "negated": false,
          "operator": ">=",
          "expr": 4
        }
      ]
    },
    {
      "field": ["biosamples", "[item]", "id"],
      "negated": false,
      "operator": ">=",
      "expr": ["#plus", 5, 3]
    }
  ],
  "response": {
    "type": "items",
    "item": ["biosamples", "[item]"],
    "item": {
      "subject_id": ["subject", "id"],
      "filename": ["experiments", "[item]", "experiment_results", "[item]", "file_name"]
    },
    "key": "id"
  }
}
```

```json
[
  {"subject_id":  "aaaa", "filename":  "jdsd"},
  {"subject_id":  "aaaa", "filename":  "jdsd"},
  {"subject_id":  "aaaa", "filename":  "jdsd"},
  {"subject_id":  "aaaa", "filename":  "jdsd"},
  {"subject_id":  "aaaa", "filename":  "jdsd"}
]
```

* `negated` is optional; defaults to `false`
* `key` must be in `required[]` of the schema for `item`


## Response format

TODO

```json
{
  "result": true,
  "time": 0.2
}
```

TODO

```json
{
  "result": 5,
  "time": 0.3
}
```

TODO

```json
{
  "result": [
    {"id": "BIO100", "type": "blood"}
  ],
  "time": 0.5
}
```


## Schemas

TODO

```json
{
  "properties": {
    "id": {
      "type": "integer",
      "x-bento": {
        
      }
    }
  },
  "required": ["id"]
}
```


## Data services: querying endpoints

* Aggregation: `POST /search`
  * `{"dataset": "..." OR ["..."], "data-type-queries": {"phenopacket": [...], "variant": [...]}, "join-query": [...]}`
  * Cache search until we get new WES signals to invalidate cache, or it is older than 24H

* Data service: `POST /data-types/<...>/search`
  * `{"dataset": "..." OR ["...", "..."], ...(query format)}`
  * Cache search until invalidated by new ingestion
