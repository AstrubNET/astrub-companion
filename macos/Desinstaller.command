#!/bin/bash
set -euo pipefail
answer="$(osascript -e 'display dialog "Désinstaller Astrub Companion ? La configuration locale et la file d’attente seront également supprimées." with title "Astrub Companion" buttons {"Annuler", "Désinstaller"} default button "Annuler" cancel button "Annuler"' -e 'button returned of result')" || exit 0
[[ "$answer" == "Désinstaller" ]] || exit 0
sudo launchctl bootout system "/Library/LaunchDaemons/net.astrub.companion.plist" 2>/dev/null || true
sudo launchctl remove net.astrub.companion 2>/dev/null || true
launchctl bootout "gui/$(id -u)" "/Library/LaunchAgents/net.astrub.companion.update.plist" 2>/dev/null || true
sudo /bin/rm -f "/Library/LaunchDaemons/net.astrub.companion.plist"
sudo /bin/rm -f "/Library/LaunchAgents/net.astrub.companion.update.plist"
sudo /bin/rm -rf "/Library/Application Support/Astrub Companion"
osascript -e 'display notification "Désinstallation terminée." with title "Astrub Companion"'
