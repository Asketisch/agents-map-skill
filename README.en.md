<p align="center">
  <a href="README.md">中文</a> · <b>English</b>
</p>

# AGENTS Map

AGENTS Map is an agent skill, triggered with `/agents-map`, that maintains an "AGENTS.md system" for any project: the root file stays resident in context, while layer files, directory files and member files are read on demand as tasks drill down; system-level notes live in docs/. The goal is for the agent to read **accurate contracts** per task, instead of grepping the whole repo and stitching together information that may be wrong.

It is not a doc generator — a one-time scaffold whose output starts drifting the moment it is produced. AGENTS Map is a living map that maintains itself: when code changes, it converges along the diff (sync); periodically it runs a health check and proposes structural evolution (audit).

## Quick Start

It is not tied to any particular harness — the artifact it maintains, AGENTS.md, is a standard that mainstream agent runtimes (Claude Code, Codex, Cursor, etc.) all read, and the skill format itself works across tools. The check script uses only bash + coreutils. With Claude Code as an example, put this repo into your skills directory:

```bash
git clone https://github.com/Asketisch/agents-map-skill ~/.claude/skills/agents-map
```

Then run it inside the target project:

```
/agents-map
```

The mode argument can be omitted and is inferred from the project's state: no AGENTS.md anywhere → init; an existing system → sync. Sync first prints a drift report and only applies precise edits after you confirm — no full rewrites; audit is read-only and changes nothing.

## Three Ways to Use It

**init — first-time build / fill in missing layers** — scans the project's shape and scale, evaluates each directory node's capacity to derive a target tree, then generates bottom-up:

```
/agents-map init
```

Member/directory files are the real content sources; layer files distill overviews; the root file keeps only a navigation table and a "code change → files to update" mapping table. After generation it runs the check script and spot-reverifies assertions against code (anti-guessing).

**sync — converge drift along the diff** — anchors on the last commit that touched any AGENTS.md and routes subsequent code changes to the {file, section} that needs updating:

```
/agents-map sync
```

Three signal layers (structural → mapping table → assertion comparison) locate each change; build artifacts and submodule mirrors are on the exclusion list and never edited; drift patterns a human newly discovers go into the learning loop `LEARNINGS.md`.

**audit — health report and structural evolution** — a full check that does not depend on git diff, read-only:

```
/agents-map audit
```

Checks links, line budgets, section completeness and index closure, plus a "high-churn directories × doc freshness" matrix to catch silent drift, and outputs split-down / merge-up / grow-here suggestions. Suggestions are never executed automatically; after confirmation, init or sync applies them.

## Core Features

- **Progressive disclosure** — the root file is resident, layer/member files are read on demand; every file has a line budget (root: 120–180, hard cap 200), so context is never drowned.
- **Dynamic splitting** — no fixed tree depth; a subtree splits by module once its weighted code volume passes ~30k, thresholds calibrated on a real 45-crate Rust workspace.
- **Drift routing** — diffs route precisely to the target section through three signal layers; only the drifted part changes, each file's structure and voice stay intact.
- **Self-iterating learning** — `LEARNINGS.md` with four fixed sections (threshold calibration / template tweaks / drift patterns / project exceptions) and three anti-bloat gates: a 120-line cap, promotion at seen≥2, and human review before promotion.
- **Multi-shape fit** — Rust workspace / JS monorepo / Python / Go each get their own vocabulary mapping and file skeletons; doc language follows the target project rather than defaulting to Chinese.
- **Hard rules** — only assert what actually exists in the code, no speculative docs; AGENTS.md inside submodule mirrors is never edited.

## Documentation

| Document | Contents |
|------|------|
| [SKILL.md](SKILL.md) | Skill definition: Phase 0 inference and the full workflows of the three modes |
| [references/templates.md](references/templates.md) | Four AGENTS.md file skeletons and the shape→vocabulary mapping |
| [references/splitting.md](references/splitting.md) | Shape detection, dynamic splitting rules, line budgets, threshold calibration |
| [references/sync-routing.md](references/sync-routing.md) | Sync's three-layer signal routing algorithm and noise exclusion blacklist |
| [scripts/check_agents_docs.sh](scripts/check_agents_docs.sh) | System check script: links / line budgets / sections / index closure |

## Repository

<https://github.com/Asketisch/agents-map-skill>
