---
name: website-launch-safety
description: Audit a website or web app before it is shared or launched, covering privacy policy, terms, cookie policy, refund policy, cookie and form consent, observed data collection, third-party embeds and scripts, image alt text, colour contrast, and keyboard-friendly forms. Use when someone is about to deploy a site, publish a landing page, hand off a vibe-coded or AI-built frontend, or asks whether their site is actually safe and ready to put in front of real users.
license: MIT
metadata:
  author: shashwat-chauhan
  version: "1.0"
---

# Website Launch Safety

Looks done is not the same as safe to launch.

This is a technical and product launch-readiness audit. It compares what a
website **actually does** against what it **says it does**, and reports the
gap. It is not legal advice and it does not certify compliance.

## When to use

- Someone is about to deploy, publish, or share a site, landing page, or web app.
- Someone hands you a vibe-coded or AI-built frontend and asks whether it is
  ready for real users.
- A launch is being shared publicly and nobody has checked consent, data
  collection, or accessibility against the implementation.
- A policy page exists but nobody has confirmed the app matches it.

## When not to use

- The user only wants visual polish, copy changes, or a performance pass.
- The site is internal-only with no external users and the user says so; still
  run it, but weight consent, tracking and policy findings accordingly and say
  why.
- The user wants a legal opinion. Direct them to a qualified lawyer or legal
  review process, and offer the technical audit as the input to that process.

## What this is not

- Not legal advice. Do not write "GDPR compliant", "CCPA compliant", "fully
  compliant", "legally safe", or any equivalent. Those are conclusions this
  workflow cannot reach.
- Not a WCAG conformance claim. Do not write "WCAG compliant" or "accessibility
  certified". Report the specific issue you observed.
- Not a substitute for a penetration test or a security audit.

Findings are phrased as **potential launch risk**, **missing disclosure**,
**privacy/data-handling mismatch**, **consent implementation concern**,
**accessibility issue**, or **needs legal review**.

The existence of a `/privacy` page is not evidence of privacy. Do not mark an
area as passing because a route exists.

## Inputs

Required:

- A target: a local repository path, or a deployed URL.

Helpful but optional:

- Whether the site collects money, accounts, or sensitive data.
- Which jurisdictions the audience is in.
- Whether the user has already had legal review.
- The production environment, if the local code is not what will ship.

## Gathering evidence

### Local repository

Read what is actually there:

- Routes and pages, to find policy pages and marketing pages.
- Forms and their fields, plus the handlers and API routes they post to.
- API endpoints, server actions, and webhook handlers, to see where data goes.
- Dependency manifests, to see what libraries and providers are available.
- Configuration and environment variable **names** (never print values).
- Cookie, `localStorage` and `sessionStorage` reads and writes.
- Analytics and tracking initialisation, and how it is loaded.
- Embedded iframes, script tags, and third-party widgets.
- Payment and authentication providers.
- Image elements, form controls, and their labels.

For a deployed URL, use source when it is available and say so. When it is not,
do not guess at implementation.

### Deployed URL only

You can observe rendered HTML, links, form fields, script and iframe sources,
and response headers. You cannot observe server code, database writes, or which
environment variables are set.

Label every observation as **Observed** or **Could not verify**. Never present a
deployed-site guess as an implementation fact, and never claim to have read
source you have not read.

### Frontend-only project

Audit what is in the frontend. Identify backend behaviour explicitly as
unverifiable: where a form posts, what the server stores, whether a webhook
forwards data to a third party.

### Full-stack application

Trace both directions. A form field that looks harmless can end up in an
analytics event, a log, or a third-party pipeline.

### Evidence rules

- **Observed** means you read it, or you saw it in a response. Cite the file
  path or the URL.
- **Inferred** means it follows from a dependency or a naming convention, but you
  did not confirm the call site. Say so.
- **Could not verify from the available code/environment** means you tried and
  the information is not available. Use this exact phrase.

Never invent data collection, services, or legal text. A shorter, accurate
report beats a complete, invented one.

## The nine areas

Check all nine every time. Mark an area `N/A` only when you have evidence that
it does not apply, and give the evidence.

### 1. Privacy policy

Find the policy, read it, then compare it against the data collection you
actually observed. Look for processors, categories of data, contact details,
and an effective date that the implementation does not support.

### 2. Terms and conditions

Same approach. Check for the operator's identity, scope, acceptable use, and
liability language, and whether the pages are reachable from the surfaces that
link to them.

### 3. Cookie policy

