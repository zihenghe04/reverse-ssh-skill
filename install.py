#!/usr/bin/env python3
"""Install the skill locally without changing SSH or system settings."""
import argparse
import os
from pathlib import Path
import shutil


def install(target, destination=None):
    source = Path(__file__).resolve().parent / 'skills' / 'reverse-ssh-bridge'
    roots = {'codex': Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'skills',
             'claude': Path.home() / '.claude' / 'skills',
             'agents': Path.home() / '.agents' / 'skills'}
    root = Path(destination).expanduser() if destination else roots[target]
    output = root / source.name
    if output.exists():
        raise FileExistsError('Skill already installed; review it before replacing or updating')
    shutil.copytree(source, output, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for script in (output / 'scripts').rglob('*.sh'):
        script.chmod(0o755)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=('codex', 'claude', 'agents'), default='claude')
    parser.add_argument('--dest', help='Override the skill root directory')
    args = parser.parse_args()
    try:
        print('Installed:', install(args.target, args.dest))
        print('Restart or refresh your AI client. SSH and system settings have not been changed.')
    except FileExistsError as error:
        parser.exit(1, str(error) + '\n')
