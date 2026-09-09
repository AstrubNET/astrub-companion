#!/bin/bash
sudo launchctl disable system/net.astrub.companion
sudo launchctl bootout system "/Library/LaunchDaemons/net.astrub.companion.plist" 2>/dev/null || true
osascript -e 'display notification "Collecte suspendue." with title "Astrub Companion"'
