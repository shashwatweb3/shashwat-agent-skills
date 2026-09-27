# Contributing

Thanks for adding a skill.

## The one rule that matters most

**A skill is written once, under `skills/<skill-name>/SKILL.md`, and is
tool-agnostic.**

Do not create a Claude version and a Codex version of the same skill. Do not
fork a skill because one platform wanted a different file. The canonical skill
lives at `skills/<skill-name>/SKILL.md`, and every platform consumes that same
directory.

If a platform needs something extra, add it as packaging or documentation that
*points at* `skills/`. Never a copy of the instructions.

The validator enforces this directly: a `SKILL.md` found anywhere outside
`skills/` is an error, with the single exception of `templates/skill/SKILL.md`.
So you cannot accidentally commit `skills/<name>/`, then copy it into
`.claude/skills/`, `.agents/skills/`, `.opencode/skills/` or a build directory.
If a client wants a different location, symlink it at install time, or install
the plugin. Do not commit the copy.

`templates/skill/SKILL.md` is deliberately outside `skills/`, so it is a
starting point and never loads as a skill in any client. It is also exempt from
the behaviour-case requirement.

## Adding a skill

```bash
cp -r templates/skill skills/my-new-skill
```

Then edit `skills/my-new-skill/SKILL.md` and write behaviour cases under
`tests/my-new-skill/`.

`templates/skill/README.md` walks through the steps in detail.

There is no registry to update. `skills/` is the source of truth, and
`scripts/list-skills` plus `scripts/validate-skills` discover skills by scanning
it. Adding a skill requires no other edit anywhere.

## Naming

- Lowercase letters, digits, and single hyphens: `seo-audit`, `pr-review`.
- Start with a letter, end with a letter or digit.
- 1 to 64 characters.
- No underscores, capitals, spaces, or consecutive hyphens.
- The directory name must equal the `name` value in the frontmatter.
- The name describes the **workflow**, not the tool: `accessibility-audit`, not
  `axe-runner`.

Avoid the names `synced` and `anthropic-skills`. Claude Code reserves them and
will not load a skill that uses either.

## Frontmatter

Required:

```yaml
---
name: my-new-skill
description: What the skill does, and when an agent should reach for it.
---
```

Optional: `license`, `compatibility`, `metadata`, `allowed-tools`.

**No other keys.** Claude Code accepts extra keys, but claude.ai uploads and the
Anthropic Skills API reject the file outright. The validator treats an unknown
key as an error for that reason. If you need platform-specific behaviour, put it
in the body as prose, or in a separate packaging file that does not touch
`SKILL.md`.

### Writing the description

The description is the only part of a skill an agent sees before it decides to
load it, so it does the discovery work. A host may truncate it, so front-load
the use case.

Good:

```yaml
description: Audit a website before launch for privacy, consent, accessibility, third-party services, and other launch-readiness risks.
```

Bad:

```yaml
description: Helps with websites.
```

Rules:

- Say what the skill does, then when to use it.
- Include the words a user would actually type: `audit`, `review`, `check`,
  `before launch`, `accessibility`.
- Keep it under 1024 characters, and much shorter than that if you can.
- Do not put the workflow in the description. That belongs in the body.
- Do not shout. `MUST ALWAYS USE THIS SKILL` is not a trigger, it is noise. The
  validator warns on it.

## Writing the body

Keep `SKILL.md` focused. The specification recommends under 500 lines, and a
skill body stays in context once loaded, so every line is a recurring cost.
Move detail out rather than writing it inline.

Structure that works:

| Section     | What goes in it                                            |
| ----------- | ---------------------------------------------------------- |
| Purpose     | The user problem, in a sentence or two                       |
| When to use | Requests that should trigger it, and ones that should not   |
| Inputs      | What the workflow needs, required versus optional            |
| Workflow    | Numbered, imperative steps in the order that gives a result  |
| Rules       | The constraints that are not obvious from the steps          |
| Output      | The exact expected shape, with allowed values enumerated     |
| Edge cases  | What to do when information is missing or unverified         |

