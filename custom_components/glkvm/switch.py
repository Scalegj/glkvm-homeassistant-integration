import time

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError

from .api import GlkvmError
from .entity import GlkvmAtxEntity, GlkvmEntity, async_add_atx_entities

PARALLEL_UPDATES = 1
PENDING_TIMEOUT = 120


def _create_atx_switches(coordinator):
    return [GlkvmPowerSwitch(coordinator)]


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities([GlkvmJigglerSwitch(coordinator)])
    async_add_atx_entities(entry, async_add_entities, _create_atx_switches)


class GlkvmPowerSwitch(GlkvmAtxEntity, SwitchEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, "power")
        self._pending = None

    @property
    def _actual_is_on(self):
        return self.coordinator.data["atx"]["power"] == "on"

    @property
    def is_on(self):
        if self._pending is not None:
            return self._pending[0]
        return self._actual_is_on

    @callback
    def _handle_coordinator_update(self):
        if self._pending is not None:
            target, deadline = self._pending
            if self._actual_is_on == target or time.monotonic() > deadline:
                self._pending = None
        super()._handle_coordinator_update()

    async def _async_switch(self, action, target):
        await self._async_set_power(action)
        self._pending = (target, time.monotonic() + PENDING_TIMEOUT)
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs):
        await self._async_switch("on", True)

    async def async_turn_off(self, **kwargs):
        await self._async_switch("off", False)


class GlkvmJigglerSwitch(GlkvmEntity, SwitchEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator):
        super().__init__(coordinator, "jiggler")

    @property
    def available(self):
        hid = self.coordinator.data["hid"]
        return bool(
            super().available
            and hid is not None
            and hid.get("jiggler", {}).get("enabled", False)
        )

    @property
    def is_on(self):
        return self.coordinator.data["hid"]["jiggler"]["active"]

    async def _async_set(self, active):
        try:
            await self.coordinator.client.async_set_jiggler(active)
        except GlkvmError as err:
            raise HomeAssistantError(f"Setting jiggler failed: {err}") from err
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs):
        await self._async_set(True)

    async def async_turn_off(self, **kwargs):
        await self._async_set(False)
