from abc import ABC, abstractmethod
from collections.abc import Callable

from jsonschema import Draft7Validator

__all__ = ["BaseEventBus", "Serializable"]

# Types
type Serializable = bool | float | int | str | dict | list | tuple | None


class BaseEventBus(ABC):
    @abstractmethod
    def add_handler(self, pattern: str, callback: Callable[[dict], None]) -> bool: ...

    @abstractmethod
    def start_event_loop(self) -> None: ...

    @abstractmethod
    def stop_event_loop(self) -> None: ...

    @staticmethod
    def validate_event(
        event_types: dict[str, Draft7Validator], event_type: str, event_data: Serializable
    ) -> bool:
        """
        TODO
        :param event_types: TODO
        :param event_type: TODO
        :param event_data: TODO
        :return:
        """

        if event_type not in event_types:
            return False

        return event_types[event_type].is_valid(event_data)

    @abstractmethod
    def _publish_event(
        self,
        event_types: dict[str, Draft7Validator],
        channel: str,
        event_type: str,
        event_data: Serializable,
        attrs: dict,
    ) -> bool: ...

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
            attrs={"service_artifact": service_artifact},
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
            attrs={"data_type": data_type},
        )
