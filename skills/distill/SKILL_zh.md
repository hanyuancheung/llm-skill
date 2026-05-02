---
name: distill
version: 0.2.0
status: active
triggers:
  keywords: [沉淀, 复盘, 记住这个, 以后都这么做, 总结经验, 写成 skill]
  intents:
    - 把一次执行中的痕迹提炼为可复用 skill
    - 修订已有 skill
    - 合并/弃用 skill
dependencies: [guide]
owner: agent
updated: 2026-05-01
hooks:
  pre:
    - name: have-candidates
      when: "distill-candidates 列表为空"
      action: skip
  post:
    - name: propose-guide
      when: "存在 SKILL.md 的新建/合并/弃用"
      action: propose-guide
    - name: validate-skills
      when: "有任何 skill 的 front-matter 被修改"
      action: require-validator
  on_error: []
---

# distill — 沉淀层元技能

## What
把 Raw 层的执行痕迹（对话、踩坑、最佳实践）**提炼**为 Wiki 层的 skill，或对既有 skill 做 CRUD，并触发 `guide` 更新路由表。

## When to use
- ✅ Execute 报告了非空 `distill-candidates`。
- ✅ 用户显式说"沉淀一下 / 记住 / 写成 skill"。
- ✅ 发现两个 skill 重叠或冲突需要合并。

## When NOT to use
- ❌ 一次性的偶发问题，判断"下次不会再用"。
- ❌ 仅为一个小修正就新建 skill（应 update 已有 skill）。

## How（SOP）

### Phase 1：分类决策
对每个 candidate，按下表归类：

| 情形 | 动作 |
|---|---|
| 路由表无命中 & 有复用价值 | **Create**：新建 skill |
| 路由表有命中但记录不准/缺步骤 | **Update**：修订该 skill |
| 两个 skill 职责重叠 | **Merge**：合并为一，旧的标 deprecated |
| 长期未被命中（2 个周期） | **Deprecate** |
| 仅一次性、无通用性 | **Discard**：丢弃 |

### Phase 2：写作/修订（遵守 Schema）

遵守 `AGENT.md` 第 3 节的 SKILL.md 契约。核心要求：

1. **命名**：`kebab-case`，动词-领域 或 领域-动作，如 `review-go-pr`、`debug-cuda-oom`。
2. **front-matter 完整**：`name/version/status/triggers/dependencies/owner/updated` 一个不少。
3. **6 个必选章节**：What / When / How / Examples / Pitfalls / Changelog。
4. **每一条 Pitfall 来自真实痕迹**，不要凭空编造。
5. **> 500 行**时，把引用资料拆到 `references/`。

### Phase 3：版本与状态

- 新建：起 `version: 0.1.0`，`status: experimental`。
- 修订：
  - 小修 → patch (`0.1.0 → 0.1.1`)
  - 增 How 步骤 → minor (`0.1.0 → 0.2.0`)
  - 改动触发/契约 → major (`0.1.0 → 1.0.0`)，并在 Changelog 写清楚迁移说明。
- 被第 2 次独立任务复用后，`experimental → active`。

### Phase 4：联动 Guide

**Distill 完成后必须**触发 `guide` skill，更新：
- `AGENT.md` 第 2.2 节 Skill 注册表。
- 若新 skill 有依赖，检查依赖方是否需要同步改动。

## 提炼的质量准则（Distill Quality Bar）

一条知识是否"值得成为 skill"，用下面 4 问自检：

1. **Reusable**：下一次类似任务真的会被用到吗？
2. **Teachable**：能不能用 ≤ 10 行说清楚 How？
3. **Falsifiable**：Pitfalls 能否描述成"如果 A 发生，就 B"？
4. **Orthogonal**：与已有 skill 是否正交、没有重叠？

4 个都 Yes 才落盘；否则回到 Discard 或 Merge。

## Examples

### 例：从 candidate 到 new skill

**输入（Execute 登记）**：
> "CUDA OOM 排查时，先看 `nvidia-smi` 确认是否进程残留，再看 batch size，再看是否有 tensor 未释放。临场成了 5 步法。"

**Distill 产出**：
```
skills/debug-cuda-oom/SKILL.md
---
name: debug-cuda-oom
version: 0.1.0
status: experimental
triggers:
  keywords: [CUDA, OOM, 显存, out of memory]
...
---
# debug-cuda-oom
## How
1. nvidia-smi 看残留进程
2. ...
```

**联动**：通知 guide 往 AGENT.md 注册表加行。

## Pitfalls

- **P1**：一次沉淀塞太多主题 → 一次只收敛一个主题，其它留到下次。
- **P2**：把具体项目的上下文当通用知识 → 提炼前先问"去掉项目名/路径后是否仍成立"。
- **P3**：新建时和已有 skill 重叠 → 先 `grep triggers` 再动手，重叠必须 Merge 而非 Create。
- **P4**：忘了升版本号和 Changelog → 每次写入 SKILL.md 前最后检查这两项。

## Changelog
- 2026-05-01 v0.2.0 — 声明 `pre.have-candidates`（无候选则跳过）、`post.propose-guide`、`post.validate-skills`。
- 2026-05-01 v0.1.0 — 初版，定义四相 SOP 与质量准则。
