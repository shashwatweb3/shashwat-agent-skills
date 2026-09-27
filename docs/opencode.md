# OpenCode

OpenCode reads the standard Agent Skills format. The file is `SKILL.md` with
frontmatter, and it is never modified for OpenCode.

## Option 1: point OpenCode at this repository (recommended)

Add the `skills/` directory to `skills.paths` in your `opencode.json`. OpenCode
scans the given paths recursively for `**/SKILL.md`.

```jsonc
// opencode.json  (project, or ~/.config/opencode/opencode.json for global)
{
  "$schema": "https://opencode.ai/config.json",
  "skills": {
    "paths": ["/path/to/shashwat-agent-skills/skills"]
  }
}
```

That loads every skill in the repository, and keeps working as skills are added.
`paths` also accepts a relative path, so if the repository is a sibling of your
project, `"../shashwat-agent-skills/skills"` works.

## Option 2: symlink one skill into a project

If you only want one skill in one project:

```bash
mkdir -p .opencode/skills
ln -s /path/to/shashwat-agent-skills/skills/website-launch-safety \
        .opencode/skills/website-launch-safety
```

OpenCode scans `.opencode/skill/` and `.opencode/skills/` in a project, and
`~/.config/opencode/skill(s)/` globally. Both singular and plural work.

## Option 3: the global external directories

OpenCode also auto-loads skills from `~/.claude/skills/` and
`~/.agents/skills/` without any configuration. If you keep a personal copy of a
skill in either directory, OpenCode picks it up.

## Notes

- `skills.paths` and `skills.urls` are the two keys. `paths` is an array of
  paths or globs; `urls` serves a list of skills over HTTP.
- The skill `name` must be lowercase hyphen-separated, at most 64 characters,
  and match its folder name. A skill with no `description` is filtered out and
  never shown to the model, so the description is effectively required.
- Frontmatter is the Agent Skills set. OpenCode documents `license`,
  `compatibility`, and `metadata` as optional, exactly as the specification does.
- Config is read at startup, so quit and restart OpenCode after changing
  `opencode.json`.
- `opencode.json` must declare `"$schema": "https://opencode.ai/config.json"`.
  OpenCode validates config strictly and refuses to start on a bad field.
- This repository's own tooling is separate: run `./scripts/validate-skills`
  here to check a skill before you point OpenCode at it.
