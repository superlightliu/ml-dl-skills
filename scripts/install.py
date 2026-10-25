#!/usr/bin/env python3
"""Install all eleven skills with Python 3.10+; no downloads or global changes.

--dest names the directory containing the sibling skill folders. Without --apply
this command only reads files. Identical installed skills are skipped; a conflict
aborts before writing. Source and destination links/reparse points are refused.

Files are checked in staging inside --dest, then committed one skill at a time.
A commit failure returns nonzero and reports complete/incomplete folders: this
is not a whole-batch atomic transaction. No skill code is executed.
"""
from __future__ import annotations
import sys

# Keep direct invocation read-only too, without requiring Python's -B flag.
sys.dont_write_bytecode = True

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import uuid
from validate import (
    EXPECTED_SKILLS, absolute, is_within, regular_files, reject_link_path,
    validate_skills,
)

class InstallError(Exception):
    pass

def manifest(root: Path) -> dict[str, str]:
    result = {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in regular_files(root)
    }
    for current, dirs, _ in os.walk(root, followlinks=False):
        for name in dirs:
            result[(Path(current) / name).relative_to(root).as_posix() + "/"] = "directory"
    return result

def plan_install(source: Path, destination: Path) -> tuple[dict, list[str], list[str]]:
    source, destination = absolute(source), absolute(destination)
    reject_link_path(source)
    reject_link_path(destination)
    if is_within(destination, source) or is_within(source, destination):
        raise InstallError("Source and destination must not overlap or contain one another.")
    if destination.exists() and not destination.is_dir():
        raise InstallError(f"Destination is not a directory: {destination}")
    errors = validate_skills(source)
    if errors:
        raise InstallError("Source validation failed:\n" + "\n".join(errors))
    snapshots = {name: manifest(source / name) for name in EXPECTED_SKILLS}
    install, skip, conflicts = [], [], []
    for name in EXPECTED_SKILLS:
        target = destination / name
        reject_link_path(target)
        if target.exists():
            if not target.is_dir() or manifest(target) != snapshots[name]:
                conflicts.append(name)
            else:
                skip.append(name)
        else:
            install.append(name)
    if conflicts:
        raise InstallError("Conflicting destination skills; nothing was changed: " + ", ".join(conflicts))
    return snapshots, install, skip

def commit_staged_skill(staged: Path, target: Path) -> None:
    """Reserve the final name exclusively, never replacing an existing folder."""
    reject_link_path(target.parent)
    target.mkdir(exist_ok=False)
    for item in sorted(staged.iterdir()):
        destination = target / item.name
        reject_link_path(target)
        if destination.exists() or destination.is_symlink():
            raise InstallError(f"Concurrent destination change: {destination}")
        item.rename(destination)
    staged.rmdir()

def remove_own_stage(stage: Path, destination: Path) -> None:
    if stage.parent != destination or not stage.name.startswith(".ml-dl-skills-stage-"):
        raise InstallError("Refusing to clean an unexpected staging path.")
    reject_link_path(stage)
    if stage.exists():
        shutil.rmtree(stage)

def install_collection(source: Path, destination: Path, apply: bool = False) -> dict:
    source, destination = absolute(source), absolute(destination)
    snapshots, install, skip = plan_install(source, destination)
    result = {"mode": "apply" if apply else "dry-run", "install": install, "skip": skip}
    if not apply or not install:
        return result
    reject_link_path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    reject_link_path(destination)
    lock = destination / ".ml-dl-skills-install.lock"
    lock_fd = None
    stage = destination / (".ml-dl-skills-stage-" + uuid.uuid4().hex)
    stage_created, committed, current = False, [], None
    try:
        lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.write(lock_fd, (str(os.getpid()) + "\n").encode("ascii"))
        stage.mkdir(exist_ok=False)
        stage_created = True
        for name in install:
            reject_link_path(source / name)
            # Preserve links introduced after preflight, so the staged validator
            # rejects them without following them into unrelated directories.
            shutil.copytree(source / name, stage / name, symlinks=True)
            if manifest(stage / name) != snapshots[name]:
                raise InstallError(f"Staged files differ from source preflight: {name}")
        fresh, fresh_install, fresh_skip = plan_install(source, destination)
        if fresh != snapshots or fresh_install != install or fresh_skip != skip:
            raise InstallError("Source/destination changed during staging; no skills committed.")
        for name in install:
            current = name
            commit_staged_skill(stage / name, destination / name)
            if manifest(destination / name) != snapshots[name]:
                raise InstallError(f"Post-copy verification failed: {name}")
            committed.append(name)
            current = None
        result["installed"] = committed
        return result
    except BaseException as exc:
        message = "Interrupted" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else str(exc)
        incomplete = current if current and (destination / current).exists() else "none"
        raise InstallError(
            f"Installation failed: {message}\n"
            f"Completed in this run: {', '.join(committed) or 'none'}\n"
            f"Possibly incomplete folder: {incomplete}\n"
            "No pre-existing skill folder was intentionally overwritten. "
            "Inspect the reported folder before retrying."
        ) from exc
    finally:
        if stage_created:
            try:
                remove_own_stage(stage, destination)
            except (OSError, ValueError, InstallError) as exc:
                print(f"WARNING: inspect staging folder {stage}: {exc}", file=sys.stderr)
        if lock_fd is not None:
            os.close(lock_fd)
            try:
                reject_link_path(lock)
                lock.unlink()
            except (OSError, ValueError) as exc:
                print(f"WARNING: inspect install lock {lock}: {exc}", file=sys.stderr)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", required=True, type=Path,
                        help="Explicit target skills directory; no default user folder")
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1] / "skills",
                        help="Source skills directory (default: checkout's skills)")
    parser.add_argument("--apply", action="store_true",
                        help="Copy after preflight; without this flag only preview")
    args = parser.parse_args(argv)
    try:
        result = install_collection(args.source, args.dest, args.apply)
    except (InstallError, ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("Mode: " + result["mode"])
    print(("Installed: " if args.apply else "Would install: ") + (", ".join(result["install"]) or "none"))
    print("Identical, skipped: " + (", ".join(result["skip"]) or "none"))
    if not args.apply:
        print("Dry run only: no files or directories created. Add --apply to install.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

