# AI Response Evaluation Portfolio

**Cybersecurity and IT domain evaluations of AI model outputs, scored against a consistent rubric and verified by testing, not by trust.**

This repo shows how I evaluate AI-generated answers in my domain: Linux security, networking, incident response, and Python security tooling. Each evaluation compares responses, scores them on the same rubric, quotes the exact problem, and proves each claim with documentation or code that runs.

It's the same work AI training platforms ask for in RLHF, response ranking, and code review tasks, applied to technical content where a confident-sounding answer can still be dangerously wrong.

---

## Method

1. **Same prompt, multiple responses.** Each evaluation starts from one realistic user prompt with a named environment.
2. **One rubric for everything.** Correctness, completeness, safety, instruction following and clarity, scored 1 to 5 against written anchors. Code tasks add code quality. See [RUBRIC.md](RUBRIC.md).
3. **Verify, don't trust.** Log paths, defaults and commands are checked against documentation. Code is run against test data that includes the edge cases, in [`scripts/`](scripts).
4. **Label the evidence.** Every issue quotes the exact line, gets a severity, and is marked Documented, Executed, or Reasoned.
5. **Show what "right" looks like.** Each verdict ends with a suggested ideal response.

## Evaluations

| # | Task | Domain | Type | Verdict | Key finding |
|---|---|---|---|---|---|
| [001](evaluations/001-ssh-bruteforce-response.md) | Detect and stop an SSH brute-force attack | Linux security | Pairwise | A, clear margin | B points Ubuntu users to `/var/log/secure`, a Red Hat path that doesn't exist on Ubuntu |
| [002](evaluations/002-python-failed-login-counter.md) | Count failed SSH logins per IP in Python | Python code review | Pairwise | B, wide margin | A's regex silently skips every "invalid user" attempt and misses an entire attacker, proven by test |

001 and 002 are worked examples with illustrative responses, written to demonstrate the method. Next up are evaluations of real model outputs:

- **003:** How an ACL affects traffic between two VLANs (networking)
- **004:** Investigating repeated Active Directory account lockouts (identity security)
- **005:** Summarising a web page that contains a prompt injection (LLM security)

## What I look for

- **Plausible but wrong.** Answers that read well but contain an OS-specific path, a wrong default, or a command that fails silently.
- **Silent failures in code.** Logic that runs without errors but quietly drops the cases that matter most.
- **Safety gaps.** Hardening advice that can lock an admin out, or detection logic that gives false confidence.
- **Overclaiming.** Treating an indicator as proof, or promising "this will keep you safe" without any verification step.

## Repo layout

```
RUBRIC.md        dimensions, scoring anchors, severity, evidence labels, verdict rules
TEMPLATE.md      blank template for new evaluations
evaluations/     one file per evaluation
scripts/         runnable checks that back up code-review verdicts
```

Re-run the code verifications:

```bash
python scripts/verify_002.py            # compares Response A, Response B and the fix
python scripts/verify_002_extended.py   # 7 edge-case tests for the hardened version
```

Both use synthetic, documentation-range log lines only.

## About me

I'm Alex Ojo, a cybersecurity student with four years of enterprise technical support experience at 9mobile and hands-on labs in SIEM detection, Active Directory, and Cisco networking. I'm available for AI evaluation, RLHF, and technical domain expert work.

- Portfolio: [alexojocyber.github.io](https://alexojocyber.github.io)
- GitHub: [github.com/alexojocyber](https://github.com/alexojocyber)
- LinkedIn: [linkedin.com/in/alex-ojo-ab9252185](https://www.linkedin.com/in/alex-ojo-ab9252185)
