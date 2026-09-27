#!/usr/bin/env python3
"""Unit tests for the validation and listing tooling.

Run directly, or through `tests/run-tests`:

    python3 tests/test_tooling.py

Each test builds a throwaway repository in a temporary directory and asserts
that the validator accepts or rejects it for the right reason.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO_ROOT, "scripts")
VALIDATE = os.path.join(SCRIPTS, "validate-skills")
LIST = os.path.join(SCRIPTS, "list-skills")

sys.path.insert(0, SCRIPTS)

import skilllib as lib  # noqa: E402


def run(script: str, root: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, script, "--root", root, *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _filesystem_is_case_insensitive() -> bool:
    """True when the filesystem treats `Foo` and `foo` as one name."""
    with tempfile.TemporaryDirectory() as tmp:
        probe = os.path.join(tmp, "probe")
        os.makedirs(probe)
        os.makedirs(os.path.join(probe, "Case"))
        # If a differently-cased name resolves to the directory we just made,
        # the filesystem folds case.
        return os.path.exists(os.path.join(probe, "case"))


class TempRepo:
    """Context manager building a minimal valid repository."""

    def __init__(self) -> None:
        self._tmp: tempfile.TemporaryDirectory | None = None
        self.root = ""

    def __enter__(self) -> "TempRepo":
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        os.makedirs(os.path.join(self.root, "skills"))
        self.write(
            "templates/skill/SKILL.md",
            "---\nname: example-skill\ndescription: A placeholder.\n---\n\n# Body\n",
        )
        self.write(
            "skills/example-skill/SKILL.md",
            "---\nname: example-skill\ndescription: Does a thing. Use for things.\n---\n\n# Body\n",
        )
        return self

    def __exit__(self, *exc) -> None:
        if self._tmp:
            self._tmp.cleanup()

    def write(self, relpath: str, content: str) -> str:
        path = os.path.join(self.root, relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        return path

    def write_bytes(self, relpath: str, raw: bytes) -> str:
        path = os.path.join(self.root, relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(raw)
        return path

    def validate(self, *args: str) -> subprocess.CompletedProcess:
        return run(VALIDATE, self.root, *args)


class ValidRepositoryTests(unittest.TestCase):
    def test_minimal_repository_passes(self):
        with TempRepo() as repo:
            result = repo.validate()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASSED", result.stdout)

    def test_list_derives_output_from_frontmatter(self):
        with TempRepo() as repo:
            result = run(LIST, repo.root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("example-skill", result.stdout)
            self.assertIn("Does a thing", result.stdout)

    def test_list_json_is_parseable(self):
        with TempRepo() as repo:
            result = run(LIST, repo.root, "--json")
            data = json.loads(result.stdout)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["name"], "example-skill")
            self.assertEqual(data[0]["path"], "skills/example-skill/SKILL.md")

    def test_list_markdown_points_at_real_files(self):
        with TempRepo() as repo:
            result = run(LIST, repo.root, "--markdown")
            self.assertIn("(skills/example-skill/SKILL.md)", result.stdout)


class FrontmatterTests(unittest.TestCase):
    def test_missing_frontmatter_is_rejected(self):
        with TempRepo() as repo:
            repo.write("skills/example-skill/SKILL.md", "# No frontmatter\n")
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("must start with a `---` line", result.stdout)

    def test_unterminated_frontmatter_is_rejected(self):
        with TempRepo() as repo:
            repo.write(
                "skills/example-skill/SKILL.md",
                "---\nname: example-skill\n\n# Body\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("closing", result.stdout)

    def test_missing_description_is_rejected(self):
        with TempRepo() as repo:
            repo.write("skills/example-skill/SKILL.md", "---\nname: example-skill\n---\n\n# Body\n")
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("missing the required field 'description'", result.stdout)

    def test_description_over_limit_is_rejected(self):
        with TempRepo() as repo:
            long_description = "x" * (lib.MAX_DESCRIPTION_LENGTH + 1)
            repo.write(
                "skills/example-skill/SKILL.md",
                f"---\nname: example-skill\ndescription: {long_description}\n---\n\n# Body\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("maximum", result.stdout)

    def test_unknown_frontmatter_key_is_rejected(self):
        with TempRepo() as repo:
            repo.write(
                "skills/example-skill/SKILL.md",
                "---\nname: example-skill\ndescription: A thing.\nwhen_to_use: Always.\n---\n\n# Body\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("not part of the Agent Skills specification", result.stdout)

    def test_malformed_yaml_is_rejected(self):
        with TempRepo() as repo:
            repo.write(
                "skills/example-skill/SKILL.md",
                "---\nname: example-skill\ndescription A thing\n---\n\n# Body\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("expected `key: value`", result.stdout)

    def test_duplicate_key_is_rejected(self):
        with TempRepo() as repo:
            repo.write(
                "skills/example-skill/SKILL.md",
                "---\nname: example-skill\nname: other-skill\ndescription: A thing.\n---\n\n# Body\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("duplicate field", result.stdout)

    def test_metadata_must_be_a_map_of_strings(self):
        with TempRepo() as repo:
            repo.write(
                "skills/example-skill/SKILL.md",
                "---\nname: example-skill\ndescription: A thing.\nmetadata:\n  version: 1\n---\n\n# Body\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("must be a string", result.stdout)

    def test_optional_spec_fields_are_accepted(self):
        with TempRepo() as repo:
            repo.write(
                "skills/example-skill/SKILL.md",
                "---\n"
                "name: example-skill\n"
                "description: A thing. Use for things.\n"
                "license: MIT\n"
                'compatibility: Requires python3\n'
                "metadata:\n"
                "  author: someone\n"
                '  version: "1.0"\n'
                "allowed-tools: Read Grep\n"
                "---\n\n# Body\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class NameTests(unittest.TestCase):
    def test_uppercase_name_is_rejected(self):
        with TempRepo() as repo:
            repo.write(
                "skills/Example-Skill/SKILL.md",
                "---\nname: Example-Skill\ndescription: A thing.\n---\n\n# Body\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("is invalid", result.stdout)

    def test_consecutive_hyphens_are_rejected(self):
        with TempRepo() as repo:
            repo.write(
                "skills/bad--name/SKILL.md",
                "---\nname: bad--name\ndescription: A thing.\n---\n\n# Body\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("is invalid", result.stdout)

    def test_trailing_hyphen_is_rejected(self):
        with TempRepo() as repo:
            repo.write(
                "skills/bad-/SKILL.md",
                "---\nname: bad-\ndescription: A thing.\n---\n\n# Body\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 1)

    def test_name_must_match_directory(self):
        with TempRepo() as repo:
            repo.write(
                "skills/directory-name/SKILL.md",
                "---\nname: other-name\ndescription: A thing.\n---\n\n# Body\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("the specification requires them to match", result.stdout)

    def test_duplicate_names_are_rejected(self):
        with TempRepo() as repo:
            repo.write(
                "skills/second-copy/SKILL.md",
                "---\nname: example-skill\ndescription: A thing.\n---\n\n# Body\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("duplicate skill 'name'", result.stdout)

    def test_case_insensitive_directory_collision_is_rejected(self):
        if _filesystem_is_case_insensitive():
            self.skipTest(
                "filesystem is case-insensitive, so both paths are the same "
                "directory; see test_uniqueness_check_is_filesystem_independent"
            )
        with TempRepo() as repo:
            repo.write(
                "skills/Example-Skill/SKILL.md",
                "---\nname: example-skill\ndescription: A thing.\n---\n\n# Body\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("differ only by case or separator", result.stdout)

    def test_uniqueness_check_is_filesystem_independent(self):
        """The collision rules hold even where the filesystem folds case."""
        import importlib.util
        from importlib.machinery import SourceFileLoader

        # `validate-skills` has no .py suffix, so name the loader explicitly.
        loader = SourceFileLoader("validate_skills", VALIDATE)
        spec = importlib.util.spec_from_file_location(
            "validate_skills", VALIDATE, loader=loader
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        def fake(directory, name):
            skill = lib.Skill(directory, os.path.join(REPO_ROOT, directory))
            skill.name = name
            return skill

        skills = [fake("skills/example-skill", "example-skill")]
        self.assertEqual(module.check_uniqueness(skills, REPO_ROOT), [])

        skills.append(fake("skills/Example_Skill", "example-skill"))
        messages = " ".join(
            p.message for p in module.check_uniqueness(skills, REPO_ROOT)
        )
        self.assertIn("duplicate skill 'name'", messages)
        self.assertIn("differ only by case or separator", messages)

    def test_reserved_name_is_rejected(self):
        with TempRepo() as repo:
            repo.write(
                "skills/synced/SKILL.md",
                "---\nname: synced\ndescription: A thing.\n---\n\n# Body\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("reserved by Claude Code", result.stdout)

    def test_name_at_max_length_is_accepted(self):
        with TempRepo() as repo:
            name = "a" + "b" * 62 + "c"
            self.assertEqual(len(name), 64)
            repo.write(
                f"skills/{name}/SKILL.md",
                f"---\nname: {name}\ndescription: A thing.\n---\n\n# Body\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_name_over_max_length_is_rejected(self):
        with TempRepo() as repo:
            name = "a" * 65
            repo.write(
                f"skills/{name}/SKILL.md",
                f"---\nname: {name}\ndescription: A thing.\n---\n\n# Body\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("maximum is 64", result.stdout)


class PackagingManifestTests(unittest.TestCase):
    """Packaging manifests are optional, but must be valid when present."""

    def manifest(self, repo, relative, payload):
        repo.write(relative, json.dumps(payload, indent=2) + "\n")

    def test_a_valid_claude_manifest_is_accepted(self):
        with TempRepo() as repo:
            self.manifest(
                repo,
                ".claude-plugin/plugin.json",
                {
                    "name": "example-skill-repo",
                    "version": "0.1.0",
                    "description": "Skills.",
                    "license": "MIT",
                },
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 0, result.stdout)

    def test_a_manifest_must_be_valid_json(self):
        with TempRepo() as repo:
            repo.write("plugin.json", "{ not json")
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("is not valid JSON", result.stdout)

    def test_a_manifest_name_must_be_kebab_case(self):
        with TempRepo() as repo:
            self.manifest(
                repo, "plugin.json", {"name": "Example_Skill_Repo", "version": "1.0.0"}
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("must be kebab-case", result.stdout)

    def test_a_skill_copy_outside_skills_is_rejected(self):
        """`skills/` is the only place a SKILL.md may live."""
        for platform_dir in (".claude/skills", ".agents/skills", ".opencode/skills", "dist"):
            with self.subTest(platform=platform_dir):
                with TempRepo() as repo:
                    repo.write(
                        f"{platform_dir}/example-skill/SKILL.md",
                        "---\nname: example-skill\ndescription: A copy.\n---\n\n# Body\n",
                    )
                    result = repo.validate()
                    self.assertEqual(result.returncode, 1)
                    self.assertIn("may only live under skills/", result.stdout)

    def test_the_template_skill_md_is_exempt(self):
        with TempRepo() as repo:
            repo.write(
                "templates/skill/SKILL.md",
                "---\nname: example-skill\ndescription: A placeholder.\n---\n\n# Purpose\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 0, result.stdout)

    def test_a_manifest_may_not_point_at_a_skill_copy(self):
        with TempRepo() as repo:
            repo.write(
                "claude-copy/SKILL.md",
                "---\nname: claude-copy\ndescription: A duplicate.\n---\n\n# Body\n",
            )
            self.manifest(
                repo,
                ".agents/plugins/marketplace.json",
                {
                    "name": "example-skill-repo",
                    "plugins": [
                        {
                            "name": "example-skill-repo",
                            "source": {"source": "local", "path": "./claude-copy"},
                        }
                    ],
                },
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("skills must live", result.stdout)

    def test_a_manifest_path_must_exist(self):
        with TempRepo() as repo:
            self.manifest(
                repo,
                ".agents/plugins/marketplace.json",
                {
                    "name": "example-skill-repo",
                    "plugins": [
                        {
                            "name": "example-skill-repo",
                            "source": {"source": "local", "path": "./nope"},
                        }
                    ],
                },
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("does not exist", result.stdout)

    def test_a_manifest_path_may_not_escape_the_repository(self):
        with TempRepo() as repo:
            self.manifest(
                repo,
                "plugin.json",
                {"name": "example-skill-repo", "skills": ["./../elsewhere"]},
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("escapes the repository", result.stdout)

    def test_manifests_must_agree_on_the_plugin_name(self):
        with TempRepo() as repo:
            self.manifest(repo, "plugin.json", {"name": "example-skill-repo"})
            self.manifest(repo, ".claude-plugin/plugin.json", {"name": "other-name"})
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("disagree on the plugin name", result.stdout)

    def test_this_repository_ships_valid_manifests(self):
        result = subprocess.run(
            [sys.executable, VALIDATE, "--root", REPO_ROOT, "--strict"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for relative in (
            "plugin.json",
            ".claude-plugin/plugin.json",
            ".claude-plugin/marketplace.json",
            ".agents/plugins/marketplace.json",
        ):
            self.assertTrue(
                os.path.isfile(os.path.join(REPO_ROOT, relative)), f"missing {relative}"
            )


class StructureTests(unittest.TestCase):
    def test_missing_skill_md_is_rejected(self):
        with TempRepo() as repo:
            os.remove(os.path.join(repo.root, "skills/example-skill/SKILL.md"))
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("no SKILL.md found", result.stdout)

    def test_lowercase_skill_md_is_rejected(self):
        with TempRepo() as repo:
            os.remove(os.path.join(repo.root, "skills/example-skill/SKILL.md"))
            repo.write("skills/example-skill/skill.md", "---\nname: example-skill\ndescription: A thing.\n---\n")
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("named exactly SKILL.md", result.stdout)

    def test_nested_second_skill_md_is_rejected(self):
        with TempRepo() as repo:
            repo.write("skills/example-skill/references/other/SKILL.md", "# nested\n")
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("exactly one SKILL.md", result.stdout)

    def test_hidden_skill_directory_is_rejected(self):
        with TempRepo() as repo:
            repo.write("skills/.draft/SKILL.md", "---\nname: draft\ndescription: A thing.\n---\n")
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("hidden skill directory", result.stdout)

    def test_stray_file_in_skills_is_rejected(self):
        with TempRepo() as repo:
            repo.write("skills/notes.md", "# notes\n")
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("only directories are allowed", result.stdout)

    def test_empty_supporting_directory_is_a_warning(self):
        with TempRepo() as repo:
            os.makedirs(os.path.join(repo.root, "skills/example-skill/references"))
            result = repo.validate("--strict")
            self.assertEqual(result.returncode, 1)
            self.assertIn("directory is empty", result.stdout)
            self.assertEqual(repo.validate().returncode, 0)

    def test_supporting_directories_are_allowed(self):
        with TempRepo() as repo:
            repo.write("skills/example-skill/references/notes.md", "# Notes\n")
            repo.write("skills/example-skill/scripts/run.sh", "#!/bin/sh\necho hi\n")
            repo.write("skills/example-skill/assets/template.txt", "hello\n")
            result = repo.validate()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class ReferenceTests(unittest.TestCase):
    def test_broken_markdown_link_is_rejected(self):
        with TempRepo() as repo:
            repo.write(
                "skills/example-skill/SKILL.md",
                "---\nname: example-skill\ndescription: A thing.\n---\n\n"
                "See [the guide](references/guide.md).\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("does not exist", result.stdout)

    def test_valid_markdown_link_is_accepted(self):
        with TempRepo() as repo:
            repo.write("skills/example-skill/references/guide.md", "# Guide\n")
            repo.write(
                "skills/example-skill/SKILL.md",
                "---\nname: example-skill\ndescription: A thing.\n---\n\n"
                "See [the guide](references/guide.md).\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_broken_code_reference_is_rejected(self):
        with TempRepo() as repo:
            repo.write(
                "skills/example-skill/SKILL.md",
                "---\nname: example-skill\ndescription: A thing.\n---\n\n"
                "Run `scripts/check.py` first.\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("file reference", result.stdout)

    def test_valid_code_reference_is_accepted(self):
        with TempRepo() as repo:
            repo.write("skills/example-skill/scripts/check.py", "print('ok')\n")
            repo.write(
                "skills/example-skill/SKILL.md",
                "---\nname: example-skill\ndescription: A thing.\n---\n\n"
                "Run `scripts/check.py` first.\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_external_links_are_ignored(self):
        with TempRepo() as repo:
            repo.write(
                "skills/example-skill/SKILL.md",
                "---\nname: example-skill\ndescription: A thing.\n---\n\n"
                "See [the spec](https://agentskills.io/specification) and "
                "[anchor](#when-to-use) and `https://example.com/a.js`.\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_broken_relative_link_in_readme_is_rejected(self):
        with TempRepo() as repo:
            repo.write("README.md", "See [the guide](docs/guide.md).\n")
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("docs/guide.md", result.stdout)

    def test_machine_specific_absolute_path_is_a_warning(self):
        with TempRepo() as repo:
            repo.write("README.md", "Run `/Users/someone/bin/tool`.\n")
            result = repo.validate("--strict")
            self.assertEqual(result.returncode, 1)
            self.assertIn("machine-specific absolute path", result.stdout)


class EncodingTests(unittest.TestCase):
    def test_invalid_utf8_is_rejected(self):
        with TempRepo() as repo:
            repo.write_bytes("skills/example-skill/references/bad.md", b"\xff\xfe\x00bad")
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("UTF-8", result.stdout)

    def test_byte_order_mark_is_rejected(self):
        with TempRepo() as repo:
            repo.write_bytes(
                "skills/example-skill/references/bom.md",
                b"\xef\xbb\xbf# Title\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("BOM", result.stdout)

    def test_valid_utf8_is_accepted(self):
        with TempRepo() as repo:
            repo.write("skills/example-skill/references/unicode.md", "# Título — ok\n")
            result = repo.validate()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class FrontmatterParserTests(unittest.TestCase):
    def test_quoted_and_comment_handling(self):
        data, errors = lib.parse_frontmatter(
            'name: a-skill  # trailing comment\n'
            'description: "A thing: with a colon # and a hash"\n'
            "metadata:\n"
            '  version: "1.0"\n'
            '  author: someone\n'
        )
        self.assertEqual(errors, [])
        self.assertEqual(data["name"], "a-skill")
        self.assertEqual(data["description"], "A thing: with a colon # and a hash")
        self.assertEqual(data["metadata"], {"version": "1.0", "author": "someone"})

    def test_block_sequence(self):
        data, errors = lib.parse_frontmatter(
            "name: a-skill\ndescription: A thing.\nallowed-tools:\n  - Read\n  - Grep\n"
        )
        self.assertEqual(errors, [])
        self.assertEqual(data["allowed-tools"], ["Read", "Grep"])

    def test_flow_sequence(self):
        data, errors = lib.parse_frontmatter(
            "name: a-skill\ndescription: A thing.\nallowed-tools: [Read, Grep]\n"
        )
        self.assertEqual(errors, [])
        self.assertEqual(data["allowed-tools"], ["Read", "Grep"])

    def test_links_inside_code_fences_are_not_checked(self):
        with TempRepo() as repo:
            repo.write(
                "docs/notes.md",
                "Example only:\n\n"
                "```markdown\n"
                "See [the tree](references/does-not-exist.md) for details.\n"
                "```\n\n"
                "Real link: [the skill](../skills/example-skill/SKILL.md)\n",
            )
            result = repo.validate()
            self.assertEqual(result.returncode, 0, result.stdout)

    def test_a_real_broken_link_is_still_caught(self):
        with TempRepo() as repo:
            repo.write("docs/notes.md", "Broken: [gone](missing.md)\n")
            result = repo.validate()
            self.assertEqual(result.returncode, 1)
            self.assertIn("'missing.md' does not exist", result.stdout)

    def test_tab_indentation_is_reported(self):
        _, errors = lib.parse_frontmatter("name: a-skill\nmetadata:\n\tversion: 1\n")
        self.assertTrue(any("tab" in error for error in errors), errors)

    def test_unterminated_quote_is_reported(self):
        _, errors = lib.parse_frontmatter('name: "a-skill\n')
        self.assertTrue(any("unterminated" in error for error in errors), errors)

    def test_name_helper_reports_problems(self):
        problems = lib.validate_skill_name("Bad Name", "x")
        self.assertTrue(any("is invalid" in p.message for p in problems))
        self.assertEqual(lib.validate_skill_name("good-name", "x"), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
