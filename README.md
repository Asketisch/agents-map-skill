<p align="center">
  <b>中文</b> · <a href="README.en.md">English</a>
</p>

# AGENTS Map 文档地图

AGENTS Map 是一个 Agent skill,用 `/agents-map` 触发,为任意项目维护「AGENTS.md 体系」:根篇常驻上下文,层篇、目录篇、成员篇按任务下钻,系统级说明放 docs/。目标是让 Agent 按任务读到**准确的契约**,而不是靠 grep 全库拼凑可能错误的信息。

它不是文档生成器那种一次性脚手架——生成完那一刻就开始漂移。AGENTS Map 是一张会自己维护的活地图:代码变了它跟着 diff 收敛(sync),隔段时间它体检并提议结构演进(audit)。

## 快速开始

它不绑定某个特定 harness——产出物 AGENTS.md 是各家 Agent 运行环境(Claude Code、Codex、Cursor 等)都会读的标准;不同工具的加载和触发方式可能不同，尚未进行跨工具兼容性实测。自检脚本需要 bash 和 Python 3。以 Claude Code 为例,把本仓库放进 skills 目录:

```bash
git clone https://github.com/Asketisch/agents-map-skill ~/.claude/skills/agents-map
```

再到目标项目里运行:

```
/agents-map
```

模式参数可省略,由项目现状自动推断:没有任何 AGENTS.md 走 init,已有体系走 sync。sync 会先输出漂移报告、按用户授权逐条精确编辑,不全文重写;audit 只读,输出报告与提案;代码搬移只发生在显式批准的门禁阶段(restructure)。

## 三种模式 + 一个门禁阶段

**init —— 首次建档 / 补齐缺失层** —— 扫描项目形态与量级,逐节点评估容量得出目标树形,再自底向上生成:

```
/agents-map init
```

成员篇/目录篇是真正的内容源,层篇提炼速览,根篇只留导航表和「代码改动 → 同步更新」映射表。生成后跑自检脚本,再随机抽篇逐断言回查代码(反猜测)。

**sync —— 按 diff 同步漂移** —— 以各篇最近一次提交为独立参考锚,把其后的代码变更路由到该更新的篇与节:

```
/agents-map sync
```

三层信号(结构性 → 映射表 → 断言比对)逐条定位;构建产物和 submodule 镜像目录在排除名单里,绝不代改;不确定的漂移会列为待审。

**audit —— 健康体检与结构演进** —— 不依赖 git diff 的全量检查,只读:

```
/agents-map audit
```

查链接、行数提示、根篇可达性和平铺目录信号(`--structure`),外加「高变更目录 × 文档新鲜度」矩阵揪出沉默漂移,输出下拆/上合/生长建议。建议不自动执行,经确认后由 init 或 sync 落地;涉及代码结构的是搬移提案,交给 restructure。

**restructure —— 按功能重组代码(需批准)** —— 某目录平铺源文件过多(约 >20)且无功能子结构时,单靠文档枚举违背渐进披露的初衷,该动的是目录本身:

```
/agents-map restructure
```

audit 或此命令产出**搬移提案**(文件→子目录,逐文件带证据与风险标注),逐目录批准后执行:每簇一批纯 `git mv` 提交,随批跑构建+测试,失败即回滚该批;文档树在同一阶段跟随新结构生长。Go 仓默认仅提案。sync 永不移动代码。

## 为什么动结构

细分精神要能无限下钻:每篇 AGENTS.md 40–130 行、导航表每项一行,**>15 个直接子项必然超限**——所以"每篇都短"必须由目录结构保证,而不是压缩文字。目录按功能拆分后,agent 定位代码就像读 skill 一样逐层下钻,精准命中,永远不必吞下一篇长枚举。

## 核心特性

- **渐进式披露** —— 根篇常驻、层篇/成员篇按需读,每篇有行数预算(根篇 120–180,硬上限 200),不拿全文喂上下文。
- **动态拆分** —— 树不设固定层数,子树规模、公开契约数、**目录直接平铺源文件数**等信号提示是否需要下拆;细分由目录结构承载,不靠长枚举文档;阈值来自 45-crate Rust workspace 实测标定。
- **结构演进落地(受控)** —— 目录该拆而没得拆时,restructure 阶段带证据提案、逐目录批准、每批一提交随批验证、失败即回滚;skill 从不在无人批准时动代码。
- **漂移路由** —— diff 经三层信号精确落到目标篇节,只改漂移处,保持各篇章节序与文风。
- **经验回流** —— 项目例外留在项目中，通用经验由维护者审查。
- **多形态适配** —— Rust workspace / JS monorepo / Python / Go 各有词汇映射与篇型骨架;文档语言跟随目标项目,不默认套中文。
- **硬规则** —— 只断言代码中实际存在的内容,不写推测性文档;submodule 镜像里的 AGENTS.md 永不编辑。

## 文档

| 文档 | 内容 |
|------|------|
| [SKILL.md](SKILL.md) | skill 主定义:Phase 0 推断、三个模式与 restructure 阶段的完整流程 |
| [references/templates.md](references/templates.md) | 四种 AGENTS.md 篇型骨架与形态→词汇映射 |
| [references/splitting.md](references/splitting.md) | 形态识别与动态拆分规则、行数预算、阈值标定 |
| [references/sync-routing.md](references/sync-routing.md) | sync 的三层信号路由算法与噪声排除黑名单 |
| [references/restructure.md](references/restructure.md) | 代码搬移协议:聚类取证、批准门、执行与回滚、语言机制、禁移清单 |
| [scripts/check_agents_docs.sh](scripts/check_agents_docs.sh) | 体系自检脚本:链接/行数/章节/索引闭合 |

## 仓库

<https://github.com/Asketisch/agents-map-skill>

## 验证与局限

运行 `python3 -m unittest discover -s tests` 检查基础场景。同步锚点和语义路由均为启发式，不能证明文档没有漂移；浅克隆或缺少历史时需要完整审查。尚未完成跨工具兼容性和任务效果的实测。
