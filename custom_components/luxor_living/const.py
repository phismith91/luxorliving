"""Constants for the LUXORliving integration."""

from __future__ import annotations

DOMAIN = "luxor_living"

# Configuration
CONF_LXP_FILE = "lxp_file"
CONF_SIMULATION_MODE = "simulation_mode"
CONF_CONNECTION_TYPE = "connection_type"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_LOG_LEVEL = "log_level"
CONF_DISCOVERY_TIMEOUT = "discovery_timeout"

# Defaults
DEFAULT_PORT = 3671  # KNX/IP default port
DEFAULT_HTTP_PORT = 443  # REST API HTTPS port (secure by default)
DEFAULT_CONNECTION_TYPE = "tunneling"
# Default credentials are used as UI form defaults only (common BAOS factory defaults)
# Actual credentials are entered by users and stored in encrypted config entry
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin"
DEFAULT_SCAN_INTERVAL = 30  # seconds
SESSION_REFRESH_INTERVAL = 4 * 3600  # proactive REST session refresh every 4 h
DEFAULT_LOG_LEVEL = "info"
DEFAULT_DISCOVERY_TIMEOUT = 2.0  # seconds

# KNX Connection Types
CONNECTION_TYPE_TUNNELING = "tunneling"
CONNECTION_TYPE_ROUTING = "routing"

# LXP Project
LXP_NAMESPACE = "{http://www.luxor.de/LuxorPlug}"

# Entity naming
ATTR_ROOM = "room"
ATTR_FUNCTION = "function"
ATTR_DEVICE = "device"

# Push / Webhook options
CONF_PUSH_TOKEN = "push_token"
CONF_PUSH_WS_URL = "push_ws_url"
CONF_PUSH_WS_TOKEN = "push_ws_token"
# Push auth method: none | token | bearer | hmac
CONF_PUSH_AUTH_METHOD = "push_auth_method"
PUSH_AUTH_NONE = "none"
PUSH_AUTH_TOKEN = "token"
PUSH_AUTH_BEARER = "bearer"
PUSH_AUTH_HMAC = "hmac"

# Diagnostics consent option
CONF_ALLOW_DIAGNOSTICS = "allow_diagnostics"
DEFAULT_ALLOW_DIAGNOSTICS = False

# KNX Gateway
DATA_KNX_GATEWAY = "knx_gateway"
DATA_COORDINATOR = "coordinator"
