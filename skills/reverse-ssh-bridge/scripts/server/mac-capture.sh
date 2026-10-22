#!/usr/bin/env bash
# 在服务器上运行：让 Mac 上的 shotd 截图或录屏，并把文件存到本地目录。
#   mac-capture.sh shot [名称]          → $MAC_BRIDGE_DIR/shots/<时间>_<名称>.png
#   mac-capture.sh rec <秒数> [名称]     → $MAC_BRIDGE_DIR/recordings/<时间>_<名称>.mov
# 环境变量：MAC_BRIDGE_DIR（默认 ~/mac-bridge）、MAC_HOST（默认 mac）、
#           CLAUDE_BRIDGE_DIR（Mac 上 shotd 的目录，默认 .claude-bridge，相对 Mac 家目录）
set -euo pipefail
ROOT="${MAC_BRIDGE_DIR:-$HOME/mac-bridge}"
HOST="${MAC_HOST:-mac}"
B="${CLAUDE_BRIDGE_DIR:-.claude-bridge}"
ts=$(date +%Y-%m-%d_%H%M%S)
mkdir -p "$ROOT/shots" "$ROOT/recordings"; chmod 700 "$ROOT"

remote() { ssh -n -o BatchMode=yes "$HOST" "$@"; }

wait_for() {  # $1 = Mac 上的完成标记，$2 = 超时秒数
  remote "for i in \$(seq 1 $(( $2 * 2 ))); do [ -f $B/$1 ] && exit 0; sleep 0.5; done; exit 1" \
    || { echo "超时：shotd.sh 是否正在 Mac 的 Terminal.app 中运行？" >&2; exit 1; }
}

case "${1:-}" in
  shot)
    out="$ROOT/shots/${ts}_${2:-screen}.png"
    remote "rm -f $B/done; touch $B/req"
    wait_for done 15
    scp -q "$HOST:$B/shot-s.png" "$out"
    ;;
  rec)
    secs=${2:-10}
    [[ "$secs" =~ ^[0-9]+$ ]] || { echo "秒数必须是整数" >&2; exit 2; }
    out="$ROOT/recordings/${ts}_${3:-screen}.mov"
    remote "rm -f $B/rec-done; echo $secs > $B/rec"
    wait_for rec-done $(( secs + 30 ))
    scp -q "$HOST:$B/rec.mov" "$out"
    ;;
  *) echo "用法: $0 shot [名称] | rec <秒数> [名称]" >&2; exit 2 ;;
esac
echo "$out"
