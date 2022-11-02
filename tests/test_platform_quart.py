import asyncio
import bento_lib.auth.quart_decorators as qd
import bento_lib.responses.quart_errors as qe
import pytest
import pytest_asyncio

from quart import Quart
from werkzeug.exceptions import BadRequest, NotFound


@pytest_asyncio.fixture
async def quart_client():
    application = Quart(__name__)

    application.register_error_handler(Exception, qe.quart_error_wrap_with_traceback(qe.quart_internal_server_error))
    application.register_error_handler(BadRequest, qe.quart_error_wrap(qe.quart_bad_request_error))
    application.register_error_handler(NotFound, qe.quart_error_wrap(qe.quart_not_found_error, drs_compat=True))

    @application.route("/500")
    async def r500():
        await asyncio.sleep(0.5)
        raise Exception("help")

    @application.route("/test1")
    @qd.quart_permissions_any_user
    async def test1():
        await asyncio.sleep(0.5)
        return "test1"

    @application.route("/test2")
    @qd.quart_permissions_owner
    async def test2():
        await asyncio.sleep(0.5)
        return "test2"

    @application.route("/test3", methods=["GET", "POST"])
    @qd.quart_permissions({"POST": {"owner"}})
    async def test3():
        await asyncio.sleep(0.5)
        return "test3"

    yield application.test_client()


@pytest.mark.asyncio
async def test_quart_errors(quart_client):
    # Turn CHORD permissions mode on to make sure we're getting real permissions checks
    qd.BENTO_PERMISSIONS = True

    # non-existent endpoint

    r = await quart_client.get("/non-existent")
    assert r.status_code == 404
    rj = await r.get_json()
    assert rj["code"] == 404

    # - We passed drs_compat=True to this, so check for DRS-specific fields
    assert rj["status_code"] == rj["code"]
    assert rj["msg"] == rj["message"]

    # server error endpoint

    r = await quart_client.get("/500")
    assert r.status_code == 500
    assert (await r.get_json())["code"] == 500

    # /test1

    r = await quart_client.get("/test1")
    assert r.status_code == 403
    assert (await r.get_json())["code"] == 403

    r = await quart_client.get("/test1", headers={"X-User": "test", "X-User-Role": "user"})
    assert r.status_code == 200
    assert (await r.get_data()).decode("utf-8") == "test1"

    r = await quart_client.get("/test1", headers={"X-User": "test", "X-User-Role": "owner"})
    assert r.status_code == 200
    assert (await r.get_data()).decode("utf-8") == "test1"

    # /test2

    r = await quart_client.get("/test2")
    assert r.status_code == 403
    assert (await r.get_json())["code"] == 403

    r = await quart_client.get("/test2", headers={"X-User": "test", "X-User-Role": "user"})
    assert r.status_code == 403
    assert (await r.get_json())["code"] == 403

    r = await quart_client.get("/test2", headers={"X-User": "test", "X-User-Role": "owner"})
    assert r.status_code == 200
    assert (await r.get_data()).decode("utf-8") == "test2"

    # /test3

    r = await quart_client.get("/test3")
    assert r.status_code == 200
    assert (await r.get_data()).decode("utf-8") == "test3"

    r = await quart_client.post("/test3")
    assert r.status_code == 403
    assert (await r.get_json())["code"] == 403

    r = await quart_client.get("/test3", headers={"X-User": "test", "X-User-Role": "owner"})
    assert r.status_code == 200
    assert (await r.get_data()).decode("utf-8") == "test3"
