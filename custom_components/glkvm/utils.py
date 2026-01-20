"""Utility functions for the GL.iNet KVM integration."""

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.translation import async_get_translations

from .const import (
    CONF_HOST,
    CONF_PASSWORD,
    DEFAULT_HOST,
    DEFAULT_PASSWORD,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def format_url(input_url):
    """Ensure the URL is properly formatted."""
    if not input_url.startswith("http"):
        input_url = f"https://{input_url}"
    return input_url.rstrip("/")


def create_data_schema(user_input):
    """Create the data schema for the form."""
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=user_input.get(CONF_HOST, DEFAULT_HOST)): str,
            vol.Required(
                CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, DEFAULT_PASSWORD)
            ): str,
        }
    )


def update_existing_entry(hass: HomeAssistant | None, existing_entry, user_input):
    """Update an existing config entry."""
    updated_data = existing_entry.data.copy()
    updated_data.update(user_input)
    if "serial" not in updated_data:
        updated_data["serial"] = existing_entry.data.get("serial")
    if hass is not None:
        hass.config_entries.async_update_entry(existing_entry, data=updated_data)


def find_existing_entry(flow_handler, serial) -> config_entries.ConfigEntry | None:
    """Find an existing entry with the same serial number."""
    if not serial:
        return None
    existing_entries = flow_handler._async_current_entries()
    for entry in existing_entries:
        entry_serial = entry.data.get("serial")
        _LOGGER.debug("Checking existing %s against %s", entry_serial, serial)
        if entry_serial and entry_serial.lower() == serial.lower():
            return entry
    _LOGGER.debug("No existing entry found for %s, configuring", serial)
    return None


async def get_translations(hass: HomeAssistant, language, domain):
    """Get translations for the given language and domain."""
    if hass is None:
        raise ValueError("HomeAssistant instance cannot be None")
    translations = await async_get_translations(hass, language, "config")

    def translate(key, default):
        return translations.get(f"component.{domain}.{key}", default)

    return translate


def get_unique_id_base(config_entry, coordinator):
    """Generate the unique_id_base for the sensors."""
    serial = None
    if coordinator.data:
        hw = coordinator.data.get("hw", {})
        platform = hw.get("platform", {})
        serial = platform.get("serial")
    if not serial:
        serial = config_entry.data.get("serial", config_entry.entry_id)
    return f"{config_entry.entry_id}_{serial}"


def get_nested_value(data, keys, default=None):
    """Safely get a nested value from a dictionary."""
    if not data:
        return default
    for key in keys:
        if not isinstance(data, dict):
            return default
        data = data.get(key, {})
    return data if data else default


def bytes_to_mb(bytes_value):
    """Convert bytes to megabytes."""
    if bytes_value is None:
        return None
    return bytes_value / (1024 * 1024)
