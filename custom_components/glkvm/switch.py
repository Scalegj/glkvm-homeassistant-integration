"""Switch platform for GL.iNet KVM power control."""

import functools
import logging

from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    API_ATX_POWER,
    ATX_ACTION_POWER_ON,
    ATX_ACTION_POWER_OFF,
    DOMAIN,
)
from .entity import GLKVMEntity

_LOGGER = logging.getLogger(__name__)


class GLKVMPowerSwitch(GLKVMEntity, SwitchEntity):
    """Switch to control computer power state."""

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(
        self,
        coordinator,
        unique_id_base: str,
        device_name: str,
    ) -> None:
        """Initialize the power switch."""
        super().__init__(coordinator, unique_id_base)
        self._attr_unique_id = f"{unique_id_base}_power_switch"
        self._attr_name = f"{device_name} Power"
        self._attr_icon = "mdi:power"

    @property
    def available(self) -> bool:
        """Return True if the switch data is available."""
        atx = self.coordinator.data.get("atx", {}) if self.coordinator.data else {}
        return "power" in atx

    @property
    def is_on(self) -> bool | None:
        """Return True if the system is powered on."""
        atx = self.coordinator.data.get("atx", {}) if self.coordinator.data else {}
        if "power" not in atx:
            return None
        power_value = atx["power"]
        return self._parse_power_value(power_value)

    def _parse_power_value(self, value) -> bool:
        """Parse various power value formats and return boolean."""
        if isinstance(value, str):
            return value.lower() in ("on", "true", "1", "yes")
        return bool(value)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on the system (only if currently off)."""
        if not self.is_on:
            _LOGGER.debug("System is off, sending power on command")
            await self._send_atx_command(ATX_ACTION_POWER_ON)
        else:
            _LOGGER.debug("System is already on, skipping power on command")

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off the system (graceful shutdown)."""
        if self.is_on:
            _LOGGER.debug("System is on, sending power off command")
            await self._send_atx_command(ATX_ACTION_POWER_OFF)
        else:
            _LOGGER.debug("System is already off, skipping power off command")

    async def _send_atx_command(self, action: str) -> None:
        """Send ATX power command to the device."""
        try:
            url = f"{self.coordinator.url}{API_ATX_POWER}"
            _LOGGER.debug("Sending ATX command: %s to %s", action, url)

            response = await self.coordinator.hass.async_add_executor_job(
                functools.partial(
                    self.coordinator.session.post,
                    url,
                    params={"action": action},
                    auth=self.coordinator.auth,
                    timeout=10,
                )
            )

            if response.status_code == 200:
                _LOGGER.info("ATX command '%s' sent successfully", action)
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error(
                    "ATX command '%s' failed with status %s: %s",
                    action,
                    response.status_code,
                    response.text,
                )

        except Exception as err:
            _LOGGER.error("Error sending ATX command '%s': %s", action, err)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GLKVM switches from a config entry."""
    _LOGGER.debug("Setting up GLKVM power switch from config entry")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    serial = config_entry.data.get("serial", config_entry.entry_id)
    unique_id_base = f"{config_entry.entry_id}_{serial}"

    device_name = config_entry.title or "GLKVM"

    switches = [
        GLKVMPowerSwitch(coordinator, unique_id_base, device_name),
    ]

    async_add_entities(switches, True)
    _LOGGER.debug("%d GLKVM switch(es) added to Home Assistant", len(switches))
