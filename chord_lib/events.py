import json
import os
import redis

from typing import Callable

__all__ = [
    "add_handler",
    "run_event_loop",

    "register_service_event_type",
    "register_data_type_event_type",

    "publish_service_event",
    "publish_data_type_event",
]


# Redis

_connection_info = {"unix_socket_path": os.environ.get("REDIS_SOCKET")} if "REDIS_SOCKET" in os.environ else {}

_rc = redis.Redis(**_connection_info)
_ps = _rc.pubsub()


_ps_handlers = {}
_event_thread = None


def add_handler(pattern: str, callback: Callable) -> bool:
    if _event_thread is not None:
        return False

    _ps_handlers[pattern] = callback
    return True


def run_event_loop():
    global _event_thread
    _ps.psubscribe(**_ps_handlers)
    _event_thread = _ps.run_in_thread(sleep_time=0.001)


# Events

_SERVICE_CHANNEL_TPL = "service.{}"
_DATA_TYPE_CHANNEL_TPL = "data_type.{}"

_service_event_types = set()
_data_type_event_types = set()


def _make_event(event_type: str, event_data):
    return json.dumps({
        "type": event_type.lower(),
        "data": event_data
    })


def _publish_event(channel, event_type: str, event_data):
    _rc.publish(channel, _make_event(event_type, event_data))


def register_service_event_type(event_type: str) -> None:
    _service_event_types.add(event_type.lower)


def register_data_type_event_type(event_type: str) -> None:
    _data_type_event_types.add(event_type.lower)


def get_service_event_types() -> set:
    return _service_event_types.copy()


def get_data_type_event_types() -> set:
    return _data_type_event_types.copy()


def publish_service_event(service_artifact: str, event_type: str, event_data) -> bool:
    if event_type not in _service_event_types:
        return False

    _publish_event(_SERVICE_CHANNEL_TPL.format(service_artifact), event_type, event_data)
    return True


def publish_data_type_event(data_type: str, event_type: str, event_data) -> bool:
    # TODO: Validate data type?

    if event_type not in _data_type_event_types:
        return False

    _publish_event(_DATA_TYPE_CHANNEL_TPL.format(data_type), event_type, event_data)
    return True
