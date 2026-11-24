"""Tests for the GL.iNet KVM config flow."""

from contextlib import contextmanager
from unittest.mock import patch

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_VERIFY_SSL
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant.common import MockConfigEntry

from custom_components.glkvm.api import (
    GlkvmAuthError,
    GlkvmClient,
    GlkvmError,
    GlkvmSslError,
)
from custom_components.glkvm.const import CONF_TOTP_SECRET, DOMAIN

from .const import INFO, SERIAL, USER_INPUT, VERSION

SECRET = "N4Z5UKVNYK7WWEY7KLOZCSO4P566EVCO"  # Fake secret, not used anywhere


@contextmanager
def mock_kvm(
    two_fa=False, two_fa_error=None, info=INFO, info_error=None, version=VERSION
):
    """Fake the KVM's answers"""
    with (
        patch.object(
            GlkvmClient,
            "async_get_2fa_enabled",
            return_value=two_fa,
            side_effect=two_fa_error,
        ),
        patch.object(
            GlkvmClient, "async_get_info", return_value=info, side_effect=info_error
        ),
        patch.object(GlkvmClient, "async_get_version", return_value=version),
        patch("custom_components.glkvm.async_setup_entry", return_value=True),
    ):
        yield


async def start_flow(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    return result


async def test_user_success(hass):
    result = await start_flow(hass)
    with mock_kvm():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "GL.iNet RM1PE (RIAL)"
    assert result["data"] == {
        **USER_INPUT,
        CONF_VERIFY_SSL: False,
        CONF_TOTP_SECRET: None,
    }
    assert result["result"].unique_id == SERIAL


async def test_user_success_with_2fa(hass):
    result = await start_flow(hass)
    with mock_kvm(two_fa=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**USER_INPUT, CONF_TOTP_SECRET: "n4z5 ukvn yk7w wey7 kloz cso4 p566 evco"},
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_TOTP_SECRET] == SECRET


async def test_user_old_firmware(hass):
    result = await start_flow(hass)
    with mock_kvm(two_fa_error=GlkvmError):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY


@pytest.mark.parametrize(
    ("two_fa", "extra_input", "info_error", "errors"),
    [
        (True, {}, None, {CONF_TOTP_SECRET: "totp_required"}),
        (
            False,
            {CONF_TOTP_SECRET: SECRET},
            None,
            {CONF_TOTP_SECRET: "totp_not_enabled"},
        ),
        (False, {}, GlkvmAuthError, {"base": "invalid_auth"}),
        (
            True,
            {CONF_TOTP_SECRET: SECRET},
            GlkvmAuthError,
            {"base": "invalid_auth_totp"},
        ),
        (False, {}, GlkvmError, {"base": "cannot_connect"}),
        (
            False,
            {CONF_TOTP_SECRET: "not!base32"},
            None,
            {CONF_TOTP_SECRET: "invalid_totp_secret"},
        ),
        (False, {}, GlkvmSslError, {"base": "ssl_error"}),
    ],
)
async def test_user_errors(hass, two_fa, extra_input, info_error, errors):
    result = await start_flow(hass)
    with mock_kvm(two_fa=two_fa, info_error=info_error):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**USER_INPUT, **extra_input}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == errors

    with mock_kvm():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_already_configured(hass):
    MockConfigEntry(domain=DOMAIN, unique_id=SERIAL, data=USER_INPUT).add_to_hass(hass)

    result = await start_flow(hass)
    with mock_kvm():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=SERIAL, data={**USER_INPUT, CONF_TOTP_SECRET: None}
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"

    with mock_kvm():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PASSWORD: "new-password"}
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_PASSWORD] == "new-password"


async def test_reauth_different_kvm(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=SERIAL, data={**USER_INPUT, CONF_TOTP_SECRET: None}
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    other_kvm = {"system": {"platform": {"serial": "OTHERSERIAL"}}}
    with mock_kvm(info=other_kvm):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PASSWORD: "new-password"}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "unique_id_mismatch"
    assert entry.data[CONF_PASSWORD] == USER_INPUT[CONF_PASSWORD]


async def test_user_host_is_cleaned(hass):
    result = await start_flow(hass)
    with mock_kvm():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**USER_INPUT, CONF_HOST: " https://kvm.local/ "},
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_HOST] == "kvm.local"


async def test_user_updates_host_of_existing_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=SERIAL,
        data={**USER_INPUT, CONF_HOST: "old.local", CONF_TOTP_SECRET: None},
    )
    entry.add_to_hass(hass)

    result = await start_flow(hass)
    with mock_kvm():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data[CONF_HOST] == "kvm.local"


async def test_user_title_without_model(hass):
    result = await start_flow(hass)
    with mock_kvm(version={}):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "GL.iNet KVM (RIAL)"


async def test_user_second_kvm(hass):
    MockConfigEntry(
        domain=DOMAIN, unique_id="OTHERSERIAL", data=USER_INPUT
    ).add_to_hass(hass)

    result = await start_flow(hass)
    with mock_kvm():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**USER_INPUT, CONF_HOST: "kvm2.local"}
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert len(hass.config_entries.async_entries(DOMAIN)) == 2


async def test_reconfigure(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=SERIAL, data={**USER_INPUT, CONF_TOTP_SECRET: None}
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    assert result["step_id"] == "reconfigure"

    with mock_kvm():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "https://new.local/"}
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_HOST] == "new.local"
    assert entry.data[CONF_VERIFY_SSL] is False


async def test_reconfigure_different_kvm(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=SERIAL, data={**USER_INPUT, CONF_TOTP_SECRET: None}
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    other_kvm = {"system": {"platform": {"serial": "OTHERSERIAL"}}}
    with mock_kvm(info=other_kvm):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "other.local"}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "unique_id_mismatch"
    assert entry.data[CONF_HOST] == "kvm.local"


async def test_reconfigure_cannot_connect(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=SERIAL, data={**USER_INPUT, CONF_TOTP_SECRET: None}
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    with mock_kvm(info_error=GlkvmError):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "dead.local"}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    assert entry.data[CONF_HOST] == "kvm.local"
