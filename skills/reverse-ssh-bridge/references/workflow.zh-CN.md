# 反向 SSH 桥接：中文工作流

与 SKILL.md 英文版等价，以英文版为准。

拓扑：Agent 跑在**服务器**上。用户的 **Mac** 执行 `ssh -R <端口>:localhost:22 <服务器>`，服务器再用 `ssh mac` 连回 Mac（`mac` 是指向 `localhost:<端口>` 的别名）。整条链路不对公网开放任何端口。

## 先判断自己在哪一端

运行 `uname -s` 和 `hostname`。在服务器上，就通过 `ssh mac` 操作；在 Mac 上，就负责建立隧道。主机名、端口、用户名不要凭空假设，用 `grep '^Host ' ~/.ssh/config` 或 `ss -ltn` 查出来，查不到就问用户。

## 一次性配置

**Mac 端**（用户自己操作，或由能访问本机的 Agent 执行）：

1. 打开远程登录：系统设置 → 通用 → 共享 → 远程登录。macOS 13 起，命令行开启需要终端有完全磁盘访问权限，所以推荐用图形界面。
2. 安装 autossh：`brew install autossh`。
3. 确认 Mac 能免密登录服务器：`ssh -o BatchMode=yes <服务器> true`。
4. 启动隧道：`scripts/local/start-tunnel.sh <服务器别名>`，脚本会先做 5 项预检。想要开机自启、断线自动重连，就运行 `scripts/local/install-launchagent.sh <服务器别名>`。

**服务器端**：

1. 生成专用密钥：`ssh-keygen -t ed25519 -f ~/.ssh/to_mac -N '' -C reverse-ssh-bridge`。
2. 把公钥追加到 Mac 的 `~/.ssh/authorized_keys`，建议加上 `from="127.0.0.1,::1"` 前缀，这样这把钥匙只能经隧道使用。
3. 写入别名：`scripts/server/add-ssh-alias.sh <Mac 用户名> [端口] [私钥]`。脚本不会覆盖已有的 `Host mac`。
4. 验证：`ssh -n -o BatchMode=yes mac 'hostname; whoami'`。

## 日常使用

- **一律加 `-n`**。不加的话，ssh 会读走调用方的 stdin，脚本或循环里后面的命令就会被悄悄吞掉。
- 非交互 ssh 不加载登录 shell，PATH 里通常没有 Homebrew、nvm 和 `~/.local/bin`。用 `ssh -n mac 'zsh -lc "cd ~/proj && npm test"'` 包一层，或者让用户在 `~/.zshenv` 里设置 PATH。
- 引号：外层用单引号，服务器端的变量要有意识地展开。Mac 默认是 zsh，带 `?` 或 `*` 的 URL 必须加引号。
- 用本地编辑器打开文件：`ssh -n mac "open -a <App> '<绝对路径>'"`。先用 `ls /Applications` 确认装了哪个编辑器，不要默认是 VS Code。
- 传文件：`scp mac:<路径> <目标>`。
- 钥匙串里的凭据（gh、git 等）在 ssh 会话里通常读不到。gh 可以让用户执行 `gh auth login --insecure-storage`，执行前先说明代价：token 会以明文存在 600 权限的文件里。

## 截图与录屏

ssh 会话无法截屏，给 sshd 授予屏幕录制权限也没用。做法如下：

1. 用户在 **Terminal.app** 里运行 `scripts/local/shotd.sh` 并保持窗口打开。它会继承终端的录屏权限，第一次截图时 macOS 会弹窗请求授权。
2. 在服务器上执行 `scripts/server/mac-capture.sh shot [名称]` 截图，或 `scripts/server/mac-capture.sh rec <秒数> [名称]` 录屏，录屏最长 120 秒。
3. 文件保存在 `$MAC_BRIDGE_DIR`（默认 `~/mac-bridge`）下的 `shots/` 和 `recordings/`，文件名带时间戳。看图直接读 PNG；视频先用 `ffmpeg -i rec.mov -vf fps=2 frame_%03d.png` 抽帧再读。

截图、录屏和拷回来的对话记录都是个人数据，存在用户指定的目录里，不要放在公共的 `/tmp`。截图可能拍到私人窗口，不要上传，也不要提交到仓库。

## 安全边界

- 隧道等于把 Mac 用户的 shell 交给了服务器，服务器上有 root 权限的人同样能用。配置时要把这一点告诉用户。
- `-R` 只能绑定 loopback 地址，不要写 `0.0.0.0`，也不要开启 `GatewayPorts`。
- 使用专用密钥，并设置 `IdentitiesOnly=yes`。建议在 Mac 上配置 `PasswordAuthentication no` 和 `AllowUsers <用户>`。
- 遵守宿主环境的权限规则。所有命令都作用在用户的真实电脑上：删除文件、替换已安装的 App、`git push`、对外发布这类操作，先确认再执行。一次批准只对那一件事有效。
- 不要绕过 macOS 的隐私授权（TCC），需要权限时请用户去系统设置里授予。
- 用完告诉用户怎么停、怎么卸，这是两件事，都在 Mac 上做：
  - 前台的 `scripts/local/start-tunnel.sh`：在那个终端按 Ctrl+C，会停掉 `autossh`。
  - LaunchAgent 只停这一次登录：`launchctl unload ~/Library/LaunchAgents/com.user.reversetunnel.plist`。这会停掉 launchd 拉起的 `autossh`，plist 还在，下次登录会再启动。不要只杀掉 `autossh`：plist 里开了 `KeepAlive`，launchd 会把它再拉起来。
  - 彻底卸载：`scripts/local/install-launchagent.sh --uninstall`。它会对同一份 plist 执行 `launchctl unload -w`（停掉 `autossh` 并禁用该任务），然后删除该文件。标签是 `com.user.reversetunnel`。这不会停掉前台的 `start-tunnel.sh`。
