"""Constants for the GLKVM integration."""

DOMAIN = "glkvm"
CONF_MODEL = "model"
CONF_HOST = "url"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_CERTIFICATE = "tls-certificate"
CONF_SERIAL = "serial"
DEFAULT_HOST = "glkvm.local"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin"
MANUFACTURER = "GLiNet"

# ATX Power Control Actions
ATX_ACTION_POWER_ON = "on"
ATX_ACTION_POWER_OFF = "off"
ATX_ACTION_POWER_OFF_HARD = "off_hard"
ATX_ACTION_RESET = "reset"
ATX_ACTION_RESET_HARD = "reset_hard"

# ATX API Endpoints
API_ATX = "/api/atx"
API_ATX_POWER = "/api/atx/power"
API_INFO = "/api/info"

# Shutdown mode options (for switch turn_off behavior)
CONF_SHUTDOWN_MODE = "shutdown_mode"
SHUTDOWN_MODE_GRACEFUL = "graceful"
SHUTDOWN_MODE_FORCE = "force"
