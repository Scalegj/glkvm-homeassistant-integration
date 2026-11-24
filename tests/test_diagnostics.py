"""Tests for the diagnostics download."""

from homeassistant.components.diagnostics import REDACTED

from custom_components.glkvm.diagnostics import async_get_config_entry_diagnostics

from . import setup_integration
from .const import SERIAL, USER_INPUT


async def test_diagnostics_are_redacted(hass, mock_config_entry, mock_client):
    await setup_integration(hass, mock_config_entry)
    diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert diagnostics["entry"]["password"] == REDACTED
    assert diagnostics["entry"]["host"] == REDACTED
    assert diagnostics["data"]["info"]["system"]["platform"]["serial"] == REDACTED

    dump = str(diagnostics)
    assert USER_INPUT["password"] not in dump
    assert USER_INPUT["host"] not in dump
    assert SERIAL not in dump
