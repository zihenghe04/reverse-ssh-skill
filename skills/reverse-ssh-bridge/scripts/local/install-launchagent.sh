#!/usr/bin/env bash
# 在 Mac 上运行：生成并加载 LaunchAgent，让反向隧道开机自启、断线自愈。
#
# 用法：
#   ./install-launchagent.sh <服务器别名或 user@host>      安装并加载
#   ./install-launchagent.sh --uninstall                    卸载
#
# 可用环境变量覆盖：REVERSE_SSH_PORT（默认 2222）、REVERSE_SSH_KEY（默认 ~/.ssh/id_ed25519）
set -euo pipefail

LABEL=com.user.reversetunnel
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

die() { echo "错误：$*" >&2; exit 1; }

if [ "${1:-}" = "--uninstall" ]; then
  launchctl unload -w "$PLIST" 2>/dev/null || true
  rm -f "$PLIST"
  echo "已卸载 $LABEL"
  exit 0
fi

SERVER="${1:-}"
[ -n "$SERVER" ] || die "用法: $(basename "$0") <服务器别名或 user@host> | --uninstall"
RPORT="${REVERSE_SSH_PORT:-2222}"
KEY="${REVERSE_SSH_KEY:-$HOME/.ssh/id_ed25519}"
AUTOSSH="$(command -v autossh || true)"
[ -n "$AUTOSSH" ] || die "缺少 autossh，请先执行: brew install autossh"
[ -f "$KEY" ] || die "私钥不存在: $KEY"
[ -e "$PLIST" ] && die "$PLIST 已存在；先 --uninstall 再重新安装"

# launchd 不展开 ~，也不读 shell 配置：所有路径必须是绝对路径。
mkdir -p "$(dirname "$PLIST")"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$AUTOSSH</string>
    <string>-M</string><string>0</string>
    <string>-N</string>
    <string>-o</string><string>ServerAliveInterval=30</string>
    <string>-o</string><string>ServerAliveCountMax=3</string>
    <string>-o</string><string>ExitOnForwardFailure=yes</string>
    <string>-o</string><string>IdentitiesOnly=yes</string>
    <string>-F</string><string>$HOME/.ssh/config</string>
    <string>-i</string><string>$KEY</string>
    <string>-R</string><string>$RPORT:localhost:22</string>
    <string>$SERVER</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/tmp/reversetunnel.log</string>
  <key>StandardErrorPath</key><string>/tmp/reversetunnel.err</string>
</dict>
</plist>
EOF
plutil -lint "$PLIST" >/dev/null
launchctl load -w "$PLIST"
echo "已安装并加载 $LABEL：$SERVER 的 localhost:$RPORT → 本机:22"
echo "查看状态：launchctl list | grep reversetunnel；日志：tail -f /tmp/reversetunnel.err"
