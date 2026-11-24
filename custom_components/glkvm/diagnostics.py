from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST, CONF_PASSWORD

from .const import CONF_TOTP_SECRET

TO_REDACT = {CONF_HOST, CONF_PASSWORD, CONF_TOTP_SECRET, "serial", "uuid"}


async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = entry.runtime_data
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "version": async_redact_data(coordinator.version or {}, TO_REDACT),
        "data": async_redact_data(coordinator.data, TO_REDACT),
    }
