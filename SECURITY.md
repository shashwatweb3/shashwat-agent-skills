# Security

## Skills are executable instructions

A skill is not documentation. It is a set of instructions an agent follows, and
it can cause an agent to read files, run commands, call network endpoints, or
edit your project. Treat installing a skill with the same care as installing a
package.

Read the `SKILL.md` before you install it, especially any `scripts/` directory
it contains.

## Rules for contributing a skill

Every skill in this repository must:

- **Never contain secrets.** No API keys, tokens, passwords, private keys, or
  real `.env` values. Not in examples, not in test fixtures, not in comments.
- **Never request credentials it does not need.** If a skill does not need a
  credential to do its job, it must not ask for one.
- **Never instruct an agent to send project data anywhere.** Skills must not
  upload files, source code, credentials, or environment values to an external
  service. If a workflow needs a network call, it must say exactly what is sent
  and why.
- **Never instruct an agent to execute code it downloaded.** No
  `curl ... | bash`, no "run this to install the dependency". Agents may run
  bundled `scripts/`, and those must be readable in the pull request.
- **Avoid destructive commands.** No `rm -rf`, no force pushes, no dropping
  tables, no rewriting history, unless the task genuinely requires it. A skill
  that must be destructive has to say so explicitly and ask first.
- **Read-only by default.** A skill should inspect and report unless its entire
  purpose is to change something.
- **Reference external resources by URL with a reason.** A link the reader is
  expected to fetch is fine; a link that quietly sends project content is not.

## Reviewing a third-party contribution

Before installing a skill from outside this repository:

1. Read the whole `SKILL.md`, not just the `description`.
2. List every file in the skill directory. Anything under `scripts/` executes.
3. Search the text for network calls, `curl`, `wget`, `eval`, base64, and
   encoded blobs.
4. Check that it does not read `~/.ssh`, `~/.aws`, `.env`, or credentials
   without a stated reason.
5. Check that any script it runs is short enough to read end to end.

Pull requests from outside contributors are reviewed against the rules above.
Do not merge a skill you have not read.

## Reporting a problem

Report a security issue through GitHub's private vulnerability reporting on this
repository, or by contacting the maintainer directly. Please do not open a
public issue for an unfixed vulnerability.

Report:

- the skill name and the file path within it
- what the skill instructs the agent to do
- why you believe it is unsafe
- a reproduction, if you have one

Valid reports are fixed and credited. Reports that turn out to be a
misunderstanding are still welcome; we would rather explain than have you stop
reporting.
