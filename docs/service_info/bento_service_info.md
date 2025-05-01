# Bento's use of the GA4GH `/service-info` specification

All Bento services implement an extended version of the 
[GA4GH `/service-info` endpoint specification](https://github.com/ga4gh-discovery/ga4gh-service-info/blob/develop/service-info.yaml),
which are then aggregated into a [Bento Service Registry](https://github.com/bento-platform/bento_service_registry),
which extends the 
[GA4GH Service Registry specification](https://github.com/ga4gh-discovery/ga4gh-service-registry/blob/develop/service-registry.yaml).


## Bento's extensions to `/service-info`

A `bento` property has been added, which contains Bento service-specific information, e.g.:

```js
{
    // ...
    "bento": {
        "serviceKind": "metadata",
        "dataService": true,
        "gitRepository": "https://github.com/bento-platform/katsu",
        "gitTag: "v10.0.0",
        "gitBranch": "refact/discovery-config-model",
        "gitCommit": "6862f22c462b8366abacdf42e01a5ddaff173143",
    }
}
```

The following properties are allowed in the `bento` object inside Bento `/service-info` responses:

* `serviceKind: string`
  * A unique identifier for the kind of Bento service this is (e.g., `drop-box`, `wes`, `service-registry`, ...). 
    Styled lowercase and with dashes as word-separators.
* `dataService: boolean`
  * Whether the service is a data-providing service and serves a Bento-compatible `/data-types` endpoint defining the
    "data types" it can store. Can be left out, which implicitly means `false` here.
* `workflowProvider: boolean`
  * Whether the service is a workflow-providing service and serves Bento-compatible `/workflows`, `/workflows/<id>`, and
    `/workflows/<id>.wdl` endpoints. Implicitly defaults to `true` if `dataService` is `true`, and `false` otherwise.
* `gitRepository: string` (URL)
  * The service's Git repository URL.
* `gitTag: string`
  * If in local development mode, the most recent ancestor Git tag in the cloned service repository's current tree.
* `gitBranch: string`
  * If in local development mode, the current branch of the cloned service repository.
* `gitCommit: string`
  * If in local development mode, the most recent commit hash in the cloned service repository's current branch.


## Interacting with the Bento Service Registry from another service

If, in another service, you need the URL or other information about a service, the best way is to instantiate an 
instance of the [`bento_lib.service_info.ServiceManager` class](../../bento_lib/service_info/manager.py). The docstrings
of the class and its methods describe some possible interaction scenarios.