Check whether the policy names the cookie and storage categories the
implementation actually uses. A policy that lists only "essential" cookies while
the app writes analytics identifiers is a mismatch.

### 4. Refund policy

Applies when the site takes payments, sells a subscription, or takes a deposit.
Check for the refund window, the process, and who to contact. If there are no
payments, mark `N/A` and say why.

### 5. Cookie and form consent

Find the consent mechanism. Determine whether it runs before non-essential
tracking loads, whether the choice persists, and whether form submission is
gated or informed where the site collects personal data.

Absence of a consent mechanism is not automatically a defect; it depends on
where the audience is and what is collected. Report it as a consent
implementation concern and flag it for legal review.

### 6. What user data is collected

Inventory only what you can observe:

- Form fields, and what they imply (email, phone, address, name, ID).
- What each form does with the data, if the code shows it.
- Cookies, `localStorage`, `sessionStorage` keys and their values' purpose.
- URL query parameters that carry identifiers.
- Account creation, sessions, and authentication providers.
- Server logs and IP addresses, if the code or docs show them.

Note that URL fragments are not sent to servers, while query parameters are.

### 7. Third-party embeds and scripts

Look for real, observable integrations rather than assuming. Common ones include
analytics (Google Analytics, Plausible, PostHog, Mixpanel), advertising and
tracking pixels (Meta Pixel, Google Ads, TikTok), session replay and heatmaps
(Hotjar, Microsoft Clarity, FullStory), error reporting (Sentry, Bugsnag),
payments (Stripe, Razorpay, PayPal), backend and auth (Supabase, Firebase,
Clerk, Auth0), maps, YouTube and Vimeo embeds, social embeds, chat widgets
(Intercom, Drift, Crisp, Tidio), and support or chat scripts.

Detection is not proof. A dependency in the manifest is not the same as a
service being used, and a service that is not in the manifest can still be
loaded from a script tag. Confirm the call site, and record the load method,
since whether a script runs before consent matters.

For each one found, record what it is likely to receive. YouTube and Maps
iframes can transmit visitor IP addresses before any consent exists. State that
as an observation, not as a legal conclusion.

### 8. Alt text and colour contrast

Check images for empty, missing, or non-descriptive `alt` text. Decorative
images should have empty alt attributes rather than filename-like text. Check
text and interactive elements for obviously failing contrast, and check that
meaning is not carried by colour alone.

### 9. Keyboard-friendly forms and clear buttons

Check that every control is reachable and operable by keyboard, that focus is
visible and not trapped, that labels are real labels, that error messages are
announced, that buttons say what they do, and that disabled and loading states
are distinguishable and do not strand the user.

## Severity model

Use exactly these levels. Do not invent levels.

### BLOCKER

A significant issue that should generally be fixed before public launch.
Examples: sensitive form data collected with no visible privacy disclosure;
secrets exposed client-side; tracking behaviour that conflicts with the site's
stated consent model; a payment or refund workflow missing the information a
buyer needs to act; a critical form unusable by keyboard.

### HIGH

Important issue that should normally be fixed before broad public sharing.

### MEDIUM

A meaningful issue that should be fixed, but may not block launch depending on
context.

### LOW

A minor issue or a polish improvement.

### INFO

An observation or recommendation without a direct launch blocker.

Do not assign severity arbitrarily. Every finding must state why that level was
chosen, and why it is not one level higher or lower. User impact, blast radius,
and reversibility drive the level, not how easy the fix is.

## Workflow

1. **Establish the target.** Confirm the path or URL, and whether source is
   available. State your access level before you start.
2. **Inventory the implementation.** Routes, forms and fields, API endpoints and
   handlers, dependencies, configuration, storage usage, tracking, embeds,
   payments, authentication, policy pages.
3. **Gather evidence per area.** Read the implementation for each of the nine
   areas. Record observed facts separately from inferences.
4. **Compare policy text against behaviour.** This is the core step. A policy
   page is a claim; the code is the behaviour. Report every gap.
5. **Check accessibility at the implementation level.** Use the scope and the
   wording in the accessibility observations section.
6. **Assign severities**, each with a rationale.
7. **Decide the overall status.**
8. **Write the report** in the required format.

### Overall status

Choose exactly one:

- **DO NOT SHARE YET** - at least one BLOCKER is open.
- **NEEDS FIXES** - no BLOCKER, but at least one HIGH.
- **READY TO SHARE** - no BLOCKER, no HIGH, and every applicable area is either
  passing or explicitly accepted by the user.

