"""Shared helpers for validating and listing Agent Skills.

Standard library only, on purpose: this repository must be usable without
installing anything.

The YAML handling here is a deliberately small parser for the subset of YAML
that the Agent Skills specification allows in `SKILL.md` frontmatter. It is
strict, so malformed frontmatter is reported rather than silently accepted, but
it is not a general YAML implementation. If you need a full YAML check, run the
reference validator from https://agentskills.io/specification:

    skills-ref validate ./skills/<skill-name>
"""

from __future__ import annotations

import os
import re
import sys
import unicodedata

# --------------------------------------------------------------------------
# Specification constants
# https://agentskills.io/specification
# --------------------------------------------------------------------------

SKILL_FILENAME = "SKILL.md"

#: The only top-level frontmatter keys the Agent Skills specification defines.
#: Anthropic's claude.ai uploads and the Skills API reject any other key, so an
#: unknown key is reported as an error rather than a warning.
SPEC_FIELDS = (
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
)

#: Fields that must be a plain string.
STRING_FIELDS = ("name", "description", "license", "compatibility", "allowed-tools")

MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_COMPATIBILITY_LENGTH = 500
MAX_SKILL_MD_LINES = 500  # Spec recommendation, not a hard limit.

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

#: A field-name token the parser is willing to read. Deliberately looser than
#: `NAME_RE`: the parser accepts, then `validate_frontmatter_fields` rejects
#: with an accurate message about the specification.
FIELD_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

_INT_RE = re.compile(r"^[-+]?\d+$")
_FLOAT_RE = re.compile(r"^[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?$")

#: Names Claude Code reserves for skills it syncs from a claude.ai account.
#: A skill using one of these does not load. See
#: https://code.claude.com/docs/en/skills
RESERVED_SKILL_NAMES = ("synced", "anthropic-skills")

#: Claude Code only reads frontmatter when the opening `---` is line 1.
FRONTMATTER_FENCE = "---"

#: Optional directories the specification defines for supporting files.
SUPPORTING_DIRS = ("scripts", "references", "assets")

_SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", ".DS_Store"}


class Problem:
    """One validation finding.

    `level` is "error" or "warning". `path` is repository-relative when known.
    """

    __slots__ = ("level", "path", "message")

    def __init__(self, level: str, path: str, message: str) -> None:
        self.level = level
        self.path = path
        self.message = message

    def __str__(self) -> str:
        return f"{self.level.upper()}: {self.path}: {self.message}"


def repo_root(start: str | None = None) -> str:
    """Return the repository root, detected by the presence of `skills/`."""
    here = os.path.abspath(start or os.path.dirname(os.path.abspath(__file__)))
    probe = here
    while True:
        if os.path.isdir(os.path.join(probe, "skills")):
            return probe
        parent = os.path.dirname(probe)
        if parent == probe:
            return here
        probe = parent


def rel(path: str, root: str) -> str:
    """Repository-relative, forward-slash path for display."""
    try:
        out = os.path.relpath(path, root)
    except ValueError:  # pragma: no cover - different drives on Windows
        return path
    return out.replace(os.sep, "/")


# --------------------------------------------------------------------------
# UTF-8 / text reading
# --------------------------------------------------------------------------


class TextError(Exception):
    pass


def read_text(path: str) -> str:
    """Read a file as strict UTF-8. Raises TextError on invalid UTF-8."""
    with open(path, "rb") as handle:
        raw = handle.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise TextError("file starts with a UTF-8 byte order mark (BOM)")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TextError(f"not valid UTF-8 at byte {exc.start}: {exc.reason}") from None


def read_text_checked(path: str) -> tuple[str | None, str | None]:
    """Return (text, error_message). Never raises."""
    try:
        return read_text(path), None
    except TextError as exc:
        return None, str(exc)
    except OSError as exc:
        return None, f"cannot read file: {exc.strerror or exc}"


def iter_files(base: str) -> list[str]:
    """Every file under `base`, skipping VCS and tooling noise."""
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in _SKIP_DIRS)
        for name in sorted(filenames):
            if name in _SKIP_DIRS:
                continue
            found.append(os.path.join(dirpath, name))
    return found


# --------------------------------------------------------------------------
# Frontmatter
# --------------------------------------------------------------------------


