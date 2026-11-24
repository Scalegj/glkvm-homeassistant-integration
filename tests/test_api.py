"""Tests for the KVM API client."""

import pytest

from custom_components.glkvm.api import GlkvmAuthError, GlkvmClient, GlkvmError

URL = "https://kvm.local/api"


@pytest.fixture
def client(hass, aioclient_mock):
    session = aioclient_mock.create_session(hass.loop)
    return GlkvmClient("kvm.local", "admin", "secret", session)


async def test_success_returns_result(client, aioclient_mock):
    aioclient_mock.get(f"{URL}/atx", json={"ok": True, "result": {"power": "on"}})
    assert await client.async_get_atx() == {"power": "on"}


async def test_error_message_from_kvm(client, aioclient_mock):
    aioclient_mock.post(
        f"{URL}/atx/power",
        status=409,
        json={
            "ok": False,
            "result": {"error": "AtxIsBusyError", "error_msg": "ATX is busy"},
        },
    )
    with pytest.raises(GlkvmError, match="ATX is busy"):
        await client.async_set_power("off_hard")


async def test_plain_text_error(client, aioclient_mock):
    aioclient_mock.post(
        f"{URL}/atx/power", status=500, text="500: Internal Server Error"
    )
    with pytest.raises(GlkvmError, match="returned HTTP 500"):
        await client.async_set_power("on")


async def test_invalid_json_on_success(client, aioclient_mock):
    aioclient_mock.get(f"{URL}/atx", text="<html>not json</html>")
    with pytest.raises(GlkvmError, match="invalid JSON"):
        await client.async_get_atx()


async def test_ok_false_on_success(client, aioclient_mock):
    aioclient_mock.get(
        f"{URL}/atx",
        json={"ok": False, "result": {"error": "Weird", "error_msg": "Odd reply"}},
    )
    with pytest.raises(GlkvmError, match="Odd reply"):
        await client.async_get_atx()


@pytest.mark.parametrize("status", [401, 403])
async def test_auth_error(client, aioclient_mock, status):
    aioclient_mock.get(f"{URL}/atx", status=status, json={"ok": False, "result": {}})
    with pytest.raises(GlkvmAuthError):
        await client.async_get_atx()


async def test_get_info_requests_only_system(client, aioclient_mock):
    aioclient_mock.get(f"{URL}/info", json={"ok": True, "result": {"system": {}}})
    await client.async_get_info()
    assert aioclient_mock.mock_calls[0][1].query["fields"] == "system"


async def test_get_edid_list_without_envelope(client, aioclient_mock):
    aioclient_mock.get(
        f"{URL}/upgrade/edid_list",
        json=[
            {
                "key": "E1",
                "label": "Preset/60Hz",
                "content": "00ff",
                "audio": True,
                "hz": 60,
                "is_default": True,
            }
        ],
    )
    assert await client.async_get_edid_list() == {"Preset/60Hz": "00ff"}
