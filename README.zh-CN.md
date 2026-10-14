# 反向 SSH 桥接 Skill

[English](README.md) · [简体中文](README.zh-CN.md)

一个可安装的 AI Skill。编程 Agent（Claude Code、Codex 等）跑在**远程服务器**上，通过反向 SSH 隧道回连**你自己的 Mac**，可以：

- 执行本地命令
- 用本地编辑器打开文件
- 截图或录一小段屏

```text
Mac（sshd :22、编辑器、屏幕） ──ssh -R 2222:localhost:22──▶  服务器（Agent）
                              ◀──────── ssh mac ────────────
```

整个过程不对公网开放端口，转发的端口只监听在服务器的本机回环地址上。仓库里不包含原机器的主机名、用户名、密钥或 IP。

## 安装

需要 Git 和 Python 3.9 及以上版本。

```sh
git clone https://github.com/zihenghe04/reverse-ssh-skill.git
cd reverse-ssh-skill
python3 install.py --target claude     # 装到 ~/.claude/skills
python3 install.py --target codex      # 装到 ~/.codex/skills
python3 install.py --target agents     # 装到 ~/.agents/skills
```

- 想装到别的目录，加 `--dest /path/to/skills`。
- 安装时不会覆盖已有的同名 Skill，只复制文件，不会改动 SSH 或系统设置。
- 请装在**跑 Agent 的服务器**上。Mac 端用到的脚本在 `scripts/local/` 里，把这个目录拷到 Mac 上，或者在 Mac 上也 clone 一份仓库。

## 对 AI 说

Claude Code：

```text
/reverse-ssh-bridge 检查 ssh mac 是否可用，然后在我的 Mac 上跑 ~/code/my-app 的测试，并截图给我看结果。
```

Codex：

```text
用 $reverse-ssh-bridge 帮我在 Mac 和这台服务器之间建立反向隧道。
```

## 包含的脚本

| 脚本 | 在哪运行 | 作用 |
|---|---|---|
| `scripts/local/start-tunnel.sh <服务器>` | Mac | 先做 5 项预检，再用 `autossh -R` 建立保活隧道 |
| `scripts/local/install-launchagent.sh <服务器>` | Mac | 开机自启、断线自动重连（加 `--uninstall` 卸载） |
| `scripts/local/shotd.sh` | Mac 的 Terminal.app | 截图服务，继承终端的屏幕录制权限 |
| `scripts/server/add-ssh-alias.sh <Mac 用户名>` | 服务器 | 添加 `Host mac` 别名，并输出要追加到 Mac `authorized_keys` 的那一行 |
| `scripts/server/mac-capture.sh shot\|rec <秒>` | 服务器 | 请求截图或录屏，并把文件拷到 `$MAC_BRIDGE_DIR` |

为什么需要单独的截图服务？macOS 不允许 SSH 会话截屏，就算给 sshd 授予了屏幕录制权限，也会报 `could not create image from display`。从图形界面的终端里启动的进程则可以截屏。

## 安全

隧道等于把你 Mac 用户的 shell 交给了服务器，服务器上有 root 权限的人同样能用。建议：

- 使用专用密钥，并在 `authorized_keys` 里加上 `from="127.0.0.1,::1"` 限制；
- 转发只绑定回环地址；
- 不用的时候关掉隧道。

截图可能拍到私人窗口，请存在私有目录里，不要提交到仓库。Skill 会要求 Agent 在你的 Mac 上执行破坏性或对外的操作之前先征得你的确认。

## 开发

```sh
python3 -m unittest discover -s tests -v
python3 tools/privacy_check.py
```

见 [CONTRIBUTING.md](CONTRIBUTING.md)。MIT 许可。
