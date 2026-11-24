import time

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError

from .api import GlkvmError
from .entity import GlkvmEntity

PARALLEL_UPDATES = 1
NO_IMAGE = "None"
CUSTOM_EDID = "Custom"
PENDING_TIMEOUT = 35


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities([GlkvmMsdImageSelect(coordinator), GlkvmEdidSelect(coordinator)])


class GlkvmMsdImageSelect(GlkvmEntity, SelectEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, "msd_image")
        self._pending = None

    @property
    def _msd(self):
        return self.coordinator.data["msd"]

    @property
    def available(self):
        return bool(
            super().available
            and self._msd is not None
            and self._msd.get("enabled")
            and self._msd.get("online")
        )

    @property
    def options(self):
        storage = (self._msd or {}).get("storage") or {}
        images = storage.get("images") or {}
        return [
            NO_IMAGE,
            *sorted(name for name, image in images.items() if image.get("complete")),
        ]

    @property
    def _actual_option(self):
        drive = self._msd["drive"]
        if (
            drive["connected"]
            and drive["image"]
            and drive["image"]["name"] in self.options
        ):
            return drive["image"]["name"]
        return NO_IMAGE

    @property
    def current_option(self):
        if self._pending is not None:
            return self._pending[0]
        return self._actual_option

    @callback
    def _handle_coordinator_update(self):
        if self._pending is not None:
            target, deadline = self._pending
            if time.monotonic() > deadline or (
                self._msd is not None and self._actual_option == target
            ):
                self._pending = None
        super()._handle_coordinator_update()

    async def async_select_option(self, option):
        if option == self.current_option:
            return
        client = self.coordinator.client
        try:
            if self._msd["drive"]["connected"]:
                await client.async_set_msd_connected(False)
            if option != NO_IMAGE:
                await client.async_set_msd_image(option)
                await client.async_set_msd_connected(True)
        except GlkvmError as err:
            self._pending = None
            await self.coordinator.async_request_refresh()
            raise HomeAssistantError(f"Changing virtual media failed: {err}") from err
        self._pending = (option, time.monotonic() + PENDING_TIMEOUT)
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()


def _normalize_edid(edid):
    """Ignore spacing, letter case and trailing zeros"""
    return "".join(edid.split()).lower().rstrip("0")


def _format_edid(edid):
    """Write hex as 16 space-separated bytes per line"""
    hex_digits = "".join(edid.split())
    pairs = [hex_digits[i : i + 2] for i in range(0, len(hex_digits), 2)]
    return "\n".join(" ".join(pairs[i : i + 16]) for i in range(0, len(pairs), 16))


class GlkvmEdidSelect(GlkvmEntity, SelectEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator):
        super().__init__(coordinator, "edid")

    @property
    def _presets(self):
        return self.coordinator.edid_presets

    @property
    def available(self):
        return bool(
            super().available
            and self.coordinator.data["edid"] is not None
            and self._presets
        )

    @property
    def options(self):
        return [*self._presets, CUSTOM_EDID]

    @property
    def current_option(self):
        current = _normalize_edid(self.coordinator.data["edid"])
        for name, edid in self._presets.items():
            if _normalize_edid(edid) == current:
                return name
        return CUSTOM_EDID

    async def async_select_option(self, option):
        if option == self.current_option:
            return
        if option == CUSTOM_EDID:
            raise HomeAssistantError("Set a custom EDID from the GLKVM web UI")
        try:
            await self.coordinator.client.async_set_edid(
                _format_edid(self._presets[option])
            )
        except GlkvmError as err:
            raise HomeAssistantError(f"Changing EDID failed: {err}") from err
        await self.coordinator.async_request_refresh()
