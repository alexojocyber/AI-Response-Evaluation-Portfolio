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
| B | **Major** | "Look in `/var/log/secure`" | That path is the Red Hat / CentOS auth log. On Ubuntu 22.04 it doesn't exist, so the user sees "No such file", finds nothing, and may wrongly conclude there is no attack. This defeats the "confirm it" half of the prompt. | **Documented:** Ubuntu and Debian log authentication to `/var/log/auth.log` via rsyslog. |
| A | **Major** (safety) | "turn off passwords ... `PasswordAuthentication no`" | No warning to install and **test** an SSH key first. If the user disables passwords before key login works, they lock themselves out of a remote server. A plain restart with no `sshd -t` check adds the risk that a typo takes SSH down entirely. | **Reasoned:** standard hardening practice is to confirm key login in a second session before restarting `ssh`. |
| B | Minor | "The best defence is moving SSH off port 22" | Changing the port cuts log noise but is obscurity, not protection; port scanners find it quickly. Calling it "the best defence" ranks it above key auth and Fail2Ban, which actually stop the attack. It also needs a firewall rule for the new port, which B doesn't mention, so the user can lose access. | **Reasoned** |
| A | Minor | "`sudo nano /etc/fail2ban/jail.conf`" | Fail2Ban's docs say not to edit `jail.conf`, because package upgrades overwrite it. Settings belong in `jail.local`. (Response B gets this right.) | **Documented:** header comment in `jail.conf` itself. |
| A | Minor | "bans an IP after 3 failed attempts" by default | The default `maxretry` is 5, not 3. The user still gets protection, just with a looser threshold than they think. | **Documented:** `[DEFAULT] maxretry = 5` in the stock `jail.conf`. |
| B | Minor | "Great question! ... These steps will keep your server safe!" | Filler and an overconfident closing claim, given none of the steps were verified. | **Reasoned** |

## Verdict

**Preferred: A**, by a clear margin.

The user asked two things: confirm the attack, then stop it. Response A's detection command works on Ubuntu and even ranks attacking IPs, so the user gets a real answer. Response B sends them to a log file that doesn't exist on their OS, so they can't confirm anything. A's issues are real, especially the missing lockout warning, but they are fixable additions. B's core diagnostic step is wrong for the stated system.

## Suggested ideal response

Response A's structure, plus:
- **Read the evidence, not just the count.** Many failures from a few IPs is a strong sign of password guessing, not proof of compromise. Check whether any of those IPs later shows `Accepted password`, which would mean a guess succeeded.
- If `/var/log/auth.log` is missing (for example, on a minimal install without rsyslog), use `journalctl -u ssh` instead of concluding nothing is happening.
- Before disabling passwords: generate a key, copy it with `ssh-copy-id`, **confirm key login in a second terminal**, run `sudo sshd -t` to validate the config, and only then restart `ssh` while keeping the original session open.
- Put Fail2Ban settings in `/etc/fail2ban/jail.local`, set `maxretry` explicitly (the default is 5), and confirm it's working with `sudo fail2ban-client status sshd`.
- Optionally mention `sudo ufw limit ssh` (Response B's good idea) as an extra layer.

## Verification

- Log path: Ubuntu writes SSH authentication events to `/var/log/auth.log`; `/var/log/secure` is the RHEL-family path.
- The `awk '{print $(NF-3)}'` field: on a line ending `from 203.0.113.7 port 51022 ssh2`, the 4th field from the end is the IP. This holds for both `Failed password for root` and `Failed password for invalid user admin` lines.
- Fail2Ban defaults: `maxretry = 5` and the "do not modify this file" notice are both in the stock `jail.conf`.
