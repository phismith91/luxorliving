#!/bin/bash

echo "🧪 Dashboard Update Test - LIVE"
echo "================================"
echo ""
echo "ANLEITUNG:"
echo "1. Öffne Dashboard im Browser"
echo "2. Führe dieses Script aus"
echo "3. Drücke PHYSISCHEN Schalter für 'Badlicht'"
echo "4. Beobachte Logs UND Dashboard"
echo ""
echo "Starte Log-Monitor in 3 Sekunden..."
sleep 3
echo ""
echo "📡 Warte auf KNX Telegrams..."
echo "   Drücke JETZT den Badlicht-Schalter!"
echo ""

# Monitor für 30 Sekunden
timeout 30 tail -f ~/.homeassistant/home-assistant.log | grep --line-buffered -E "Incoming CEMI|_handle_telegram|1/1/0|Badlicht|async_schedule" &
TAIL_PID=$!

echo ""
echo "⏱️  Monitoring für 30 Sekunden..."
echo "   Drücke den Schalter mehrmals!"
echo ""

# Nach 30 Sekunden
wait $TAIL_PID

echo ""
echo "================================"
echo "ERWARTETE LOGS:"
echo "  ✅ 'Incoming CEMI' - Telegram empfangen"
echo "  ✅ '1/1/0' - GroupAddress erkannt"
echo "  ✅ '_handle_telegram' - Handler aufgerufen"
echo "  ✅ 'async_schedule_update_ha_state' - Update getriggert"
echo ""
echo "WENN NICHTS KOMMT:"
echo "  → Routing/Tunneling Konflikt"
echo "  → Standard KNX Integration deaktivieren"
echo ""
