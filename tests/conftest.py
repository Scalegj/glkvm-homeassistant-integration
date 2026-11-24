from copy import deepcopy
from unittest.mock import patch

import pytest
from pytest_homeassistant.common import MockConfigEntry

from custom_components.glkvm.const import DOMAIN

from .const import (
    ATX,
    EDID_A,
    EDID_LIST,
    ENTRY_DATA,
    HID,
    INFO,
    MSD,
    SERIAL,
    VERSION,
)


@pytest.fixture
def mock_config_entry():
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=SERIAL,
        title="GL.iNet RM1PE (RIAL)",
        data=ENTRY_DATA,
    )


@pytest.fixture
def mock_client():
    with patch("custom_components.glkvm.GlkvmClient", autospec=True) as client_class:
        client = client_class.return_value
        client.async_get_info.return_value = deepcopy(INFO)
        client.async_get_version.return_value = deepcopy(VERSION)
        client.async_get_atx.return_value = deepcopy(ATX)
        client.async_get_hid.return_value = deepcopy(HID)
        client.async_get_msd.return_value = deepcopy(MSD)
        client.async_get_edid.return_value = EDID_A
        client.async_get_edid_list.return_value = dict(EDID_LIST)
        yield client
