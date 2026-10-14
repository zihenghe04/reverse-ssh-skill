#!/usr/bin/env bash
# 在服务器上运行：把 `Host mac` 别名写入 ~/.ssh/config，指向反向隧道端口。
#   add-ssh-alias.sh <Mac 用户名> [端口=2222] [私钥=~/.ssh/to_mac] [别名=mac]
# 已存在同名 Host 时拒绝覆盖。
set -euo pipefail
USER_ON_MAC="${1:-}"
PORT="${2:-2222}"
KEY="${3:-$HOME/.ssh/to_mac}"
ALIAS="${4:-mac}"
CONFIG="$HOME/.ssh/config"

[ -n "$USER_ON_MAC" ] || { echo "用法: $0 <Mac 用户名> [端口] [私钥] [别名]" >&2; exit 2; }
[ -f "$KEY" ] || { echo "私钥不存在：$KEY（先 ssh-keygen -t ed25519 -f $KEY -N '' -C reverse-ssh-bridge）" >&2; exit 1; }
mkdir -p "$HOME/.ssh"; chmod 700 "$HOME/.ssh"; touch "$CONFIG"; chmod 600 "$CONFIG"
if grep -Eq "^[[:space:]]*Host[[:space:]]+(.*[[:space:]])?$ALIAS([[:space:]]|$)" "$CONFIG"; then
  echo "~/.ssh/config 里已有 Host $ALIAS，未修改。请人工核对后再改。" >&2
  exit 1
fi
cat >> "$CONFIG" <<EOF

Host $ALIAS
  HostName localhost
  Port $PORT
  User $USER_ON_MAC
  IdentityFile $KEY
  IdentitiesOnly yes
  ServerAliveInterval 30
  ServerAliveCountMax 3
EOF
echo "已添加 Host $ALIAS → localhost:$PORT（用户 $USER_ON_MAC）。验证：ssh -n -o BatchMode=yes $ALIAS 'hostname; whoami'"
echo "Mac 的 ~/.ssh/authorized_keys 需要加入这一行（from= 限制只能经隧道使用）："
echo "from=\"127.0.0.1,::1\" $(cat "$KEY.pub")"
