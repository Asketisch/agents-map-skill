import subprocess
import tempfile
import unittest
from pathlib import Path

CHECK = Path(__file__).resolve().parents[1] / 'scripts/check_agents_docs.sh'

class CheckerTests(unittest.TestCase):
    def run_check(self, root, *args):
        return subprocess.run(['bash', str(CHECK), *args, str(root)], capture_output=True, text=True)

    def test_reachable_english_and_spaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            child = root / 'deep path' / 'nested'
            child.mkdir(parents=True)
            (root / 'AGENTS.md').write_text('[Guide](<deep path/nested/AGENTS.md>)\n')
            (child / 'AGENTS.md').write_text('# Local instructions\n')
            result = self.run_check(root)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertNotIn('[warn ]', result.stdout)

    def test_broken_and_unreachable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'AGENTS.md').write_text('[Missing](missing.md)\n')
            (root / 'child').mkdir()
            (root / 'child/AGENTS.md').write_text('# Child\n')
            result = self.run_check(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn('死链', result.stdout)
            self.assertIn('无法从根篇访问', result.stdout)

    def test_gitfile_submodule_is_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'AGENTS.md').write_text('# Root\n')
            (root / 'module').mkdir()
            (root / 'module/.git').write_text('gitdir: elsewhere\n')
            (root / 'module/AGENTS.md').write_text('[Broken](bad)\n')
            self.assertEqual(self.run_check(root).returncode, 0)

    def make_flat(self, tmp, count):
        root = Path(tmp)
        (root / 'AGENTS.md').write_text('# Root\n')
        (root / 'pkg').mkdir()
        for i in range(count):
            (root / 'pkg' / f'f{i}.py').write_text('x = 1\n')
        return root

    def test_structure_flags_flat_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_flat(tmp, 21)
            result = self.run_check(root, '--structure')
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn('[struct ] pkg: 21', result.stdout)

    def test_structure_silent_below_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_check(self.make_flat(tmp, 10), '--structure')
            self.assertNotIn('[struct ]', result.stdout)

    def test_structure_excludes_tests_generated_and_colocated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_flat(tmp, 0)
            for name in ('tests', 'target'):
                (root / name).mkdir()
                for i in range(25):
                    (root / name / f'f{i}.py').write_text('x = 1\n')
            for i in range(25):
                (root / 'pkg' / f'f{i}_test.py').write_text('x = 1\n')
            result = self.run_check(root, '--structure')
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertNotIn('[struct ]', result.stdout)

    def test_structure_off_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_flat(tmp, 21)
            plain = self.run_check(root)
            self.assertNotIn('[struct ]', plain.stdout)
            full = self.run_check(root, '--structure')
            self.assertIn('[struct ]', full.stdout)
            self.assertEqual(
                [line for line in full.stdout.splitlines() if '[struct ]' not in line],
                plain.stdout.splitlines())

if __name__ == '__main__':
    unittest.main()
