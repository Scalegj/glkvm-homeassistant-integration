"""Tests for the switch entities"""

from copy import deepcopy

import pytest
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.exceptions import HomeAssistantError

from custom_components.glkvm.api import GlkvmError

from . import setup_integration
from .const import ATX, HID

POWER = "switch.gl_inet_rm1pe_rial_power"
JIGGLER = "switch.gl_inet_rm1pe_rial_mouse_jiggler"


async def _call(hass, service, entity_id):
    await hass.services.async_call(
        SWITCH_DOMAIN, service, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )


async def test_power_off_is_optimistic(hass, mock_config_entry, mock_client):
    await setup_integration(hass, mock_config_entry)
    assert hass.states.get(POWER).state == STATE_ON

    await _call(hass, SERVICE_TURN_OFF, POWER)
    mock_client.async_set_power.assert_awaited_once_with("off")
    assert hass.states.get(POWER).state == STATE_OFF

    mock_client.async_get_atx.return_value = {**deepcopy(ATX), "power": "off"}
    await mock_config_entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(POWER).state == STATE_OFF


async def test_power_on(hass, mock_config_entry, mock_client):
    mock_client.async_get_atx.return_value = {**deepcopy(ATX), "power": "off"}
    await setup_integration(hass, mock_config_entry)

    await _call(hass, SERVICE_TURN_ON, POWER)
    mock_client.async_set_power.assert_awaited_once_with("on")
    assert hass.states.get(POWER).state == STATE_ON


async def test_power_error(hass, mock_config_entry, mock_client):
    await setup_integration(hass, mock_config_entry)
    mock_client.async_set_power.side_effect = GlkvmError("ATX is busy")

    with pytest.raises(HomeAssistantError, match="ATX is busy"):
        await _call(hass, SERVICE_TURN_OFF, POWER)
    assert hass.states.get(POWER).state == STATE_ON


async def test_jiggler(hass, mock_config_entry, mock_client):
    await setup_integration(hass, mock_config_entry)
    assert hass.states.get(JIGGLER).state == STATE_OFF

    await _call(hass, SERVICE_TURN_ON, JIGGLER)
    mock_client.async_set_jiggler.assert_awaited_once_with(True)


async def test_jiggler_unavailable_when_disabled(hass, mock_config_entry, mock_client):
    hid = deepcopy(HID)
    hid["jiggler"]["enabled"] = False
    mock_client.async_get_hid.return_value = hid
    await setup_integration(hass, mock_config_entry)
    assert hass.states.get(JIGGLER).state == STATE_UNAVAILABLE
