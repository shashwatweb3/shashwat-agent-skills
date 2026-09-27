name: Skill request
description: Propose a new agent skill for this repository
title: 'skill: <skill-name>'
labels: ['skill-request']
body:
  - type: markdown
    attributes:
      value: |
        Thanks for proposing a skill. Before you submit, read [CONTRIBUTING.md](../../CONTRIBUTING.md) and note: **a skill must live once at `skills/<skill-name>/SKILL.md` and be tool-agnostic.**

  - type: input
    id: name
    attributes:
      label: Skill name
      description: Lowercase letters, digits, hyphens. Must match the directory name.
      placeholder: 'website-accessibility-check'
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: One-sentence use case
      description: What does this skill do, and when should an agent reach for it?
      placeholder: 'Audit public pages for WCAG 2.2 issues before publishing a site.'
    validations:
      required: true

  - type: textarea
    id: inputs
    attributes:
      label: Required inputs
      description: What information must be provided (URLs, paths, environment, etc.)
      placeholder: 'A list of base URLs to audit. Credentials are not required.'
    validations:
      required: false

  - type: textarea
    id: workflow
    attributes:
      label: High-level workflow (3–6 steps)
      description: The concrete steps the skill would follow, in order.
      placeholder: |
        1. Collect the provided URLs
        2. Check that each URL is publicly reachable
        3. Run the agreed checks
        4. Report findings, distinguishing observed from unverified
        5. Return a structured summary
    validations:
      required: true

  - type: textarea
    id: outputs
    attributes:
      label: Expected output shape
      description: The exact format the agent should return (fields, allowed values).
      placeholder: |
        A markdown report with sections: summary, blockers, findings (with severity), evidence, and open questions.
    validations:
      required: true

  - type: textarea
    id: not-doing
    attributes:
      label: What will this skill deliberately NOT do?
      description: Scope is more important than features. List exclusions explicitly.
      placeholder: |
        - It will not fix code (report-only)
        - It will not log in to sites
        - It will not send page content to third-party services
        - It will not require an API key
    validations:
      required: true

  - type: textarea
    id: test-cases
    attributes:
      label: Proposed behaviour test cases
      description: Suggest at least two positive cases and one non-trigger case.
      placeholder: |
        Positive: "Audit example.com before launch"
        Indirect: "Is example.com ready to go live from an accessibility standpoint?"
        Non-trigger: "Deploy example.com" (deployment task, not audit)
    validations:
      required: true

  - type: checkboxes
    id: checklist
    attributes:
      label: Pre-submission checklist
      options:
        - label: I have read CONTRIBUTING.md and the specification.
          required: true
        - label: This is one workflow under `skills/<skill-name>/SKILL.md`, not platform-specific copies.
          required: true
        - label: The skill needs no secrets and defaults to read-only.
          required: true
        - label: I will add behaviour test cases under `tests/<skill-name>/`.
          required: true
