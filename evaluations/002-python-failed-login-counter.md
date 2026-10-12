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
| A | **Major** | `r"Failed password for (\w+) from ..."` | Silently misses every attempt against a username that doesn't exist. Those lines read `Failed password for invalid user admin from ...`. `(\w+)` matches only `invalid`, then the regex expects ` from` but finds ` user`, so the line is skipped. Invalid-username guessing is the most common brute-force pattern, so the function under-reports exactly the attacks it exists to find. | `scripts/verify_002.py`: A counts **3 of 8** failures and misses attacker `198.51.100.23` entirely. |
| A | Minor | The explanation says the regex "captures the username" | The username group is captured but never used, which adds risk (the bug above) for no benefit. | |
| B | Minor | `r"from (\d+\.\d+\.\d+\.\d+)"` | IPv4 only, so attempts from IPv6 addresses (e.g. `2001:db8::25`) are dropped. Response A shares this gap. | `scripts/verify_002.py`: B counts **7 of 8**, missing only the IPv6 line. |

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

---

## Addendum A — Point-by-point code-review walkthrough (added 2026-10-12)

> This is an explanatory addition. The original candidate code, scores, and test output are preserved above.

### What the prompt is really testing

The function must count **failed SSH password attempts by source IP**. It should not count successful logins, should include attempts against nonexistent usernames, and should not silently drop supported IP formats. Because this is detection code, a false negative can give an analyst a misleading picture of attack activity.

### Response A, explained

1. **`import re`** imports Python's regular-expression module. Regex is a reasonable way to find a structured log fragment, but it must account for the actual variants in OpenSSH log messages.
2. **`r"Failed password for (\w+) from (\d+\.\d+\.\d+\.\d+)"`** expects a single word between `for` and `from`, followed immediately by an IPv4 address. In an invalid-user message, the text is `for invalid user admin from ...`; the expression captures `invalid` and then expects ` from`, but encounters ` user`, so the entire match fails. That is why this implementation silently skips those events.
3. **`counts = {}`** creates a dictionary mapping an IP string to its count.
4. **`for line in lines` / `pattern.search(line)`** examines each line and searches for the pattern anywhere in it. It does not validate the entire log format; it only finds a matching substring.
5. **`match.group(2)`** selects the second capture group, the IPv4 string. The first group captures the username but is not used, which is unnecessary complexity in this task.
6. **`counts.get(ip, 0) + 1`** increments the current count or starts it at one. This part is sound.
7. **The return value** is a normal dictionary. That is a valid shape for the requested result, but its counts are incomplete because of the regex limitation.

### Response B, explained

1. **`Counter`** is a dictionary-like standard-library class designed for counting. It makes the intent clear and concise.
2. **`if "Failed password" in line`** correctly excludes a line like `Accepted password ...`, so successful authentication is not counted.
3. **`r"from (\d+\.\d+\.\d+\.\d+)"`** matches only dotted-decimal IPv4 addresses. It does catch invalid-user attempts because it does not try to parse the username, but it cannot capture an IPv6 address such as `2001:db8::25`.
4. **`counts[match.group(1)] += 1`** increments the source address's count. `Counter` initializes missing keys to zero.
5. **Overall result.** It is better than A on the provided sample, but the IPv4-only assumption remains a documented limitation. Also, the generic `from IP` pattern is less tightly connected to the exact failed-password event than a pattern anchored to the event phrase.

### Why the test fixture matters

The sample includes four important cases: ordinary failed attempts, attempts against invalid usernames, one successful login that must be excluded, and an IPv6 source address. A useful test suite deliberately includes these edge cases; a happy-path-only sample would not expose A's silent failure or B's IPv6 limitation.

The existing script was run on 2026-10-12 and produced:

```text
Response A  FAIL  total=3
Response B  FAIL  total=7
Fixed       PASS  total=8
Expected          total=8
```

This proves the stated result for this fixture—not that the function is production-ready for every OpenSSH version, locale, log format, or malformed input.

### A more defensive implementation

The original “Fixed” regex accepts any non-space token as the source address. That captures the IPv6 sample, but it does not itself verify that the token is a valid IP address. The following additive alternative uses the standard library to validate addresses and keeps the requested output as a dictionary:

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
            ip_address(candidate_ip)  # Validate IPv4 or IPv6.
        except ValueError:
            continue
        counts[candidate_ip] += 1
    return dict(counts)
```

This is still a targeted parser for the log shape shown in the fixture. For production use, add tests for log variants, rotated/journal input, malformed lines, and any additional OpenSSH message forms that your environment emits. Consider whether invalid lines should be counted in a separate parse-error metric rather than silently discarded.

### Suggested test cases

| Case | Expected behaviour | Why it matters |
|---|---|---|
| Failed password for a valid username | Increment source IP | Basic positive case |
| Failed password for `invalid user admin` | Increment source IP | Avoids missing username enumeration |
| Accepted password | Do not increment | Avoids false positive count |
| IPv6 source address | Increment source IP | Supports modern network logs |
| Malformed source token | Reject or explicitly report parse failure | Avoids counting invalid data as an IP |
| Repeated source address | Increase same counter | Confirms aggregation |
| Empty input | Return an empty mapping | Defines edge-case behaviour |

### Security evaluator questions to ask

- Does the function count only failed password events, not successful logins?
- Does it handle both valid and nonexistent usernames?
- Does it support both IPv4 and IPv6, and does it validate addresses?
- Are test cases representative of realistic log variation?
- Could the implementation silently undercount an attack?
- Is the claim “handles all cases” justified by the actual test coverage?

### Research notes

Python's [`ipaddress` documentation](https://docs.python.org/3/library/ipaddress.html) defines IPv4/IPv6 address parsing and raises `ValueError` for invalid address strings. The [`re` module documentation](https://docs.python.org/3/library/re.html) explains regex matching and capture groups. Use these references to support technical findings rather than treating the presence of a passing fixture as universal proof.

> **Portfolio integrity note:** The responses above are labelled illustrative in the original file. If you later run this prompt on actual models, save the exact prompt, model names/versions, date, raw outputs, and test results before updating the metadata.
