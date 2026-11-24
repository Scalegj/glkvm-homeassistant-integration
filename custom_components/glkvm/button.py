from homeassistant.components.button import ButtonDeviceClass, ButtonEntity

from .entity import GlkvmAtxEntity, async_add_atx_entities

PARALLEL_UPDATES = 1


def _create_atx_buttons(coordinator):
    return [
        GlkvmAtxButton(coordinator, "power_long", "force_off"),
        GlkvmAtxButton(coordinator, "reset", "reset", ButtonDeviceClass.RESTART),
    ]


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_atx_entities(entry, async_add_entities, _create_atx_buttons)


class GlkvmAtxButton(GlkvmAtxEntity, ButtonEntity):
    def __init__(self, coordinator, action, key, device_class=None):
        super().__init__(coordinator, key)
        self._action = action
        self._attr_device_class = device_class

    async def async_press(self):
        await self._async_click(self._action)
        await self.coordinator.async_request_refresh()
