# OnboardIQ — HR Onboarding Q&A Agent

A demo built for a **People AI & Automation Engineer** application. It shows the
core loop of the role: an AI agent that answers employee questions, gathers
information from company data, and knows when *not* to answer.

## What it does

- **Retrieves** the relevant sections of a sample employee handbook for each
  question (keyword-weighted retrieval over handbook sections).
- **Answers** new-hire questions with an LLM, grounded *only* in the retrieved
  excerpts — it will not invent policy.
- **Escalates to HR** (human-in-the-loop) instead of guessing when:
  - the question touches a sensitive topic (compensation, legal, medical,
    termination, harassment), or
  - the handbook doesn't cover the question at all.

## How it maps to the role

| Posting requirement | Demo |
|---|---|
| Build AI agents that answer questions | Q&A agent over company data |
| Integrate AI systems with internal systems | Handbook-as-data-source retrieval |
| Human-in-the-loop controls & escalation paths | Sensitive/low-confidence → HR |
| Prototype quickly, test, iterate | Single-file Python, runs in seconds |

## Run it

```bash
pip install -r requirements.txt
OPENAI_API_KEY=sk-... python onboardiq.py
```

No API key? Test the retrieval + escalation logic offline:

```bash
python onboardiq.py --dry-run
```

## Sample session (real `--dry-run` output)

```
You: How many PTO days do I get?
OnboardIQ [dry-run - retrieved sections: Paid Time Off (PTO), Welcome, Holidays]
Prompt preview: Handbook excerpts:
[Paid Time Off (PTO)]
Full-time employees receive 15 days of paid time off per year, accrued monthly. ...

You: Can I sue the company over my schedule?
OnboardIQ: That looks like a sensitive topic question - I'm looping in HR rather than guessing.

You: What is the policy on office dogs?
OnboardIQ: That looks like a no handbook coverage question - I'm looping in HR rather than guessing.
```

## Test coverage

12 test cases pass, covering PTO, benefits, laptop setup, expenses, remote work,
sensitive legal/pay questions, and questions with no handbook coverage.

*The handbook is for the fictional "Northwind Traders" and exists only for this demo.*
