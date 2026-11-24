from copy import deepcopy

from homeassistant.const import STATE_ON, STATE_UNAVAILABLE

from . import setup_integration
from .const import ATX

POWER = "switch.gl_inet_rm1pe_rial_power"
FORCE_OFF = "button.gl_inet_rm1pe_rial_force_off"
RESET = "button.gl_inet_rm1pe_rial_reset"
NO_BOARD = {**ATX, "enabled": False, "power": "off"}


async def _refresh(hass, entry):
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()


async def test_atx_entries_with_board(hass, mock_config_entry, mock_client):
    await setup_integration(hass, mock_config_entry)
    assert hass.states.get(POWER).state == STATE_ON
    assert hass.states.get(FORCE_OFF) is not None
    assert hass.states.get(RESET) is not None


async def test_atx_entities_added_when_board_appears(
    hass, mock_config_entry, mock_client
):
    mock_client.async_get_atx.return_value = deepcopy(NO_BOARD)
    await setup_integration(hass, mock_config_entry)
    assert hass.states.get(POWER) is None
    assert hass.states.get(FORCE_OFF) is None

    mock_client.async_get_atx.return_value = deepcopy(ATX)
    await _refresh(hass, mock_config_entry)
    assert hass.states.get(POWER).state == STATE_ON
    assert hass.states.get(FORCE_OFF) is not None

    await _refresh(hass, mock_config_entry)
    assert len(hass.states.async_entity_ids("switch")) == 2


async def test_atx_entities_unavailable_when_board_removed(
    hass, mock_config_entry, mock_client
):
    await setup_integration(hass, mock_config_entry)

    mock_client.async_get_atx.return_value = deepcopy(NO_BOARD)
    await _refresh(hass, mock_config_entry)
    assert hass.states.get(POWER).state == STATE_UNAVAILABLE
    assert hass.states.get(FORCE_OFF).state == STATE_UNAVAILABLE