def split_frontmatter(text: str) -> tuple[str | None, str, str | None]:
    """Split `text` into (frontmatter_yaml, body, error).

    Returns (None, text, error) when no complete frontmatter block is present.
    """
    if not text.startswith(FRONTMATTER_FENCE):
        return None, text, (
            "file must start with a `---` line on line 1 before the frontmatter"
        )

    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_FENCE:
        return None, text, "line 1 must be exactly `---`"

    for index in range(1, len(lines)):
        if lines[index].strip() == FRONTMATTER_FENCE:
            return "\n".join(lines[1:index]), "\n".join(lines[index + 1:]), None

    return None, text, "frontmatter is missing its closing `---`"


def _strip_comment(value: str) -> str:
    """Remove a trailing ` # comment` that sits outside quotes."""
    out: list[str] = []
    quote: str | None = None
    index = 0
    while index < len(value):
        char = value[index]
        if quote:
            out.append(char)
            if char == "\\" and quote == '"' and index + 1 < len(value):
                out.append(value[index + 1])
                index += 2
                continue
            if char == quote:
                quote = None
        elif char in "'\"":
            quote = char
            out.append(char)
        elif char == "#" and (not out or out[-1] in " \t"):
            break
        else:
            out.append(char)
        index += 1
    return "".join(out).rstrip()


def _parse_scalar(raw: str, line_no: int) -> tuple[object, str | None]:
    """Parse a single YAML scalar or flow collection. Returns (value, error)."""
    text = raw.strip()
    if not text:
        return "", None

    if text[0] == '"':
        if len(text) < 2 or text[-1] != '"':
            return None, f"line {line_no}: unterminated double-quoted string"
        body = text[1:-1]
        try:
            return (
                body.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"'),
                None,
            )
        except Exception:  # pragma: no cover - defensive
            return None, f"line {line_no}: invalid escape in string"
    if text[0] == "'":
        if len(text) < 2 or text[-1] != "'":
            return None, f"line {line_no}: unterminated single-quoted string"
        return text[1:-1].replace("''", "'"), None

    if text.startswith("[") or text.startswith("{"):
        parsed, error = _parse_flow(text, line_no)
        return parsed, error

    if text in ("true", "false"):
        return text == "true", None
    if text in ("null", "~"):
        return None, None
    if _INT_RE.match(text):
        return int(text), None
    if _FLOAT_RE.match(text):
        return float(text), None

    return text, None


def _parse_flow(text: str, line_no: int) -> tuple[object, str | None]:
    """Parse a one-line flow sequence or mapping."""
    closing = "]" if text.startswith("[") else "}"
    if not text.endswith(closing):
        return None, f"line {line_no}: unterminated flow collection"

    inner = text[1:-1].strip()
    if not inner:
        return ([], None) if closing == "]" else ({}, None)

    if closing == "]":
        items: list[object] = []
        for chunk in _split_flow(inner):
            value, error = _parse_scalar(chunk, line_no)
            if error:
                return None, error
            items.append(value)
        return items, None

    result: dict[str, object] = {}
    for chunk in _split_flow(inner):
        key, sep, value_text = chunk.partition(":")
        if not sep:
            return None, f"line {line_no}: flow mapping entry needs `key: value`"
        value, error = _parse_scalar(value_text, line_no)
        if error:
            return None, error
        result[str(_parse_scalar(key, line_no)[0]).strip()] = value
    return result, None


