# Codex CLI

Codex reads the standard Agent Skills format, so the repository's `SKILL.md`
files are used unmodified.

## Option 1: install as a plugin (recommended)

This repository ships a portable plugin manifest at `plugin.json` and a
marketplace catalog at `.agents/plugins/marketplace.json`, verified end to end
with `codex plugin marketplace add` and `codex plugin add`.

```bash
# Add this repository as a marketplace
codex plugin marketplace add shashwatweb3/shashwat-agent-skills

# Install the plugin
codex plugin add shashwat-agent-skills@shashwat-agent-skills
```

Confirm what is available:

```bash
codex plugin list
codex plugin marketplace list
```

To remove it again:

```bash
codex plugin remove shashwat-agent-skills@shashwat-agent-skills
codex plugin marketplace remove shashwat-agent-skills
```

## Option 2: symlink a skill into a project

To use one skill in one project without installing the plugin:

```bash
mkdir -p .agents/skills
ln -s /path/to/shashwat-agent-skills/skills/website-launch-safety \
        .agents/skills/website-launch-safety
```

## About the two manifests

- `plugin.json` at the repository root is the portable Agent Plugins manifest.
  It declares `$schema`, `name`, `version`, `description`, `author`,
  `homepage`, `repository`, `license`, and `keywords`. A portable package
  discovers `skills/` by fixed path, so it declares no `skills` key.
- `.claude-plugin/plugin.json` is the Claude Code manifest for the same
  repository. Claude Code only reads that path, and Codex only reads the root
  `plugin.json`. Neither file duplicates a `SKILL.md`.

## Notes

- There is no central registry to update. Codex discovers skills by scanning
  `skills/`, so adding a skill to this repository needs no other change.
- A skill's `name` must match its directory, be lowercase hyphen-separated, and
  be at most 64 characters. The validator enforces all three.
- `template/skill/SKILL.md` is a starting point, not a loadable skill. It sits
  outside `skills/`, so neither client picks it up.
- Run `./scripts/validate-skills` here before publishing a change.
