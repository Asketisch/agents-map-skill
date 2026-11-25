#!/usr/bin/env python3
"""Check local AGENTS.md links and reachability without imposing a language."""
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
STRUCT_MIN_SOURCES = 20
TEST_NAME_RE = re.compile(r'^(test_|.*[_\.-](test|spec)\.|\w*_test\.)')
submodules = set()
if (root / '.gitmodules').is_file():
    result = subprocess.run(['git', 'config', '-f', str(root / '.gitmodules'), '--get-regexp', r'\.path$'], capture_output=True, text=True)
    submodules = {line.split(None, 1)[1] for line in result.stdout.splitlines() if len(line.split(None, 1)) == 2}

def prunable(base, d, extra=()):
    return d in excluded or d in extra or (base / d / '.git').is_file() or (base / d).relative_to(root).as_posix() in submodules

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
    # Ignore fenced and inline code, then inspect ordinary inline Markdown links.
    text = re.sub(r'(?ms)^\s*(`{3,}|~{3,}).*?^\s*\1\s*$', '', content)
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
    # Advisory only, never counted in errors: a flat directory with many direct
    # source files is a code-structure signal (see references/restructure.md).
    for current, dirs, files in os.walk(root, followlinks=False):
        base = Path(current)
        dirs[:] = [d for d in dirs if not prunable(base, d, STRUCT_EXCLUDE_DIRS)]
        count = sum(1 for f in files if Path(f).suffix in SOURCE_EXTS and not TEST_NAME_RE.match(f))
        if count > STRUCT_MIN_SOURCES:
            print(f'  [struct ] {base.relative_to(root).as_posix()}: {count} 个直接源文件(>{STRUCT_MIN_SOURCES})，评估按功能分子目录(见 references/restructure.md)')
            dirs[:] = []
print(f'AGENTS.md 自检({root}): {len(docs)} 篇 | error={errors}')
sys.exit(1 if errors else 0)
