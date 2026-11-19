<p align="center">
  <b>中文</b> · <a href="README.en.md">English</a>
</p>

# AGENTS Map 文档地图

AGENTS Map 是一个 Claude Code skill,用 `/agents-map` 触发,为任意项目维护「AGENTS.md 体系」:根篇常驻上下文,层篇、目录篇、成员篇按任务下钻,系统级说明放 docs/。目标是让 Agent 按任务读到**准确的契约**,而不是靠 grep 全库拼凑可能错误的信息。

它不是文档生成器那种一次性脚手架——生成完那一刻就开始漂移。AGENTS Map 是一张会自己维护的活地图:代码变了它跟着 diff 收敛(sync),隔段时间它体检并提议结构演进(audit)。

## 快速开始

需要 Claude Code;自检脚本只用 bash + coreutils。把本仓库放进 skills 目录:

```bash
git clone https://github.com/Asketisch/agents-map-skill ~/.claude/skills/agents-map
```

再到目标项目里运行:

```
/agents-map
```

模式参数可省略,由项目现状自动推断:没有任何 AGENTS.md 走 init,已有体系走 sync。sync 会先输出漂移报告、经你确认后才逐条精确编辑,不全文重写;audit 只读,不改动任何东西。

## 三种用法

**init —— 首次建档 / 补齐缺失层** —— 扫描项目形态与量级,逐节点评估容量得出目标树形,再自底向上生成:

```
/agents-map init
```

成员篇/目录篇是真正的内容源,层篇提炼速览,根篇只留导航表和「代码改动 → 同步更新」映射表。生成后跑自检脚本,再随机抽篇逐断言回查代码(反猜测)。

**sync —— 按 diff 同步漂移** —— 以最近一次触及 AGENTS.md 的提交为锚,把其后的代码变更路由到该更新的篇与节:

```
/agents-map sync
```

三层信号(结构性 → 映射表 → 断言比对)逐条定位;构建产物和 submodule 镜像目录在排除名单里,绝不代改;人工新发现的漂移模式会进学习回路 `LEARNINGS.md`。

**audit —— 健康体检与结构演进** —— 不依赖 git diff 的全量检查,只读:

```
/agents-map audit
```

查链接、行数预算、章节完整、索引闭合,外加「高变更目录 × 文档新鲜度」矩阵揪出沉默漂移,输出下拆/上合/生长建议。建议不自动执行,经确认后由 init 或 sync 落地。

## 核心特性

- **渐进式披露** —— 根篇常驻、层篇/成员篇按需读,每篇有行数预算(根篇 120–180,硬上限 200),不拿全文喂上下文。
- **动态拆分** —— 树不设固定层数,子树加权代码量越过约 30k 即按模块下拆;阈值来自 45-crate Rust workspace 实测标定。
- **漂移路由** —— diff 经三层信号精确落到目标篇节,只改漂移处,保持各篇章节序与文风。
- **自迭代学习** —— `LEARNINGS.md` 四节固定(阈值校准/模板调整/漂移模式/项目例外),三闸防膨胀:120 行硬上限、seen≥2 建议晋升、晋升需人审。
- **多形态适配** —— Rust workspace / JS monorepo / Python / Go 各有词汇映射与篇型骨架;文档语言跟随目标项目,不默认套中文。
- **硬规则** —— 只断言代码中实际存在的内容,不写推测性文档;submodule 镜像里的 AGENTS.md 永不编辑。

## 文档

| 文档 | 内容 |
|------|------|
| [SKILL.md](SKILL.md) | skill 主定义:Phase 0 推断与三个模式的完整流程 |
| [references/templates.md](references/templates.md) | 四种 AGENTS.md 篇型骨架与形态→词汇映射 |
| [references/splitting.md](references/splitting.md) | 形态识别与动态拆分规则、行数预算、阈值标定 |
| [references/sync-routing.md](references/sync-routing.md) | sync 的三层信号路由算法与噪声排除黑名单 |
| [scripts/check_agents_docs.sh](scripts/check_agents_docs.sh) | 体系自检脚本:链接/行数/章节/索引闭合 |

## 仓库

<https://github.com/Asketisch/agents-map-skill>
