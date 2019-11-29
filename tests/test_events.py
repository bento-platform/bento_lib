import chord_lib.events
import time

TEST_SERVICE = "test_service"
TEST_SERVICE_EVENT = "test_service_event"

TEST_DATA_TYPE = "data_type"
TEST_DATA_TYPE_EVENT = "test_data_type_event"

TEST_EVENT_SCHEMA = {"type": "string"}
TEST_EVENT_BODY = "test"


event_bus = chord_lib.events.EventBus()


def test_registration():
    r = event_bus.register_service_event_type(TEST_SERVICE_EVENT, TEST_EVENT_SCHEMA)
    assert r
    assert TEST_SERVICE_EVENT in event_bus.get_service_event_types()
    r = event_bus.register_service_event_type(TEST_SERVICE_EVENT, TEST_EVENT_SCHEMA)
    assert not r

    r = event_bus.register_data_type_event_type(TEST_DATA_TYPE_EVENT, TEST_EVENT_SCHEMA)
    assert r
    assert TEST_DATA_TYPE_EVENT in event_bus.get_data_type_event_types()
    r = event_bus.register_data_type_event_type(TEST_DATA_TYPE_EVENT, TEST_EVENT_SCHEMA)
    assert not r

    assert TEST_SERVICE_EVENT not in event_bus.get_data_type_event_types()
    assert TEST_DATA_TYPE_EVENT not in event_bus.get_service_event_types()

    # Invalid schema
    r = event_bus.register_data_type_event_type("some_event", {
        "type": "object",
        "additionalProperties": 7
    })
    assert not r


def test_service_events():
    try:
        def handle_service_event(message):
            event = message["data"]
            assert event["service"] == TEST_SERVICE
            assert event["type"] == TEST_SERVICE_EVENT
            assert event["data"] == TEST_EVENT_BODY

        event_bus.add_handler(chord_lib.events.ALL_SERVICE_EVENTS, handle_service_event)
        event_bus.start_event_loop()

        r = event_bus.publish_service_event(TEST_SERVICE, TEST_SERVICE_EVENT, TEST_EVENT_BODY)
        assert r

        r = event_bus.publish_service_event(TEST_SERVICE, "fake_event", TEST_EVENT_BODY)
        assert not r

        r = event_bus.publish_service_event(TEST_SERVICE, TEST_SERVICE_EVENT, {"bad": "body"})
        assert not r

        # TODO: False r case

        time.sleep(0.1)

    finally:
        event_bus.stop_event_loop()


def test_data_type_events():
    try:
        def handle_data_type_event(message):
            event = message["data"]
            assert event["data_type"] == TEST_DATA_TYPE
            assert event["type"] == TEST_DATA_TYPE_EVENT
            assert event["data"] == TEST_EVENT_BODY

        event_bus.add_handler(chord_lib.events.ALL_DATA_TYPE_EVENTS, handle_data_type_event)
        event_bus.start_event_loop()

        r = event_bus.publish_data_type_event(TEST_DATA_TYPE, TEST_DATA_TYPE_EVENT, TEST_EVENT_BODY)
        assert r

        time.sleep(0.1)

    finally:
        event_bus.stop_event_loop()


def test_premature_stop():
    event_bus.stop_event_loop()


def test_late_handler():
    try:
        event_bus.start_event_loop()
        r = event_bus.add_handler(chord_lib.events.ALL_SERVICE_EVENTS, lambda _: None)
        assert not r
    finally:
        event_bus.stop_event_loop()


# TODO: Verify cross-talk