Delete sections that genuinely do not apply. A short skill is better than a
padded one.

A skill should solve **one** recognisable problem. If you find yourself writing
`and also` in the description, split it. `ultimate-web-development-everything`
is not a skill; it is a project.

## When to add supporting directories

Only when the content genuinely does not belong in `SKILL.md`. Do not create
them to look thorough, and do not ship an empty one.

### `references/`

Documentation the agent reads only when it needs it: long checklists, domain
background, detailed format specifications, worked examples. Keep each file
focused, because the agent loads the whole file it opens. Reference them with
relative paths from the skill root:

```markdown
See [the consent decision tree](references/consent.md) for which cookies need consent.
```

Keep references one level deep. Avoid chains of reference.

### `scripts/`

Deterministic, repeatable operations where prose instructions would be
error-prone: parsers, formatters, checkers. A skill works fine with none.

- Use the Python standard library, or a language already present in the
  environment.
- Declare every dependency and pin versions.
- Support `--help`.
- Fail loudly with a clear message rather than exiting zero on error.
- Never print secret values.
- Add `[PEP 723](https://peps.python.org/pep-0723/)` inline metadata if the
  script needs third-party packages, so `uv run scripts/check.py` just works.

### `assets/`

Files the agent copies or fills in: templates, fixtures, boilerplate the user
will reuse. Not for things the agent only reads; that is `references/`.

## Testing a skill

Behaviour test cases are Markdown under `tests/<skill-name>/`. They document
what an agent should do so a human can check it.

Do **not** try to automate judgement of model reasoning. It is not reliable
enough to gate a merge on, and a test that only passes sometimes is worse than
no test. Document the cases; check them by hand.

Cover four kinds:

| File                   | Contents                                             |
| ---------------------- | ---------------------------------------------------- |
| `positive-cases.md`    | Requests that clearly should invoke the skill        |
| `indirect-cases.md`    | Requests that should be recognised without keywords  |
| `non-trigger-cases.md` | Requests that should **not** invoke it                |
| `edge-cases.md`        | Hard situations, and the required behaviour          |

`tests/run-tests` checks that every skill has these files and that they contain
real cases, so a new skill cannot ship undocumented.

Follow `tests/website-launch-safety/` for the level of detail expected.

## Validating

```bash
./scripts/validate-skills          # add --strict to fail on warnings
./scripts/list-skills              # add --markdown or --json
./tests/run-tests                  # everything
```

`validate-skills` checks frontmatter, naming, required fields, unknown keys, file
references, Markdown links, UTF-8, hidden directories, duplicate names, and the
template. It exits non-zero on any error.

## Submitting a pull request

1. `cp -r templates/skill skills/my-new-skill`, or edit an existing skill.
2. Fill in `skills/<skill-name>/SKILL.md`.
3. Add `tests/<skill-name>/`.
4. Run `./tests/run-tests` until it passes.
5. Update the `Available skills` section of `README.md`. The list must match
   `./scripts/list-skills --markdown`; the test suite enforces this.
6. Open the PR describing the workflow, the trigger, and what it deliberately
   does not do.

CI runs `validate-skills` on every push and pull request that touches
`skills/`, `templates/`, `scripts/`, or the workflow itself.

## Review criteria

A reviewer will ask whether the skill:

- **Triggers** — can an agent tell when to use it from the description alone?
- **Scopes** — does it solve one recognisable workflow?
- **Specifies inputs** — is it clear what information it needs?
- **Is executable** — are the steps explicit without being bloated?
- **Separates evidence** — does it distinguish observed facts from assumptions?
- **Is predictable** — does it define the output shape?
- **Fails honestly** — does it say what to do when something cannot be verified?
- **Is safe** — no unnecessary destructive actions, credential exposure, or data
  exfiltration?
- **Is portable** — the same file works in any Agent Skills client?

## Licence

Contributions are accepted under the [MIT Licence](LICENSE).