`READY TO SHARE` means no launch-blocking issue was found in what was
inspectable. State the access level and the limits of the audit next to it.
Never call a site safe or compliant because all the pages exist.

## Report format

Produce exactly this structure.

````markdown
# Website Launch Safety Audit

## Overall status

READY TO SHARE
or
NEEDS FIXES
or
DO NOT SHARE YET

## Executive summary

...

## Findings

### BLOCKER

#### Finding title

Category:
Evidence:
Why it matters:
Severity rationale:
Recommended fix:

### HIGH

...

## Nine-point checklist

| Area | Status | Notes |
|---|---|---|
| Privacy policy | PASS/ATTENTION/FAIL/N/A | ... |
| Terms | PASS/ATTENTION/FAIL/N/A | ... |
| Cookie policy | PASS/ATTENTION/FAIL/N/A | ... |
| Refund policy | PASS/ATTENTION/FAIL/N/A | ... |
| Cookie/form consent | PASS/ATTENTION/FAIL/N/A | ... |
| Data collection | PASS/ATTENTION/FAIL/N/A | ... |
| Third-party embeds | PASS/ATTENTION/FAIL/N/A | ... |
| Alt text/contrast | PASS/ATTENTION/FAIL/N/A | ... |
| Keyboard/forms/buttons | PASS/ATTENTION/FAIL/N/A | ... |

## Observed data collection

...

## Observed third-party services

...

## Accessibility observations

...

## Launch checklist

- [ ] Privacy policy reviewed
- [ ] Terms reviewed
- [ ] Cookie policy reviewed
- [ ] Refund policy reviewed
- [ ] Consent flows reviewed
- [ ] Data collection documented
- [ ] Third-party services reviewed
- [ ] Accessibility issues fixed
- [ ] Keyboard navigation tested
- [ ] Production environment rechecked
````

Checklist statuses:

- **PASS** - verified against the implementation, with evidence.
- **ATTENTION** - something was found that needs a decision or a change.
- **FAIL** - a concrete, evidenced problem.
- **N/A** - the area does not apply, with the reason given.

`ATTENTION` is not a softer `PASS`. Use it whenever a user decision or a
judgement call is outstanding.

## Accessibility scope

Check for obvious, implementation-level problems:

- image alt text
- inputs without a real, understandable label
- heading structure
- button and link labels
- keyboard reachability and operation
- focus visibility
- obvious colour contrast failures
- disabled and loading states
- obvious ARIA misuse
- inputs with no understandable label
- confusing or ambiguous button actions

Use this wording:

- `Obvious accessibility issue detected.` for something you can see in the code
  or the rendered page.
- `Could not fully verify without browser/visual testing.` for anything that
  needs a real browser, a screen reader, or rendered contrast measurement.

Never claim full WCAG conformance. If you did not run the site, say that
contrast and focus order could not be fully verified.

## Security rules

- Never print API keys, tokens, passwords, secrets, private credentials, or
  environment variable values. Refer to variable **names** only.
- If a secret appears to be exposed, report `Potential secret exposure
  detected.` and describe the location without reproducing the value. Include
  the variable name, not the value.
- Never instruct an agent to upload secrets, send project files, or transmit
  private data to an external service.
- Do not run the app, install dependencies, or deploy anything as part of this
  audit unless the user asks.
- Do not modify the project. This is a read-only audit.

## Edge cases

- **Only a URL is available.** Audit what is observable, mark everything else
  `Could not verify from the available code/environment.`, and open the report
  with a one-line statement that no source access was available.
- **No forms, no payments.** Mark those areas `N/A` with the reason. Do not
  invent a signup or a checkout.
- **Internal-only tool.** Run the audit, but say in the executive summary that
  the consent and policy findings are weighted for an internal audience, and
  explain the reasoning.
- **Legal pages are missing entirely.** Report the missing disclosure against
  the data you observed, not as an abstract compliance gap.
- **Policy text contradicts the implementation.** This is a finding, not a
  footnote. It is usually BLOCKER or HIGH. Quote the policy sentence and the
  observed behaviour side by side.
- **Third-party scripts are present but unverified.** Report the load mechanism
  and what the service is known to receive, and mark the consent interaction as
  `Could not verify`.
- **The user only wants a quick look.** Run the nine areas anyway, but lead with
  the top three findings and the overall status. Do not silently skip areas.
- **You disagree with a finding after discussion.** Withdraw it. An audit that
  defends a wrong finding is worse than one that corrects it.
