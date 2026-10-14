# 排错 / Troubleshooting

| 现象 / Symptom | 原因与处理 / Cause and fix |
|---|---|
| `Turning Remote Login on or off requires Full Disk Access privileges` | macOS 13+ 的限制。用 GUI 打开「远程登录」，或者给终端 App 授予完全磁盘访问权限，然后 ⌘Q 退出 App 再重开。 |
| zsh: `Error: # is not a valid command` | zsh 交互模式默认不认 `#` 注释。只粘贴命令本身，或者先执行 `setopt interactive_comments`。 |
| `./start-tunnel.sh your-server` 只输出两行就像卡住 | 传的是占位符，ssh 解析失败，autossh 一直在重试。换成真实的别名（`grep '^Host ' ~/.ssh/config`）。脚本自带预检，会直接报错。 |
| `remote port forwarding failed for listen port 2222` | 服务器上这个端口已被占用（可能是旧隧道还没退出），或者服务器 sshd 关掉了 `AllowTcpForwarding`。换一个端口，或等旧连接超时。 |
| 服务器 `ssh mac` 报 `Connection refused` | 隧道断了，或者 Mac 的 22 端口没在监听。在 Mac 上重新运行 `start-tunnel.sh`，并确认「远程登录」已打开。 |
| 服务器 `ssh mac` 报 `Permission denied (publickey)` | Mac 的 `~/.ssh/authorized_keys` 里没有服务器的公钥，或者 `from=` 限制写错了。 |
| 服务器 `ssh mac` 报 `Connection to localhost closed by remote host` | 一般是隧道或 Mac 的网络短暂中断。等几秒再试；在 Mac 上已经启动的进程不受影响。 |
| 脚本里 `ssh mac` 后面的命令没有执行 | ssh 读走了 stdin。改用 `ssh -n mac`。 |
| `npm: command not found`、`gh: not found` | 非交互 ssh 不加载登录 shell。用 `zsh -lc "…"` 包一层，或者在 `~/.zshenv` 里设置 PATH。 |
| `zsh: no matches found: …?per_page=…` | Mac 上是 zsh，带 `?` 或 `*` 的参数要加引号。 |
| `zsh: bad math expression` | zsh 算术表达式里不能用空变量或带逗号的值。先单独取出数值再计算。 |
| `gh`: `The token in default is invalid`，但在 Mac 终端里正常 | token 存在钥匙串里，ssh 会话读不到。在 Mac 终端执行 `gh auth login --insecure-storage`，token 会存到 600 权限的明文文件里，按需选择。 |
| `security …: User interaction is not allowed` | 同上：ssh 会话无法解锁登录钥匙串。 |
| `screencapture`: `could not create image from display` | ssh 会话不能截屏，给 sshd 授权也没用。在 Terminal.app 里运行 `shotd.sh`，再从服务器调用 `mac-capture.sh`。 |
| `mac-capture.sh` 超时 | `shotd.sh` 没有在运行，或者运行它的 App 没有屏幕录制权限。第一次截图时 macOS 会弹窗请求授权。 |
| `launchctl asuser …: Operation not permitted` | 普通用户不能从 ssh 切换到 GUI 会话。改用 shotd 方案，不要尝试绕过。 |
| `open -a` 没反应 | Mac 没有登录图形界面，或者 App 名字不对（用 `ls /Applications` 查）。 |
| launchd 隧道起不来 | plist 里必须写绝对路径。查看 `/tmp/reversetunnel.err`。 |
| 隧道频繁掉线 | 用 autossh 并设置 `ServerAliveInterval/CountMax`。Mac 睡眠时隧道一定会断，唤醒后 LaunchAgent 会自动重连。 |
| 代理 / TUN 环境下直连失败 | Clash 等工具开了 TUN 模式时，所有出站流量都走 TUN，按网卡绑定直连通常会失败。把服务器地址加进代理的直连规则，或者保持经代理连接。 |
