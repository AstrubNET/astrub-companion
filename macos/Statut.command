#!/bin/bash
set -u
CONFIG="/Library/Application Support/Astrub Companion/config.json"
PYTHON_BIN="$(command -v python3 || true)"
if sudo launchctl print system/net.astrub.companion >/dev/null 2>&1; then state="Actif"; else state="Arrêté"; fi
server="$(sudo "$PYTHON_BIN" - "$CONFIG" <<'PY' 2>/dev/null
import json,sys
try:
    c=json.load(open(sys.argv[1])); print(f"{c.get('server_name','Inconnu')} — ID {c.get('server_id','?')}")
except Exception: print("Non configuré")
PY
)"
osascript -e "display dialog \"État : $state\\nServeur : $server\" with title \"Astrub Companion\" buttons {\"Fermer\"} default button \"Fermer\""
