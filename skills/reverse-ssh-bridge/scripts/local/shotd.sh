#!/bin/zsh
# 在 Mac 的 Terminal.app（或 iTerm）中运行并保持窗口打开：它继承该 App 的「屏幕录制」权限。
# ssh 会话本身无法截屏，服务器通过在 $D 下写请求文件来触发：
#   req          → 截图，输出 shot.png 和缩小版 shot-s.png
#   rec（内容为秒数）→ 录屏（默认 10 秒，最长 120 秒），输出 rec.mov
D="${CLAUDE_BRIDGE_DIR:-$HOME/.claude-bridge}"
mkdir -p "$D"; chmod 700 "$D"
echo "shotd 运行中，目录 $D（Ctrl+C 退出）"
while true; do
  if [[ -f $D/req ]]; then
    rm -f $D/req
    /usr/sbin/screencapture -x $D/shot.png && sips -Z 1800 $D/shot.png --out $D/shot-s.png >/dev/null 2>&1
    touch $D/done
  fi
  if [[ -f $D/rec ]]; then
    secs=$(head -c 8 $D/rec | tr -cd 0-9); rm -f $D/rec
    secs=${secs:-10}; (( secs > 120 )) && secs=120; (( secs < 1 )) && secs=1
    rm -f $D/rec.mov
    /usr/sbin/screencapture -x -v -V $secs $D/rec.mov
    touch $D/rec-done
  fi
  sleep 0.3
done
