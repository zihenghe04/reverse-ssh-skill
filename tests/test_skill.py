"""Checks for the skill package. Run: python -m unittest discover -s tests -v"""
from pathlib import Path
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills' / 'reverse-ssh-bridge'
sys.path.insert(0, str(ROOT))
import install  # noqa: E402

# Direct entry points: each has a shebang and is invoked as a program.
# Nothing in this tree is sourced. A sourced library stays 100644 and is
# not listed here; adding one means updating this test on purpose.
ENTRY_POINTS = {
    'skills/reverse-ssh-bridge/scripts/local/install-launchagent.sh',
    'skills/reverse-ssh-bridge/scripts/local/shotd.sh',
    'skills/reverse-ssh-bridge/scripts/local/start-tunnel.sh',
    'skills/reverse-ssh-bridge/scripts/server/add-ssh-alias.sh',
    'skills/reverse-ssh-bridge/scripts/server/mac-capture.sh',
}
STOP_DOCS = (
    ROOT / 'README.md',
    ROOT / 'README.zh-CN.md',
    SKILL / 'SKILL.md',
    SKILL / 'references' / 'workflow.zh-CN.md',
    SKILL / 'references' / 'troubleshooting.md',
)


class SkillPackage(unittest.TestCase):
    def test_frontmatter(self):
        text = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
        match = re.match(r'^---\nname: ([a-z0-9-]+)\ndescription: (.+?)\n---\n', text, re.S)
        self.assertIsNotNone(match, 'SKILL.md needs name/description frontmatter')
        self.assertEqual(match.group(1), SKILL.name)
        self.assertLessEqual(len(match.group(2)), 1024)

    def test_linked_files_exist(self):
        text = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
        for link in re.findall(r'\]\(([^)#]+)\)', text):
            self.assertTrue((SKILL / link).exists(), link)
        for script in re.findall(r'`(scripts/[\w./-]+\.sh)', text):
            self.assertTrue((SKILL / script).exists(), script)

    @unittest.skipUnless(shutil.which('bash'), 'bash not available')
    def test_bash_scripts_parse(self):
        for script in sorted(SKILL.glob('scripts/**/*.sh')):
            if script.read_text(encoding='utf-8').startswith('#!/bin/zsh'):
                continue
            result = subprocess.run(['bash', '-n', str(script)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, f'{script.name}: {result.stderr}')

    @unittest.skipUnless(shutil.which('zsh'), 'zsh not available')
    def test_zsh_scripts_parse(self):
        for script in sorted(SKILL.glob('scripts/**/*.sh')):
            if script.read_text(encoding='utf-8').startswith('#!/bin/zsh'):
                result = subprocess.run(['zsh', '-n', str(script)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, f'{script.name}: {result.stderr}')

    def test_tunnel_binds_loopback_only(self):
        for script in SKILL.glob('scripts/**/*.sh'):
            text = script.read_text(encoding='utf-8')
            self.assertNotIn('0.0.0.0:', text, script.name)
            self.assertNotIn('GatewayPorts yes', text, script.name)

    @unittest.skipIf(os.name == 'nt', 'POSIX permissions')
    def test_install_copies_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = install.install('claude', tmp)
            self.assertTrue((output / 'SKILL.md').is_file())
            for script in output.glob('scripts/**/*.sh'):
                self.assertTrue(os.access(script, os.X_OK), script.name)
            with self.assertRaises(FileExistsError):
                install.install('claude', tmp)

    @unittest.skipUnless(shutil.which('git'), 'git not available')
    def test_script_entry_points_are_executable_in_git(self):
        result = subprocess.run(
            ['git', 'ls-files', '-s', '-z', '--', 'skills/reverse-ssh-bridge/scripts'],
            cwd=ROOT, capture_output=True, check=True)
        modes = {}
        for entry in result.stdout.split(b'\0'):
            if not entry:
                continue
            meta, path = entry.split(b'\t', 1)
            rel = path.decode()
            mode = meta.split()[0].decode()
            if not rel.endswith('.sh'):
                self.assertEqual(mode, '100644', rel)
                continue
            modes[rel] = mode
        self.assertEqual(set(modes), ENTRY_POINTS)
        for rel, mode in sorted(modes.items()):
            self.assertEqual(mode, '100755', rel)
        on_disk = {p.relative_to(ROOT).as_posix() for p in SKILL.glob('scripts/**/*.sh')}
        self.assertEqual(on_disk, ENTRY_POINTS)
        for rel in sorted(ENTRY_POINTS):
            first = (ROOT / rel).read_text(encoding='utf-8').splitlines()[0]
            self.assertTrue(first.startswith('#!'), rel)

    def test_stop_and_uninstall_docs_agree(self):
        for doc in STOP_DOCS:
            text = doc.read_text(encoding='utf-8')
            self.assertIn('--uninstall', text, doc.name)
            self.assertIn('launchctl unload', text, doc.name)
            self.assertIn('com.user.reversetunnel', text, doc.name)

    @unittest.skipUnless(shutil.which('bash'), 'bash not available')
    def test_uninstall_unloads_and_removes_plist(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            plist = home / 'Library' / 'LaunchAgents' / 'com.user.reversetunnel.plist'
            plist.parent.mkdir(parents=True)
            plist.write_text('placeholder', encoding='utf-8')
            bin_dir = home / 'bin'
            bin_dir.mkdir()
            log = home / 'launchctl.log'
            fake = bin_dir / 'launchctl'
            fake.write_text(
                '#!/bin/sh\n'
                'printf \'%s\\n\' "$@" >> "$LAUNCHCTL_LOG"\n'
                'plist=${3:-}\n'
                'if [ ! -e "$plist" ]; then echo missing >&2; exit 1; fi\n',
                encoding='utf-8')
            fake.chmod(0o755)
            env = os.environ.copy()
            env['HOME'] = str(home)
            env['PATH'] = str(bin_dir) + os.pathsep + env.get('PATH', '')
            env['LAUNCHCTL_LOG'] = str(log)
            script = SKILL / 'scripts' / 'local' / 'install-launchagent.sh'

            result = subprocess.run(
                ['bash', str(script), '--uninstall'],
                capture_output=True, text=True, env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('com.user.reversetunnel', result.stdout)
            self.assertFalse(plist.exists())
            self.assertEqual(
                log.read_text(encoding='utf-8').splitlines(),
                ['unload', '-w', str(plist)])

            again = subprocess.run(
                ['bash', str(script), '--uninstall'],
                capture_output=True, text=True, env=env)
            self.assertEqual(again.returncode, 0, again.stderr)
            self.assertFalse(plist.exists())


if __name__ == '__main__':
    unittest.main()
