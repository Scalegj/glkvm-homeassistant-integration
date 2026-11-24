"""Tests for the select entities."""

from copy import deepcopy

import pytest
from homeassistant.components.select import ATTR_OPTION, SERVICE_SELECT_OPTION
from homeassistant.components.select import DOMAIN as SELECT_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNAVAILABLE
from homeassistant.exceptions import HomeAssistantError

from custom_components.glkvm.select import _format_edid

from . import setup_integration
from .const import EDID_B, MSD

EDID = "select.gl_inet_rm1pe_rial_edid"
MEDIA = "select.gl_inet_rm1pe_rial_virtual_media"


async def _select(hass, option):
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: EDID, ATTR_OPTION: option},
        blocking=True,
    )


async def test_edid_shows_matching_preset(hass, mock_config_entry, mock_client):
    await setup_integration(hass, mock_config_entry)
    state = hass.states.get(EDID)
    assert state.state == "Preset A/60Hz"
    assert state.attributes["options"] == ["Preset A/60Hz", "Preset B/60Hz", "Custom"]


async def test_edid_matches_padded_and_uppercase(hass, mock_config_entry, mock_client):
    mock_client.async_get_edid.return_value = (EDID_B + "00" * 128).upper()
    await setup_integration(hass, mock_config_entry)
    assert hass.states.get(EDID).state == "Preset B/60Hz"


async def test_edid_unknown_is_custom(hass, mock_config_entry, mock_client):
    mock_client.async_get_edid.return_value = "00ffffffffffff00" + "ff" * 240
    await setup_integration(hass, mock_config_entry)
    assert hass.states.get(EDID).state == "Custom"


async def test_edid_select_sends_formatted_content(
    hass, mock_config_entry, mock_client
):
    await setup_integration(hass, mock_config_entry)
    await _select(hass, "Preset B/60Hz")
    mock_client.async_set_edid.assert_awaited_once_with(_format_edid(EDID_B))


async def test_edid_custom_cannot_be_selected(hass, mock_config_entry, mock_client):
    await setup_integration(hass, mock_config_entry)
    with pytest.raises(HomeAssistantError):
        await _select(hass, "Custom")
    mock_client.async_set_edid.assert_not_awaited()


async def test_edid_unavailable_without_list(hass, mock_config_entry, mock_client):
    mock_client.async_get_edid_list.return_value = {}
    await setup_integration(hass, mock_config_entry)
    assert hass.states.get(EDID).state == STATE_UNAVAILABLE


def test_format_edid():
    assert _format_edid("00ff" * 9) == (
        "00 ff 00 ff 00 ff 00 ff 00 ff 00 ff 00 ff 00 ff\n00 ff"
    )


async def test_media_options_skip_incomplete(hass, mock_config_entry, mock_client):
    await setup_integration(hass, mock_config_entry)
    state = hass.states.get(MEDIA)
    assert state.state == "None"
    assert state.attributes["options"] == ["None", "debian.iso"]


async def test_media_mount(hass, mock_config_entry, mock_client):
    await setup_integration(hass, mock_config_entry)
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: MEDIA, ATTR_OPTION: "debian.iso"},
        blocking=True,
    )
    mock_client.async_set_msd_connected.assert_awaited_once_with(True)
    mock_client.async_set_msd_image.assert_awaited_once_with("debian.iso")
    assert hass.states.get(MEDIA).state == "debian.iso"


async def test_media_unmount(hass, mock_config_entry, mock_client):
    msd = deepcopy(MSD)
    msd["drive"] = {"connected": True, "image": {"name": "debian.iso"}}
    mock_client.async_get_msd.return_value = msd
    await setup_integration(hass, mock_config_entry)
    assert hass.states.get(MEDIA).state == "debian.iso"

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: MEDIA, ATTR_OPTION: "None"},
        blocking=True,
    )
    mock_client.async_set_msd_connected.assert_awaited_once_with(False)
    mock_client.async_set_msd_image.assert_not_awaited()


async def test_media_storage_missing(hass, mock_config_entry, mock_client):
    mock_client.async_get_msd.return_value = {
        **deepcopy(MSD),
        "online": False,
        "storage": None,
    }
    await setup_integration(hass, mock_config_entry)
    assert hass.states.get(MEDIA).state == STATE_UNAVAILABLE
