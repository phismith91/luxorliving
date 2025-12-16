"""Constants for the Theben LUXORliving integration."""
from datetime import timedelta

# Integration domain
DOMAIN = "luxorliving"

# Default values
DEFAULT_PORT = 80
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_TIMEOUT = 10

# API endpoints (placeholder - adjust based on actual API)
API_ENDPOINT_STATUS = "/api/status"
API_ENDPOINT_DEVICES = "/api/devices"
API_ENDPOINT_CONTROL = "/api/control"

# Device types
DEVICE_TYPE_LIGHT = "light"
DEVICE_TYPE_SWITCH = "switch"
DEVICE_TYPE_SENSOR = "sensor"

# Attributes
ATTR_DEVICE_ID = "device_id"
ATTR_DEVICE_NAME = "device_name"
ATTR_DEVICE_TYPE = "device_type"
ATTR_STATE = "state"
