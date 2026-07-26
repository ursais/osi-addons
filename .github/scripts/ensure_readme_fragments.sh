#!/bin/sh
# Ensure OCA-style readme/ fragments exist for each given addon.
# Usage: ensure_readme_fragments.sh addon1 [addon2 ...]
set -eu

python_summary() {
  addon="$1"
  python3 - <<PY
import ast
from pathlib import Path
manifest = Path("${addon}") / "__manifest__.py"
if not manifest.exists():
    manifest = Path("${addon}") / "__openerp__.py"
data = ast.literal_eval(manifest.read_text())
print(data.get("summary") or data.get("name") or "${addon}")
PY
}

for addon in "$@"; do
  [ -d "${addon}" ] || continue
  mkdir -p "${addon}/readme"
  summary="$(python_summary "${addon}")"

  if [ ! -f "${addon}/readme/DESCRIPTION.md" ]; then
    printf '%s\n' "${summary}" >"${addon}/readme/DESCRIPTION.md"
    echo "Created ${addon}/readme/DESCRIPTION.md"
  fi
  if [ ! -f "${addon}/readme/USAGE.md" ]; then
    cat >"${addon}/readme/USAGE.md" <<EOF
To use this module, you need to:

1. Go to the related application menu.
2. Review the new features provided by this module.
EOF
    echo "Created ${addon}/readme/USAGE.md"
  fi
  if [ ! -f "${addon}/readme/CONFIGURE.md" ]; then
    cat >"${addon}/readme/CONFIGURE.md" <<'EOF'
No special configuration is required beyond installing the module and assigning
the relevant security groups to users.
EOF
    echo "Created ${addon}/readme/CONFIGURE.md"
  fi
  if [ ! -f "${addon}/readme/CONTRIBUTORS.md" ]; then
    cat >"${addon}/readme/CONTRIBUTORS.md" <<'EOF'
- [Open Source Integrators](https://www.opensourceintegrators.com)
- [Gray Matter Logic](https://www.graymatterlogic.com):
  - Maxime Chambreuil <maxime.chambreuil@graymatterlogic.com>
EOF
    echo "Created ${addon}/readme/CONTRIBUTORS.md"
  fi
  if [ ! -f "${addon}/readme/CREDITS.md" ]; then
    cat >"${addon}/readme/CREDITS.md" <<'EOF'
The development of this module was originally supported by Open Source Integrators.
EOF
    echo "Created ${addon}/readme/CREDITS.md"
  fi
done
