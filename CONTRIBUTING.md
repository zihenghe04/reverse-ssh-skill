# Contributing / 参与贡献

Use placeholder hosts (`my-server`, `user@203.0.113.10`) and documentation-range IPs in examples and tests. Never include real host names, user names, IP addresses, private keys, `authorized_keys` lines, tokens, screenshots or recordings. Describe the macOS version, the side (Mac or server), the exact command and the error text.

示例和测试使用占位主机（`my-server`、`user@203.0.113.10`）和文档保留 IP。不要包含真实主机名、用户名、IP、私钥、`authorized_keys` 内容、令牌、截图或录屏。反馈时说明 macOS 版本、出问题的一端（Mac 还是服务器）、具体命令和报错原文。

Run the unit tests and `python3 tools/privacy_check.py` before opening a PR. Report a suspected exposure privately, not in a public issue.

提交 PR 前运行单元测试和 `python3 tools/privacy_check.py`。发现可能的泄露时请私下报告，不要发到公开 issue。
