#!/bin/sh
# Keep a full local copy of the repo on this machine, with every branch and the whole history.
# Usage: tools/backup_local.sh [folder]   (default ~/nba-picks-backup)
# Safe to run any time; it only fetches. Needs git access to the repo (gh auth login or a token).
set -eu
DEST="${1:-$HOME/nba-picks-backup}"
REPO="${NBA_REPO:-https://github.com/ubajwa02/nba-picks.git}"
if [ -d "$DEST/nba-picks.git" ]; then
  git -C "$DEST/nba-picks.git" remote update --prune
else
  mkdir -p "$DEST"
  git clone --mirror "$REPO" "$DEST/nba-picks.git"
fi
git -C "$DEST/nba-picks.git" bundle create "$DEST/nba-picks-$(date +%Y%m%d).bundle" --all
echo "Backed up to $DEST"
