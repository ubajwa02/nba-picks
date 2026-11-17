#!/usr/bin/env bash
# Install (or remove) the local nba-daily runner as a macOS launchd job that wakes every 30 minutes.
#   bash ops/local/install_mac.sh            install / update
#   bash ops/local/install_mac.sh uninstall  remove
# Uses the Mac's own git sign-in to push to main, like the GitHub workflow does. Pause without uninstalling:
#   touch ~/nba-picks-runner/STOP
set -euo pipefail
LABEL=com.nbapicks.local
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
RUNNER="$HOME/nba-picks-runner"
if [ "${1:-}" = "uninstall" ]; then
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  rm -f "$PLIST"; echo "removed $LABEL"; exit 0
fi
PY="$(command -v python3)"
"$PY" -c 'import sys; assert sys.version_info >= (3, 9), "python 3.9+ needed"'
mkdir -p "$RUNNER/logs" "$HOME/Library/LaunchAgents"
cp "$(cd "$(dirname "$0")" && pwd)/nba_local.py" "$RUNNER/nba_local.py"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array><string>$PY</string><string>$RUNNER/nba_local.py</string></array>
  <key>StartInterval</key><integer>1800</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$RUNNER/logs/launchd.out</string>
  <key>StandardErrorPath</key><string>$RUNNER/logs/launchd.err</string>
  <key>EnvironmentVariables</key><dict><key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string></dict>
</dict></plist>
EOF
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "installed $LABEL: runs due nba-daily slots every 30 min; logs in $RUNNER/logs"
