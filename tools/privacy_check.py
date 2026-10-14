#!/usr/bin/env python3
"""Conservative publication check; never print matching sensitive content."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    'absolute-user-path': re.compile(r'(?:/Users/|/home/)(?!you\b|example\b|USER\b)[A-Za-z0-9_.-]+|[A-Z]:\\Users\\[A-Za-z0-9_.-]+'),
    'ipv4-address': re.compile(r'\b(?!127\.|0\.0\.0\.0|192\.0\.2\.|198\.51\.100\.|203\.0\.113\.)(?:\d{1,3}\.){3}\d{1,3}\b'),
    'credential-shaped-token': re.compile(r'(?:gh[pousr]_|sk-ant-|sk-proj-)[A-Za-z0-9_-]{12,}'),
    'uuid-shaped-value': re.compile(r'\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b'),
    'credential-query': re.compile(r'[?&](?:token|key|secret|password)=[A-Za-z0-9_-]{16,}', re.I),
}


def main():
    result = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
                            cwd=ROOT, capture_output=True)
    if result.returncode:
        print('Initialize Git before running the publication check', file=sys.stderr)
        return 1
    findings = []
    for name in result.stdout.decode().split('\0'):
        if not name:
            continue
        file = ROOT / name
        if file.is_symlink():
            findings.append((name, 0, 'symlink'))
            continue
        if any(part in {'runs', 'backups', '.venv', 'captures'} for part in file.relative_to(ROOT).parts):
            findings.append((name, 0, 'private-artifact'))
        try:
            text = file.read_text(encoding='utf-8')
        except (UnicodeDecodeError, IsADirectoryError):
            findings.append((name, 0, 'unreviewed-binary'))
            continue
        for number, line in enumerate(text.splitlines(), 1):
            for label, pattern in PATTERNS.items():
                if pattern.search(line):
                    findings.append((name, number, label))
    for name, number, label in findings:
        print(f'{name}:{number}: review required ({label})')
    if findings:
        return 1
    print('Publication pattern check passed; review staged content before publishing.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
