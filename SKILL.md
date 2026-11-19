---
name: agents-map
description: "维护任意项目的「AGENTS.md 体系」——一张让 Agent 按需下钻、而非靠 grep 全库找信息的项目地图(分层渐进式披露文档)。支持 init(按代码量级自动拆分生成)/ sync(按 diff 路由同步漂移)/ audit(健康审计与结构演进建议)。当用户要求建立/同步/审计 AGENTS.md 文档体系、代码已变更但文档漂移、或其它会话报告 AGENTS.md 过时时使用。触发:/agents-map"
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

1. **读回学习**:若本 skill 目录下存在 `LEARNINGS.md`,读取其中 `状态:open` 且形态标签匹配当前项目(或 `generic`)的条目,在本次执行中应用。
2. **形态扫描**:按 [splitting.md](references/splitting.md) 的"形态识别"两步(manifest 扫描 + 规模统计)判定项目形态与量级。
3. **模式推断**:
   - 无任何 AGENTS.md → `init`(全新建立);
   - 只有单层平文件,但规模已越过拆分阈值 → `init`(增量扩展,不推倒重写);
   - 已有嵌套 AGENTS.md 体系(存在非根 AGENTS.md) → `sync`;
   - `audit` 任何时候可跑,只读。

## 模式:init —— 首次生成 / 补齐缺失层

1. 跑 splitting.md 的 **DFS 生长算法**(逐节点评估容量,超载节点按模块下拆,层数不设上限),得到目标树形状。小项目宁可欠拆:形状先展示给用户确认,再生成。
2. 按 templates.md **自底向上生成**:成员篇/目录篇(真正的内容源)→ 层篇(速览表经实际 `ls` + 读入口文件公开面提炼)→ 根篇(导航表 + 「代码改动 → 同步更新」映射表)。
3. 内容硬规则:
   - 只断言代码中**实际存在**的内容,不写推测性文档;
   - 每篇的「何时读我」必须是可操作条件(什么改动/什么排查场景),不得同义反复;
   - 断言核心文件/符号前先 `ls`/grep 验证其存在;
   - 文档语言跟随目标项目既有文档语言(探测现有 docs 或 commit message),不默认套中文。
4. 收尾:`bash scripts/check_agents_docs.sh <repo>` + 随机抽 2 篇逐断言回查代码(反猜测自查);输出生成的树形状与各篇行数。

## 模式:sync —— 按代码变更路由更新(先报告,后动手)

1. **取锚点**:`git log -1 --format=%H -- '*AGENTS.md'`;从未提交过 AGENTS.md → 退 `HEAD~20`;无 git → 改用 audit 的实体集合全量比对。
2. **收集变更**:`git diff --name-only $ANCHOR..HEAD` + `git status --porcelain`。排除:`target/ dist/ build/ node_modules/ vendor/ *.lock *.snap` 及 `.gitmodules` 列出的 submodule 镜像目录(**绝不路由更新镜像目录**,只报"submodule 指针已升级,检查本地适配篇")。
3. **路由**:按 [sync-routing.md](references/sync-routing.md) 的三层信号(结构性 → 映射表 → 断言比对)把每条变更路径映射到 {目标篇, 目标节}。
4. **报告**:按篇、按节输出漂移清单,例:
   ```
   AGENTS.md 体系同步报告
   - crates/foo/AGENTS.md §核心文件导航:+1 文件需登记 (src/new.rs)
   - crates/bar/AGENTS.md §本地契约:~ 断言涉及 Xfn,代码已改,需人审
   - 其余篇:OK
   ```
   无差异 → 输出"体系已是最新"并结束(仍走第 6 步学习回路)。
5. **应用**:用户确认后逐条 Edit 精确更新,**不全文重写**,保持各篇章节序与文风。
6. **收敛与自检**:重跑一次路由,输出应为空;跑 check_agents_docs.sh。
7. **学习回路**:本次人工发现的"代码改了但文档没跟上"新模式 → 追加进本 skill 目录 `LEARNINGS.md` 的「漂移模式」节(格式见下)。

## 模式:audit —— 健康报告(只读)

不依赖 git diff,全量体检:

```bash
bash scripts/check_agents_docs.sh <repo>     # 链接/行数/章节/索引闭合
git log --name-only --since=3.months | ...   # 高变更目录 × 文档新鲜度矩阵
```

外加结构演进建议(阈值见 splitting.md):哪篇超上限该下拆、哪篇太薄该上合、哪个目录节点子树已超 ~30k 加权代码量 却没有子篇(该在第 N 层继续生长)、哪个超载目录内部无模块结构(输出"建议模块划分"供人工重构,文档不代拆代码)。输出健康评分 + 建议列表;建议**不自动执行**,经确认后由 init(增量扩展)或 sync 落地。audit 同时负责 LEARNINGS 的压实与晋升整理(见下)。

## 自迭代机制(按需调整,人审门控)

- **位置**:本 skill 目录 `LEARNINGS.md`(不存在则首次运行时创建)。用文件而非 Claude memory——避免项目事实被跨项目召回污染。
- **记什么**:只记**可泛化规则**,四节固定——`阈值校准`(某形态下阈值不合身的实测)、`模板调整`(某章节对某形态空洞)、`漂移模式`(新检查规则,将来成为 sync-routing 信号行或映射表行)、`项目例外`(显式豁免的形态)。
- **条目格式**(每条 ≤3 行):`- [日期] [形态:x] [状态:open|promoted|wontfix] [seen:N] 规则描述`
- **读回**:Phase 0 第 1 步;形态标签为 `generic` 的条目恒适用。
- **防膨胀三闸**:
  1. 硬上限 120 行,超了触发压实:合并重复;`wontfix` 且半年以上的移入 `LEARNINGS.archive.md`(不参与读回);
  2. `seen≥2` 时建议**晋升**:写入对应 references 文件后标 `promoted` 并从 LEARNINGS 删除;
  3. 晋升要动 skill 自身文件——**只出建议,等用户确认**,绝不静默改写。压实与晋升整理由 audit 模式执行。

## 拆分与行数预算速查(细则见 splitting.md)

**树不设固定层数**:每个目录节点独立评估"一篇能否讲清子树契约"——子树加权代码量 >30k 或单篇 >130 行且有节 >40 行 → 按模块下拆子篇,父篇退化为路由/速览篇;收缩则反向上合。递归可达任意深度(例:十万行的目录 A 必须拆成 A 路由篇 + 若干模块篇)。skill 不移动代码,只为既成(或已提议)的模块边界建篇。

| 角色 | 预算 |
|---|---|
| 常驻根篇 | 120–180(硬上限 200);导航表与映射表恒留根篇 |
| 路由篇(任意深度的非叶节点) | 40–130 |
| 叶子篇(成员/目录) | 40–90 |
| 多仓路由篇 | ≤120 |

## 硬规则(全程适用)

- 不重写仍然准确的内容;不添加推测性文档;不含真实密钥。
- submodule / 镜像目录里的 AGENTS.md 永不编辑。
- 拿不准某变更该同步哪篇时,至少更新其所在层篇与根导航表,确保索引不失真。
- 与 CLAUDE.md 并存且矛盾时:推荐 CLAUDE.md 退化为指向 AGENTS.md 的一行指针(或 `@AGENTS.md` 导入),此建议写入报告,不自动改 CLAUDE.md。
