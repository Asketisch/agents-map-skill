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

    def test_structure_flags_root_clutter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'AGENTS.md').write_text('# Root\n')
            for i in range(12):
                (root / f'script{i}.py').write_text('x = 1\n')
            result = self.run_check(root, '--structure')
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn('[struct ] .: 仓库根直接平铺 12', result.stdout)

    def test_structure_flags_lonely_dir_but_spares_entries_nested_and_uniform(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'AGENTS.md').write_text('# Root\n')
            for parent, name in (('cmd/serv', 'main.go'), ('lonely', 'util.py'),
                                 ('wrap/deep', 'x.py'), ('wrap/deep/sub', 'y.py'),
                                 ('features/plan', 'plan.ts'), ('features/about', 'about.ts'),
                                 ('hub', 'a.ts'), ('hub', 'b.ts'), ('hub', 'c.ts'),
                                 ('hub/odd', 'x.ts')):
                (root / parent).mkdir(parents=True, exist_ok=True)
                (root / parent / name).write_text('x = 1\n')
            result = self.run_check(root, '--structure')
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn('[struct ] lonely:', result.stdout)
            self.assertIn('[struct ] hub/odd', result.stdout)  # 多文件目录旁的孤挂子目录应并入引用者
            self.assertNotIn('[struct ] cmd', result.stdout)  # 构建入口不算孤儿
            self.assertNotIn('[struct ] wrap/deep:', result.stdout)  # 有源子孙不算孤儿
            self.assertNotIn('[struct ] features', result.stdout)  # 兄弟多为单文件属本地惯例

    def test_structure_skips_hidden_and_artifact_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'AGENTS.md').write_text('# Root\n')
            for parent in ('dist-visual/assets', '.test-results/real-machine', '.agents/x'):
                (root / parent).mkdir(parents=True)
                for i in range(21):
                    (root / parent / f'f{i}.js').write_text('x = 1\n')
            result = self.run_check(root, '--structure')
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertNotIn('[struct ]', result.stdout)

    def test_structure_reports_stale_backtick_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'real.md').write_text('# ok\n')
            (root / 'assets').mkdir()
            (root / 'assets/logo.svg').write_text('<svg/>\n')
            (root / 'src/stores').mkdir(parents=True)
            for name in ('ui.ts', 'bus.ts'):
                (root / 'src/stores' / name).write_text('export {}\n')
            for parent, files in (('pkg', ('local.rs', 'other.rs')),
                                  ('pkg/sub', ('nested.rs', 'more.rs')),
                                  ('pkg/lib', ('helper.ts',)),
                                  ('pkg/deep', ())):
                (root / parent).mkdir(parents=True, exist_ok=True)
                for name in files:
                    (root / parent / name).write_text('x\n')
            (root / 'AGENTS.md').write_text(
                '[Guide](real.md)\n[Pkg](pkg/AGENTS.md)\n\n'
                '`real.md`\n`ghost/missing.py`\n`ghost/also.py:42`\n`stores/ui.ts`\n')
            (root / 'pkg/AGENTS.md').write_text('[Deep](deep/AGENTS.md)\n\n`sub/nested.rs`\n')
            (root / 'pkg/deep/AGENTS.md').write_text(
                '# deep\n\n`lib/helper.ts`\n`assets/logo.svg`\n')
            result = self.run_check(root, '--structure')
            self.assertEqual(result.returncode, 0, result.stdout)  # advisory，不计错误
            self.assertIn('位置断言失效 -> ghost/missing.py', result.stdout)
            self.assertIn('位置断言失效 -> ghost/also.py', result.stdout)  # 行号后缀剥掉
            self.assertNotIn('位置断言失效 -> real.md', result.stdout)
            self.assertNotIn('位置断言失效 -> sub/nested.rs', result.stdout)  # 文档相对可解析
            self.assertNotIn('位置断言失效 -> lib/helper.ts', result.stdout)  # 祖先目录可解析
            self.assertNotIn('位置断言失效 -> assets/logo.svg', result.stdout)  # 仓库根可解析
            self.assertNotIn('位置断言失效 -> stores/ui.ts', result.stdout)  # src/ 前缀缩写可解析

    def test_structure_ignores_prose_and_placeholder_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'AGENTS.md').write_text(
                '# Root\n\n`pnpm tauri dev`\n`<repo>/src`\n`目录/子目录`\n`docs/*`\n`vendor/x/y.py`\n')
            result = self.run_check(root, '--structure')
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertNotIn('[struct ]', result.stdout)

    def test_structure_root_at_threshold_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'AGENTS.md').write_text('# Root\n')
            for i in range(10):
                (root / f'script{i}.py').write_text('x = 1\n')
            result = self.run_check(root, '--structure')
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertNotIn('[struct ]', result.stdout)
            self.assertNotIn('仓库根', result.stdout)

    def test_structure_keeps_source_dirs_that_only_share_an_artifact_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'AGENTS.md').write_text('# Root\n')
            (root / 'distribution').mkdir()
            for i in range(21):
                (root / 'distribution' / f'f{i}.py').write_text('x = 1\n')
            result = self.run_check(root, '--structure')
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn('[struct ] distribution:', result.stdout)

    def test_structure_ignores_fenced_backtick_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'AGENTS.md').write_text(
                '# Root\n\n```\n`ghost/fenced.py`\n```\n\n`ghost/live.py`\n')
            result = self.run_check(root, '--structure')
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertNotIn('ghost/fenced.py', result.stdout)
            self.assertIn('位置断言失效 -> ghost/live.py', result.stdout)

    def test_structure_flags_directory_fanout_but_not_at_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'AGENTS.md').write_text('# Root\n')
            for name, count in (('wide', 16), ('ok', 15)):
                for i in range(count):
                    child = root / name / f'm{i}'
                    child.mkdir(parents=True)
                    (child / 'a.py').write_text('x = 1\n')
            result = self.run_check(root, '--structure')
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn('[struct ] wide: 16 个直接子目录', result.stdout)
            self.assertNotIn('[struct ] ok:', result.stdout)

    def test_nested_overload_under_overloaded_parent_is_reported(self):
        # 回归:旧版在上层超载时截断下钻,嵌套的平铺目录(如 zhuye-tools/src/builtins)被藏起来。
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'AGENTS.md').write_text('# Root\n')
            packed = root / 'packed'
            packed.mkdir()
            for i in range(21):
                (packed / f'f{i}.py').write_text('x = 1\n')
            for i in range(16):
                child = packed / f'm{i}'
                child.mkdir()
                (child / 'a.py').write_text('x = 1\n')
            inner = packed / 'm0' / 'inner'
            inner.mkdir()
            for j in range(21):
                (inner / f'g{j}.py').write_text('x = 1\n')
            result = self.run_check(root, '--structure')
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn('[struct ] packed: 21 个直接源文件', result.stdout)
            self.assertIn('[struct ] packed: 16 个直接子目录', result.stdout)
            self.assertIn('[struct ] packed/m0/inner: 21 个直接源文件', result.stdout)

    def test_cargo_bin_single_file_is_not_a_lonely_dir(self):
        # 回归:src/bin/*.rs 是 Cargo 自动发现的构建目标,不是碎目录。
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'AGENTS.md').write_text('# Root\n')
            (root / 'crates/t/src/bin').mkdir(parents=True)
            (root / 'crates/t/src/lib.rs').write_text('pub fn a() {}\n')
            (root / 'crates/t/src/bin/tool.rs').write_text('fn main() {}\n')
            result = self.run_check(root, '--structure')
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertNotIn('crates/t/src/bin', result.stdout)

    def test_rust_tests_submodule_file_is_not_source(self):
        # 回归:load/tests.rs 只是测试子模块,不能把 load/ 当成单源文件目录。
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'AGENTS.md').write_text('# Root\n')
            (root / 'crates/c/src/load').mkdir(parents=True)
            (root / 'crates/c/src/lib.rs').write_text('pub fn a() {}\n')
            (root / 'crates/c/src/load/tests.rs').write_text('#[test] fn t() {}\n')
            result = self.run_check(root, '--structure')
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertNotIn('crates/c/src/load', result.stdout)

    def test_non_bin_single_file_dir_still_flagged(self):
        # 对照:普通单文件目录仍要报,避免把豁免放得太宽。
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'AGENTS.md').write_text('# Root\n')
            (root / 'crates/t/src/lonely').mkdir(parents=True)
            (root / 'crates/t/src/lib.rs').write_text('pub fn a() {}\n')
            (root / 'crates/t/src/lonely/util.rs').write_text('fn u() {}\n')
            result = self.run_check(root, '--structure')
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn('[struct ] crates/t/src/lonely: 单源文件目录', result.stdout)

if __name__ == '__main__':
    unittest.main()
