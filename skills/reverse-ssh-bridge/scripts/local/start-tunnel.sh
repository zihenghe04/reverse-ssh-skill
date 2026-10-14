#!/usr/bin/env bash
# 在 Mac 上运行：建立「服务器:RPORT → 本机:22」的反向隧道，并保活。
#
# 用法：
#   ./start-tunnel.sh <服务器别名或 user@host>
#   例：  ./start-tunnel.sh my-server
#         ./start-tunnel.sh user@203.0.113.10
#
# 可用环境变量覆盖：
#   REVERSE_SSH_SERVER  服务器别名 / user@host（等价于第一个参数）
#   REVERSE_SSH_PORT    服务器上监听的端口（默认 2222）
#   REVERSE_SSH_KEY     使用的私钥（默认 ~/.ssh/id_ed25519）
set -euo pipefail

SERVER="${1:-${REVERSE_SSH_SERVER:-}}"
RPORT="${REVERSE_SSH_PORT:-2222}"
KEY="${REVERSE_SSH_KEY:-$HOME/.ssh/id_ed25519}"

die() { echo "错误：$*" >&2; exit 1; }

# ── 预检 1：必须给出真实服务器（否则会对着占位符无限重试）──────────────
if [ -z "$SERVER" ]; then
  cat >&2 <<EOF
用法: $(basename "$0") <服务器别名或 user@host>

示例:
  $(basename "$0") my-server
  $(basename "$0") user@203.0.113.10

查看本机已配置的服务器别名:
  grep '^Host ' ~/.ssh/config
EOF
  exit 2
fi
case "$SERVER" in
  your-server|server-alias)
    die "'$SERVER' 是文档里的占位符，请换成真实服务器别名或 user@host。" ;;
esac

# ── 预检 2：autossh ─────────────────────────────────────────────────
command -v autossh >/dev/null 2>&1 \
  || die "缺少 autossh，请先执行: brew install autossh"

# ── 预检 3：本机 sshd（没开的话隧道建了也没用）────────────────────────
if ! nc -z -G 2 localhost 22 >/dev/null 2>&1; then
  echo "警告：本机 22 端口未监听，「远程登录」可能未开。" >&2
  echo "  开启：系统设置 → 通用 → 共享 → 远程登录" >&2
  echo "  （命令行派：给终端 App 授予完全磁盘访问权限后 sudo systemsetup -setremotelogin on）" >&2
fi

# ── 预检 4：Mac 侧 authorized_keys（服务器回连的免密依据）───────────────
if [ ! -s "$HOME/.ssh/authorized_keys" ]; then
  echo "警告：~/.ssh/authorized_keys 不存在或为空 → 服务器无法免密回连本机。" >&2
  echo "  修法：把【服务器】上用于回连的公钥追加进本文件（见 SKILL.md「Set up」）。" >&2
fi

# ── 预检 5：真正 ssh 一次目标（关键！不通立即失败，不再静默重试）─────────
echo "→ 预检目标服务器: ${SERVER} ..."
if ! ssh -o BatchMode=yes -o ConnectTimeout=10 -o IdentitiesOnly=yes \
        -i "$KEY" "$SERVER" true 2>/dev/null; then
  die "无法以密钥免密登录 ${SERVER}：
  - 确认主机可达：      ping ${SERVER}
  - 确认公钥已部署：    ssh-copy-id -i ${KEY}.pub ${SERVER}
  - 该主机若只能密码登录，请先配置免密（后台保活的隧道无法交互输密码）"
fi
echo "  ✓ ${SERVER} 免密登录正常"

echo "建立反向隧道: ${SERVER} 的 localhost:${RPORT} → 本机:22"
echo "保活参数：ServerAliveInterval=30 ServerAliveCountMax=3 ExitOnForwardFailure=yes"
echo "（前台运行，Ctrl+C 停止；开机自启见 install-launchagent.sh）"
echo

exec autossh -M 0 -N \
  -o "ServerAliveInterval 30" \
  -o "ServerAliveCountMax 3" \
  -o "ExitOnForwardFailure yes" \
  -o "IdentitiesOnly yes" \
  -i "$KEY" \
  -R "${RPORT}:localhost:22" \
  "$SERVER"