def _split_flow(inner: str) -> list[str]:
    """Split on commas that are not inside quotes or nested brackets."""
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    quote: str | None = None
    for char in inner:
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in "'\"":
            quote = char
            current.append(char)
        elif char in "[{":
            depth += 1
            current.append(char)
        elif char in "]}":
            depth -= 1
            current.append(char)
        elif char == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def parse_frontmatter(yaml_text: str) -> tuple[dict, list[str]]:
    """Parse the YAML subset allowed in SKILL.md frontmatter.

    Returns (mapping, error_messages). Supports top-level scalars, block
    sequences, one level of nested mapping, single-line flow collections, and
    comments. Anything else is an error rather than a guess.
    """
    errors: list[str] = []
    data: dict[str, object] = {}
    lines = yaml_text.split("\n")

    index = 0
    while index < len(lines):
        raw = lines[index]
        line_no = index + 1
        index += 1

        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            errors.append(f"line {line_no}: tab used for indentation")
            continue

        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if raw[:1] in (" ", "\t"):
            errors.append(
                f"line {line_no}: unexpected indented line; expected `key: value`"
            )
            continue

        if ":" not in stripped:
            errors.append(
                f"line {line_no}: expected `key: value`, got {stripped!r}"
            )
            continue

        key, _, rest = stripped.partition(":")
        key = key.strip()
        if not key:
            errors.append(f"line {line_no}: empty key")
            continue
        if not FIELD_NAME_RE.match(key):
            errors.append(f"line {line_no}: invalid field name {key!r}")
            continue
        if key in data:
            errors.append(f"line {line_no}: duplicate field {key!r}")
            continue

        rest = _strip_comment(rest).strip()

        if rest:  # inline scalar or flow collection
            value, error = _parse_scalar(rest, line_no)
            if error:
                errors.append(error)
                continue
            data[key] = value
            continue

        # Block value: gather the indented lines that follow.
        block: list[tuple[int, str]] = []
        while index < len(lines):
            nxt = lines[index]
            if not nxt.strip():
                block.append((index + 1, ""))
                index += 1
                continue
            if not nxt[:1].isspace():
                break
            leading = nxt[: len(nxt) - len(nxt.lstrip())]
            if "\t" in leading:
                errors.append(
                    f"line {index + 1}: tab used for indentation; use spaces"
                )
            block.append((index + 1, nxt))
            index += 1

        while block and not block[-1][1].strip():
            block.pop()

        if not block:
            data[key] = ""
            continue

        indent = min(len(text) - len(text.lstrip()) for _, text in block)
        entries = [(no, text[indent:]) for no, text in block]

        if all(text.strip().startswith("- ") or text.strip() == "-" for _, text in entries):
            items = []
            for no, text in entries:
                item = text.strip()[1:].strip()
                if not item:
                    errors.append(f"line {no}: empty sequence item")
                    continue
                value, error = _parse_scalar(_strip_comment(item), no)
                if error:
                    errors.append(error)
                    continue
                items.append(value)
            data[key] = items
        elif all(":" in text for _, text in entries):
            nested: dict[str, object] = {}
            for no, text in entries:
                sub_key, _, sub_rest = text.strip().partition(":")
                sub_key = sub_key.strip()
                if not sub_key:
                    errors.append(f"line {no}: empty nested key")
                    continue
                if sub_key in nested:
                    errors.append(f"line {no}: duplicate nested key {sub_key!r}")
                    continue
                value, error = _parse_scalar(_strip_comment(sub_rest), no)
                if error:
                    errors.append(error)
                    continue
                nested[sub_key] = value
            data[key] = nested
        else:
            errors.append(
                f"line {entries[0][0]}: block value under {key!r} is neither a "
                "sequence of `- item` lines nor a `key: value` mapping"
            )

    return data, errors


# --------------------------------------------------------------------------
# Frontmatter field validation
# --------------------------------------------------------------------------


def validate_frontmatter_fields(data: dict, where: str) -> list[Problem]:
    """Check parsed frontmatter against the specification's field rules."""
    problems: list[Problem] = []

    for key in data:
        if key not in SPEC_FIELDS:
            problems.append(
                Problem(
                    "error",
                    where,
                    f"frontmatter key {key!r} is not part of the Agent Skills "
                    f"specification. Allowed keys: {', '.join(SPEC_FIELDS)}. "
                    "Platform-specific keys break claude.ai uploads and the "
                    "Skills API.",
                )
            )

    for field in ("name", "description"):
        if field not in data:
            problems.append(
                Problem(
                    "error",
                    where,
                    f"frontmatter is missing the required field {field!r}",
                )
            )

    for field in STRING_FIELDS:
        if field in data and not isinstance(data[field], str):
            problems.append(
                Problem(
                    "error",
                    where,
                    f"{field!r} must be a single-line string, got "
                    f"{type(data[field]).__name__}",
                )
            )

    name = data.get("name")
    if isinstance(name, str):
        problems.extend(validate_skill_name(name, where))

    description = data.get("description")
    if isinstance(description, str):
        if not description.strip():
            problems.append(Problem("error", where, "'description' is empty"))
        if len(description) > MAX_DESCRIPTION_LENGTH:
            problems.append(
                Problem(
                    "error",
                    where,
                    f"'description' is {len(description)} characters; the maximum "
                    f"is {MAX_DESCRIPTION_LENGTH}",
                )
            )
        lowered = description.lower()
        for phrase in ("must always", "always use this skill", "use this skill for everything"):
            if phrase in lowered:
                problems.append(
                    Problem(
                        "warning",
                        where,
                        "'description' uses exaggerated trigger language "
                        f"({phrase!r}); write what the skill does and when to "
                        "use it so it can be matched naturally",
                    )
                )
                break

    compatibility = data.get("compatibility")
    if isinstance(compatibility, str) and len(compatibility) > MAX_COMPATIBILITY_LENGTH:
        problems.append(
            Problem(
                "error",
                where,
                f"'compatibility' is {len(compatibility)} characters; the maximum "
                f"is {MAX_COMPATIBILITY_LENGTH}",
            )
        )

    metadata = data.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        problems.append(
            Problem(
                "error",
                where,
                f"'metadata' must be a mapping, got {type(metadata).__name__}",
            )
        )
    elif isinstance(metadata, dict):
        for key, value in metadata.items():
            if isinstance(value, str):
                continue
            hint = ""
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                hint = f"; quote it, for example version: {value!r} as \"{value}\""
            problems.append(
                Problem(
                    "error",
                    where,
                    f"'metadata.{key}' must be a string, got "
                    f"{type(value).__name__}{hint}",
                )
            )

    return problems


