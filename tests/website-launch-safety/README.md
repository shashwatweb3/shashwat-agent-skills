# website-launch-safety test cases

These cases document **expected agent behaviour** for a human to check by
hand. They are not automated assertions: judging model reasoning is not
reliable enough to gate a pull request on, and pretending otherwise would make
the tests theatre.

What *is* automated lives one directory up:

- `tests/run-tests` runs the tooling checks.
- `tests/test_tooling.py` unit-tests the validator and lister.
- `tests/run-tests` also asserts that every skill has a test-case directory
  here, so a new skill cannot ship undocumented.

## Files

| File                  | Purpose                                                    |
| --------------------- | ---------------------------------------------------------- |
| `positive-cases.md`   | Requests that clearly should invoke the skill               |
| `indirect-cases.md`   | Requests that should be recognised naturally, without saying "audit" |
| `non-trigger-cases.md`| Requests that should not invoke the skill                   |
| `edge-cases.md`       | Hard situations, and what the agent must do in each         |

## How to run a case by hand

1. Install the skill in the agent you are testing (see the repository README).
2. Paste the request verbatim. Do not paraphrase it; wording drives triggering.
3. Check the behaviour against `Expected behaviour` and `Must not`.
4. Record whether the agent loaded the skill at all, and whether it loaded it
   for the right reason.

## Case format

```text
## <case id> - <one line name>

Request:      the verbatim user message
Context:      what exists in the project or environment
Expected:     what the agent should do
Must not:     what would make this a failure
```

## Scoring a run

- **Pass** - expected behaviour present, none of `Must not` present.
- **Partial** - the workflow was followed but something required, such as
  separating observed from unverified, is missing.
- **Fail** - `Must not` triggered, or the skill was not invoked when it should
  have been.

A run that invents an observation, or claims a compliance conclusion, is always
a fail, regardless of the rest of the output.
