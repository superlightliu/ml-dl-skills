"""Behavioral tests for portable skill tools. Set ML_DL_SKILLS_TEST_ROOT first.

Run: python -B -m unittest discover -s tests -v
Fixtures are synthetic; no user's installed skill is read or modified.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest import mock

TEST_PARENT_VALUE = os.environ.get("ML_DL_SKILLS_TEST_ROOT")
if not TEST_PARENT_VALUE:
    raise RuntimeError("Set ML_DL_SKILLS_TEST_ROOT to an explicit disposable test directory.")
TEST_PARENT = Path(TEST_PARENT_VALUE).absolute()
TEST_PARENT.mkdir(parents=True, exist_ok=True)
for variable in ("TEMP", "TMP", "TMPDIR"):
    os.environ[variable] = str(TEST_PARENT)
import tempfile  # Environment is set before importing this module.

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import install
import validate

def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def snapshot(root: Path) -> dict:
    if not root.exists():
        return {}
    result = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_dir():
            result[relative + "/"] = "directory"
        else:
            result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result

def make_collection(root: Path) -> Path:
    skills = root / "skills"
    for index, name in enumerate(validate.EXPECTED_SKILLS):
        next_name = validate.EXPECTED_SKILLS[(index + 1) % len(validate.EXPECTED_SKILLS)]
        write(skills / name / "SKILL.md",
              f"---\nname: {name}\ndescription: Teach concepts and inspect assumptions on demand.\n---\n"
              f"# {name}\n\n[Another skill](../{next_name}/SKILL.md)\n\n"
              "[Official book](https://www.deeplearningbook.org/)\n\n"
              "[Local guide](references/guide.md#reading)\n\n"
              "Probabilistic Machine Learning: An Introduction\n"
              "Mathematics for Machine Learning\n")
        write(skills / name / "references" / "guide.md", "# Reading\n\nUse the learner's actual question.\n")
        write(skills / name / "agents" / "openai.yaml",
              'interface:\n'
              f'  display_name: "{name}"\n'
              '  short_description: "Read concepts and examine assumptions"\n'
              f'  default_prompt: "Use ${name} to explain this concept."\n')
    template = {
        "schema_version": 1,
        "learner_profile": {"statistics": None, "python": "unknown", "daily_minutes": None},
        "status": "not_assessed", "lessons": {}, "evidence": [],
        "current_week": None, "current_lesson": None,
    }
    write(skills / "ml-dl-study-coach" / "assets" / "progress-template.json",
          json.dumps(template, ensure_ascii=False, indent=2))
    plugin = {"name": "ml-dl-skills", "version": "1.0.0",
              "description": "Portable learning skills", "skills": "./skills/"}
    write(root / "plugin.json", json.dumps(plugin))
    write(root / ".codex-plugin" / "plugin.json", json.dumps(plugin))
    return skills

class CollectionToolTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix="skill-tool-test-", dir=TEST_PARENT)
        self.base = Path(self.workspace.name)
        self.repo = self.base / "repository"
        self.source = make_collection(self.repo)
        self.destination = self.base / "new-parent" / "installed-skills"

    def tearDown(self):
        self.workspace.cleanup()

    def cli(self, script: str, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / script), *map(str, args)],
            capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"},
            check=False,
        )

    def test_valid_collection_and_official_titles_urls(self):
        self.assertEqual([], validate.validate_skills(self.source))
        result = self.cli("validate.py", "--root", self.repo)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("11 skills", result.stdout)

    def test_default_dry_run_writes_nothing(self):
        before = snapshot(self.base)
        result = self.cli("install.py", "--source", self.source, "--dest", self.destination)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Dry run only", result.stdout)
        self.assertEqual(before, snapshot(self.base))
        self.assertFalse(self.destination.parent.exists())

    def test_plain_dry_run_does_not_create_bytecode(self):
        copied_scripts = self.repo / "scripts"
        copied_scripts.mkdir()
        for name in ("install.py", "validate.py"):
            shutil.copy2(SCRIPTS / name, copied_scripts / name)
        before = snapshot(self.base)
        child_env = {**os.environ, "PYTHONUTF8": "1"}
        child_env.pop("PYTHONDONTWRITEBYTECODE", None)
        child_env.pop("PYTHONPYCACHEPREFIX", None)
        result = subprocess.run(
            [sys.executable, str(copied_scripts / "install.py"),
             "--source", str(self.source), "--dest", str(self.destination)],
            capture_output=True, text=True, encoding="utf-8", env=child_env,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Dry run only", result.stdout)
        self.assertEqual(before, snapshot(self.base))
        self.assertFalse(self.destination.parent.exists())

    def test_apply_installs_all_hashes_and_second_apply_skips(self):
        before = snapshot(self.source)
        result = install.install_collection(self.source, self.destination, apply=True)
        self.assertEqual(11, len(result["installed"]))
        self.assertEqual(before, snapshot(self.destination))
        second = install.install_collection(self.source, self.destination, apply=True)
        self.assertEqual([], second["install"])
        self.assertEqual(set(validate.EXPECTED_SKILLS), set(second["skip"]))
        self.assertEqual(before, snapshot(self.destination))
        self.assertEqual(before, snapshot(self.source))
        self.assertEqual([], list(self.destination.glob(".ml-dl-skills-*")))

    def test_conflict_stops_entire_batch_without_changes(self):
        self.destination.mkdir(parents=True)
        first = validate.EXPECTED_SKILLS[0]
        shutil.copytree(self.source / first, self.destination / first)
        write(self.destination / first / "SKILL.md", "User-owned content, keep it.\n")
        before = snapshot(self.destination)
        source_before = snapshot(self.source)
        result = self.cli("install.py", "--source", self.source,
                          "--dest", self.destination, "--apply")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("Conflicting", result.stderr)
        self.assertEqual(before, snapshot(self.destination))
        self.assertEqual(source_before, snapshot(self.source))
        self.assertFalse((self.destination / validate.EXPECTED_SKILLS[-1]).exists())

    def test_extra_empty_directory_is_a_conflict(self):
        install.install_collection(self.source, self.destination, apply=True)
        (self.destination / validate.EXPECTED_SKILLS[0] / "user-empty-folder").mkdir()
        before = snapshot(self.destination)
        with self.assertRaisesRegex(install.InstallError, "Conflicting"):
            install.install_collection(self.source, self.destination, apply=True)
        self.assertEqual(before, snapshot(self.destination))

    def test_empty_existing_skill_folder_is_not_overwritten(self):
        target = self.destination / validate.EXPECTED_SKILLS[0]
        target.mkdir(parents=True)
        with self.assertRaisesRegex(install.InstallError, "Conflicting"):
            install.install_collection(self.source, self.destination, apply=True)
        self.assertEqual([], list(target.iterdir()))

    def test_source_and_destination_overlap_are_rejected(self):
        before = snapshot(self.source)
        for destination in (self.source, self.source / "new-target", self.repo):
            with self.subTest(destination=destination):
                with self.assertRaisesRegex(install.InstallError, "overlap"):
                    install.install_collection(self.source, destination, apply=True)
        self.assertEqual(before, snapshot(self.source))

    def test_staging_failure_never_commits_skills(self):
        source_before = snapshot(self.source)
        with mock.patch.object(install.shutil, "copytree", side_effect=OSError("simulated disk full")):
            with self.assertRaisesRegex(install.InstallError, "Completed in this run: none"):
                install.install_collection(self.source, self.destination, apply=True)
        self.assertEqual({}, snapshot(self.destination))
        self.assertEqual(source_before, snapshot(self.source))

    def test_commit_failure_reports_partial_without_false_success(self):
        original = install.commit_staged_skill
        count = 0
        def fail_after_one(staged, target):
            nonlocal count
            count += 1
            if count == 2:
                target.mkdir()
                raise OSError("simulated interruption after reservation")
            return original(staged, target)
        with mock.patch.object(install, "commit_staged_skill", side_effect=fail_after_one):
            with self.assertRaisesRegex(install.InstallError, "Possibly incomplete folder: dl-foundations"):
                install.install_collection(self.source, self.destination, apply=True)
        self.assertTrue((self.destination / "ml-foundations" / "SKILL.md").is_file())
        self.assertEqual([], list((self.destination / "dl-foundations").iterdir()))
        self.assertFalse((self.destination / "ml-math-foundations").exists())
        self.assertEqual([], list(self.destination.glob(".ml-dl-skills-*")))

    def test_missing_skill_is_caught_before_install_writes(self):
        shutil.rmtree(self.source / validate.EXPECTED_SKILLS[-1])
        self.assertTrue(any("Missing skills" in e for e in validate.validate_skills(self.source)))
        with self.assertRaisesRegex(install.InstallError, "Source validation failed"):
            install.install_collection(self.source, self.destination, apply=True)
        self.assertFalse(self.destination.parent.exists())

    def test_missing_escaping_and_fragment_links(self):
        file = self.source / "ml-foundations" / "references" / "guide.md"
        for content, expected in (
            ("[missing](missing.md)", "missing link target"),
            ("[escape](../../../../outside.md)", "escapes skills"),
            ("[anchor](../SKILL.md#nonexistent)", "missing Markdown anchor"),
        ):
            with self.subTest(content=content):
                write(file, content)
                errors = validate.validate_skills(self.source)
                self.assertTrue(any(expected in error for error in errors), errors)
        write(file, "# Reading\n")

    def test_nonempty_learner_profile_and_evidence_are_rejected(self):
        file = self.source / "ml-dl-study-coach" / "assets" / "progress-template.json"
        template = json.loads(file.read_text(encoding="utf-8"))
        template["learner_profile"]["daily_minutes"] = [60, 120]
        template["evidence"] = [{"answer": "personal answer"}]
        write(file, json.dumps(template))
        errors = validate.validate_skills(self.source)
        self.assertTrue(any("is not unknown" in e for e in errors))
        self.assertTrue(any("must not contain learning evidence" in e for e in errors))

    def test_blank_learner_and_topic_schema_is_valid(self):
        file = self.source / "ml-dl-study-coach" / "assets" / "progress-template.json"
        template = {
            "schema_version": 1, "learner": None, "goal": None,
            "current_topic": None, "status": "not_assessed", "evidence": [],
            "topics": {"linear_models": {"status": "not_assessed", "evidence_ids": []}},
            "updated_at": None,
        }
        write(file, json.dumps(template))
        self.assertEqual([], validate.validate_skills(self.source))
        template["topics"]["linear_models"]["status"] = "passed"
        write(file, json.dumps(template))
        self.assertTrue(any("must be unassessed" in e for e in validate.validate_skills(self.source)))

    def test_bad_name_prompt_and_short_description_are_rejected(self):
        file = self.source / "ml-foundations" / "SKILL.md"
        write(file, file.read_text(encoding="utf-8").replace("name: ml-foundations", "name: wrong-name"))
        config = self.source / "ml-foundations" / "agents" / "openai.yaml"
        write(config, 'interface:\n  display_name: "Name"\n  short_description: "Too short"\n'
                      '  default_prompt: "Explain a concept."\n')
        errors = validate.validate_skills(self.source)
        for expected in ("frontmatter name", "25–64", "default_prompt"):
            self.assertTrue(any(expected in e for e in errors), errors)

    def test_unquoted_yaml_colons_are_rejected_but_quotes_and_urls_are_valid(self):
        file = self.source / "ml-foundations" / "SKILL.md"
        original = file.read_text(encoding="utf-8")
        description = "description: Teach concepts and inspect assumptions on demand."
        for value in ("Probabilistic Machine Learning: An Introduction", "Explain a concept:"):
            with self.subTest(invalid=value):
                write(file, original.replace(description, "description: " + value))
                result = self.cli("validate.py", "--root", self.repo)
                self.assertNotEqual(0, result.returncode)
                self.assertIn("unquoted", result.stderr)
        for value in ('"Probabilistic Machine Learning: An Introduction"',
                      "'Probabilistic Machine Learning: An Introduction'",
                      "https://www.deeplearningbook.org/"):
            with self.subTest(valid=value):
                write(file, original.replace(description, "description: " + value))
                result = self.cli("validate.py", "--root", self.repo)
                self.assertEqual(0, result.returncode, result.stderr)

    def test_private_paths_excerpt_and_unfinished_placeholder_are_rejected(self):
        file = self.source / "ml-foundations" / "references" / "guide.md"
        for text, expected in (
            ("E:/private/file.pdf", "machine drive path"),
            ("/home/sample-user/private.md", "absolute user home path"),
            ('{"displayed_excerpt": "Original prose"}', "private source excerpt"),
            ("TODO add source later", "unfinished placeholder"),
        ):
            with self.subTest(expected=expected):
                write(file, "# Reading\n\n" + text)
                errors = validate.validate_skills(self.source)
                self.assertTrue(any(expected in e for e in errors), errors)

    def test_plugin_manifest_identity_must_match(self):
        file = self.repo / ".codex-plugin" / "plugin.json"
        data = json.loads(file.read_text(encoding="utf-8"))
        data["version"] = "9.9.9"
        write(file, json.dumps(data))
        self.assertIn("Plugin manifests disagree on version", validate.validate_plugin(self.repo))

    def test_existing_installer_lock_is_preserved(self):
        self.destination.mkdir(parents=True)
        lock = self.destination / ".ml-dl-skills-install.lock"
        write(lock, "another process\n")
        before = snapshot(self.destination)
        with self.assertRaises(install.InstallError):
            install.install_collection(self.source, self.destination, apply=True)
        self.assertEqual(before, snapshot(self.destination))

    def test_symbolic_link_ancestors_and_source_members_are_rejected(self):
        link = self.base / "linked-repository"
        try:
            link.symlink_to(self.repo, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Symbolic links unavailable without extra privileges: {exc}")
        try:
            with self.assertRaisesRegex(ValueError, "Link/reparse"):
                install.install_collection(link / "skills", self.destination, apply=True)
            with self.assertRaisesRegex(ValueError, "Link/reparse"):
                install.install_collection(self.source, link / "new-destination", apply=True)
        finally:
            link.unlink()
        member = self.source / "ml-foundations" / "references" / "linked.md"
        member.symlink_to(self.source / "dl-foundations" / "SKILL.md")
        try:
            self.assertTrue(any("Link/reparse" in e for e in validate.validate_skills(self.source)))
        finally:
            member.unlink()

    @unittest.skipUnless(os.name == "nt", "Windows junction test")
    def test_windows_junction_ancestors_are_rejected(self):
        shell = Path("C:/Program Files/PowerShell/7/pwsh.exe")
        if not shell.is_file():
            self.skipTest("PowerShell 7 unavailable")
        link = self.base / "junction-repository"
        quote = lambda text: "'" + str(text).replace("'", "''") + "'"
        command = ("New-Item -ItemType Junction -Path " + quote(link)
                   + " -Target " + quote(self.repo) + " -ErrorAction Stop | Out-Null")
        result = subprocess.run([str(shell), "-NoLogo", "-NoProfile", "-Command", command],
                                capture_output=True, text=True, check=False)
        if result.returncode:
            self.skipTest("Junction creation unavailable without extra permissions")
        try:
            with self.assertRaisesRegex(ValueError, "Link/reparse"):
                install.install_collection(link / "skills", self.destination, apply=True)
            with self.assertRaisesRegex(ValueError, "Link/reparse"):
                install.install_collection(self.source, link / "new-destination", apply=True)
            self.assertTrue((self.repo / "skills" / "ml-foundations" / "SKILL.md").is_file())
        finally:
            os.rmdir(link)

if __name__ == "__main__":
    unittest.main()

