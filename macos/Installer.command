#!/bin/bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVERS_URL="https://www.astrub.net/api/companion/servers.php"
PYTHON_BIN="$(command -v python3 || true)"

[[ -n "$PYTHON_BIN" ]] || {
  osascript -e 'display alert "Astrub Companion" message "Python 3 est requis sur ce Mac." as critical'
  exit 1
}

choices="$("$PYTHON_BIN" - "$SERVERS_URL" <<'PY'
import json, sys, urllib.request
with urllib.request.urlopen(sys.argv[1], timeout=10) as response:
    data = json.load(response)
for server in data.get("servers", []):
    print(f"{int(server['id'])} — {server['name']}")
PY
)" || {
  osascript -e 'display alert "Astrub Companion" message "Impossible de télécharger la liste des serveurs. Vérifie ta connexion puis réessaie." as critical'
  exit 1
}

[[ -n "$choices" ]] || {
  osascript -e 'display alert "Astrub Companion" message "Aucun serveur actif n’est disponible." as critical'
  exit 1
}

selection="$(osascript - "$choices" <<'APPLESCRIPT'
on run argv
    set serverList to paragraphs of item 1 of argv
    set picked to choose from list serverList with title "Astrub Companion" with prompt "Choisis ton serveur Dofus :" OK button name "Installer" cancel button name "Annuler"
    if picked is false then error number -128
    return item 1 of picked
end run
APPLESCRIPT
)" || exit 0

consent="$(osascript <<'APPLESCRIPT'
display dialog "Astrub Companion écoute passivement le trafic réseau local de Dofus pour reconnaître uniquement les prix HDV consultés, achetés ou mis en vente. Il ne clique pas, n’injecte aucun paquet, ne lit pas tes identifiants Ankama et ne conserve aucun fichier PCAP.\n\nLes prix, l’identifiant de l’objet, le serveur, le type d’observation, la date et un identifiant aléatoire d’installation sont envoyés à Astrub.net." with title "Transparence et consentement" buttons {"Annuler", "J’accepte"} default button "J’accepte" cancel button "Annuler"
return button returned of result
APPLESCRIPT
)" || exit 0

[[ "$consent" == "J’accepte" ]] || exit 0
server_id="${selection%% — *}"
server_name="${selection#* — }"

sudo "$SOURCE_DIR/install.sh" "$server_id" "$server_name"
osascript -e 'display notification "Installation terminée. Le service fonctionne en arrière-plan." with title "Astrub Companion"'
echo
echo "Installation terminée pour le serveur : $server_name (ID $server_id)"
echo "Tu peux fermer cette fenêtre."
