"""Manages fetching data from the GLKVM API."""

import asyncio
from datetime import timedelta
import functools
import logging
import os

import requests
from requests.auth import HTTPBasicAuth

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .cert_handler import create_session_with_cert
from .const import DOMAIN, API_INFO, API_ATX

_LOGGER = logging.getLogger(__name__)


def format_url(input_url):
    """Ensure the URL is properly formatted."""
    if not input_url.startswith("http"):
        input_url = f"https://{input_url}"
    return input_url.rstrip("/")


class AuthenticationFailed(Exception):
    """Custom exception for authentication failures."""


class GLKVMDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the GLKVM API."""

    url: str = ""

    def __init__(
        self, hass: HomeAssistant, url: str, username: str, password: str, cert: str
    ) -> None:
        """Initialize."""
        self.hass = hass
        self.url = format_url(url)
        self.username = username
        self.password = password
        self.cert = cert
        self.session = None
        self.cert_file_path = None
        self.auth = HTTPBasicAuth(self.username, self.password)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )

    async def async_setup(self) -> None:
        """Async setup method to create session and handle async code."""
        await self._create_session()

    async def _create_session(self):
        """Create the session with the certificate."""
        self.auth = HTTPBasicAuth(self.username, self.password)
        session_with_cert = await create_session_with_cert(self.cert)
        self.session, self.cert_file_path = session_with_cert
        if not self.session:
            _LOGGER.error("Failed to create session with certificate")
        else:
            _LOGGER.debug("Session created successfully")

    async def _async_update_data(self):
        """Fetch data from GLKVM API."""
        max_retries = 5
        backoff_time = 2

        retries = 0
        while retries < max_retries:
            try:
                _LOGGER.debug("Fetching GLKVM Info at %s", self.url)

                if not self.session:
                    await self._create_session()

                # Fetch device info
                response = await self.hass.async_add_executor_job(
                    functools.partial(
                        self.session.get,
                        f"{self.url}{API_INFO}",
                        auth=self.auth,
                        timeout=10,
                    )
                )

                if response.status_code == 401:
                    raise AuthenticationFailed("Invalid username or password")

                response.raise_for_status()
                data_info = response.json().get("result", {})

                # Fetch ATX status
                try:
                    response_atx = await self.hass.async_add_executor_job(
                        functools.partial(
                            self.session.get,
                            f"{self.url}{API_ATX}",
                            auth=self.auth,
                            timeout=10,
                        )
                    )
                    if response_atx.status_code == 200:
                        data_atx = response_atx.json().get("result", {})
                        data_info["atx"] = data_atx
                        _LOGGER.debug("ATX status: %s", data_atx)
                    else:
                        _LOGGER.debug("ATX endpoint not available (status %s)", response_atx.status_code)
                        data_info["atx"] = {}
                except Exception as atx_err:
                    _LOGGER.debug("Could not fetch ATX status: %s", atx_err)
                    data_info["atx"] = {}

                _LOGGER.debug("Received GLKVM Info from %s", self.url)
                return data_info

            except AuthenticationFailed as auth_err:
                _LOGGER.error("Authentication failed: %s", auth_err)
                raise UpdateFailed(f"Authentication failed: {auth_err}") from auth_err
            except requests.exceptions.RequestException as err:
                retries += 1
                if retries < max_retries:
                    _LOGGER.warning(
                        "Error communicating with API: %s. Retrying in %s seconds",
                        err,
                        backoff_time,
                    )
                    await asyncio.sleep(backoff_time)
                    backoff_time *= 2
                else:
                    _LOGGER.error(
                        "Max retries exceeded. Error communicating with API: %s", err
                    )
                    raise UpdateFailed(f"Error communicating with API: {err}") from err
            except (ValueError, KeyError) as e:
                _LOGGER.error("Data processing error: %s", e)
                raise UpdateFailed(f"Data processing error: {e}") from e
            finally:
                if self.cert_file_path and os.path.exists(self.cert_file_path):
                    os.remove(self.cert_file_path)
        return None


