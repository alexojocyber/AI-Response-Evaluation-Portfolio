# 001: Detecting and stopping an SSH brute-force attack

| | |
|---|---|
| **Domain** | Linux security, incident response |
| **Task type** | Pairwise comparison |
| **Responses from** | Worked example with illustrative responses |
| **Date** | 2026-10-12 |

## Prompt

> I run an Ubuntu 22.04 web server and I think someone is trying to brute-force SSH. How do I confirm it and stop it?

## Response A

> **1. Confirm the attack.** SSH logins on Ubuntu are logged to `/var/log/auth.log`. Count failed attempts per IP:
>
> ```bash
> sudo grep "Failed password" /var/log/auth.log | awk '{print $(NF-3)}' | sort | uniq -c | sort -nr | head
> ```
>
> Hundreds of failures from a handful of IPs means you're being brute-forced.
>
> **2. Block it automatically with Fail2Ban.**
>
> ```bash
> sudo apt install fail2ban
> sudo nano /etc/fail2ban/jail.conf
> ```
>
> Make sure the `[sshd]` jail is enabled. By default Fail2Ban bans an IP after 3 failed attempts. Restart with `sudo systemctl restart fail2ban` and check bans with `sudo fail2ban-client status sshd`.
>
> **3. Harden SSH.** Switch to key-based authentication and turn off passwords in `/etc/ssh/sshd_config`:
>
> ```
> PasswordAuthentication no
> PermitRootLogin no
> ```
>
> Then run `sudo systemctl restart ssh`.

## Response B

> Great question! Brute-force attacks are very common. Here's how to handle it:
>
> **Check the logs.** Look in `/var/log/secure` for lines containing "Failed password":
>
> ```bash
> sudo grep "Failed password" /var/log/secure
> ```
>
> **Change your SSH port.** The best defence is moving SSH off port 22 so bots can't find it. Edit `/etc/ssh/sshd_config`, set `Port 2222`, and restart SSH.
>
> **Rate-limit with UFW.**
>
> ```bash
> sudo ufw limit ssh
> ```
>
> **Install Fail2Ban** and create `/etc/fail2ban/jail.local` with an `[sshd]` section set to `enabled = true`.
>
> These steps will keep your server safe!

## Scores

| Dimension | A | B |
|---|---|---|
| Correctness | 4 | 2 |
| Completeness | 4 | 3 |
| Safety | 3 | 4 |
| Instruction following | 5 | 3 |
| Clarity | 5 | 4 |

## Issues found

| Response | Severity | Quote | Problem | Evidence |
|---|---|---|---|---|
| B | **Major** | "Look in `/var/log/secure`" | That path is the Red Hat / CentOS auth log. On Ubuntu 22.04 it doesn't exist, so the user sees "No such file", finds nothing, and may wrongly conclude there is no attack. This defeats the "confirm it" half of the prompt. | Ubuntu and Debian log authentication to `/var/log/auth.log` via rsyslog. |
| A | **Major** (safety) | "turn off passwords ... `PasswordAuthentication no`" | No warning to install and **test** an SSH key first. If the user disables passwords before key login works, they lock themselves out of a remote server. | Standard hardening guidance: confirm key login in a second session before restarting `ssh`. |
| B | Minor | "The best defence is moving SSH off port 22" | Changing the port cuts log noise but is obscurity, not protection; port scanners find it quickly. Calling it "the best defence" ranks it above key auth and Fail2Ban, which actually stop the attack. | |
| A | Minor | "`sudo nano /etc/fail2ban/jail.conf`" | Fail2Ban's docs say not to edit `jail.conf`, because package upgrades overwrite it. Settings belong in `jail.local`. (Response B gets this right.) | Header comment in `jail.conf` itself. |
| A | Minor | "bans an IP after 3 failed attempts" by default | The default `maxretry` is 5, not 3. The user still gets protection, just with a looser threshold than they think. | `[DEFAULT] maxretry = 5` in `jail.conf`. |
| B | Minor | "Great question! ... These steps will keep your server safe!" | Filler and an overconfident closing claim, given none of the steps were verified. | |

## Verdict

**Preferred: A**, by a clear margin.

The user asked two things: confirm the attack, then stop it. Response A's detection command works on Ubuntu and even ranks attacking IPs, so the user gets a real answer. Response B sends them to a log file that doesn't exist on their OS, so they can't confirm anything. A's issues are real, especially the missing lockout warning, but they are fixable additions. B's core diagnostic step is wrong for the stated system.

## Suggested ideal response

