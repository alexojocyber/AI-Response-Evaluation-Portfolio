"""
Reproduces the comparison in evaluations/002-python-failed-login-counter.md.

Runs both candidate functions against the same realistic auth.log sample and
prints what each one counts, so the verdict can be checked rather than trusted.

Usage:  python scripts/verify_002.py
"""
import re
from collections import Counter

SAMPLE_LOG = """\
Oct 10 02:14:01 web01 sshd[1201]: Failed password for root from 203.0.113.7 port 51022 ssh2
Oct 10 02:14:03 web01 sshd[1203]: Failed password for root from 203.0.113.7 port 51030 ssh2
Oct 10 02:14:05 web01 sshd[1205]: Failed password for invalid user admin from 203.0.113.7 port 51041 ssh2
Oct 10 02:14:07 web01 sshd[1207]: Failed password for invalid user oracle from 198.51.100.23 port 40112 ssh2
Oct 10 02:14:09 web01 sshd[1209]: Failed password for invalid user test from 198.51.100.23 port 40118 ssh2
Oct 10 02:14:11 web01 sshd[1211]: Failed password for invalid user ubuntu from 198.51.100.23 port 40125 ssh2
Oct 10 02:15:30 web01 sshd[1290]: Accepted password for alex from 192.0.2.10 port 50500 ssh2
Oct 10 02:16:02 web01 sshd[1301]: Failed password for alex from 192.0.2.10 port 50510 ssh2
Oct 10 02:17:44 web01 sshd[1320]: Failed password for invalid user pi from 2001:db8::25 port 6022 ssh2
"""

# Response A, copied as written
def count_failed_logins_a(lines):
    pattern = re.compile(r"Failed password for (\w+) from (\d+\.\d+\.\d+\.\d+)")
    counts = {}
    for line in lines:
        match = pattern.search(line)
        if match:
            ip = match.group(2)
            counts[ip] = counts.get(ip, 0) + 1
    return counts

# Response B, copied as written
def count_failed_logins_b(lines):
    pattern = re.compile(r"from (\d+\.\d+\.\d+\.\d+)")
    counts = Counter()
    for line in lines:
        if "Failed password" in line:
            match = pattern.search(line)
            if match:
                counts[match.group(1)] += 1
    return counts

# Corrected version (see "Suggested fix" in the evaluation)
def count_failed_logins_fixed(lines):
    pattern = re.compile(r"Failed password for (?:invalid user )?\S+ from (\S+) port")
    counts = Counter()
    for line in lines:
        match = pattern.search(line)
        if match:
            counts[match.group(1)] += 1
    return counts


if __name__ == "__main__":
    lines = SAMPLE_LOG.splitlines()
    expected = {"203.0.113.7": 3, "198.51.100.23": 3, "192.0.2.10": 1, "2001:db8::25": 1}
    for name, fn in [("Response A", count_failed_logins_a),
                     ("Response B", count_failed_logins_b),
                     ("Fixed", count_failed_logins_fixed)]:
        got = dict(fn(lines))
        total = sum(got.values())
        status = "PASS" if got == expected else "FAIL"
        print(f"{name:<11} {status}  total={total}  {got}")
    print(f"{'Expected':<11}       total={sum(expected.values())}  {expected}")
