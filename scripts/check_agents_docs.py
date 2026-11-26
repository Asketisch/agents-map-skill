#!/usr/bin/env python3
"""检查 AGENTS.md 的本地链接与根篇可达性,不预设文档语言。

--structure 额外给出代码位置初筛(advisory,不计 error):文件扇出、目录扇出、
根目录散件、碎目录、失效的路径断言。判据见 references/layout.md。
"""
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

argv = list(sys.argv[1:])
structure = '--structure' in argv
if structure:
    argv.remove('--structure')
root = Path(argv[0] if argv else '.').resolve()
if not root.is_dir() or len(argv) > 1:
    print('Usage: check_agents_docs.sh [--structure] [repo_root]', file=sys.stderr)
    sys.exit(2)
excluded = {'.git', 'target', 'node_modules', 'dist', 'build', 'vendor'}
SOURCE_EXTS = {'.rs', '.py', '.ts', '.tsx', '.js', '.jsx', '.mjs', '.go', '.rb', '.java', '.kt', '.c', '.h', '.cpp', '.hpp', '.cs', '.swift', '.php'}
STRUCT_EXCLUDE_DIRS = excluded | {'tests', 'test', 'spec', 'docs', 'examples', 'benches', 'migrations'}
# 只跳过隐藏目录,以及 dist/target/coverage 本体或「名字-」产物(dist-visual、target-*)。
# 不用裸前缀:distribution/、targets/ 这类源目录要留下来。
ARTIFACT_BASENAMES = ('dist', 'target', 'coverage')
STRUCT_MIN_SOURCES = 20
STRUCT_ROOT_MAX = 10
STRUCT_MAX_CHILD_DIRS = 15
# 各语言构建入口的文件干名,不算碎目录(restructure.md §6)。
ENTRY_STEMS = {'main', 'index', 'lib', 'mod', '__init__', '__main__'}
# 目录名即入口约定:Cargo 自动发现 src/bin/*.rs,其中每个文件都是构建目标。
ENTRY_DIRS = {'bin'}
FENCE_RE = re.compile(r'(?ms)^\s*(`{3,}|~{3,}).*?^\s*\1\s*$')
BACKTICK_RE = re.compile(r'`([^`\n]+)`')
LINE_REF_RE = re.compile(r':\d+$')
PATHISH_RE = re.compile(r'\.[A-Za-z0-9]{1,8}$')
PATH_TOKEN_SKIP = set(' <>{*|$~"\'')
# 测试文件:test_*、*_test.*、*.test.*、*.spec.*,以及 Rust 的 tests.rs 子模块。
TEST_NAME_RE = re.compile(r'^(tests?\.|test_|.*[_\.-](test|spec)\.|\w*_test\.)')
submodules = set()
if (root / '.gitmodules').is_file():
    result = subprocess.run(['git', 'config', '-f', str(root / '.gitmodules'), '--get-regexp', r'\.path$'], capture_output=True, text=True)
    submodules = {line.split(None, 1)[1] for line in result.stdout.splitlines() if len(line.split(None, 1)) == 2}

def prunable(base, d, extra=()):
    return d in excluded or d in extra or (base / d / '.git').is_file() or (base / d).relative_to(root).as_posix() in submodules

def is_struct_artifact(name):
    """结构扫描要跳过的目录名:点开头,或构建产物名本身 / 连字符变体。"""
    if name.startswith('.'):
        return True
    return any(name == stem or name.startswith(stem + '-') for stem in ARTIFACT_BASENAMES)

docs = []
for current, dirs, files in os.walk(root, followlinks=False):
    base = Path(current)
    dirs[:] = [d for d in dirs if not prunable(base, d)]
    if 'AGENTS.md' in files:
        docs.append(base / 'AGENTS.md')
docs.sort()
if not docs:
    print('未发现任何 AGENTS.md')
    sys.exit(1)
errors = 0
edges = {doc: set() for doc in docs}
for doc in docs:
    rel = doc.relative_to(root)
    content = doc.read_text(encoding='utf-8')
    lines = content.splitlines()
    limit = 200 if doc == root / 'AGENTS.md' else 130
    if len(lines) > limit:
        print(f'  [warn ] {rel}: {len(lines)} 行 > {limit}，考虑精简或拆分')
    # 先剥围栏再剥行内代码,只检查普通正文里的链接。
    text = FENCE_RE.sub('', content)
    text = re.sub(r'`[^`\n]*`', '', text)
    for match in re.finditer(r'(?<!!)\[[^\]]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)', text):
        target = match.group(1).strip('<>')
        url = urlsplit(target)
        if url.scheme or url.netloc or target.startswith('#'):
            continue
        path = unquote(url.path)
        dest = (root / path.lstrip('/') if path.startswith('/') else doc.parent / path).resolve()
        if not dest.exists():
            print(f'  [ERROR] {rel}: 死链 -> {target}')
            errors += 1
        elif dest.is_dir():
            candidate = dest / 'AGENTS.md'
            if candidate in edges:
                edges[doc].add(candidate)
        elif dest in edges:
            edges[doc].add(dest)
