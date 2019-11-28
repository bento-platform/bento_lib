import json
import os
import redis

from typing import Callable

__all__ = [
    "add_handler",
    "start_event_loop",
    "stop_event_loop",

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
    _event_thread.stop()
    _event_thread = None


# Events

ALL_SERVICE_EVENTS = "service.*"
ALL_DATA_TYPE_EVENTS = "data_type.*"

_SERVICE_CHANNEL_TPL = "service.{}"
_DATA_TYPE_CHANNEL_TPL = "data_type.{}"

_service_event_types = set()
_data_type_event_types = set()


def _make_event(event_type: str, event_data, attrs: dict):
    return json.dumps({
        "type": event_type.lower(),
        "data": event_data,
        **attrs
    })


def _publish_event(channel, event_type: str, event_data, attrs: dict):
    _rc.publish(channel, _make_event(event_type, event_data, attrs))


# TODO: Incorporate schemas into registration

def register_service_event_type(event_type: str) -> None:
    _service_event_types.add(event_type.lower())


def register_data_type_event_type(event_type: str) -> None:
    _data_type_event_types.add(event_type.lower())


def get_service_event_types() -> set:
    return _service_event_types.copy()


def get_data_type_event_types() -> set:
    return _data_type_event_types.copy()


def publish_service_event(service_artifact: str, event_type: str, event_data) -> bool:
    if event_type not in _service_event_types:
        return False

    _publish_event(
        channel=_SERVICE_CHANNEL_TPL.format(service_artifact),
        event_type=event_type,
        event_data=event_data,
        attrs={"service_artifact": service_artifact}
    )
    return True


def publish_data_type_event(data_type: str, event_type: str, event_data) -> bool:
    # TODO: Validate data type?

    if event_type not in _data_type_event_types:
        return False

    _publish_event(
        channel=_DATA_TYPE_CHANNEL_TPL.format(data_type),
        event_type=event_type,
        event_data=event_data,
        attrs={"data_type": data_type}
    )

    return True


# TODO: Wrapper for handlers which destructure event into an object?
