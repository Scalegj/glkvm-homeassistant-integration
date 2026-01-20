"""GLKVM entity base class."""

import logging

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import GLKVMDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class GLKVMEntity(CoordinatorEntity):
    """Base class for a GLKVM entity."""

    DEVICE_INFO: DeviceInfo | None = None
    coordinator: GLKVMDataUpdateCoordinator

    def __init__(
        self, coordinator: GLKVMDataUpdateCoordinator, unique_id_base: str
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._attr_device_info = self.DEVICE_INFO
        self._attr_unique_id_base = unique_id_base