def validate_skill_name(name: str, where: str) -> list[Problem]:
    """Validate a skill `name` value against the specification."""
    problems: list[Problem] = []
    if not name:
        return [Problem("error", where, "'name' is empty")]
    if len(name) > MAX_NAME_LENGTH:
        problems.append(
            Problem(
                "error",
                where,
                f"'name' is {len(name)} characters; the maximum is "
                f"{MAX_NAME_LENGTH}",
            )
        )
    if not NAME_RE.match(name):
        problems.append(
            Problem(
                "error",
                where,
                f"'name' {name!r} is invalid: use lowercase letters, digits and "
                "single hyphens, without a leading or trailing hyphen",
            )
        )
    elif name in RESERVED_SKILL_NAMES or name.startswith("anthropic-skills:"):
        problems.append(
            Problem(
                "error",
                where,
                f"'name' {name!r} is reserved by Claude Code for skills synced "
                "from a claude.ai account and will not load",
            )
        )
    return problems


# --------------------------------------------------------------------------
# Discovery
# --------------------------------------------------------------------------


class Skill:
    """A discovered skill directory."""

    __slots__ = ("directory", "basename", "path", "name", "description", "data", "problems")

    def __init__(self, directory: str, path: str) -> None:
        self.directory = directory  # basename
        self.path = path  # absolute path
        self.name: str | None = None
        self.description: str | None = None
        self.data: dict = {}
        self.problems: list[Problem] = []


def normalize_name(value: str) -> str:
    """Case- and separator-insensitive form, for duplicate detection."""
    folded = unicodedata.normalize("NFKD", value).casefold()
    return re.sub(r"[-_\s]+", "-", folded)


def discover_skills(skills_dir: str) -> tuple[list[Skill], list[Problem]]:
    """Find every skill directory under `skills_dir` and read its metadata."""
    problems: list[Problem] = []
    if not os.path.isdir(skills_dir):
        return [], problems

    skills: list[Skill] = []
    for entry in sorted(os.listdir(skills_dir)):
        path = os.path.join(skills_dir, entry)
        if entry in _SKIP_DIRS:
            continue
        if entry.startswith("."):
            problems.append(
                Problem(
                    "error",
                    f"skills/{entry}",
                    "hidden skill directory; hidden directories are not "
                    "discoverable and are almost always accidental",
                )
            )
            continue
        if not os.path.isdir(path):
            problems.append(
                Problem(
                    "error",
                    f"skills/{entry}",
                    "only directories are allowed inside `skills/`",
                )
            )
            continue
        skill = Skill(entry, path)
        _read_skill_metadata(skill, path, os.path.dirname(path))
        skills.append(skill)

    return skills, problems


def _read_skill_metadata(skill: Skill, path: str, root: str) -> None:
    """Load `name`/`description` from a skill, recording problems as needed."""
    where = f"skills/{skill.directory}/{SKILL_FILENAME}"
    text, error = read_text_checked(os.path.join(path, SKILL_FILENAME))
    if text is None:
        skill.problems.append(
            Problem("error", where, f"cannot read {SKILL_FILENAME}: {error}")
        )
        return
    yaml_text, body, split_error = split_frontmatter(text)
    if split_error:
        skill.problems.append(Problem("error", where, split_error))
        return
    assert yaml_text is not None
    data, errors = parse_frontmatter(yaml_text)
    for message in errors:
        skill.problems.append(Problem("error", where, message))
    skill.data = data
    name = data.get("name")
    skill.name = name if isinstance(name, str) else None
    description = data.get("description")
    skill.description = description if isinstance(description, str) else None


# --------------------------------------------------------------------------
# Reference extraction
# --------------------------------------------------------------------------

