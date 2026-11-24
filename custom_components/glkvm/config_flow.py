import logging

import pyotp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import GlkvmAuthError, GlkvmClient, GlkvmError, GlkvmSslError
from .const import CONF_TOTP_SECRET, DOMAIN

_LOGGER = logging.getLogger(__name__)

PASSWORD_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME, default="admin"): str,
        vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR,
        vol.Optional(CONF_TOTP_SECRET): PASSWORD_SELECTOR,
        vol.Required(CONF_VERIFY_SSL, default=False): bool,
    }
)

STEP_REAUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR,
        vol.Optional(CONF_TOTP_SECRET): PASSWORD_SELECTOR,
    }
)

STEP_RECONFIGURE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_VERIFY_SSL, default=False): bool,
    }
)


def _clean_secret(secret):
    """Normalize a TOTP secret. Returns None if blank, raises ValueError if invalid."""
    if not secret:
        return None
    secret = secret.replace(" ", "").upper()
    pyotp.TOTP(secret).now()
    return secret


def _clean_host(host):
    """Strip a scheme, trailing slash and spaces so only host[:port] is left."""
    host = host.strip()
    for prefix in ("https://", "http://"):
        if host.lower().startswith(prefix):
            host = host[len(prefix) :]
    return host.rstrip("/")


class GlkvmConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _async_validate(self, host, username, password, totp_secret, verify_ssl):
        client = GlkvmClient(
            host,
            username,
            password,
            async_get_clientsession(self.hass, verify_ssl=verify_ssl),
            totp_secret,
        )

        try:
            enabled = await client.async_get_2fa_enabled()
            if enabled and not totp_secret:
                return None, None, {CONF_TOTP_SECRET: "totp_required"}
            if totp_secret and not enabled:
                return None, None, {CONF_TOTP_SECRET: "totp_not_enabled"}
        except GlkvmError, KeyError:
            pass

        try:
            info = await client.async_get_info()
            serial = info["system"]["platform"]["serial"]
        except GlkvmSslError:
            return None, None, {"base": "ssl_error"}
        except GlkvmAuthError:
            if totp_secret:
                return None, None, {"base": "invalid_auth_totp"}
            return None, None, {"base": "invalid_auth"}
        except GlkvmError, KeyError, TypeError:
            return None, None, {"base": "cannot_connect"}
        except Exception:
            _LOGGER.exception("Unexpected error validating GLKVM")
            return None, None, {"base": "unknown"}

        try:
            model = (await client.async_get_version()).get("model")
        except GlkvmError, AttributeError:
            model = None
        return serial, model, {}

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            host = _clean_host(user_input[CONF_HOST])
            try:
                secret = _clean_secret(user_input.get(CONF_TOTP_SECRET))
            except ValueError:
                errors[CONF_TOTP_SECRET] = "invalid_totp_secret"
            else:
                serial, model, errors = await self._async_validate(
                    host,
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                    secret,
                    user_input[CONF_VERIFY_SSL],
                )
                if not errors:
                    await self.async_set_unique_id(serial)
                    self._abort_if_unique_id_configured(updates={CONF_HOST: host})
                    name = f"GL.iNet {model}" if model else "GL.iNet KVM"
                    return self.async_create_entry(
                        title=f"{name} ({serial[-4:]})",
                        data={**user_input, CONF_HOST: host, CONF_TOTP_SECRET: secret},
                    )

        suggested = None
        if user_input is not None:
            suggested = {
                CONF_HOST: user_input[CONF_HOST],
                CONF_USERNAME: user_input[CONF_USERNAME],
                CONF_VERIFY_SSL: user_input[CONF_VERIFY_SSL],
            }
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_SCHEMA, suggested
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        errors = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            try:
                secret = _clean_secret(user_input.get(CONF_TOTP_SECRET))
            except ValueError:
                errors[CONF_TOTP_SECRET] = "invalid_totp_secret"
            else:
                serial, _, errors = await self._async_validate(
                    entry.data[CONF_HOST],
                    entry.data[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                    secret,
                    entry.data.get(CONF_VERIFY_SSL, False),
                )
                if not errors:
                    await self.async_set_unique_id(serial)
                    self._abort_if_unique_id_mismatch()
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={
                            CONF_PASSWORD: user_input[CONF_PASSWORD],
                            CONF_TOTP_SECRET: secret,
                        },
                    )

        return self.async_show_form(
            step_id="reauth_confirm", data_schema=STEP_REAUTH_SCHEMA, errors=errors
        )

    async def async_step_reconfigure(self, user_input=None):
        errors = {}
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            host = _clean_host(user_input[CONF_HOST])
            serial, _, errors = await self._async_validate(
                host,
                entry.data[CONF_USERNAME],
                entry.data[CONF_PASSWORD],
                entry.data.get(CONF_TOTP_SECRET),
                user_input[CONF_VERIFY_SSL],
            )
            if not errors:
                await self.async_set_unique_id(serial)
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_HOST: host,
                        CONF_VERIFY_SSL: user_input[CONF_VERIFY_SSL],
                    },
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                STEP_RECONFIGURE_SCHEMA,
                user_input
                or {
                    CONF_HOST: entry.data[CONF_HOST],
                    CONF_VERIFY_SSL: entry.data.get(CONF_VERIFY_SSL, False),
                },
            ),
            errors=errors,
        )
