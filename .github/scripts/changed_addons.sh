#!/usr/bin/env bash
# List installable addon directories touched between two git refs.
# Usage: changed_addons.sh [base_sha] [head_sha]
# If base is empty/missing/zero, list all addons that have pyproject.toml.
set -euo pipefail

base="${1:-}"
head_ref="${2:-HEAD}"

is_addon() {
  local dir="$1"
  [[ -f "${dir}/__manifest__.py" || -f "${dir}/__openerp__.py" ]]
}

list_all_addons() {
  find . -mindepth 2 -maxdepth 2 -name pyproject.toml -printf '%h\n' \
    | sed 's|^\./||' \
    | sort -u \
    | while read -r dir; do
        if is_addon "${dir}"; then
          echo "${dir}"
        fi
      done
}

if [[ -z "${base}" || "${base}" =~ ^0+$ ]]; then
  list_all_addons
  exit 0
fi

git diff --name-only "${base}" "${head_ref}" \
  | awk -F/ 'NF >= 2 { print $1 }' \
  | sort -u \
  | while read -r dir; do
      if is_addon "${dir}" && [[ -f "${dir}/pyproject.toml" ]]; then
        echo "${dir}"
      fi
    done
