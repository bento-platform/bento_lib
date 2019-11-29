import json
import jsonschema
import os
import redis

from typing import Callable, Union

__all__ = [
    "add_handler",
    "start_event_loop",
    "stop_event_loop",

    "register_service_event_type",
    "register_data_type_event_type",

    "publish_service_event",
    "publish_data_type_event",
]


# Types

Serializable = Union[bool, float, int, str, dict, list, tuple]


# Redis

_connection_info = {"unix_socket_path": os.environ.get("REDIS_SOCKET")} if "REDIS_SOCKET" in os.environ else {}

_rc = redis.Redis(**_connection_info)
_ps = _rc.pubsub()


_ps_handlers = {}
_event_thread = None


def add_handler(pattern: str, callback: Callable[[dict], None]) -> bool:
    if _event_thread is not None:
        return False

    _ps_handlers[pattern] = callback
    return True


def start_event_loop():
    global _event_thread
    _ps.psubscribe(**_ps_handlers)
    _event_thread = _ps.run_in_thread(sleep_time=0.001)


def stop_event_loop():
    global _event_thread

    if _event_thread is None:
        return

    _event_thread.stop()
    _event_thread = None


# Events

ALL_SERVICE_EVENTS = "service.*"
ALL_DATA_TYPE_EVENTS = "data_type.*"

_SERVICE_CHANNEL_TPL = "service.{}"
_DATA_TYPE_CHANNEL_TPL = "data_type.{}"

_service_event_types = {}
_data_type_event_types = {}


def _make_event(event_type: str, event_data, attrs: dict):
    return json.dumps({
        "type": event_type.lower(),
        "data": event_data,
        **attrs
    })


# TODO: Incorporate schemas into registration

def _add_schema(event_types: dict, event_type: str, event_schema: dict) -> bool:
    if event_type in event_types:
        return False

    try:
        jsonschema.validators.Draft7Validator.check_schema(event_schema)
    except jsonschema.exceptions.SchemaError:
        return False

    event_types[event_type.lower()] = event_schema
    return True


def register_service_event_type(event_type: str, event_schema: dict) -> bool:
    return _add_schema(_service_event_types, event_type, event_schema)


def register_data_type_event_type(event_type: str, event_schema: dict) -> bool:
    return _add_schema(_data_type_event_types, event_type, event_schema)


def get_service_event_types() -> dict:
    return {**_service_event_types}


def get_data_type_event_types() -> dict:
    return {**_data_type_event_types}


def _publish_event(event_types: dict, channel: str, event_type: str, event_data: Serializable, attrs: dict) -> bool:
    if event_type not in event_types:
        return False

    if not jsonschema.validators.Draft7Validator(event_types[event_type]).is_valid(event_data):
        return False

    _rc.publish(channel, _make_event(event_type, event_data, attrs))
    return True


def publish_service_event(service_artifact: str, event_type: str, event_data: Serializable) -> bool:
    return _publish_event(
        event_types=_service_event_types,
        channel=_SERVICE_CHANNEL_TPL.format(service_artifact),
        event_type=event_type,
        event_data=event_data,
        attrs={"service_artifact": service_artifact}
    )


def publish_data_type_event(data_type: str, event_type: str, event_data: Serializable) -> bool:
    return _publish_event(
        event_types=_data_type_event_types,
        channel=_DATA_TYPE_CHANNEL_TPL.format(data_type),
        event_type=event_type,
        event_data=event_data,
        attrs={"data_type": data_type}
    )


# TODO: Wrapper for handlers which destructure event into an object?
