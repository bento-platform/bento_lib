from .permissions import Permission, LEVEL_PROJECT, LEVEL_DATASET, PERMISSIONS

__all__ = [
    "permission_valid_for_resource",
    "valid_permissions_for_resource",
]


def permission_valid_for_resource(permission: Permission, resource: dict) -> bool:
    valid_data_type_narrowing = permission.supports_data_type_narrowing or "data_type" not in resource

    if permission.min_level_required == LEVEL_DATASET:
        return valid_data_type_narrowing
    elif permission.min_level_required == LEVEL_PROJECT:
        return valid_data_type_narrowing and "dataset" not in resource
    else:  # LEVEL_INSTANCE
        return (
            valid_data_type_narrowing
            and "dataset" not in resource
            and "project" not in resource
            and resource.get("everything", False)
        )
        # otherwise, invalid resource (so False)


def valid_permissions_for_resource(resource: dict) -> list[Permission]:
    return [p for p in PERMISSIONS if permission_valid_for_resource(p, resource)]
