import json
import jsonschema
import os
import redis

from typing import Callable, Union

__all__ = [
    "ALL_SERVICE_EVENTS",
    "ALL_DATA_TYPE_EVENTS",
    "EventBus",
]


ALL_SERVICE_EVENTS = "service.*"
ALL_DATA_TYPE_EVENTS = "data_type.*"

_SERVICE_CHANNEL_TPL = "service.{}"
_DATA_TYPE_CHANNEL_TPL = "data_type.{}"


# Types

Serializable = Union[bool, float, int, str, dict, list, tuple]


# Redis

_connection_info = {"unix_socket_path": os.environ.get("REDIS_SOCKET")} if "REDIS_SOCKET" in os.environ else {}


class EventBus:
    def __init__(self):
        self._rc = redis.Redis(**_connection_info)
        self._ps = self._rc.pubsub()

        self._ps_handlers = {}
        self._event_thread = None

        self._service_event_types = {}
        self._data_type_event_types = {}

    @staticmethod
    def _callback_deserialize(callback: Callable[[dict], None]):
        return lambda message: callback({
            **message,
            "data": json.loads(message["data"])
        })

    def add_handler(self, pattern: str, callback: Callable[[dict], None]) -> bool:
        if self._event_thread is not None:
            return False

        self._ps_handlers[pattern] = self._callback_deserialize(callback)
        return True

    def start_event_loop(self):
        self._ps.psubscribe(**self._ps_handlers)
        self._event_thread = self._ps.run_in_thread(sleep_time=0.001)

    def stop_event_loop(self):
        if self._event_thread is None:
            return

        self._event_thread.stop()
        self._event_thread = None

    @staticmethod
    def _make_event(event_type: str, event_data, attrs: dict):
        return json.dumps({
            "type": event_type.lower(),
            "data": event_data,
            **attrs
        })

    @staticmethod
    def _add_schema(event_types: dict, event_type: str, event_schema: dict) -> bool:
        if event_type in event_types:
            return False

        try:
            jsonschema.validators.Draft7Validator.check_schema(event_schema)
        except jsonschema.exceptions.SchemaError:
            return False

        event_types[event_type.lower()] = event_schema
        return True

    def register_service_event_type(self, event_type: str, event_schema: dict) -> bool:
        return self._add_schema(self._service_event_types, event_type, event_schema)

    def register_data_type_event_type(self, event_type: str, event_schema: dict) -> bool:
        return self._add_schema(self._data_type_event_types, event_type, event_schema)

    def get_service_event_types(self) -> dict:
        return {**self._service_event_types}

    def get_data_type_event_types(self) -> dict:
        return {**self._data_type_event_types}

    def _publish_event(
        self,
        event_types: dict,
        channel: str,
        event_type: str,
        event_data: Serializable,
        attrs: dict
    ) -> bool:
        if event_type not in event_types:
            return False

        if not jsonschema.validators.Draft7Validator(event_types[event_type]).is_valid(event_data):
            return False

        self._rc.publish(channel, self._make_event(event_type, event_data, attrs))
        return True

    def publish_service_event(self, service_artifact: str, event_type: str, event_data: Serializable) -> bool:
        return self._publish_event(
            event_types=self._service_event_types,
            channel=_SERVICE_CHANNEL_TPL.format(service_artifact),
            event_type=event_type,
            event_data=event_data,
            attrs={"service_artifact": service_artifact}
        )

    def publish_data_type_event(self, data_type: str, event_type: str, event_data: Serializable) -> bool:
        return self._publish_event(
            event_types=self._data_type_event_types,
            channel=_DATA_TYPE_CHANNEL_TPL.format(data_type),
            event_type=event_type,
            event_data=event_data,
            attrs={"data_type": data_type}
        )
