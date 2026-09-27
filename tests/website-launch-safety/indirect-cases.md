# Indirect cases

Requests with no audit vocabulary at all. The agent should recognise the
workflow from context, not because the user said "audit" or "launch safety".

---

## I1 - vibe-coded pre-launch check

Request: `I vibe coded this landing page. Can you do a pre-launch check?`

Context: A single-page React app with a waitlist email form and a testimonial
carousel.

Expected: The skill loads. "Pre-launch check" on a freshly built site is the
canonical trigger.

Must not: Ask what kind of check the user wants before loading the skill.

---

## I2 - nervous about sharing a link

Request: `I built this over the weekend and I am nervous about sharing the link publicly. Is there anything obviously wrong with it?`

Context: A static marketing page, source available.

Expected: The skill loads. The user is describing exactly the workflow without
naming it. Lead with the overall status and the top three findings, and be
reassuring where the evidence supports it.

Must not: Only answer the emotional question and skip the audit.

---

## I3 - handoff to another person

Request: `Handing this off to my client tomorrow. Anything I should fix first?`

Context: A full-stack app with auth and a database.

Expected: The skill loads. Report findings ordered by severity so the top of
the report is what the user needs tomorrow.

Must not: Produce an unstructured wall of observations.

---

## I4 - data question that is really a launch question

Request: `Does my site send my visitors' emails anywhere I should know about?`

Context: A Next.js app with Supabase Auth, Resend for magic links, and PostHog
for analytics.

Expected: The skill loads, because the question is about data handling on a
site. Answer the question directly first, then report the surrounding launch
findings.

Must not: Answer the data question and omit consent and policy comparison.

---

## I5 - design partner preview

Request: `Opening this up to 50 design partners next week. What do I need to sort out before then?`

Context: A SaaS marketing site with a trial signup, Intercom, and a Sentry
integration.

Expected: The skill loads. Scope the audit to what changes at small scale, and
say that a 50-user preview is lower risk than a public launch while still
reporting the same findings.

Must not: Refuse to run the audit because the audience is small.

---

## I6 - asking about a specific observation

Request: `I noticed a Hotjar script on a site I built. Is that going to be a problem?`

Context: The user has the repo open.

Expected: The skill loads. Verify the Hotjar integration from the code rather
than reasoning from the user's statement, then report it against the consent
model the site actually implements.

Must not: Treat the user's description as verified evidence.

---

## I7 - competitive comparison framing

Request: `Compare my site to what a launch-ready site looks like. Mine is at ./site.`

Context: A repo with a checkout flow and no policy pages.

Expected: The skill loads. Run the audit and present the gaps as the difference
between the two.

Must not: Turn it into a feature comparison against competitor products.
