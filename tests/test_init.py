from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState

from custom_components.glkvm.api import GlkvmAuthError, GlkvmError


async def test_setup_and_unload(hass, mock_config_entry, mock_client):
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_cannot_connect(hass, mock_config_entry, mock_client):
    mock_client.async_get_atx.side_effect = GlkvmError("boom")
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_setup_auth_failed_starts_reauth(hass, mock_config_entry, mock_client):
    mock_client.async_get_atx.side_effect = GlkvmAuthError("bad password")
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR

    flows = hass.config_entries.flow.async_progress()
    assert [flow["context"]["source"] for flow in flows] == [SOURCE_REAUTH]


async def test_setup_survives_optional_failures(hass, mock_config_entry, mock_client):
    mock_client.async_get_hid.side_effect = GlkvmError("no hid")
    mock_client.async_get_edid.side_effect = KeyError("edid")
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED
