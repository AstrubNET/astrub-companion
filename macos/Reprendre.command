#!/bin/bash
sudo launchctl bootstrap system "/Library/LaunchDaemons/net.astrub.companion.plist" 2>/dev/null || true
sudo launchctl enable system/net.astrub.companion
sudo launchctl kickstart -k system/net.astrub.companion
osascript -e 'display notification "Collecte réactivée." with title "Astrub Companion"'
