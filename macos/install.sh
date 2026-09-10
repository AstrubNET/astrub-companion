#!/bin/bash
set -euo pipefail

[[ $EUID -eq 0 ]] || { echo "Installation administrateur requise."; exit 1; }
[[ $# -eq 2 ]] || { echo "Usage: sudo ./install.sh SERVER_ID SERVER_NAME"; exit 1; }

SERVER_ID="$1"
SERVER_NAME="$2"
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="/Library/Application Support/Astrub Companion"
PLIST="/Library/LaunchDaemons/net.astrub.companion.plist"
UPDATE_PLIST="/Library/LaunchAgents/net.astrub.companion.update.plist"
CONFIG="$INSTALL_DIR/config.json"
PYTHON_BIN="$(command -v python3 || true)"

[[ "$SERVER_ID" =~ ^[1-9][0-9]*$ ]] || { echo "Identifiant de serveur invalide."; exit 1; }
[[ -n "$PYTHON_BIN" ]] || { echo "Python 3 est requis."; exit 1; }

mkdir -p "$INSTALL_DIR"
install -m 755 "$SOURCE_DIR/astrub_companion.py" "$INSTALL_DIR/astrub_companion.py"
install -m 755 "$SOURCE_DIR/RechercherUneMiseAJour.command" "$INSTALL_DIR/RechercherUneMiseAJour.command"
printf '%s\n' '1.1.3' > "$INSTALL_DIR/version"
/usr/bin/sed "s|__PYTHON3__|$PYTHON_BIN|g" "$SOURCE_DIR/net.astrub.companion.plist" > "$PLIST"
install -m 644 "$SOURCE_DIR/net.astrub.companion.update.plist" "$UPDATE_PLIST"

"$PYTHON_BIN" - "$CONFIG" "$SERVER_ID" "$SERVER_NAME" <<'PY'
import json, pathlib, sys, uuid
path = pathlib.Path(sys.argv[1])
old = {}
if path.exists():
    try: old = json.loads(path.read_text())
    except (OSError, ValueError): pass
config = {
    "api_url": "https://www.astrub.net/api/companion/prices.php",
    "server_id": int(sys.argv[2]),
    "server_name": sys.argv[3],
    "device_id": old.get("device_id") or str(uuid.uuid4()),
    "interface": "auto",
    "selection_ttl_seconds": 120,
    "purchase_ttl_seconds": 20,
    "market_view_ttl_seconds": 20,
    "market_view_dedupe_seconds": 300,
}
path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
PY

chown -R root:wheel "$INSTALL_DIR"
chmod 600 "$CONFIG"
chown root:wheel "$PLIST"
chmod 644 "$PLIST"
/usr/bin/plutil -lint "$PLIST"
launchctl bootout system "$PLIST" 2>/dev/null || true
launchctl remove net.astrub.companion 2>/dev/null || true
launchctl bootstrap system "$PLIST"
launchctl enable system/net.astrub.companion
launchctl kickstart -k system/net.astrub.companion

LOGIN_USER="${SUDO_USER:-}"
if [[ -n "$LOGIN_USER" && "$LOGIN_USER" != "root" ]]; then
    LOGIN_UID="$(id -u "$LOGIN_USER")"
    chown "$LOGIN_USER":staff "$UPDATE_PLIST"
    launchctl bootout "gui/$LOGIN_UID" "$UPDATE_PLIST" 2>/dev/null || true
    launchctl bootstrap "gui/$LOGIN_UID" "$UPDATE_PLIST" 2>/dev/null || true
fi

echo "Astrub Companion installé pour $SERVER_NAME (ID $SERVER_ID)."
