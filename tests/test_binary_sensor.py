"""Tests for the USB connected sensor."""

from homeassistant.const import STATE_ON, STATE_UNAVAILABLE

from custom_components.glkvm.api import GlkvmError

from . import setup_integration

USB = "binary_sensor.gl_inet_rm1pe_rial_usb_connected"


async def test_usb_connected(hass, mock_config_entry, mock_client):
    await setup_integration(hass, mock_config_entry)
    assert hass.states.get(USB).state == STATE_ON


async def test_usb_unavailable_without_hid(hass, mock_config_entry, mock_client):
    mock_client.async_get_hid.side_effect = GlkvmError("no hid")
    await setup_integration(hass, mock_config_entry)
    assert hass.states.get(USB).state == STATE_UNAVAILABLE
