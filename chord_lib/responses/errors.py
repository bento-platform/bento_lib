import datetime


__all__ = ["forbidden_error"]


def forbidden_error():
    return {
        "code": 403,
        "message": "Forbidden",
        "timestamp": datetime.datetime.utcnow().isoformat("T") + "Z",
        # TODO: Error list, like in service-info / similar
    }
