#!/usr/bin/env python3
"""Read-only validation for the collection, using Python 3.10+.

YAML support is deliberately limited to this repository's single-line scalar
frontmatter and two-level openai.yaml mappings. This is not a general YAML parser.
No dependency is installed and no skill code is executed.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import stat
import sys
from urllib.parse import unquote, urlsplit

EXPECTED_SKILLS = (
    "ml-foundations", "dl-foundations", "ml-math-foundations",
    "ml-dl-workflows", "ml-dl-study-coach", "understanding-deep-learning",
    "d2l-english-reference", "probabilistic-ml-intro",
    "probabilistic-ml-advanced", "statistical-learning-theory",
    "deep-learning-theory",
)
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py", ".txt"}
LINK = re.compile(r"!?\[[^\]\n]*\]\((<[^>\n]+>|[^)\n]+)\)")
PRIVATE_PATTERNS = (
    ("machine drive path", re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]")),
    ("local file URL", re.compile(r"file://", re.I)),
    ("absolute user home path", re.compile(r"(?<![:/\w])/(?:home|Users)/[^/\s]+(?:/|$)")),
    ("private source excerpt field", re.compile(
        r'["\x27](?:displayed_excerpt|source_excerpt|raw_text|full_text|source_text)["\x27]\s*:')),
    ("credential-like value", re.compile(
        r"github_pat_[A-Za-z0-9_]{15,}|gh[pousr]_[A-Za-z0-9]{20,}|"
        r"sk-[A-Za-z0-9_-]{24,}|-----BEGIN [A-Z ]*PRIVATE KEY-----")),
)
PLACEHOLDERS = re.compile(
    r"\b(?:TODO|FIXME|TBD|REPLACE_ME|YOUR_[A-Z_]+)\b|"
    r"\{\{[^}\n]+\}\}|https?://(?:www\.)?example\.(?:com|org|net)(?:[/\s]|$)|"
    r"<(?:YOUR|your|填写|替换|待填|项目路径|文件路径|目标路径|参数值)[^>\n]*>"
)

def absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))

def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False

def reject_link_path(path: Path) -> None:
    """Check existing ancestors without following symlinks or Windows junctions."""
    path = absolute(path)
    for component in reversed((path, *path.parents)):
        try:
            info = component.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or (
            getattr(info, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        ):
            raise ValueError(f"Link/reparse path is not allowed: {component}")
        if component != path and not stat.S_ISDIR(info.st_mode):
            raise ValueError(f"Ancestor is not a directory: {component}")

def regular_files(root: Path) -> list[Path]:
    reject_link_path(root)
    if not root.is_dir():
        raise ValueError(f"Directory does not exist: {root}")
    files = []
    for current, dirs, names in os.walk(root, followlinks=False):
        for name in sorted(dirs + names):
            path = Path(current, name)
            reject_link_path(path)
            info = path.lstat()
            if stat.S_ISREG(info.st_mode):
                files.append(path)
            elif not stat.S_ISDIR(info.st_mode):
                raise ValueError(f"Special file is not allowed: {path}")
    return sorted(files)

def scalar(raw: str) -> str | bool:
    raw = raw.strip()
    if not raw or raw[0] in "|>&*!{[":
        raise ValueError("Expected a nonempty single-line YAML scalar")
    if raw.startswith('"'):
        value = json.loads(raw)
        if not isinstance(value, str):
            raise ValueError("Expected a quoted string")
        return value
    if raw.startswith("'"):
        if not raw.endswith("'") or len(raw) < 2:
            raise ValueError("Unclosed YAML single-quoted string")
        return raw[1:-1].replace("''", "'")
    if " #" in raw or "\t" in raw:
        raise ValueError("Inline comments/tabs are unsupported in YAML scalars")
    if re.search(r":(?:\s|$)", raw):
        raise ValueError("Unsupported unquoted YAML scalar: quote values containing a mapping colon")
    if raw in ("true", "false"):
        return raw == "true"
    return raw

def simple_yaml(text: str, nested: bool = False) -> dict:
    result, section = {}, None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line:
            raise ValueError("Tabs are unsupported in this YAML subset")
        match = re.fullmatch(r"( *)([A-Za-z_][A-Za-z0-9_-]*):(?: +(.*))?", line)
        if not match:
            raise ValueError(f"Unsupported YAML syntax: {line[:90]}")
        indent, key, raw = match.groups()
        if not indent:
            if key in result:
                raise ValueError(f"Duplicate YAML key: {key}")
            if raw is None and nested:
                result[key], section = {}, key
            else:
                result[key], section = scalar(raw or ""), None
        elif nested and indent == "  " and section is not None:
            if key in result[section]:
                raise ValueError(f"Duplicate YAML key: {section}.{key}")
            result[section][key] = scalar(raw or "")
        else:
            raise ValueError("Only simple two-level YAML mappings are supported")
    return result

def frontmatter(text: str) -> dict:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("Unclosed SKILL.md frontmatter") from exc
    return simple_yaml("\n".join(lines[1:end]))

def heading_anchors(text: str) -> set[str]:
    anchors = set(re.findall(r'<a\s+(?:name|id)=["\x27]([^"\x27]+)', text))
    seen = {}
    for line in text.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)(?:\s+#+)?$", line)
        if match:
            slug = re.sub(r"[^\w\- ]", "", match.group(1).lower()).replace(" ", "-")
            index = seen.get(slug, 0)
            seen[slug] = index + 1
            anchors.add(slug if index == 0 else f"{slug}-{index}")
    return anchors

def check_markdown_links(path: Path, text: str, boundary: Path) -> list[str]:
    errors = []
    for match in LINK.finditer(text):
        raw = match.group(1).strip()
        target = raw[1:-1] if raw.startswith("<") else raw.split(' "', 1)[0].strip()
        parts = urlsplit(target)
        if parts.scheme in {"http", "https", "mailto"}:
            continue
        if parts.scheme or parts.netloc or target.startswith(("/", "\\")):
            errors.append(f"{path}: nonportable link {target!r}")
            continue
        file_part = unquote(parts.path).replace("\\", "/")
        linked = absolute(path.parent / file_part) if file_part else path
        if not is_within(linked, boundary):
            errors.append(f"{path}: link escapes skills directory: {target!r}")
            continue
        try:
            reject_link_path(linked)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not linked.exists():
            errors.append(f"{path}: missing link target {target!r}")
        elif parts.fragment and linked.suffix.lower() == ".md":
            anchors = heading_anchors(linked.read_text(encoding="utf-8-sig"))
            if unquote(parts.fragment) not in anchors:
                errors.append(f"{path}: missing Markdown anchor {target!r}")
    return errors

def check_progress_template(path: Path, data: object) -> list[str]:
    """Accept the two documented blank-profile/topic schemas."""
    if not isinstance(data, dict):
        return [f"{path}: progress template must be an object"]
    errors = []
    if "learner_profile" in data:
        profile = data["learner_profile"]
        if not isinstance(profile, dict):
            errors.append(f"{path}: learner_profile must contain unknown initial values")
        else:
            for key, value in profile.items():
                if value is not None and value not in ("unknown", "not_assessed", ""):
                    errors.append(f"{path}: learner_profile.{key} is not unknown")
    elif "learner" not in data:
        errors.append(f"{path}: an unknown learner or learner_profile is required")
    for key in ("learner", "goal", "current_topic", "updated_at"):
        if key in data and data[key] is not None:
            errors.append(f"{path}: template {key} must be null")
    if data.get("status") != "not_assessed":
        errors.append(f"{path}: template status must be not_assessed")
    if data.get("evidence") != [] or data.get("lessons", {}) != {}:
        errors.append(f"{path}: template must not contain learning evidence or lessons")
    topics = data.get("topics", {})
    if not isinstance(topics, dict):
        errors.append(f"{path}: topics must be an object")
    else:
        for topic, record in topics.items():
            if (not isinstance(record, dict)
                    or record.get("status") != "not_assessed"
                    or record.get("evidence_ids") != []):
                errors.append(f"{path}: topic {topic} must be unassessed with no evidence")
    return errors

def validate_skills(skills_root: Path) -> list[str]:
    skills_root = absolute(skills_root)
    errors = []
    try:
        files = regular_files(skills_root)
    except (ValueError, OSError) as exc:
        return [str(exc)]
    actual = {p.name for p in skills_root.iterdir() if p.is_dir()}
    missing = set(EXPECTED_SKILLS) - actual
    unexpected = actual - set(EXPECTED_SKILLS)
    if missing:
        errors.append("Missing skills: " + ", ".join(sorted(missing)))
    if unexpected:
        errors.append("Unexpected skill directories: " + ", ".join(sorted(unexpected)))
    for name in EXPECTED_SKILLS:
        path = skills_root / name / "SKILL.md"
        config = skills_root / name / "agents" / "openai.yaml"
        if not path.is_file():
            if name not in missing:
                errors.append(f"Missing SKILL.md: {name}")
            continue
        try:
            data = frontmatter(path.read_text(encoding="utf-8-sig"))
            if data.get("name") != name:
                errors.append(f"{path}: frontmatter name must equal {name!r}")
            description = data.get("description")
            if not isinstance(description, str) or not description.strip() or len(description) > 1024:
                errors.append(f"{path}: description must contain 1–1024 characters")
            if isinstance(description, str) and any(c in description for c in "<>"):
                errors.append(f"{path}: description cannot contain angle brackets")
        except (ValueError, OSError) as exc:
            errors.append(f"{path}: {exc}")
        if not config.is_file():
            errors.append(f"Missing agents/openai.yaml: {name}")
            continue
        try:
            data = simple_yaml(config.read_text(encoding="utf-8-sig"), nested=True)
            interface = data.get("interface")
            if not isinstance(interface, dict):
                raise ValueError("interface mapping is required")
            display = interface.get("display_name")
            short = interface.get("short_description")
            prompt = interface.get("default_prompt")
            if not isinstance(display, str) or not display.strip():
                errors.append(f"{config}: display_name is required")
            if not isinstance(short, str) or not 25 <= len(short) <= 64:
                errors.append(f"{config}: short_description must contain 25–64 characters")
            if not isinstance(prompt, str) or not re.search(
                re.escape("$" + name) + r"(?![A-Za-z0-9_-])", prompt
            ):
                errors.append(f"{config}: default_prompt must mention $" + name)
        except (ValueError, OSError) as exc:
            errors.append(f"{config}: {exc}")
    for path in files:
        if path.suffix.lower() not in TEXT_SUFFIXES:
            errors.append(f"{path}: unexpected non-text skill artifact")
            continue
        if path.name in {"progress.json", "reading-log.json", "reading-evidence.json", "validation.json"}:
            errors.append(f"{path}: private progress or production record is not distributable")
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (UnicodeError, OSError) as exc:
            errors.append(f"{path}: cannot read UTF-8 text: {exc}")
            continue
        for label, pattern in PRIVATE_PATTERNS:
            if pattern.search(text):
                errors.append(f"{path}: {label}")
        if PLACEHOLDERS.search(text):
            errors.append(f"{path}: unfinished placeholder")
        if path.suffix.lower() == ".md":
            errors.extend(check_markdown_links(path, text, skills_root))
        if path.suffix.lower() == ".json":
            try:
                data = json.loads(text)
                if path.name == "progress-template.json":
                    errors.extend(check_progress_template(path, data))
            except ValueError as exc:
                errors.append(f"{path}: invalid JSON: {exc}")
    return errors

def validate_plugin(repo_root: Path) -> list[str]:
    errors, manifests = [], []
    for relative in ("plugin.json", ".codex-plugin/plugin.json"):
        path = repo_root / relative
        if not path.is_file():
            errors.append(f"Missing plugin manifest: {path} (use --skills-only while authoring)")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            for key in ("name", "version", "description"):
                if not isinstance(data.get(key), str) or not data[key].strip():
                    errors.append(f"{path}: nonempty {key} is required")
            manifests.append((path, data))
            skills = data.get("skills")
            if isinstance(skills, str):
                destination = absolute(repo_root / skills)
                if not is_within(destination, repo_root) or not destination.is_dir():
                    errors.append(f"{path}: skills path must be an existing directory inside the repository")
        except (ValueError, OSError, AttributeError) as exc:
            errors.append(f"{path}: {exc}")
    if len(manifests) == 2:
        for key in ("name", "version"):
            if manifests[0][1].get(key) != manifests[1][1].get(key):
                errors.append(f"Plugin manifests disagree on {key}")
    return errors

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="Repository root (default: parent of scripts)")
    parser.add_argument("--skills-only", action="store_true",
                        help="Validate skills without requiring plugin manifests")
    args = parser.parse_args(argv)
    root = absolute(args.root)
    errors = validate_skills(root / "skills")
    if not args.skills_only:
        errors.extend(validate_plugin(root))
    if errors:
        for error in errors:
            print("ERROR: " + error, file=sys.stderr)
        print(f"Validation failed: {len(errors)} error(s).", file=sys.stderr)
        return 1
    print(f"Validated {len(EXPECTED_SKILLS)} skills: files, links, metadata and learner template.")
    print("YAML checks use the documented single-line/two-level scalar subset.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

