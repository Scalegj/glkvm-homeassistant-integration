from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    Platform,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GlkvmClient
from .const import CONF_TOTP_SECRET
from .coordinator import GlkvmCoordinator

PLATFORMS = [Platform.SWITCH, Platform.BUTTON, Platform.BINARY_SENSOR, Platform.SELECT]


async def async_setup_entry(hass, entry):
    client = GlkvmClient(
        entry.data[CONF_HOST],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        async_get_clientsession(
            hass, verify_ssl=entry.data.get(CONF_VERIFY_SSL, False)
        ),
        entry.data.get(CONF_TOTP_SECRET),
    )

    coordinator = GlkvmCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
