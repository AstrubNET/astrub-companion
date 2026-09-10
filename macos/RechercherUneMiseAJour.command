#!/bin/bash
set -euo pipefail

CURRENT_VERSION="1.1.3"
VERSION_FILE="/Library/Application Support/Astrub Companion/version"
[[ -r "$VERSION_FILE" ]] && CURRENT_VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"

RESULT="$(/usr/bin/env python3 - "$CURRENT_VERSION" <<'PY'
import json, sys, urllib.request

current = tuple(int(x) for x in sys.argv[1].lstrip('v').split('.'))
request = urllib.request.Request(
    'https://api.github.com/repos/AstrubNET/astrub-companion/releases/latest',
    headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'Astrub-Companion-Updater/1.1.3'},
)
with urllib.request.urlopen(request, timeout=15) as response:
    release = json.load(response)
latest_text = str(release['tag_name']).lstrip('v')
latest = tuple(int(x) for x in latest_text.split('.'))
if release.get('draft') or release.get('prerelease') or latest <= current:
    raise SystemExit(0)
print(latest_text)
print(release['html_url'])
PY
)" || exit 0

[[ -n "$RESULT" ]] || exit 0
LATEST_VERSION="$(printf '%s\n' "$RESULT" | sed -n '1p')"
RELEASE_URL="$(printf '%s\n' "$RESULT" | sed -n '2p')"

CHOICE="$(osascript -e "display dialog \"Astrub Companion ${LATEST_VERSION} est disponible. La mise à jour peut être téléchargée depuis la release GitHub officielle.\" with title \"Mise à jour Astrub Companion\" buttons {\"Plus tard\", \"Télécharger\"} default button \"Télécharger\"" -e 'button returned of result')" || exit 0
[[ "$CHOICE" == "Télécharger" ]] && /usr/bin/open "$RELEASE_URL"
