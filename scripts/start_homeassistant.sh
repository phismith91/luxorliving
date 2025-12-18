#!/bin/bash
# Start Home Assistant for Development

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
HA_CONFIG="${HOME}/.homeassistant"

echo "🏠 Starting Home Assistant Development Environment"
echo "=================================================="

# Activate venv
echo "📦 Activating virtual environment..."
source "${PROJECT_DIR}/venv/bin/activate"

# Create config directory if it doesn't exist
if [ ! -d "${HA_CONFIG}" ]; then
    echo "📁 Creating Home Assistant config directory: ${HA_CONFIG}"
    mkdir -p "${HA_CONFIG}"
fi

# Create symbolic link for custom component
CUSTOM_COMP_DIR="${HA_CONFIG}/custom_components"
mkdir -p "${CUSTOM_COMP_DIR}"

if [ ! -L "${CUSTOM_COMP_DIR}/luxor_living" ]; then
    echo "🔗 Creating symbolic link for luxor_living integration..."
    ln -sf "${PROJECT_DIR}/custom_components/luxor_living" "${CUSTOM_COMP_DIR}/luxor_living"
    echo "   Linked: ${CUSTOM_COMP_DIR}/luxor_living -> ${PROJECT_DIR}/custom_components/luxor_living"
else
    echo "✅ Symbolic link already exists"
fi

# Check for LXP file
LXP_FILE="${PROJECT_DIR}/test_project.lxp"
if [ ! -f "${LXP_FILE}" ]; then
    echo ""
    echo "⚠️  No LXP file found at: ${LXP_FILE}"
    echo "   The integration will look for:"
    echo "   - ${HOME}/Nextcloud/Projekte_Rechner/Madeira/Schmidt_Madeira_V0.8.lxp"
    echo "   - ${HOME}/Nextcloud/Projekte_Rechner/Madeira/Madeira.lxp"
    echo ""
fi

echo ""
echo "🚀 Starting Home Assistant..."
echo "   Config: ${HA_CONFIG}"
echo "   URL: http://localhost:8123"
echo ""
echo "📊 Logs in separate terminal:"
echo "   tail -f ${HA_CONFIG}/home-assistant.log | grep luxor"
echo ""
echo "Press Ctrl+C to stop"
echo "=================================================="
echo ""

# Start Home Assistant
hass -c "${HA_CONFIG}"
