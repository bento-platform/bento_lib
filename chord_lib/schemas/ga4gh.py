from ._utils import load_json_schema


__all__ = ["SERVICE_INFO_SCHEMA"]


SERVICE_INFO_SCHEMA = load_json_schema("ga4gh_service_info.schema.json")
