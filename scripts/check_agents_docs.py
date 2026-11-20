#!/usr/bin/env python3
"""Check local AGENTS.md links and reachability without imposing a language."""
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
if not root.is_dir() or len(sys.argv) > 2:
    print('Usage: check_agents_docs.sh [repo_root]', file=sys.stderr)
    sys.exit(2)
excluded = {'.git', 'target', 'node_modules', 'dist', 'build', 'vendor'}
submodules = set()
if (root / '.gitmodules').is_file():
    result = subprocess.run(['git', 'config', '-f', str(root / '.gitmodules'), '--get-regexp', r'\.path$'], capture_output=True, text=True)
    submodules = {line.split(None, 1)[1] for line in result.stdout.splitlines() if len(line.split(None, 1)) == 2}
docs = []
for current, dirs, files in os.walk(root, followlinks=False):
    base = Path(current)
    dirs[:] = [d for d in dirs if d not in excluded and not (base / d / '.git').is_file() and (base / d).relative_to(root).as_posix() not in submodules]
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
print(f'AGENTS.md 自检({root}): {len(docs)} 篇 | error={errors}')
sys.exit(1 if errors else 0)
