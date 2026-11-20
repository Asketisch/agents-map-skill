---
name: agents-map
description: "维护任意项目的「AGENTS.md 体系」——一张让 Agent 按需下钻、而非靠 grep 全库找信息的项目地图(分层渐进式披露文档)。支持 init(按实际约束精简生成)/ sync(按 diff 路由同步漂移)/ audit(健康审计与结构演进建议)。当用户要求建立/同步/审计 AGENTS.md 文档体系、代码已变更但文档漂移、或其它会话报告 AGENTS.md 过时时使用。触发:/agents-map"
trigger: /agents-map
---

# /agents-map

维护**分层渐进式披露 AGENTS.md 体系**:根篇常驻上下文,层篇/目录篇与成员篇(crate/package)按需下钻,系统级说明在 docs/。目标是让 Agent 按任务读到**准确的契约**,而不是靠 grep 全库拼凑可能错误的信息。

用法:`/agents-map [init|sync|audit]` —— 参数可省略,由 Phase 0 自动推断。

## 渐进加载

本 skill 的重内容在 references/,**按需读取,不要一次全载**:

| 何时读 | 文件 |
|---|---|
| init、或 sync 中需新建篇时 | [references/templates.md](references/templates.md) |
| init、audit 判形态/给拆分建议时 | [references/splitting.md](references/splitting.md) |
| sync 时 | [references/sync-routing.md](references/sync-routing.md) |

自检统一用 [scripts/check_agents_docs.sh](scripts/check_agents_docs.sh)。

## Phase 0 —— 所有模式共享

1. **形态扫描**:按 [splitting.md](references/splitting.md) 识别项目形态与已有规则。
2. **模式推断**:没有 AGENTS.md 时用 init；已有文档时用 sync；audit 需显式指定。保留已有人工规则。

## 模式:init —— 首次生成 / 补齐缺失层

1. 先检查已有规则和代码证据，默认只建立简洁根篇；仅当子目录存在独立、可验证的操作约束时才建立子篇。拆分建议说明原因。
2. 参考 templates.md 自底向上组织内容，保留已有正确内容；仅记录真实存在的命令、约束和必要导航，语言跟随项目。
3. 运行 `bash scripts/check_agents_docs.sh <repo>`，抽查关键断言和命令；报告未验证内容。

## 模式:sync —— 按代码变更路由更新(先报告,后动手)

1. 按 [sync-routing.md](references/sync-routing.md) 为每篇文档独立取最近一次修改该文档的提交作为基线；无可靠基线时完整审查并报告覆盖限制。历史基线只是启发式，不能证明文档已同步。
2. 合并基线后的已提交变更、暂存、未暂存和未跟踪文件；排除构建产物及 submodule 内容，单独报告 submodule 指针变化。
3. 路由并逐条报告“确定需要更新 / 建议审查 / 无法判断”，列出每篇基线和覆盖范围。未命中只能说“未发现可检测的漂移”。
4. 按用户已授予的权限精确修改，保留正确内容。对每项记录已修改、确认无需修改或待处理及理由；核对报告事项并运行自检，不以原始 diff 信号消失作为收敛条件。

## 模式:audit —— 健康报告(只读)

不依赖 git diff,全量体检:

```bash
bash scripts/check_agents_docs.sh <repo>     # 链接/行数/章节/索引闭合
git log --name-only --since=3.months | ...   # 高变更目录 × 文档新鲜度矩阵
```

输出结构演进建议与证据；audit 全程只读，不创建或压实学习文件。项目特定例外保留在目标项目；可泛化经验向 skill 维护者提出建议，由维护者审查后纳入。代码规模和行数仅为启发式，不构成必须拆分的理由。

## 硬规则(全程适用)

- 不重写仍然准确的内容;不添加推测性文档;不含真实密钥。
- submodule / 镜像目录里的 AGENTS.md 永不编辑。
- 拿不准时报告待审；仅在内容确实需要更新时修改文档。
- 与 CLAUDE.md 并存且矛盾时:推荐 CLAUDE.md 退化为指向 AGENTS.md 的一行指针(或 `@AGENTS.md` 导入),此建议写入报告,不自动改 CLAUDE.md。
