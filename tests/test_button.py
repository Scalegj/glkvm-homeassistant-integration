"""Tests for the ATX buttons."""

import pytest
from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN
from homeassistant.components.button import SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.exceptions import HomeAssistantError

from custom_components.glkvm.api import GlkvmError

from . import setup_integration


async def _press(hass, entity_id):
    await hass.services.async_call(
        BUTTON_DOMAIN, SERVICE_PRESS, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )


@pytest.mark.parametrize(
    ("entity_id", "action"),
    [
        ("button.gl_inet_rm1pe_rial_force_off", "power_long"),
        ("button.gl_inet_rm1pe_rial_reset", "reset"),
    ],
)
async def test_press(hass, mock_config_entry, mock_client, entity_id, action):
    await setup_integration(hass, mock_config_entry)
    await _press(hass, entity_id)
    mock_client.async_click.assert_awaited_once_with(action)


async def test_press_error(hass, mock_config_entry, mock_client):
    await setup_integration(hass, mock_config_entry)
    mock_client.async_click.side_effect = GlkvmError("ATX is busy")
    with pytest.raises(HomeAssistantError, match="ATX is busy"):
        await _press(hass, "button.gl_inet_rm1pe_rial_force_off")
