#!/bin/sh
# List installable addon directories touched between two git refs.
# Usage: changed_addons.sh [base_sha] [head_sha]
# If base is empty/missing/zero, list all addons that have pyproject.toml.
set -eu

base="${1:-}"
head_ref="${2:-HEAD}"

is_addon() {
  dir="$1"
  [ -f "${dir}/__manifest__.py" ] || [ -f "${dir}/__openerp__.py" ]
}

list_all_addons() {
  find . -mindepth 2 -maxdepth 2 -name pyproject.toml -printf '%h\n' \
    | sed 's|^\./||' \
    | sort -u \
    | while IFS= read -r dir; do
        if is_addon "${dir}"; then
          echo "${dir}"
        fi
      done
}

# Empty or all-zero SHA (new branch / no previous tip)
if [ -z "${base}" ] || printf '%s' "${base}" | grep -Eq '^0+$'; then
  list_all_addons
  exit 0
fi

git diff --name-only "${base}" "${head_ref}" \
  | awk -F/ 'NF >= 2 { print $1 }' \
  | sort -u \
  | while IFS= read -r dir; do
      if is_addon "${dir}" && [ -f "${dir}/pyproject.toml" ]; then
        echo "${dir}"
      fi
    done