_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(\s*<?([^)>\s]+)>?(?:\s+\"[^\"]*\")?\s*\)")
_CODE_PATH_RE = re.compile(
    r"`([A-Za-z0-9_.][A-Za-z0-9._/@-]*\.(?:md|markdown|py|sh|bash|js|mjs|cjs|ts|json|ya?ml"
    r"|toml|txt|csv|xml|html|css|svg|png|jpe?g|gif|webp|ico|woff2?))`"
)
_ABSOLUTE_LOCAL_PATH_RE = re.compile(r"(?:^|[\s`(\"'])(/(?:Users|home)/[A-Za-z0-9._/-]+)")

#: An opening or closing code fence: three or more backticks or tildes.
FENCE_RE = re.compile(r"^(`{3,}|~{3,})")


def _is_external(target: str) -> bool:
    if target.startswith("#"):
        return True
    if target.startswith("/"):
        return True
    return bool(re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target)) or target.startswith("//")


def _clean_target(target: str) -> str:
    target = target.split("#", 1)[0].split("?", 1)[0]
    from urllib.parse import unquote

    return unquote(target.strip())


def strip_fenced_code(text: str) -> str:
    """Blank out fenced code blocks, keeping every line.

    A markdown link or a shell path that appears inside ``` or ~~~ fences is an
    example, not a reference, so link and path checks must not see it. Line
    numbers and offsets are preserved: fenced lines become empty lines.
    """
    out: list[str] = []
    fence = ""  # the marker that opened the current fence, e.g. "```"
    for line in text.split("\n"):
        stripped = line.lstrip()
        match = FENCE_RE.match(stripped)
        if fence:
            if match and match.group(1).startswith(fence[0]) and len(match.group(1)) >= len(fence):
                fence = ""
                out.append("")  # the closing fence is not prose either
            else:
                out.append("")
            continue
        if match:
            fence = match.group(1)
            out.append("")
            continue
        out.append(line)
    return "\n".join(out)


def iter_markdown_links(text: str):
    """Yield every markdown link target found in `text`."""
    for match in _MD_LINK_RE.finditer(text):
        yield match.group(1)


def iter_code_paths(text: str):
    """Yield backticked paths that look like real files inside a skill."""
    for match in _CODE_PATH_RE.finditer(text):
        yield match.group(1)


def find_issues(
    text: str, base_dir: str, *, where: str, code_refs: bool = True
) -> list[Problem]:
    """Check that relative references in `text` resolve to real files.

    `base_dir` is the directory the references are relative to. External
    targets (http, mailto, in-page anchors) are ignored. Set `code_refs` to
    False for prose documents, where a backticked path is usually an example
    rather than a link that must resolve.
    """
    problems: list[Problem] = []
    seen: set[str] = set()

    def check(target: str, kind: str) -> None:
        if _is_external(target):
            return
        cleaned = _clean_target(target)
        if not cleaned:
            return
        key = f"{kind}:{cleaned}"
        if key in seen:
            return
        seen.add(key)
        resolved = os.path.normpath(os.path.join(base_dir, cleaned))
        if os.path.exists(resolved):
            return
        hint = ""
        if cleaned.startswith("../") or os.pardir in cleaned.split("/"):
            hint = " (reference escapes the skill directory)"
        problems.append(
            Problem(
                "error",
                where,
                f"{kind} reference {cleaned!r} does not exist{hint}",
            )
        )

    for target in iter_markdown_links(text):
        check(target, "markdown link")
    if code_refs:
        for target in iter_code_paths(text):
            check(target, "file reference")

    return problems


def find_local_absolute_paths(text: str, where: str) -> list[Problem]:
    """Warn about machine-specific absolute paths leaking into committed docs."""
    problems: list[Problem] = []
    for match in _ABSOLUTE_LOCAL_PATH_RE.finditer(text):
        problems.append(
            Problem(
                "warning",
                where,
                f"machine-specific absolute path {match.group(1)!r}; use a "
                "repository-relative path instead",
            )
        )
    return problems


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------


def report(problems: list[Problem], stream=sys.stdout) -> int:
    """Print findings and return the process exit code (1 when any error)."""
    errors = [p for p in problems if p.level == "error"]
    warnings = [p for p in problems if p.level == "warning"]

    for problem in problems:
        print(str(problem), file=stream)

    print("", file=stream)
    if errors:
        print(f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s)", file=stream)
        return 1
    print(f"PASSED: 0 errors, {len(warnings)} warning(s)", file=stream)
    return 0
