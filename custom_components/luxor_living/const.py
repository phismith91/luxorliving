"""Constants for the LUXORliving integration."""

from __future__ import annotations

DOMAIN = "luxor_living"

# Configuration
CONF_LXP_FILE = "lxp_file"
CONF_SIMULATION_MODE = "simulation_mode"
CONF_CONNECTION_TYPE = "connection_type"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

# Defaults
DEFAULT_PORT = 3671  # KNX/IP default port
DEFAULT_HTTP_PORT = 80  # REST API HTTP port (per LUXORliving API documentation)
DEFAULT_CONNECTION_TYPE = "tunneling"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin"

# KNX Connection Types
CONNECTION_TYPE_TUNNELING = "tunneling"
CONNECTION_TYPE_ROUTING = "routing"

# LXP Project
LXP_NAMESPACE = "{http://www.luxor.de/LuxorPlug}"

# Entity naming
ATTR_ROOM = "room"
ATTR_FUNCTION = "function"
ATTR_DEVICE = "device"

# KNX Gateway
DATA_KNX_GATEWAY = "knx_gateway"
DATA_COORDINATOR = "coordinator"
