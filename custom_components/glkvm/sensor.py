"""Platform for GLKVM sensor integration."""

from collections.abc import Mapping
import logging

from voluptuous import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import GLKVMEntity

_LOGGER = logging.getLogger(__name__)


class GLKVMBaseSensor(GLKVMEntity):
    """Base class for a GLKVM sensor."""

    def __init__(
        self,
        coordinator,
        unique_id_base,
        sensor_type,
        name,
        unit=None,
        icon=None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, unique_id_base)
        self._attr_unique_id = f"{unique_id_base}_{sensor_type}"
        self._attr_name = name
        self._attr_unit_of_measurement = unit
        self._attr_icon = icon
        self._unique_id_base = unique_id_base
        self._sensor_type = sensor_type

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return the state attributes."""
        return {"ip": self.coordinator.url}

    @property
    def state(self) -> str | int | float | bool | None:
        """Return the state of the sensor."""
        raise NotImplementedError(
            "The state method must be implemented by the subclass."
        )


class GLKVMPowerStateSensor(GLKVMBaseSensor):
    """Sensor for ATX power state."""

    def __init__(self, coordinator, unique_id_base, device_name) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            unique_id_base,
            "atx_power_state",
            f"{device_name} Power State",
            icon="mdi:power",
        )

    @property
    def available(self):
        """Return True if the sensor data is available."""
        atx = self.coordinator.data.get("atx", {}) if self.coordinator.data else {}
        return "leds" in atx or "power" in atx

    @property
    def state(self):
        """Return the power state."""
        atx = self.coordinator.data.get("atx", {}) if self.coordinator.data else {}

        # Check atx.power first (string "on"/"off")
        if "power" in atx:
            power_value = atx["power"]
            return self._parse_power_value(power_value)

        return None

    def _parse_power_value(self, value):
        """Parse various power value formats and return 'on' or 'off'."""
        # Handle string values
        if isinstance(value, str):
            return "on" if value.lower() in ("on", "true", "1", "yes") else "off"
        # Handle boolean and numeric values
        return "on" if value else "off"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attributes = super().extra_state_attributes
        atx = self.coordinator.data.get("atx", {}) if self.coordinator.data else {}
        if atx:
            leds = atx.get("leds", {})
            if leds:
                attributes["power_led"] = leds.get("power")
                attributes["hdd_led"] = leds.get("hdd")
            # Include any other ATX data
            for key, value in atx.items():
                if key != "leds" and not isinstance(value, dict):
                    attributes[key] = value
        return attributes


class GLKVMHDDActivitySensor(GLKVMBaseSensor):
    """Sensor for HDD activity LED state."""

    def __init__(self, coordinator, unique_id_base, device_name) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            unique_id_base,
            "atx_hdd_activity",
            f"{device_name} HDD Activity",
            icon="mdi:harddisk",
        )

    @property
    def available(self):
        """Return True if the sensor data is available."""
        atx = self.coordinator.data.get("atx", {}) if self.coordinator.data else {}
        leds = atx.get("leds", {})
        return "hdd" in leds

    @property
    def state(self):
        """Return the HDD activity state."""
        atx = self.coordinator.data.get("atx", {}) if self.coordinator.data else {}
        leds = atx.get("leds", {})
        if "hdd" in leds:
            return "active" if leds["hdd"] else "idle"
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GLKVM sensors from a config entry."""
    _LOGGER.debug("Setting up GLKVM sensors from config entry")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Get unique ID base
    serial = config_entry.data.get("serial", config_entry.entry_id)
    unique_id_base = f"{config_entry.entry_id}_{serial}"

    # Get device name
    device_name = config_entry.title or "GLKVM"

    sensors = [
        GLKVMPowerStateSensor(coordinator, unique_id_base, device_name),
        GLKVMHDDActivitySensor(coordinator, unique_id_base, device_name),
    ]

    async_add_entities(sensors, True)
    _LOGGER.debug("%d GLKVM sensors added to Home Assistant", len(sensors))


