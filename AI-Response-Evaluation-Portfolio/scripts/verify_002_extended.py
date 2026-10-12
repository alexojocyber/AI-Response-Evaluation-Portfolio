"""Extended checks for the AI Response Evaluation Portfolio's evaluation 002.

Run with: python verify_002_extended.py
Uses synthetic, documentation-style log lines only; no real server logs are read.
"""
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
            ip_address(candidate_ip)
        except ValueError:
            continue
        counts[candidate_ip] += 1
    return dict(counts)


CASES = [
    (
        "valid username failure",
        ["sshd: Failed password for alex from 203.0.113.7 port 51022 ssh2"],
        {"203.0.113.7": 1},
    ),
    (
        "invalid username failure",
        ["sshd: Failed password for invalid user admin from 198.51.100.23 port 40112 ssh2"],
        {"198.51.100.23": 1},
    ),
    (
        "successful login excluded",
        ["sshd: Accepted password for alex from 192.0.2.10 port 50500 ssh2"],
        {},
    ),
    (
        "IPv6 failure",
        ["sshd: Failed password for invalid user pi from 2001:db8::25 port 6022 ssh2"],
        {"2001:db8::25": 1},
    ),
    (
        "malformed source excluded",
        ["sshd: Failed password for alex from not-an-ip port 50510 ssh2"],
        {},
    ),
    (
        "repeated source aggregated",
        [
            "sshd: Failed password for alex from 203.0.113.7 port 51022 ssh2",
            "sshd: Failed password for root from 203.0.113.7 port 51023 ssh2",
        ],
        {"203.0.113.7": 2},
    ),
    ("empty input", [], {}),
]


if __name__ == "__main__":
    failures = 0
    for name, lines, expected in CASES:
        actual = count_failed_logins(lines)
        passed = actual == expected
        print(f"{'PASS' if passed else 'FAIL'} | {name} | expected={expected} | actual={actual}")
        failures += not passed
    print(f"Summary: {len(CASES) - failures}/{len(CASES)} tests passed")
    raise SystemExit(1 if failures else 0)
