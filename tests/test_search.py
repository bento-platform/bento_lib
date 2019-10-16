from chord_lib.search import *
from datetime import datetime


def test_build_search_response():
    test_response = build_search_response({"some": "result"}, datetime.now())

    assert isinstance(test_response, dict)
    assert tuple(sorted(test_response.keys())) == ("results", "time")
    assert any((isinstance(test_response["results"], dict),
                isinstance(test_response["results"], list),
                isinstance(test_response["results"], tuple)))

    t = float(test_response["time"])
    assert t >= 0
