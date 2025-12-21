# Remote Setup über VPN (Madeira)

## Situation
- HA läuft auf VM in Madeira
- LUXORliving Gateway physisch in Madeira
- Zugriff über VPN

## Problem: Multicast über VPN
**KNX Routing (224.0.23.12) funktioniert meist NICHT über VPN!**

Multicast wird von den meisten VPNs geblockt/nicht geroutet.

## Lösung: KNX Tunneling mit echter IP

### 1. Gateway IP finden (in Madeira)
```bash
# Auf der VM in Madeira ausführen:
nmap -p 3671,80,443 192.168.1.0/24

# Oder im Angry IP Scanner auf der VM
# Suche nach offenen Ports: 80, 443, 3671
```

### 2. Config auf Tunneling umstellen

**Auf der VM in Madeira:**
```bash
python3 ~/luxorliving/scripts/set_tunneling.py <GATEWAY_IP>
```

### 3. Falls Tunneling nicht verfügbar

Manche Gateways haben Tunneling deaktiviert:
- Web-UI öffnen: `http://<GATEWAY_IP>`
- Login (meist admin/admin)
- KNX/IP Einstellungen → Tunneling aktivieren

### 4. Alternative: Routing mit HA auf Gateway-Host

Falls Tunneling nicht geht:
- HA muss auf **gleicher Maschine** wie Gateway laufen
- Oder in **gleichem Netzwerk-Segment** ohne VPN-Hop

## Wichtig
**ALLE Befehle müssen auf der VM in Madeira ausgeführt werden!**
Nicht auf deinem lokalen Rechner.
