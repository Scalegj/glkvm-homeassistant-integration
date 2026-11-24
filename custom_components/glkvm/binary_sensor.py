from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory

from .entity import GlkvmEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities([GlkvmUsbConnectedSensor(coordinator)])


class GlkvmUsbConnectedSensor(GlkvmEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator):
        super().__init__(coordinator, "usb_connected")

    @property
    def available(self):
        return super().available and self.coordinator.data["hid"] is not None

    @property
    def is_on(self):
        return self.coordinator.data["hid"]["connected"]
