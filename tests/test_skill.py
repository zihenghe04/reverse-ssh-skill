"""Static checks for the skill package. Run: python -m unittest discover -s tests -v"""
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


if __name__ == '__main__':
    unittest.main()
