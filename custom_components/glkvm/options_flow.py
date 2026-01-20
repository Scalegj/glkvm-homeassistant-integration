"""Config flow to configure GL.iNet KVM."""

import logging

from homeassistant import config_entries

from .cert_handler import fetch_serialized_cert, is_glkvm_device
from .const import (
    CONF_CERTIFICATE,
    CONF_HOST,
    CONF_PASSWORD,
    DEFAULT_PASSWORD,
    DEFAULT_USERNAME,
    DOMAIN,
)
from .utils import (
    create_data_schema,
    format_url,
    get_translations,
    update_existing_entry,
)

_LOGGER = logging.getLogger(__name__)


class GLKVMOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle GL.iNet KVM options."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.translate = None

    async def async_step_init(self, user_input=None):
        """Manage the GLKVM options."""
        errors = {}
        self.translate = await get_translations(
            self.hass, self.hass.config.language, DOMAIN
        )
        _LOGGER.debug("Entered async_step_init with data: %s", user_input)

        if user_input is not None:
            url = format_url(user_input[CONF_HOST])
            username = DEFAULT_USERNAME
            password = user_input.get(CONF_PASSWORD, DEFAULT_PASSWORD)

            _LOGGER.debug("Manual setup with URL %s, username %s", url, username)

            serialized_cert = await fetch_serialized_cert(self.hass, url)
            if not serialized_cert:
                errors["base"] = "cannot_fetch_cert"
                _LOGGER.error("Cannot fetch cert from URL: %s", url)
            else:
                _LOGGER.debug("Serialized certificate fetched successfully")
                user_input[CONF_CERTIFICATE] = serialized_cert

                response = await is_glkvm_device(
                    self.hass, url, username, password, serialized_cert
                )

                if response.error:
                    errors["base"] = response.error
                elif response.success:
                    _LOGGER.debug(
                        "KVM device successfully found at %s with serial %s",
                        url,
                        response.serial,
                    )

                    existing_entry = None
                    for entry in self.hass.config_entries.async_entries(DOMAIN):
                        if entry.unique_id == response.serial:
                            existing_entry = entry
                            break

                    if existing_entry:
                        update_existing_entry(self.hass, existing_entry, user_input)
                        return self.async_create_entry(title="", data={})

                    user_input["serial"] = response.serial
                    new_data = {**self.config_entry.data, **user_input}
                    self.hass.config_entries.async_update_entry(
                        self.config_entry, data=new_data
                    )
                    return self.async_create_entry(title="", data={})
                else:
                    errors["base"] = "cannot_connect"
                    _LOGGER.error(
                        "Cannot connect to KVM device at %s with provided credentials",
                        url,
                    )

        default_url = self.config_entry.data.get(CONF_HOST, "")
        default_password = self.config_entry.data.get(CONF_PASSWORD, DEFAULT_PASSWORD)

        data_schema = create_data_schema(
            {
                CONF_HOST: default_url,
                CONF_PASSWORD: default_password,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "url": self.translate(
                    "config.step.user.data.url", "URL or IP address of the KVM device"
                ),
                "password": self.translate(
                    "config.step.user.data.password", "Password for KVM"
                ),
            },
        )


