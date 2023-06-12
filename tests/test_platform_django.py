from django.test import Client


def test_private(client: Client):
    res = client.get("/private/get")
    assert res.status_code == 200


def test_private_missing_flag(client: Client):
    res = client.get("/private/get-missing")
    assert res.status_code == 403
