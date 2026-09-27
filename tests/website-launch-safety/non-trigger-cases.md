# Non-trigger cases

Requests that should **not** invoke the skill. Loading it here wastes context
and produces findings the user did not ask for.

The skill's `description` is scoped to pre-launch readiness. General frontend
and design work sits outside it.

---

## N1 - visual polish

Request: `Make my landing page prettier.`

Must not: Run a launch audit. This is a design change request.

Correct behaviour: Discuss or implement the visual changes. If the user also
mentions launching, the skill may become relevant.

---

## N2 - accessibility fix in progress

Request: `Add alt text to all the images in my hero section.`

Must not: Run a nine-area audit. This is a specific accessibility fix.

Correct behaviour: Add the alt text. Offer, without asserting, that a full
launch check is a separate task.

---

## N3 - performance work

Request: `My site is slow. Help me cut the bundle size.`

Must not: Run a launch audit.

---

## N4 - writing policy copy

Request: `Write a privacy policy for my SaaS.`

Must not: Run a launch audit. The user is asking for content, not an audit of
an existing implementation.

Correct behaviour: Help draft it, and note that the finished policy should be
compared against the implementation. Legal review is the appropriate route for
the policy itself.

---

## N5 - debugging a form

Request: `My contact form does not submit. Fix it.`

Must not: Run a launch audit. This is a specific bug.

---

## N6 - refactor request

Request: `Split this component into smaller pieces.`

Must not: Run a launch audit.

---

## N7 - feature work on an app with no launch framing

Request: `Add a coupon field to my checkout.`

Must not: Run a launch audit. Note that adding a field may change what the
privacy policy must describe, but do not start the audit unprompted.

---

## N8 - SEO

Request: `Improve my SEO and get me on page one.`

Must not: Run a launch audit. A dedicated SEO skill would be the right tool.

---

## N9 - general code review

Request: `Review my PR.`

Must not: Run a launch audit. This is a code review.

---

## N10 - asking about the skill itself

Request: `What does the website-launch-safety skill do?`

Must not: Run the audit. Answer the question about the skill.

Correct behaviour: Summarise the workflow and the nine areas. If the user then
provides a target, run the audit.

---

## Borderline cases

Two requests where either behaviour is defensible. What matters is that the
agent is deliberate rather than accidental.

### B1 - explicit launch of a *new* feature

Request: `I am shipping the new pricing page tomorrow. Anything to worry about?`

Options: run the audit, or audit only the pricing page's consent, tracking and
policy implications.

Either is acceptable. What is not acceptable is silently doing nothing, or
running a full audit of unrelated areas and burying the pricing-page findings.

### B2 - "is it safe" about a non-website project

Request: `Is it safe to run this script?`

Must not: Run the launch audit. The word "safe" alone is not a trigger; the
target has to be a website or web app going in front of users.