Response A's structure, plus:
- Before disabling passwords: generate a key, copy it with `ssh-copy-id`, and **confirm key login in a second terminal** before restarting `ssh`.
- Put Fail2Ban settings in `/etc/fail2ban/jail.local`, and state the real default (5 attempts) or set `maxretry` explicitly.
- Optionally mention `sudo ufw limit ssh` (Response B's good idea) as an extra layer.

## Verification

- Log path: Ubuntu writes SSH authentication events to `/var/log/auth.log`; `/var/log/secure` is the RHEL-family path.
- The `awk '{print $(NF-3)}'` field: on a line ending `from 203.0.113.7 port 51022 ssh2`, the 4th field from the end is the IP. This holds for both `Failed password for root` and `Failed password for invalid user admin` lines.
- Fail2Ban defaults: `maxretry = 5` and the "do not modify this file" notice are both in the stock `jail.conf`.

---

## Addendum A — Point-by-point evaluator walkthrough (added 2026-10-12)

> This section supplements the original worked example. It does not replace the original responses, scores, or verdict.

### What the prompt is really testing

The prompt has two required outcomes: **confirm** whether SSH password guessing is occurring, and **reduce the risk safely**. A response that only hardens SSH but never helps inspect evidence is incomplete. A response that finds failed attempts but recommends a change that can lock out the administrator has a safety gap.

### Response A, explained

1. **“SSH logins on Ubuntu are logged to `/var/log/auth.log`.”** This is the expected traditional Ubuntu file-log location when rsyslog is installed and configured to write authentication logs. A careful evaluator should avoid saying this file exists on every installation: some minimal/systemd-focused setups may require `journalctl` instead. Verify the environment before concluding that an empty/missing file means no attack.
2. **The `grep | awk | sort | uniq` pipeline.** `grep` selects lines containing `Failed password`; `awk` extracts the source address field; `sort` groups identical addresses; `uniq -c` counts them; the final numeric sort ranks the highest counts first. The `head` limits the display. It is useful triage, not proof by itself: legitimate users can mistype passwords, logs may be rotated, and the pipeline only sees lines matching this phrase.
3. **“Hundreds of failures … means you're being brute-forced.”** Repeated failures are a strong indicator of password guessing, but volume alone is not definitive proof of malicious activity. Check timestamps, source addresses, usernames, successful logins after failures, and whether the source is an approved scanner or administrator.
4. **Installing Fail2Ban.** Fail2Ban parses configured log sources and applies bans through configured actions. Installing it alone does not prove that the SSH jail is enabled, monitoring the correct source, or enforcing a firewall rule. Confirm with `fail2ban-client status` and `fail2ban-client status sshd`.
5. **Editing `jail.conf`.** The original evaluation correctly flags this as a maintainability issue. Local overrides should generally go in `jail.local` or a file under `jail.d/`, so package-managed defaults are not directly edited. Confirm the installed version and its packaged configuration.
6. **“By default … after 3 failed attempts.”** This is not a safe universal statement. Fail2Ban defaults can differ by release and configuration; the relevant effective `maxretry`, `findtime`, and `bantime` should be checked rather than assumed. Set explicit values when the task requires a predictable policy.
7. **Disabling password authentication.** `PasswordAuthentication no` can reduce password-guessing exposure, but it can lock out a remote administrator if key authentication is not already configured and tested. Keep an existing session open, test a new key-authenticated session, validate the SSH configuration with `sshd -t`, and use the service/reload procedure appropriate for the system before closing the working session.
8. **`PermitRootLogin no`.** This is a sensible hardening setting for many servers, but the evaluator should still consider the user's access model and confirm that a separate administrative account with working `sudo` access exists.
9. **Restarting SSH.** A restart is not a substitute for configuration validation. A typo or invalid directive can interrupt access. Prefer testing the configuration first and use a reload when appropriate for the deployment.

### Response B, explained

1. **`/var/log/secure`.** This is commonly associated with Red Hat-family distributions, not the normal Ubuntu 22.04 file path. Because the prompt explicitly names Ubuntu, this is a major context-specific correctness failure. If the file is absent, the correct response is to check Ubuntu's auth log or the system journal—not to infer that there is no attack.
2. **Changing SSH to port 2222.** This can reduce background noise but is not a primary security control: scanners can discover non-default ports. It also requires updating firewall/cloud security-group rules and confirming access on the new port before ending the current session.
3. **`sudo ufw limit ssh`.** This can provide rate limiting when UFW is active and the rule matches the intended SSH service/port. It is an extra layer, not a substitute for reviewing logs, using strong authentication, and maintaining a tested recovery path.
4. **Fail2Ban `jail.local`.** This is a better local-override approach than directly modifying `jail.conf`, but the answer should still show how to verify that the jail is active and reading the correct log source/backend.
5. **“These steps will keep your server safe!”** This overstates certainty. No short checklist guarantees safety; an evaluator should penalize unsupported guarantees, especially when the proposed diagnostic step is wrong for the stated OS.

### Security evaluator questions to ask

- Does the response solve both parts of the user's request: detection and mitigation?
- Are paths and commands appropriate for the named distribution and version?
- Could a recommended change lock out the administrator?
- Does the answer include a way to verify that the control actually works?
- Does it distinguish a signal of brute force from conclusive proof of compromise?
- Does it make guarantees that the evidence cannot support?

### Stronger verification checklist

On an authorized Ubuntu host, verify the available log source before searching:

```bash
sudo test -r /var/log/auth.log && echo "auth.log is readable"
sudo journalctl -u ssh --since "1 hour ago" --no-pager
```

The exact service unit can vary (`ssh` versus `sshd`), so check the system's unit name if the journal query returns no entries. Before changing SSH authentication settings, validate configuration and test a second login path. After configuring Fail2Ban, inspect the effective jail status and confirm the configured firewall action is appropriate for the host.

### Research notes

- Ubuntu authentication logging depends on the logging setup; use the host's actual log source rather than assuming a path exists.
- Fail2Ban's `maxretry` is configurable; evaluate the effective configuration, not a remembered default.
- Official references to consult for a live deployment: [Fail2Ban jail configuration manual](https://github.com/fail2ban/fail2ban/blob/master/man/jail.conf.5), [Ubuntu OpenSSH documentation](https://ubuntu.com/server/docs/openssh-server), and [systemd journalctl manual](https://www.freedesktop.org/software/systemd/man/latest/journalctl.html).

> **Portfolio integrity note:** The responses above are labelled illustrative in the original file. Keep that label unless you actually run the same prompt against named models and preserve their verbatim outputs.
