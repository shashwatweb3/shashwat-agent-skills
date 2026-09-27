# Claude Code

Claude Code reads the standard Agent Skills format, so the repository's
`SKILL.md` files are used unmodified.

## Option 1: install as a plugin (recommended)

This repository is a valid Claude Code plugin, verified against
`claude plugin validate` and an end-to-end install.

```bash
# Add this repository as a marketplace
claude plugin marketplace add shashwatweb3/shashwat-agent-skills

# Install the plugin
claude plugin install shashwat-agent-skills@shashwat-agent-skills
```

Skills load namespaced under the plugin, so the skill appears as
`/shashwat-agent-skills:website-launch-safety` and is also available to the
agent automatically when a request matches its description.

## Option 2: symlink a skill into a project

To use one skill in one project without installing the plugin:

```bash
mkdir -p .claude/skills
ln -s /path/to/shashwat-agent-skills/skills/website-launch-safety \
        .claude/skills/website-launch-safety
```

Claude Code scans `.claude/skills/` in a project and `~/.claude/skills/`
globally. A skill is invoked as `/skill-name` with the name of its directory.

## The plugin manifest

`.claude-plugin/plugin.json` holds the plugin metadata. `skills/` is Claude
Code's default skills location, so the manifest does not declare a `skills`
path. Check a change with:

```bash
claude plugin validate /path/to/shashwat-agent-skills
```

Note that `displayName` is documented in the current manifest reference but is
rejected as an unrecognized key by Claude Code 2.1.71, so the manifest omits it.

## Names to avoid

Claude Code reserves the skill names `synced` and `anthropic-skills`, and will
refuse to load a skill that uses either. The repository validator rejects both.

## Notes

- Claude Code accepts extra frontmatter keys that other clients do not, but
  claude.ai uploads and the Anthropic Skills API reject them. This repository
  restricts frontmatter to the specified set so every skill stays portable.
- Keep the body under roughly 500 lines. Put long checklists and background in
  `references/` instead of growing `SKILL.md`.
- Behaviour cases under `tests/<skill-name>/` are for human review. There is no
  automatic judge for model reasoning in this repository.
