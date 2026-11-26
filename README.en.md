<p align="center">
  <a href="README.md">中文</a> · <b>English</b>
</p>

# AGENTS Map

AGENTS Map is an agent skill, triggered with `/agents-map`, that maintains an "AGENTS.md system" for any project: the root file stays resident in context, while layer files, directory files and member files are read on demand as tasks drill down; system-level notes live in docs/. The goal is for the agent to read **accurate contracts** per task, instead of grepping the whole repo and stitching together information that may be wrong.

It is not a doc generator — a one-time scaffold whose output starts drifting the moment it is produced. AGENTS Map is a living map that maintains itself: when code changes, it converges along the diff (sync); periodically it runs a health check and proposes structural evolution (audit).

## Quick Start

Loading and invocation differ between agent tools; cross-tool compatibility has not yet been tested. The check script requires Bash and Python 3. With Claude Code as an example, put this repo into your skills directory:

```bash
git clone https://github.com/Asketisch/agents-map-skill ~/.claude/skills/agents-map
```

Then run it inside the target project:

```
/agents-map
```

The mode argument can be omitted and is inferred from the project's state: no AGENTS.md anywhere → init; an existing system → sync. Sync first prints a drift report and only applies precise edits after you confirm — no full rewrites; audit is read-only and outputs reports and proposals; code moves happen only in an explicitly approved gated phase (restructure).

## Three Modes + One Gated Phase

**init — first-time build / fill in missing layers** — scans the project's shape and scale, evaluates each directory node's capacity to derive a target tree, then generates bottom-up:

```
/agents-map init
```

Member/directory files are the real content sources; layer files distill overviews; the root file keeps only a navigation table and a "code change → files to update" mapping table. After generation it runs the check script and spot-reverifies assertions against code (anti-guessing).

**sync — converge drift along the diff** — uses each document’s last commit as its own heuristic baseline and routes subsequent code changes to the {file, section} that needs updating:

```
/agents-map sync
```

Three signal layers (structural → mapping table → assertion comparison) locate each change; build artifacts and submodule mirrors are on the exclusion list and never edited; uncertain findings are reported for review.

**audit — health report and structural evolution** — a full check that does not depend on git diff, read-only:

```
/agents-map audit
```

Checks links, line budgets, root reachability and flat-directory signals (`--structure`), plus a "high-churn directories × doc freshness" matrix to catch silent drift, and outputs split-down / merge-up / grow-here suggestions. Suggestions are never executed automatically; after confirmation, init or sync applies them — anything touching code structure becomes a move proposal handed to restructure.

**restructure — reorganize code by function (approval-gated)** — when a directory holds too many flattened source files (~>20) with no functional substructure, a long enumeration doc would betray progressive disclosure; what should change is the directory itself:

```
/agents-map restructure
```

Audit or this command emits a **move proposal** (file → subdirectory, with per-file evidence and risk notes). After per-directory approval it executes: one pure `git mv` commit per cluster, build + tests run with each batch, failure reverts that batch; the AGENTS.md tree grows to mirror the new layout within the same phase. Go repos default to proposal-only. Sync never moves code.

## Why touch structure

Infinite subdivision must stay drillable: each file is 40–130 lines with one nav-table row per child, so **>15 direct children always busts the budget** — "every file stays short" must come from the directory layout, not from compressing prose. Once directories carry the functional partition, an agent locates code by descending layer by layer, like reading a skill, precisely — never forced to swallow a long enumeration.

## Core Features

- **Progressive disclosure** — the root file is resident, layer/member files are read on demand; every file has a line budget (root: 120–180, hard cap 200), so context is never drowned.
- **Dynamic splitting** — no fixed tree depth; weighted code volume, public-contract count and **direct flat source-file count per directory** are signals to review for a split; subdivision is carried by the directory layout, not by long enumeration docs; thresholds calibrated on a real 45-crate Rust workspace.
- **Controlled structural evolution** — when a directory should split but has nothing to split into, restructure proposes with evidence, executes only after per-directory approval, one commit per batch with build + tests, reverting on failure; the skill never touches code without that approval.
- **Drift routing** — diffs route precisely to the target section through three signal layers; only the drifted part changes, each file's structure and voice stay intact.
- **Feedback** — project-specific exceptions stay in the project; maintainers review general improvements.
- **Multi-shape fit** — Rust workspace / JS monorepo / Python / Go each get their own vocabulary mapping and file skeletons; doc language follows the target project rather than defaulting to Chinese.
- **Hard rules** — only assert what actually exists in the code, no speculative docs; AGENTS.md inside submodule mirrors is never edited.

## Documentation

| Document | Contents |
|------|------|
| [SKILL.md](SKILL.md) | Skill definition: Phase 0 inference, the three modes and the restructure phase |
| [references/templates.md](references/templates.md) | Four AGENTS.md file skeletons and the shape→vocabulary mapping |
| [references/splitting.md](references/splitting.md) | Shape detection, dynamic splitting rules, line budgets, threshold calibration |
| [references/sync-routing.md](references/sync-routing.md) | Sync's three-layer signal routing algorithm and noise exclusion blacklist |
| [references/restructure.md](references/restructure.md) | Code-move protocol: evidence clustering, approval gate, execution and rollback, per-language mechanics, never-move list |
| [scripts/check_agents_docs.sh](scripts/check_agents_docs.sh) | System check script: links / line budgets / sections / index closure |

## Repository

<https://github.com/Asketisch/agents-map-skill>

## Verification and limitations

Run `python3 -m unittest discover -s tests` for checker fixtures. Sync baselines and semantic routing are heuristics, not proof that documentation is current. Shallow or missing history requires a full review. Cross-tool compatibility and task outcomes have not been validated. The checker requires Bash and Python 3.
