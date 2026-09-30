#!/usr/bin/env bash
# Install the design agent into a product repo.
#   ./install.sh /path/to/your-app [--with-baseline]
# --with-baseline also copies the Baseline design system (manifest, CLAUDE.md,
# empty design index) where the repo doesn't have them yet, as a starting point.
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="${1:?usage: ./install.sh /path/to/your-app [--with-baseline]}"
DEST="$(cd "$DEST" && pwd)"

mkdir -p "$DEST/.claude/skills" "$DEST/.claude/design-agent" "$DEST/.claude/agents"
rm -rf "$DEST/.claude/skills/design-agent"
cp -r "$SRC/skills/design-agent" "$DEST/.claude/skills/design-agent"
cp "$SRC/HARNESS.md" "$DEST/.claude/skills/design-agent/reference/HARNESS.md"
rm -rf "$DEST/.claude/design-agent/tools" "$DEST/.claude/design-agent/schemas"
cp -r "$SRC/tools" "$DEST/.claude/design-agent/tools" && rm -rf "$DEST/.claude/design-agent/tools/__pycache__"
cp -r "$SRC/schemas" "$DEST/.claude/design-agent/schemas"
mkdir -p "$DEST/.claude/design-agent/templates" && cp "$SRC/templates/page-brief.md" "$DEST/.claude/design-agent/templates/"
cp "$SRC/personas/claude-code/"*.md "$DEST/.claude/agents/"
echo "✓ skill → .claude/skills/design-agent   tools → .claude/design-agent/tools   agents → .claude/agents"

if [ ! -f "$DEST/.claude/settings.json" ]; then
  cp "$SRC/templates/claude-settings.json" "$DEST/.claude/settings.json"
  echo "✓ hooks → .claude/settings.json"
else
  echo "! .claude/settings.json exists: merge the \"hooks\" from $SRC/templates/claude-settings.json into it"
fi

if [ "${2:-}" = "--with-baseline" ]; then
  for f in design-system-manifest.yaml CLAUDE.md design-index.yaml; do
    if [ ! -f "$DEST/$f" ]; then cp "$SRC/standard/$f" "$DEST/$f"; echo "✓ $f (Baseline: replace its values with yours)"; fi
  done
  mkdir -p "$DEST/brand"
  for f in "$SRC/standard/brand/"*.yaml; do
    [ -f "$DEST/brand/$(basename "$f")" ] || { cp "$f" "$DEST/brand/"; echo "✓ brand/$(basename "$f") (Atari Brand Guidelines V1.1)"; }
  done
fi
for f in design-system-manifest.yaml CLAUDE.md; do
  [ -f "$DEST/$f" ] || echo "! No $f yet: start from $SRC/standard/ (or rerun with --with-baseline)"
done
grep -qs "design-context-seen" "$DEST/.gitignore" || printf '\n.claude/.design-context-seen/\n.design-agent/\n' >> "$DEST/.gitignore"
python3 -c "import yaml, jsonschema" 2>/dev/null || echo "! Needs: pip install pyyaml jsonschema"
command -v node >/dev/null && (npm ls -g playwright >/dev/null 2>&1 || echo "! For screenshots: npm i -g playwright") || echo "! For screenshots: install Node.js and 'npm i -g playwright'"
echo "Next: python3 .claude/design-agent/tools/check_compatibility.py design-system-manifest.yaml"
