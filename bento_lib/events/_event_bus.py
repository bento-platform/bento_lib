import json
import jsonschema
import redis

from typing import Callable, Optional, Union

__all__ = ["EventBus"]

# Channel templates
SERVICE_CHANNEL_TPL = "bento.service.{}"
DATA_TYPE_CHANNEL_TPL = "bento.data_type.{}"

# Types
Serializable = Union[bool, float, int, str, dict, list, tuple, None]

# Redis
default_connection_data = {"host": "localhost", "port": 6379}


class EventBus:
    """
    Event bus for subscribing to and publishing events for other microservices.
    """

    @staticmethod
    def _get_redis(**kwargs) -> redis.Redis:
        if "url" in kwargs:
            return redis.Redis.from_url(kwargs["url"])
        return redis.Redis(**kwargs)

    def __init__(self, allow_fake: bool = False, **kwargs):
        """
        Sets up a Redis connection based on the REDIS_SOCKET environment variable (or defaults, if the variable is
        not present.) Keyword arguments are passed to the Redis connection factory. If "url" is passed as a keyword
        argument, it is used instead of any other keyword arguments.
        :param allow_fake: Whether to allow for "fake" connections, i.e. no true connection to Redis.
        """

        self._rc: Optional[redis.Redis] = None

        try:
            self._rc = self._get_redis(**(kwargs or default_connection_data))
            self._rc.get("")  # Dummy request to check connection
        except redis.exceptions.ConnectionError as e:
            self._rc = None
            if not allow_fake:
                raise e
            # TODO: Log otherwise (as info)

        self._ps: Optional[redis.PubSub] = None

        self._ps_handlers: dict[str, Callable[[dict], None]] = {}
        self._event_thread: Optional[redis.PubSubWorkerThread] = None

        self._service_event_types = {}
        self._data_type_event_types = {}

    @staticmethod
    def _callback_deserialize(callback: Callable[[dict], None]) -> Callable[[dict], None]:
        return lambda message: callback({
            **message,
            "data": json.loads(message["data"]) if message["type"] in ("message", "pmessage") else message["data"]
        })

    def add_handler(self, pattern: str, callback: Callable[[dict], None]) -> bool:
        """
        Adds a channel pattern handler to the event bus if the event handling thread has not been started.
        :param pattern: Channel pattern (Redis syntax) to subscribe to.
        :param callback: Function to call (with message dictionary, see redis-py docs) when a matching event occurs.
        :return: True if the handler was successfully added, False otherwise.
        """

        if self._event_thread is not None:
            return False

        if pattern in self._ps_handlers:
            return False

        self._ps_handlers[pattern] = self._callback_deserialize(callback)
        return True

    def start_event_loop(self) -> None:
        """
        Starts the event handling loop in a new thread. Whichever handlers were previously added will be present.
        The loop must be restarted if the handlers are changed.
        """

        if self._rc is None:
            return

        if self._event_thread is not None:
            return

        self._ps = self._rc.pubsub()
        self._ps.psubscribe(**self._ps_handlers)
        self._event_thread = self._ps.run_in_thread(sleep_time=0.001, daemon=True)

    def stop_event_loop(self) -> None:
        """
        Stops the event handling loop, if running. Otherwise, does nothing.
        """

        if self._event_thread is None:
            return

        self._event_thread.stop()
        self._event_thread = None
        self._ps = None

    @staticmethod
    def _make_event(event_type: str, event_data, attrs: dict) -> str:
        return json.dumps({
            "type": event_type.lower(),
            "data": event_data,
            **attrs
        })

    @staticmethod
    def _add_schema(event_types: dict, event_type: str, event_schema: dict) -> bool:
        event_type = event_type.lower()

        if event_type in event_types:
            return False

        try:
            jsonschema.validators.Draft7Validator.check_schema(event_schema)
        except jsonschema.exceptions.SchemaError:
            return False

        event_types[event_type] = event_schema
        return True

    def register_service_event_type(self, event_type: str, event_schema: dict) -> bool:
        """
        Registers a service event type with the event bus.
        :param event_type: The type of event, which will be included in message objects.
        :param event_schema: JSON schema which will be checked against any events submitted.
        :return: True if the event type was successfully registered, False otherwise.
        """
        return self._add_schema(self._service_event_types, event_type, event_schema)

    def register_data_type_event_type(self, event_type: str, event_schema: dict) -> bool:
        """
        Registers a service event type with the event bus.
        :param event_type: The type of event, which will be included in message objects.
        :param event_schema: JSON schema which will be checked against any events submitted.
        :return: True if the event type was successfully registered, False otherwise.
        """
        return self._add_schema(self._data_type_event_types, event_type, event_schema)

    def get_service_event_types(self) -> dict:
        """
        :return: A dictionary of registered service event types and their associated schemas.
        """
        return {**self._service_event_types}

    def get_data_type_event_types(self) -> dict:
        """
        :return: A dictionary of registered data type event types and their associated schemas.
        """
        return {**self._data_type_event_types}

    def _publish_event(
        self,
        event_types: dict,
        channel: str,
        event_type: str,
        event_data: Serializable,
        attrs: dict
    ) -> bool:
        event_type = event_type.lower()

        if event_type not in event_types:
            return False

        if not jsonschema.validators.Draft7Validator(event_types[event_type]).is_valid(event_data):
            return False

        if self._rc is None:
            return False

        self._rc.publish(channel, self._make_event(event_type, event_data, attrs))
        return True

    def publish_service_event(self, service_artifact: str, event_type: str, event_data: Serializable) -> bool:
        """
        Publishes a service event.
        :param service_artifact: Service artifact associated with the event to publish.
        :param event_type: The identifier for the event (not to be confused with its channel.)
        :param event_data: The data to send with the event; JSON-serializable.
        :return: True if the event was successfully published, False otherwise.
        """
        return self._publish_event(
            event_types=self._service_event_types,
            channel=SERVICE_CHANNEL_TPL.format(service_artifact),
            event_type=event_type,
            event_data=event_data,
            attrs={"service_artifact": service_artifact}
        )

    def publish_data_type_event(self, data_type: str, event_type: str, event_data: Serializable) -> bool:
        """
        Publishes a data type event.
        :param data_type: Data type associated with the event to publish.
        :param event_type: The identifier for the event (not to be confused with its channel.)
        :param event_data: The data to send with the event; JSON-serializable.
        :return: True if the event was successfully published, False otherwise.
        """
        return self._publish_event(
            event_types=self._data_type_event_types,
            channel=DATA_TYPE_CHANNEL_TPL.format(data_type),
            event_type=event_type,
            event_data=event_data,
            attrs={"data_type": data_type}
        )