start = root / 'AGENTS.md'
if start in edges:
    seen, pending = set(), [start]
    while pending:
        doc = pending.pop()
        if doc not in seen:
            seen.add(doc)
            pending.extend(edges[doc] - seen)
    for doc in docs:
        if doc not in seen:
            print(f'  [ERROR] 无法从根篇访问: {doc.relative_to(root)}')
            errors += 1
else:
    print('  [warn ] 无根篇，无法检查从根篇的可达性')
if structure:
    # 只做初筛,不计 error。惯例判断留给 agent(references/layout.md)。
    def struct_prunable(base, d):
        return prunable(base, d, STRUCT_EXCLUDE_DIRS) or is_struct_artifact(d)

    # 整棵树只走一遍,不因上层超载而截断:嵌套的平铺目录同样要量、同样要报。
    source_dirs, nodes, child_names = set(), [], {}
    root_sources = 0
    for current, dirs, files in os.walk(root, followlinks=False):
        base = Path(current)
        kept = [d for d in dirs if not struct_prunable(base, d)]
        dirs[:] = kept
        child_names[base] = kept
        sources = [f for f in files if Path(f).suffix in SOURCE_EXTS and not TEST_NAME_RE.match(f)]
        if sources:
            source_dirs.add(base)
        nodes.append((base, sources))
        if base == root:
            root_sources = len(sources)
        if len(sources) > STRUCT_MIN_SOURCES:
            rel = '.' if base == root else base.relative_to(root).as_posix()
            print(f'  [struct ] {rel}: {len(sources)} 个直接源文件(>{STRUCT_MIN_SOURCES})，评估按功能分子目录(见 references/restructure.md)')
    if root_sources > STRUCT_ROOT_MAX:
        print(f'  [struct ] .: 仓库根直接平铺 {root_sources} 个源文件(>{STRUCT_ROOT_MAX})，评估是否违反项目落点约定(见 references/layout.md)')
    # 有源码的目录,其祖先也算「有实质内容」,这样中间层的子目录扇出数得着。
    substantial = set()
    for src_dir in source_dirs:
        cur = src_dir
        while True:
            substantial.add(cur)
            if cur == root:
                break
            parent = cur.parent
            if not parent.is_relative_to(root) and parent != root:
                break
            cur = parent
    for base, names in child_names.items():
        count = sum(1 for name in names if (base / name) in substantial)
        if count > STRUCT_MAX_CHILD_DIRS:
            rel = '.' if base == root else base.relative_to(root).as_posix()
            print(f'  [struct ] {rel}: {count} 个直接子目录(>{STRUCT_MAX_CHILD_DIRS})，评估插入分组层(见 references/restructure.md)')
    by_parent = {}
    for base, sources in nodes:
        by_parent.setdefault(base.parent, []).append((base, len(sources)))
    for base, sources in nodes:
        # 入口目录(Cargo 的 src/bin/)里的单文件是构建目标,不是碎目录。
        if len(sources) != 1 or base == root or base.name in ENTRY_DIRS or Path(sources[0]).stem in ENTRY_STEMS:
            continue
        if any(other != base and other.is_relative_to(base) for other in source_dirs):
            continue
        siblings = [(d, n) for d, n in by_parent.get(base.parent, []) if d != base and n > 0]
        singles = sum(1 for _, n in siblings if n == 1)
        multis = len(siblings) - singles
        if siblings and multis <= singles:
            continue  # single-file siblings are the local convention, not asymmetry
        print(f'  [struct ] {base.relative_to(root).as_posix()}: 单源文件目录，评估并入其引用者所在目录(见 references/layout.md)')
    # Documented locations must match reality: backticked repo paths in
    # AGENTS.md that resolve nowhere are layout signal 7 (advisory). Tokens
    # are tried doc-relative first, then up the ancestor chain to the root,
    # each also under a src/ source root (common shorthand drops the src/).
    for doc in docs:
        rel = doc.relative_to(root)
        bases = [doc.parent]
        for anc in doc.parent.parents:
            if anc.is_relative_to(root):
                bases.append(anc)
            else:
                break
        reported = set()
        for token in BACKTICK_RE.findall(FENCE_RE.sub('', doc.read_text(encoding='utf-8'))):
            t = LINE_REF_RE.sub('', token.strip()).rstrip('/')
            if t.startswith('..') or any(ch in t for ch in PATH_TOKEN_SKIP) or '/' not in t:
                continue
            if t in reported:
                continue
            if any((base / t).exists() or (base / 'src' / t).exists() for base in bases):
                continue
            if any(t == sm or t.startswith(sm + '/') for sm in submodules) or t.split('/')[0] in excluded:
                continue
            if not PATHISH_RE.search(t):  # prose fragments like 目录/子目录 are not path assertions
                continue
            reported.add(t)
            print(f'  [struct ] {rel}: 位置断言失效 -> {t}（文档登记的路径不存在，见 references/layout.md）')
print(f'AGENTS.md 自检({root}): {len(docs)} 篇 | error={errors}')
sys.exit(1 if errors else 0)
