__all__ = [
    "RESOURCE_EVERYTHING",
    "build_resource",
]


RESOURCE_EVERYTHING = {"everything": True}


def build_resource(project: str | None = None, dataset: str | None = None, data_type: str | None = None) -> dict:
    if project is None:
        return RESOURCE_EVERYTHING

    res = {"project": project}
    if dataset:
        res["dataset"] = dataset
    if data_type:
        res["data_type"] = data_type

    return res
