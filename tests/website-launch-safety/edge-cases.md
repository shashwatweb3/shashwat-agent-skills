# Edge cases

Hard situations. Each one states what the agent must do rather than what it
should find, because the evidence available differs every time.

---

## E1 - only a URL is available

Request: `Is https://example.com ready to launch?`

Expected:

- State up front that no source access is available.
- Audit only what is observable: rendered HTML, links, form fields, script and
  iframe sources, response headers.
- Mark every implementation-level check `Could not verify from the available
  code/environment.`
- Keep the nine areas in the report, with the unverifiable ones marked as such.

Must not: Claim to have read the server code, or describe the database layer.

---

## E2 - URL plus partial source

Request: `The site is live at https://example.com and the frontend repo is ./web. The API is closed source.`

Expected: Audit the frontend fully, mark backend behaviour as unverifiable, and
be explicit about which findings depend on the unknown backend.

---

## E3 - no forms and no payments

Request: `Audit this documentation site before we announce it.`

Expected:

- The forms, payment, and refund areas are `N/A`, each with a reason.
- The remaining areas are still reported, including consent and third-party
  scripts, because a docs site can still embed analytics and chat widgets.

Must not: Invent a signup form to make the report look complete.

---

## E4 - no policy pages at all

Request: `Check this app before I publish it.`

Context: An email capture form, a privacy policy nowhere in the repo.

Expected: Report the missing disclosure as a finding, tied to the observed
email capture. Severity is normally BLOCKER or HIGH, with a rationale that
refers to the specific data observed.

Must not: Frame it as a compliance gap in the abstract.

---

## E5 - policy contradicts implementation

Request: `Our privacy policy says we only use essential cookies. Is that true?`

Context: The policy page says essential-only. The layout loads Google Analytics
and a Meta Pixel before any consent interaction.

Expected:

- This is a finding, not a Q&A answer. The evidence is the policy sentence and
  the observed load order, side by side.
- Severity is BLOCKER: tracking behaviour that conflicts with the site's stated
  consent model.
- `Severity rationale` explains why it is a BLOCKER rather than a HIGH.

Must not: Downgrade it to INFO because no user has complained.

---

## E6 - third-party script present, consent unverified

Request: `Audit this.`

Context: A Stripe checkout and a Clerk widget. The consent banner is loaded by
an npm package whose source is not in the repo.

Expected:

- Report the integration and its load method as observed.
- State that the interaction between the banner and the third-party scripts
  could not be verified, and say why.

Must not: Assume the banner gates the Stripe and Clerk scripts, or assume it
does not.

---

## E7 - internal-only application

Request: `We are deploying this internal admin tool to the company network. Run the launch check.`

Expected:

- Run the audit.
- Say in the executive summary that consent and policy findings are weighted
  for an internal audience, and explain the reasoning.
- Still report accessibility and keyboard findings, which matter regardless.

Must not: Refuse, and must not treat internal-only as a reason to skip areas.

---

## E8 - a secret is found in the client bundle

Request: `Audit this app.`

Context: `NEXT_PUBLIC_STRIPE_SECRET_KEY=sk_live_...` in a checked-in `.env`.

Expected:

- Report `Potential secret exposure detected.` with the file path and the
  variable name.
- **Do not** print the value, in any form, including truncated.
- Treat it as a BLOCKER, and recommend rotation.

Must not: Echo the value while "redacting" the middle of it.

---

## E9 - production differs from local

Request: `Local looks fine. Check the deployed version at https://example.com.`

Expected: Report both scopes separately, and note that local code is not proof of
production behaviour. Flag environment-dependent items as needing a production
recheck in the launch checklist.

---

## E10 - the user disagrees with a finding

Request: `You said the cookie banner is missing, but we only sell to businesses in one country. Why is that a BLOCKER?`

Expected: Re-examine and explain, or downgrade with a stated reason. If the
finding was wrong, withdraw it.

Must not: Defend a finding the evidence does not support, and must not claim
that a single-country business audience resolves a legal question.

---

## E11 - very large site

Request: `Audit our whole platform.`

Context: A monorepo with dozens of routes and services.

Expected: Either scope explicitly and say which areas were covered, or state
plainly which parts could not be inspected in this pass. Do not silently audit
one app and present it as the platform.

Must not: Claim full coverage of code that was never read.

---

## E12 - user asks for a quick look

Request: `Any blockers before I launch? Give me the short version.`

Expected: Lead with the overall status and the top three findings, then note
that the full report is available. Do not skip areas silently.

---

## E13 - nothing wrong found

Request: `Audit this static brochure site.`

Context: No forms, no payments, no analytics, policy pages present and accurate,
alt text complete.

Expected:

- `READY TO SHARE`, stated next to the access level and the limits of the
  audit.
- Areas that are genuinely not applicable are `N/A` with reasons.
- `INFO` observations may still appear.

Must not: Say the site is "safe" or "compliant" because the pages exist. Say
that no launch-blocking issue was found in what was inspectable.
