---
name: reverse-ssh-bridge
description: Let an AI agent on a remote server run commands, open files in the local editor, and take screenshots or screen recordings on the user's own Mac through a reverse SSH tunnel. Use to set up, verify, troubleshoot or use `ssh mac` from a server; not for exposing a machine to the internet. 支持中文操作。
---

# Reverse SSH bridge

Respond in the user's language. For Chinese instructions read [references/workflow.zh-CN.md](references/workflow.zh-CN.md); for troubleshooting read [references/troubleshooting.md](references/troubleshooting.md). The English workflow below is authoritative.

Topology: the agent runs on a **server**. The user's **local Mac** opens `ssh -R <port>:localhost:22 <server>`. The server then reaches the Mac with `ssh mac`, an alias for `localhost:<port>`. Nothing listens publicly.

## Decide where you are

Run `uname -s` and `hostname`. If you are on the server, you can use `ssh mac` once the tunnel exists. If you are on the Mac, you set up the tunnel side. Never assume names, ports, users or hosts: discover them (`grep '^Host ' ~/.ssh/config`, `ss -ltn` / `lsof -iTCP -sTCP:LISTEN`) or ask.

## Set up (once)

Mac side, run by the user or by an agent with local access:

1. Enable Remote Login: System Settings → General → Sharing → Remote Login. On macOS 13+, `systemsetup -setremotelogin` needs Full Disk Access for the calling app, so prefer the GUI.
2. `brew install autossh`.
3. Make sure the Mac can log in to the server with a key: `ssh -o BatchMode=yes <server> true`.
4. Start the tunnel: `scripts/local/start-tunnel.sh <server-alias>`. It runs five preflight checks and then `autossh -R`. For a persistent tunnel that survives reboots and disconnects, render the LaunchAgent with `scripts/local/install-launchagent.sh <server-alias>`.

Server side:

1. Create a dedicated key: `ssh-keygen -t ed25519 -f ~/.ssh/to_mac -N '' -C reverse-ssh-bridge`.
2. Append the public key to the Mac's `~/.ssh/authorized_keys`. Recommend the prefix `from="127.0.0.1,::1"`, so the key only works through the tunnel.
3. Add the alias with `scripts/server/add-ssh-alias.sh <mac-user> [port] [key]`. It refuses to overwrite an existing `Host mac` block.
4. Verify: `ssh -n -o BatchMode=yes mac 'hostname; whoami'`.

## Use

- **Always pass `-n`**, e.g. `ssh -n mac '…'`. Without it, ssh consumes the caller's stdin and silently swallows later lines of a script or loop.
- Non-interactive ssh does not load the login shell, so PATH usually misses Homebrew, nvm or `~/.local/bin`. Wrap commands: `ssh -n mac 'zsh -lc "cd ~/proj && npm test"'`, or tell the user to export PATH in `~/.zshenv`.
- Quoting: single-quote the outer command. Expand server-side variables deliberately. Remember zsh on the Mac does not word-split unquoted variables and fails on unmatched globs (`no matches found`), so quote URLs with `?`.
- Open in the local editor: `ssh -n mac "open -a <App> '<absolute path>'"`. Discover the app (`ls /Applications`) instead of assuming VS Code. `open` needs the user's logged-in GUI session.
- Copy files: `scp mac:<path> <dest>` / `scp <file> mac:<path>`.
- Keychain items (e.g. `gh` tokens, git credentials) are often unreadable over ssh (`User interaction is not allowed`). For `gh`, the user can re-login with `gh auth login --insecure-storage`. Explain the trade-off first: the token is then stored in a mode-600 plaintext file.

## Screenshots and recordings

ssh sessions cannot capture the screen: `screencapture` fails with `could not create image from display`, even after granting Screen Recording to sshd. Use the capture daemon instead:

1. The user runs `scripts/local/shotd.sh` in **Terminal.app** (or iTerm) and keeps it open. It inherits that app's Screen Recording permission. macOS prompts on the first capture.
2. From the server: `scripts/server/mac-capture.sh shot [name]` or `scripts/server/mac-capture.sh rec <seconds> [name]`. Recordings are capped at 120 s.
3. Files land in `$MAC_BRIDGE_DIR` (default `~/mac-bridge`) under `shots/` and `recordings/` with timestamped names. Read the PNG to see the screen. For video, extract frames (`ffmpeg -i rec.mov -vf fps=2 frame_%03d.png`) and read them.

Store captures, copied transcripts and other personal files in the user's chosen directory, never in shared `/tmp`. Captures may show private windows: do not upload or commit them.

## Safety boundaries

- The tunnel grants the server a shell as the Mac user. Anyone with root on the server can use it too. Say this when setting up.
- Keep `-R <port>:localhost:22` bound to loopback. Never use `-R 0.0.0.0:…` and do not enable `GatewayPorts`.
- Use a dedicated key with `IdentitiesOnly=yes`. Suggest `PasswordAuthentication no` and `AllowUsers <user>` on the Mac.
- Follow the host's permission rules. Commands run on the user's real machine: confirm before destructive, outward-facing or hard-to-reverse actions, such as deleting files, replacing installed apps, `git push`, or publishing. Approval for one action does not carry over to another.
- Do not try to bypass macOS privacy prompts (TCC). Ask the user to grant permissions in System Settings.
- When finished, tell the user how to stop or remove the tunnel on the Mac. These are different:
  - Foreground `scripts/local/start-tunnel.sh`: Ctrl+C in that terminal. That stops `autossh`.
  - LaunchAgent, this login only: `launchctl unload ~/Library/LaunchAgents/com.user.reversetunnel.plist`. That stops the `autossh` job launchd started. The plist stays, so the tunnel starts again at the next login. Do not merely kill `autossh`: the plist sets `KeepAlive`, so launchd starts it again.
  - Full removal: `scripts/local/install-launchagent.sh --uninstall`. That runs `launchctl unload -w` on the same plist (stops `autossh` and disables the job) and deletes it. The label is `com.user.reversetunnel`. This does not stop a foreground `start-tunnel.sh`.
