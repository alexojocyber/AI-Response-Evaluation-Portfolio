# 002: Python code review, counting failed SSH logins per IP

| | |
|---|---|
| **Domain** | Python, security log analysis |
| **Task type** | Pairwise comparison, code review |
| **Responses from** | Worked example with illustrative responses |
| **Date** | 2026-10-12 |

## Prompt

> Write a Python function that takes the lines of an Ubuntu `auth.log` and returns how many failed SSH password attempts came from each IP address.

## Response A

> ```python
> import re
>
> def count_failed_logins(lines):
>     pattern = re.compile(r"Failed password for (\w+) from (\d+\.\d+\.\d+\.\d+)")
>     counts = {}
>     for line in lines:
>         match = pattern.search(line)
>         if match:
>             ip = match.group(2)
>             counts[ip] = counts.get(ip, 0) + 1
>     return counts
> ```
>
> The regex captures the username and the IP from each failed login line, and the dictionary keeps a running count per IP.

## Response B

> ```python
> import re
> from collections import Counter
>
> def count_failed_logins(lines):
>     pattern = re.compile(r"from (\d+\.\d+\.\d+\.\d+)")
>     counts = Counter()
>     for line in lines:
>         if "Failed password" in line:
>             match = pattern.search(line)
>             if match:
>                 counts[match.group(1)] += 1
>     return counts
> ```
>
> It filters to failed password lines first, then pulls the source IP. `Counter` handles the tallying.

## Scores

| Dimension | A | B |
|---|---|---|
| Correctness | 2 | 4 |
| Completeness | 2 | 4 |
| Safety | 2 | 4 |
| Instruction following | 4 | 5 |
| Clarity | 4 | 4 |
| Code quality | 2 | 4 |

## Issues found

| Response | Severity | Quote | Problem | Evidence |
|---|---|---|---|---|
| A | **Major** | `r"Failed password for (\w+) from ..."` | Silently misses every attempt against a username that doesn't exist. Those lines read `Failed password for invalid user admin from ...`. `(\w+)` matches only `invalid`, then the regex expects ` from` but finds ` user`, so the line is skipped. Invalid-username guessing is the most common brute-force pattern, so the function under-reports exactly the attacks it exists to find. | **Executed:** `scripts/verify_002.py`: A counts **3 of 8** failures and misses attacker `198.51.100.23` entirely. |
| A | Minor | The explanation says the regex "captures the username" | The username group is captured but never used, which adds risk (the bug above) for no benefit. | **Reasoned** |
| B | Minor | `r"from (\d+\.\d+\.\d+\.\d+)"` | IPv4 only, so attempts from IPv6 addresses (e.g. `2001:db8::25`) are dropped. Response A shares this gap. It also matches `from <IP>` anywhere in the line rather than anchoring to the failed-password message, which is looser than it needs to be. | **Executed:** `scripts/verify_002.py`: B counts **7 of 8**, missing only the IPv6 line. |

**Why the safety score matters here:** this is a detection tool. A counter that quietly under-reports gives a defender false confidence that an attack is smaller than it is, or not happening at all. A tool that fails loudly is safer than one that fails silently.

## Verdict

**Preferred: B**, by a wide margin.

Both functions look reasonable and would pass a quick glance. Running them against a realistic log shows the difference: A misses every "invalid user" attempt and fails to detect one of the two attackers at all. B catches all IPv4 attempts and only misses IPv6. A's bug is invisible unless you test with the right log lines, which is exactly why code should be run, not just read.

## Suggested ideal response

Match the fixed structure of the log line and accept any address format:

```python
import re
from collections import Counter

def count_failed_logins(lines):
    pattern = re.compile(r"Failed password for (?:invalid user )?\S+ from (\S+) port")
    counts = Counter()
    for line in lines:
        match = pattern.search(line)
        if match:
            counts[match.group(1)] += 1
    return counts
```

This handles valid and invalid usernames, IPv4 and IPv6, and anchors on ` port` so it can't grab the wrong field.

### Hardened version

`\S+` accepts any token in the address position, so a malformed line would be counted as if it were an IP. Validating with the standard library closes that gap:

```python
import re
from collections import Counter
from ipaddress import ip_address

FAILED_SSH_PASSWORD = re.compile(
    r"Failed password for (?:invalid user )?\S+ from (\S+) port "
)

def count_failed_logins(lines):
    counts = Counter()
    for line in lines:
        match = FAILED_SSH_PASSWORD.search(line)
        if not match:
            continue
        candidate_ip = match.group(1)
        try:
            ip_address(candidate_ip)  # accepts IPv4 and IPv6, raises ValueError otherwise
        except ValueError:
            continue
        counts[candidate_ip] += 1
    return dict(counts)
```

For production use, rejected lines would be better reported as a parse-error count than silently dropped, so a change in log format is noticed.

## Verification

Run it yourself:

```bash
python scripts/verify_002.py
```

Output:

```
Response A  FAIL  total=3  {'203.0.113.7': 2, '192.0.2.10': 1}
Response B  FAIL  total=7  {'203.0.113.7': 3, '198.51.100.23': 3, '192.0.2.10': 1}
Fixed       PASS  total=8  {'203.0.113.7': 3, '198.51.100.23': 3, '192.0.2.10': 1, '2001:db8::25': 1}
Expected          total=8  {'203.0.113.7': 3, '198.51.100.23': 3, '192.0.2.10': 1, '2001:db8::25': 1}
```

The sample log in the script includes the cases that matter: valid users, invalid users, a successful login (which must not be counted), and an IPv6 source.

The hardened version has its own edge-case tests:

```bash
python scripts/verify_002_extended.py
```

| Case | Expected | Result |
|---|---|---|
| Valid username failure | Counted | PASS |
| Invalid username failure | Counted | PASS |
| Successful login | Not counted | PASS |
| IPv6 source | Counted | PASS |
| Malformed source (`not-an-ip`) | Not counted | PASS |
| Repeated source | Aggregated under one IP | PASS |
| Empty input | Empty result | PASS |

These results cover the tested log shapes only. Other OpenSSH message forms or locales would need their own cases.
