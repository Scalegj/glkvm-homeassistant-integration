"""Config flow for GL.iNet KVM integration."""

import logging
import re

from homeassistant import config_entries
from homeassistant.core import callback

from .cert_handler import fetch_serialized_cert, is_glkvm_device
from .const import (
    CONF_CERTIFICATE,
    CONF_HOST,
    CONF_MODEL,
    CONF_PASSWORD,
    CONF_SERIAL,
    DEFAULT_HOST,
    DEFAULT_PASSWORD,
    DEFAULT_USERNAME,
    DOMAIN,
    MANUFACTURER,
)
from .options_flow import GLKVMOptionsFlowHandler
from .utils import (
    create_data_schema,
    find_existing_entry,
    get_translations,
    update_existing_entry,
)

_LOGGER = logging.getLogger(__name__)


async def perform_device_setup(flow_handler, user_input):
    """Handle initial configuration setup for the configuration."""
    errors = {}
    host = user_input[CONF_HOST]
    username = DEFAULT_USERNAME
    password = user_input[CONF_PASSWORD]

    _LOGGER.debug(
        "Entered perform_device_setup with URL %s, username %s", host, username
    )

    try:
        serialized_cert = await fetch_serialized_cert(flow_handler.hass, host)
        if not serialized_cert:
            errors["base"] = "cannot_fetch_cert"
            return None, errors

        user_input[CONF_CERTIFICATE] = serialized_cert

        response = await is_glkvm_device(
            flow_handler.hass, host, username, password, serialized_cert
        )

        if response.error:
            errors["base"] = response.error
            return None, errors

        if not response.success:
            _LOGGER.error(
                "Error detected while connecting to KVM device. Error: %s",
                response.error,
            )
            errors["base"] = "cannot_connect"
            return None, errors

        _LOGGER.debug(
            "KVM device detected: Model=%s, Serial=%s, Name=%s",
            response.model,
            response.serial,
            response.name,
        )

        existing_entry = find_existing_entry(flow_handler, response.serial)
        if existing_entry:
            update_existing_entry(
                flow_handler.hass,
                existing_entry,
                {CONF_HOST: host, CONF_PASSWORD: password},
            )
            return flow_handler.async_abort(reason="already_configured"), None

        device_name = response.name
        if device_name == "localhost.localdomain" or not device_name:
            device_name = MANUFACTURER

        user_input[CONF_MODEL] = response.model.lower() if response.model else "unknown"
        user_input[CONF_SERIAL] = response.serial
        await flow_handler.async_set_unique_id(response.serial)

        config_flow_result = flow_handler.async_create_entry(
            title=device_name if device_name else "GL.iNet KVM", data=user_input
        )
        return config_flow_result, None

    except (ConnectionError, TimeoutError, ValueError) as e:
        _LOGGER.error("Unexpected error during device setup: %s", e)
        errors["base"] = "unknown_error"

    return None, errors


class GLKVMConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GL.iNet KVM."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self) -> None:
        """Initialize the GLKVMConfigFlow."""
        self._errors: dict[str, str] = {}
        self.translations = None
        self._discovery_info: dict[str, str] = {}

    async def async_step_import(
        self, user_input=None
    ) -> config_entries.ConfigFlowResult:
        """Handle import."""
        return await self.async_step_user(user_input=user_input)

    async def async_step_user(self, user_input=None) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors = self._errors
        self._errors = {}

        translations = await get_translations(
            self.hass, self.hass.config.language, DOMAIN
        )
        if translations and not callable(translations):

            def translate(key: str, default: str) -> str:
                return translations.get(key, default)

            self.translations = translate
        else:
            self.translations = translations

        if user_input is not None:
            _LOGGER.debug(
                "Entered async_step_user with data: host=%s, password=%s",
                user_input[CONF_HOST],
                re.sub(r'.', '*', user_input[CONF_PASSWORD]),
            )
            entry, setup_errors = await perform_device_setup(self, user_input)
            if setup_errors:
                errors.update(setup_errors)
            if entry:
                return entry

        if user_input is None:
            _LOGGER.debug("Entered async_step_user with data: None")
            user_input = self._discovery_info or {
                CONF_HOST: DEFAULT_HOST,
                CONF_PASSWORD: DEFAULT_PASSWORD,
            }
            if self._discovery_info:
                user_input[CONF_PASSWORD] = ""

        data_schema = create_data_schema(user_input)

        def _translate(key: str, default: str) -> str:
            if self.translations:
                return self.translations(key, default)
            return default

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "url": _translate(
                    "step.user.data.url", "URL or IP address of the KVM device"
                ),
                "password": _translate(
                    "step.user.data.password", "Password for KVM"
                ),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return GLKVMOptionsFlowHandler(config_entry)


