from homeassistant.const import CONF_HOST
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import GlkvmError
from .const import DOMAIN


class GlkvmEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key):
        super().__init__(coordinator)
        system = coordinator.data["info"]["system"]
        platform = system.get("platform", {})
        serial = platform["serial"]
        self._attr_unique_id = f"{serial}_{key}"
        self._attr_translation_key = key
        version = coordinator.version or {}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            manufacturer="GL.iNet",
            model=version.get("model") or platform.get("model"),
            name=coordinator.config_entry.title,
            serial_number=serial,
            sw_version=version.get("version") or system.get("kvmd", {}).get("version"),
            configuration_url=f"https://{coordinator.config_entry.data[CONF_HOST]}",
        )


class GlkvmAtxEntity(GlkvmEntity):
    """Base for entities that need the ATX power control board."""

    @property
    def available(self):
        return super().available and self.coordinator.data["atx"].get("enabled", False)

    async def _async_set_power(self, action):
        try:
            await self.coordinator.client.async_set_power(action)
        except GlkvmError as err:
            raise HomeAssistantError(f"Power action '{action}' failed: {err}") from err

    async def _async_click(self, button):
        try:
            await self.coordinator.client.async_click(button)
        except GlkvmError as err:
            raise HomeAssistantError(f"ATX button '{button}' failed: {err}") from err


@callback
def async_add_atx_entities(entry, async_add_entities, create_entities):
    """Add ATX entities once KVM reports an ATX board"""
    coordinator = entry.runtime_data
    added = False

    @callback
    def _async_check():
        nonlocal added
        if added or not coordinator.data["atx"].get("enabled"):
            return
        added = True
        async_add_entities(create_entities(coordinator))

    _async_check()
    entry.async_on_unload(coordinator.async_add_listener(_async_check))
