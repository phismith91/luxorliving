#!/bin/bash
# Schnellstart für Entwicklung

cd "$(dirname "$0")/.."
source venv/bin/activate

echo "🚀 LUXORliving Development Environment"
echo ""
echo "Verfügbare Befehle:"
echo "  hass -c config          → Home Assistant starten"
echo "  pytest tests/           → Tests ausführen"
echo "  black custom_components/ → Code formatieren"
echo "  pylint custom_components/ → Linting"
echo ""
echo "VS Code Debugger: Drücke F5"
echo ""
