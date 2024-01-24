from .permissions import Permission, LEVEL_PROJECT, LEVEL_DATASET

__all__ = [
    "permission_valid_for_resource",
]


def permission_valid_for_resource(permission: Permission, resource: dict) -> bool:
    if permission.min_level_required == LEVEL_DATASET:
        return True
    elif permission.min_level_required == LEVEL_PROJECT:
        return "dataset" not in resource
    else:  # LEVEL_INSTANCE
        return "dataset" not in resource and "project" not in resource and resource.get("everything", False)
        # otherwise, invalid resource (so False)
