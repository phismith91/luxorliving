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
RECONNECT_FAILURE_THRESHOLD = 5  # forced REST refresh after this many DISCONNECTED events in window
RECONNECT_FAILURE_WINDOW = 60  # seconds window for counting consecutive disconnects
RECONNECT_COOLDOWN_SECS = 30  # skip reconnect re-auth if a refresh happened this recently
READ_REQUEST_INTERVAL = 0.15  # minimum spacing between KNX group-read requests
READ_DEGRADE_ERROR_THRESHOLD = 3  # recent confirmation timeouts before non-essential reads pause
READ_DEGRADE_WINDOW = 60  # seconds window for recent confirmation-timeout tracking
READ_DEGRADE_COOLDOWN = 120  # seconds to suppress group reads after timeout surge
ZOMBIE_CHECK_INTERVAL = 30  # seconds between cemi_count_outgoing_error polls
ZOMBIE_ERROR_THRESHOLD = (
    5  # new L_DATA_CON confirmation failures per check interval to declare zombie tunnel
)
ZOMBIE_RECONNECT_COOLDOWN = (
    300  # seconds to wait after a zombie-triggered reconnect before arming again
)
ZOMBIE_RECOVERY_TIMEOUT = 120  # seconds before a stuck zombie-recovery (disconnect+setup) is abandoned, releasing _session_lock
ZOMBIE_RECOVERY_RETRY_INTERVAL = (
    60  # seconds between async_setup() retries after a failed zombie recovery
)
XKNX_INTERFACE_STOP_TIMEOUT = (
    5  # seconds for the forced knxip_interface.stop() after a stop() timeout
)
OUTGOING_QUEUE_BACKPRESSURE_LIMIT = (
    50  # skip entity-poll reads when this many telegrams are already queued outgoing
)
XKNX_STOP_TIMEOUT = 15  # seconds before a hanging xknx.stop() is abandoned during disconnect
NOT_CONNECTED_LOG_INTERVAL = 60  # rate-limit "not connected" ERROR log to once per N seconds
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
