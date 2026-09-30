#!/usr/bin/env python3
# Copyright (c) ACSONE SA/NV 2018 (bump rules)
# Copyright (c) 2026 Gray Matter Logic
# License MIT (http://opensource.org/licenses/MIT).
"""Bump addon manifest versions the way ocabot does on merge.

Version format is ``{series}.{major}.{minor}.{patch}`` (for example
``19.0.1.1.0``). ``major`` / ``minor`` / ``patch`` follow
``oca_github_bot.manifest.bump_version``. ``nobump`` leaves versions alone.

The bump mode is the last ``/ocabot merge <mode>`` comment on the pull
request. Without that comment, the leading tag in the title is used:

* ``[FIX]`` and ``[REF]`` → patch
* ``[IMP]`` → minor
* ``[REM]`` → major
* ``[ADD]``, ``[MIG]``, ``[UPD]``, ``[BOT]`` → nobump
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

VERSION_RE = re.compile(
    r"^(?P<series>\d+\.\d+)\.(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$"
)
MANIFEST_VERSION_RE = re.compile(
    r"(?P<pre>[\"']version[\"']\s*:\s*[\"'])(?P<version>[\d\.]+)(?P<post>[\"'])"
)
OCA_MERGE_RE = re.compile(
    r"(?i)/ocabot\s+merge\s+(major|minor|patch|nobump)\b"
)
TAG_RE = re.compile(r"\[([A-Za-z]+)\]")
MANIFEST_NAMES = ("__manifest__.py", "__openerp__.py")

# Tags that are not an explicit /ocabot merge comment.
TAG_TO_MODE = {
    "FIX": "patch",
    "REF": "patch",
    "IMP": "minor",
    "REM": "major",
    "ADD": "nobump",
    "MIG": "nobump",
    "UPD": "nobump",
    "BOT": "nobump",
}


def bump_version(version, mode):
    match = VERSION_RE.match(version)
    if not match:
        raise RuntimeError(f"{version} does not match the expected version pattern.")
    series = match.group("series")
    major = match.group("major")
    minor = match.group("minor")
    patch = match.group("patch")
    if mode == "major":
        major = int(major) + 1
        minor = 0
        patch = 0
    elif mode == "minor":
        minor = int(minor) + 1
        patch = 0
    elif mode == "patch":
        patch = int(patch) + 1
    elif mode == "nobump":
        return version
    else:
        raise RuntimeError(f"Unexpected bumpversion mode {mode}")
    return f"{series}.{major}.{minor}.{patch}"


def resolve_bump_mode(title, comments):
    """Return major, minor, patch, or nobump."""
    found = OCA_MERGE_RE.findall(comments or "")
    if found:
        return found[-1].lower()
    for tag in TAG_RE.findall(title or ""):
        mode = TAG_TO_MODE.get(tag.upper())
        if mode:
            return mode
    raise RuntimeError(
        "Cannot decide the version bump. Comment `/ocabot merge patch`, "
        "`minor`, `major`, or `nobump`, or start the title with "
        "[FIX], [IMP], [REF], [REM], [ADD], [MIG], [UPD], or [BOT]. "
        f"Title was: {title!r}"
    )


def manifest_path(addon_dir: Path):
    for name in MANIFEST_NAMES:
        path = addon_dir / name
        if path.is_file():
            return path
    return None


def changed_addons(repo: Path, base: str, head: str):
    diff = subprocess.check_output(
        ["git", "diff", "--name-only", base, head],
        cwd=repo,
        text=True,
    )
    addons = []
    seen = set()
    for line in diff.splitlines():
        parts = line.split("/")
        if len(parts) < 2 or parts[0] in seen:
            continue
        addon = parts[0]
        if manifest_path(repo / addon):
            seen.add(addon)
            addons.append(addon)
    return addons


def set_manifest_version(path: Path, version: str):
    text = path.read_text()
    new_text, count = MANIFEST_VERSION_RE.subn(
        lambda match: match.group("pre") + version + match.group("post"),
        text,
        count=1,
    )
    if count != 1:
        raise RuntimeError(f"Could not replace version in {path}")
    path.write_text(new_text)


def current_version(path: Path):
    match = MANIFEST_VERSION_RE.search(path.read_text())
    if not match:
        raise RuntimeError(f"No version key in {path}")
    return match.group("version")


def bump_addons(repo: Path, addons, mode, commit=True):
    if mode == "nobump" or not addons:
        return []
    bumped = []
    for addon in addons:
        path = manifest_path(repo / addon)
        old = current_version(path)
        new = bump_version(old, mode)
        set_manifest_version(path, new)
        bumped.append((addon, old, new, path))
        if commit:
            rel = path.relative_to(repo).as_posix()
            subprocess.check_call(["git", "add", "--", rel], cwd=repo)
            subprocess.check_call(
                [
                    "git",
                    "commit",
                    "-m",
                    f"[BOT] {addon} {new}",
                    "--",
                    rel,
                ],
                cwd=repo,
            )
    return bumped


def _self_test():
    assert bump_version("19.0.1.1.0", "patch") == "19.0.1.1.1"
    assert bump_version("19.0.1.1.1", "minor") == "19.0.1.2.0"
    assert bump_version("19.0.1.1.1", "major") == "19.0.2.0.0"
    assert bump_version("12.0.1.0.0", "major") == "12.0.2.0.0"
    assert resolve_bump_mode("[FIX] fieldservice_mobile: x", "") == "patch"
    assert resolve_bump_mode("[IMP] fieldservice_mobile: x", "") == "minor"
    assert resolve_bump_mode("[ADD] new_module: x", "") == "nobump"
    assert resolve_bump_mode("[MIG] addon: x", "") == "nobump"
    assert (
        resolve_bump_mode("[FIX] x", "ship it\n/ocabot merge minor\n") == "minor"
    )
    assert (
        resolve_bump_mode("[FIX] x", "/ocabot merge patch\n/ocabot merge nobump")
        == "nobump"
    )
    print("self-test ok")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--title")
    parser.add_argument("--comments", default="")
    parser.add_argument("--comments-file")
    parser.add_argument("--merge-sha")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--no-commit", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        _self_test()
        return 0
    if not args.title or not args.merge_sha:
        parser.error("--title and --merge-sha are required")
    comments = args.comments
    if args.comments_file:
        comments = Path(args.comments_file).read_text()
    mode = resolve_bump_mode(args.title, comments)
    print(f"Bump mode: {mode}")
    if mode == "nobump":
        print("nobump: manifest versions left unchanged")
        return 0
    repo = Path(args.repo).resolve()
    addons = changed_addons(repo, f"{args.merge_sha}^1", args.merge_sha)
    print(f"Changed addons: {addons or '(none)'}")
    bumped = bump_addons(repo, addons, mode, commit=not args.no_commit)
    for addon, old, new, _path in bumped:
        print(f"{addon}: {old} -> {new}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
