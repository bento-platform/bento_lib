import chord_lib.events
import json
import time

TEST_SERVICE = "test_service"
TEST_SERVICE_EVENT = "test_service_event"

TEST_DATA_TYPE = "data_type"
TEST_DATA_TYPE_EVENT = "test_data_type_event"

TEST_EVENT_BODY = "test"


def test_registration():
    chord_lib.events.register_service_event_type(TEST_SERVICE_EVENT)
    assert TEST_SERVICE_EVENT in chord_lib.events.get_service_event_types()

    chord_lib.events.register_data_type_event_type(TEST_DATA_TYPE_EVENT)
    assert TEST_DATA_TYPE_EVENT in chord_lib.events.get_data_type_event_types()

    assert TEST_SERVICE_EVENT not in chord_lib.events.get_data_type_event_types()
    assert TEST_DATA_TYPE_EVENT not in chord_lib.events.get_service_event_types()


def test_service_events():
    def handle_service_event(message):
        event = json.loads(message["data"])
        assert event["service"] == TEST_SERVICE
        assert event["type"] == TEST_SERVICE_EVENT
        assert event["data"] == TEST_EVENT_BODY

    chord_lib.events.add_handler(chord_lib.events.ALL_SERVICE_EVENTS, handle_service_event)
    chord_lib.events.start_event_loop()

    r = chord_lib.events.publish_service_event(TEST_SERVICE, TEST_SERVICE_EVENT, TEST_EVENT_BODY)
    assert r

    # TODO: False r case

    time.sleep(0.1)

    chord_lib.events.stop_event_loop()


def test_data_type_events():
    def handle_data_type_event(message):
        event = json.loads(message["data"])
        assert event["data_type"] == TEST_DATA_TYPE
        assert event["type"] == TEST_DATA_TYPE_EVENT
        assert event["data"] == TEST_EVENT_BODY

    chord_lib.events.add_handler(chord_lib.events.ALL_DATA_TYPE_EVENTS, handle_data_type_event)
    chord_lib.events.start_event_loop()

    r = chord_lib.events.publish_data_type_event(TEST_DATA_TYPE, TEST_DATA_TYPE_EVENT, TEST_EVENT_BODY)
    assert r

    # TODO: False r case

    time.sleep(0.1)

    chord_lib.events.stop_event_loop()


# TODO: Verify cross-talk
