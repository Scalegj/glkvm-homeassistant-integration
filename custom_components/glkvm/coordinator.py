import asyncio
import logging
from datetime import timedelta

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GlkvmAuthError, GlkvmError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
AUTH_FAILURES_BEFORE_REAUTH = 3


class GlkvmCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, client):
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.client = client
        self._auth_failures = 0
        self.version = None
        self.edid_presets = {}

    async def _async_setup(self):
        try:
            self.version = await self.client.async_get_version()
        except GlkvmError as err:
            _LOGGER.debug("Could not read firmware version: %s", err)
        try:
            self.edid_presets = await self.client.async_get_edid_list()
        except (GlkvmError, KeyError, TypeError) as err:
            _LOGGER.debug("Could not read EDID list: %s", err)

    async def _async_optional(self, name, fetch):
        try:
            return await fetch()
        except GlkvmAuthError:
            raise
        except (GlkvmError, KeyError, TypeError) as err:
            _LOGGER.debug("Could not read %s: %s", name, err)
            return None

    async def _async_update_data(self):
        try:
            atx, info, hid, msd, edid = await asyncio.gather(
                self.client.async_get_atx(),
                self.client.async_get_info(),
                self._async_optional("HID", self.client.async_get_hid),
                self._async_optional("MSD", self.client.async_get_msd),
                self._async_optional("EDID", self.client.async_get_edid),
            )
        except GlkvmAuthError as err:
            self._auth_failures += 1
            if self.data is None or self._auth_failures >= AUTH_FAILURES_BEFORE_REAUTH:
                raise ConfigEntryAuthFailed(str(err)) from err
            raise UpdateFailed(
                f"{err} (attempt {self._auth_failures} of {AUTH_FAILURES_BEFORE_REAUTH})"
            ) from err
        except GlkvmError as err:
            raise UpdateFailed(str(err)) from err
        self._auth_failures = 0
        return {"atx": atx, "info": info, "hid": hid, "msd": msd, "edid": edid}
