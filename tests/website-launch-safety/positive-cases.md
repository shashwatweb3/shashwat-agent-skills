# Positive cases

Requests that clearly should invoke the skill. If the agent does not load the
skill for one of these, the `description` needs work.

---

## P1 - pre-launch check in plain language

Request: `Before I share this website, check whether it is actually safe to launch.`

Context: A Next.js repo with an email signup form, a `/privacy` page, Google
Analytics loaded in the root layout, and a Stripe checkout.

Expected:

- The skill loads.
- All nine areas are reported, each with `PASS`, `ATTENTION`, `FAIL`, or `N/A`.
- The email field is traced from the form to the handler to storage.
- Google Analytics is reported as observed, with its load method.
- The `/privacy` page is compared against what was observed, not just confirmed
  to exist.
- An overall status of `READY TO SHARE`, `NEEDS FIXES`, or `DO NOT SHARE YET`.

Must not:

- Mark the privacy area `PASS` on the basis that `/privacy` exists.
- Claim GDPR, CCPA, or any compliance status.
- Print any environment variable value.

---

## P2 - explicit skill invocation

Request: `/website-launch-safety` (Claude Code) or `$website-launch-safety`
(Codex).

Context: A deployed URL was given in the previous turn.

Expected: The skill loads and runs the workflow against the established target
without asking the user to restate it.

Must not: Restart the scope conversation from scratch.

---

## P3 - handoff of a vibe-coded frontend

Request: `I built this landing page in Cursor. Can you review it before I send it to a client?`

Context: A static site with a contact form posting to Formspree, a YouTube
embed, and no policy pages.

Expected:

- The skill loads, recognising "review before I send it" as a launch-readiness
  request.
- The missing policy pages are reported against the observed contact form, not
  as an abstract compliance gap.
- The YouTube embed is listed in observed third-party services.

Must not:

- Treat "review" as a code review request and only comment on code quality.
- Recommend a CMS migration or a redesign.

---

## P4 - targeted consent question

Request: `We added a Meta Pixel to our site last week. Is that a problem before we launch?`

Context: A React SPA with no consent banner.

Expected:

- The skill loads, because the request is about a launch risk.
- Meta Pixel is confirmed from the implementation, not assumed from the request.
- The absence of a consent mechanism is reported as a consent implementation
  concern, with legal review flagged.
- The remaining eight areas are still covered, briefly.

Must not:

- Answer only the Meta Pixel question and skip the audit.
- State that the site is legally non-compliant.

---

## P5 - accessibility-led launch request

Request: `Is my site accessible enough to launch publicly?`

Context: A marketing site with images and a signup form.

Expected:

- The skill loads.
- Accessibility is checked at the implementation level: alt text, labels,
  focus, contrast, button labels.
- Findings use `Obvious accessibility issue detected.` and, where a browser
  would be needed, `Could not fully verify without browser/visual testing.`
- Consent, data collection, and third-party areas are still covered.

Must not:

- Claim WCAG conformance or certification.
- Stop after accessibility and skip the privacy and consent areas.

---

## P6 - payment launch

Request: `I am launching a paid course site tomorrow. Check everything I might have missed.`

Context: Stripe Checkout, a seven-day refund promise in the terms page, no
refund policy page.

Expected:

- The skill loads.
- The refund area is `FAIL` or `ATTENTION`, with the inconsistency between the
  terms text and the absence of a refund policy called out.
- Stripe is listed in observed third-party services.

Must not: Invent a refund window that the site does not state.
