#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

BASE_PATH="${BASE_PATH:-/maxcode}"
export BASE_PATH
export NEXT_TELEMETRY_DISABLED=1

if [ ! -d docs/node_modules ]; then
  (cd docs && npm ci --no-audit --no-fund)
fi
(cd docs && npm run build)

rm -rf dist
mkdir -p dist
rsync -a \
  --exclude docs \
  --exclude dist \
  --exclude README.md \
  --exclude AGENTS.md \
  --exclude DESIGN.md \
  --exclude .gitignore \
  --exclude build.sh \
  ./ dist/
cp -r docs/out/. dist/
touch dist/.nojekyll

printf 'built static site + Fumadocs docs at base path %s\n' "$BASE_PATH"
