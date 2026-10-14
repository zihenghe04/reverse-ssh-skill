# Reverse SSH Bridge Skill

[English](README.md) · [简体中文](README.zh-CN.md)

An installable AI skill for running a coding agent (Claude Code, Codex, …) on a **remote server** while it works on **your own Mac**: run local commands, open files in your local editor, and take screenshots or short screen recordings, all through a reverse SSH tunnel.

```text
Mac (sshd :22, editor, screen)  ──ssh -R 2222:localhost:22──▶  Server (agent)
                                ◀──────── ssh mac ────────────
```

Nothing is exposed to the internet: the forwarded port listens only on the server's loopback interface. No host names, users, keys or IP addresses from the original machines are included.

## Install

Requires Git and Python 3.9+.

```sh
git clone https://github.com/zihenghe04/reverse-ssh-skill.git
cd reverse-ssh-skill
python3 install.py --target claude     # ~/.claude/skills
python3 install.py --target codex      # ~/.codex/skills
python3 install.py --target agents     # ~/.agents/skills
```

`--dest /path/to/skills` installs elsewhere. Existing installations are never overwritten. Installing copies only the skill; it does not change SSH or system settings. Install it on the **server** where the agent runs. The Mac-side scripts ship in the same folder; copy `scripts/local/` to the Mac or clone the repo there.

## Ask your AI

Claude Code:

```text
/reverse-ssh-bridge Check that ssh mac works, then run the tests of ~/code/my-app on my Mac and screenshot the result.
```

Codex:

```text
Use $reverse-ssh-bridge to set up the reverse tunnel between my Mac and this server.
```

## Included scripts

| Script | Runs on | Purpose |
|---|---|---|
| `scripts/local/start-tunnel.sh <server>` | Mac | Five preflight checks, then a kept-alive `autossh -R` tunnel |
| `scripts/local/install-launchagent.sh <server>` | Mac | Start the tunnel at login and reconnect automatically (`--uninstall` to remove) |
| `scripts/local/shotd.sh` | Mac, in Terminal.app | Capture daemon that inherits the terminal's Screen Recording permission |
| `scripts/server/add-ssh-alias.sh <mac-user>` | Server | Add a `Host mac` alias; prints the `authorized_keys` line to add on the Mac |
| `scripts/server/mac-capture.sh shot\|rec <s>` | Server | Request a screenshot or recording and copy it to `$MAC_BRIDGE_DIR` |

Why a capture daemon? macOS does not let an SSH session record the screen (`could not create image from display`), even if `sshd` is granted Screen Recording. A process started from a GUI terminal can.

## Security

The tunnel gives the server a shell as your Mac user, and anyone with root on the server can use it too. Use a dedicated key, restricted with `from="127.0.0.1,::1"` in `authorized_keys`. Keep the forward on loopback, and stop the tunnel when you don't need it. Screenshots can contain private windows: keep them in a private directory and never commit them. The skill tells the agent to confirm destructive or outward-facing actions on your Mac.

## Development

```sh
python3 -m unittest discover -s tests -v
python3 tools/privacy_check.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md). MIT licensed.
