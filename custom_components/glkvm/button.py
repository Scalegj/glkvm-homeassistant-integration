"""Button platform for GL.iNet KVM ATX controls."""

import functools
import logging

from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    API_ATX_POWER,
    ATX_ACTION_POWER_OFF,
    ATX_ACTION_RESET,
    DOMAIN,
)
from .entity import GLKVMEntity

_LOGGER = logging.getLogger(__name__)


class GLKVMButtonEntity(GLKVMEntity, ButtonEntity):
    """Base class for GLKVM button entities."""

    def __init__(
        self,
        coordinator,
        unique_id_base: str,
        button_type: str,
        name: str,
        action: str,
        icon: str,
        device_class: ButtonDeviceClass | None = None,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, unique_id_base)
        self._attr_unique_id = f"{unique_id_base}_{button_type}"
        self._attr_name = name
        self._attr_icon = icon
        self._action = action
        if device_class:
            self._attr_device_class = device_class

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._send_atx_command(self._action)

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


class GLKVMPowerButton(GLKVMButtonEntity):
    """Button to press the power button on the connected system."""

    def __init__(self, coordinator, unique_id_base: str, device_name: str) -> None:
        """Initialize the power button."""
        super().__init__(
            coordinator,
            unique_id_base,
            "power_button",
            f"{device_name} Power Button",
            ATX_ACTION_POWER_OFF,
            "mdi:power",
        )


class GLKVMResetButton(GLKVMButtonEntity):
    """Button to press the reset button on the connected system."""

    def __init__(self, coordinator, unique_id_base: str, device_name: str) -> None:
        """Initialize the reset button."""
        super().__init__(
            coordinator,
            unique_id_base,
            "reset_button",
            f"{device_name} Reset Button",
            ATX_ACTION_RESET,
            "mdi:restart",
            ButtonDeviceClass.RESTART,
        )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GLKVM buttons from a config entry."""
    _LOGGER.debug("Setting up GLKVM ATX buttons from config entry")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    serial = config_entry.data.get("serial", config_entry.entry_id)
    unique_id_base = f"{config_entry.entry_id}_{serial}"

    device_name = config_entry.title or "GLKVM"

    buttons = [
        GLKVMPowerButton(coordinator, unique_id_base, device_name),
        GLKVMResetButton(coordinator, unique_id_base, device_name),
    ]

    async_add_entities(buttons, True)
    _LOGGER.debug("%d GLKVM ATX buttons added to Home Assistant", len(buttons))
