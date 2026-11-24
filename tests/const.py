"""Shared test data based on GL.iNet RM1PE."""

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, CONF_VERIFY_SSL

from custom_components.glkvm.const import CONF_TOTP_SECRET

SERIAL = "TESTSERIAL"
USER_INPUT = {
    CONF_HOST: "kvm.local",
    CONF_USERNAME: "admin",
    CONF_PASSWORD: "test-password",
}
ENTRY_DATA = {**USER_INPUT, CONF_VERIFY_SSL: False, CONF_TOTP_SECRET: None}
EDID_A = "00ffffffffffff00" + "01" * 240
EDID_B = "00ffffffffffff00" + "02" * 112
EDID_LIST = {"Preset A/60Hz": EDID_A, "Preset B/60Hz": EDID_B}

INFO = {
    "system": {
        "kvmd": {"version": "4.82"},
        "platform": {"model": "v3", "serial": SERIAL},
    }
}
VERSION = {"model": "RM1PE", "version": "V1.10.3 release1"}
ATX = {
    "busy": False,
    "enabled": True,
    "leds": {"hdd": False, "power": False},
    "power": "on",
}
HID = {
    "connected": True,
    "enabled": True,
    "jiggler": {"active": False, "enabled": True},
    "online": True,
}

MSD = {
    "enabled": True,
    "online": True,
    "drive": {"connected": False, "image": None},
    "storage": {
        "images": {"debian.iso": {"complete": True}, "partial.iso": {"complete": False}}
    },
}
