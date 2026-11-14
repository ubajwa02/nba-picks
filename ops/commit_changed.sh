#!/usr/bin/env bash
# Commit only the files this job changed, on top of the latest branch tip.
# Usage: ops/commit_changed.sh "<message>" <path>...
# A file the job did not touch is never copied back, so concurrent edits elsewhere
# (data/manual/*.csv, research decisions, other backfill seasons) are not overwritten.
set -u
msg="$1"; shift
git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"
git add -A -- "$@" 2>/dev/null
git diff --cached --name-only --diff-filter=ACMR > /tmp/changed.txt
[ -s /tmp/changed.txt ] || { echo "nothing to commit"; exit 0; }
rm -rf /tmp/out && mkdir -p /tmp/out
while IFS= read -r f; do mkdir -p "/tmp/out/$(dirname "$f")"; cp -a "$f" "/tmp/out/$f"; done < /tmp/changed.txt
for i in 1 2 3 4 5 6; do
  git fetch -q origin "${GITHUB_REF_NAME:-main}" && git reset -q --hard "origin/${GITHUB_REF_NAME:-main}"
  while IFS= read -r f; do mkdir -p "$(dirname "$f")"; cp -a "/tmp/out/$f" "$f"; git add -- "$f"; done < /tmp/changed.txt
  git diff --cached --quiet && { echo "nothing to commit"; exit 0; }
  git commit -qm "$msg [skip ci]"
  git push -q origin "HEAD:${GITHUB_REF_NAME:-main}" && { echo "pushed $(wc -l < /tmp/changed.txt) files"; exit 0; }
  sleep $((i*5))
done
echo "::error::could not push state"; exit 1
