---
name: execute
version: 0.2.0
status: active
triggers:
  keywords: [执行, 开始任务, 做一下, 实现, 修 bug, debug, 跑一下]
  intents:
    - 用户提出一个具体可执行的任务
    - 需要按既有 skill 规范行事
dependencies: [guide]
owner: agent
updated: 2026-05-01
hooks:
  pre: []
  post: []
  on_error: []
---

# execute — 执行层元技能

## What
按 `AGENT.md` 路由表选择合适的领域 skill 完成任务，**并在过程中被动收集可沉淀信号**，为下一步 `distill` 提供原料。

## When to use
- ✅ 用户给出一个具体任务（写代码、改 bug、调研、回答问题）。
- ✅ 一个已有 skill 的 `triggers` 能匹配当前意图。

## When NOT to use
- ❌ 用户正在讨论 skill 系统本身（应走 `distill` 或 `guide`）。
- ❌ 任务纯闲聊/无可执行动作。

## How（SOP）

1. **读 Schema，不读全量**
   打开 `AGENT.md` 第 2 节路由表；**不要** `ls skills/` 或批量读 SKILL.md。

2. **匹配候选（≤ 3）**
   依次用 `keywords`、`file_globs`、`intents` 与用户输入做模糊匹配，选 Top-3。冲突时以 `status=active` 优先，`experimental` 次之。

3. **懒加载**
   只 `read_file` 被选中的 `SKILL.md`；若其中引用了 `references/xxx.md` 再按需读。

4. **运行 `pre` hooks**（见 `AGENT.md` §10）。
   按声明顺序对每个 hook 评估 `when`，按 `action` 执行：
   - `skip` → 静默放弃此 skill，尝试下一个候选。
   - `warn` → 向用户提示，继续执行。
   - `proceed` → 继续。
   - `run-script:<path>` → 执行脚本，非零退出视为 hook 违规。

5. **执行任务**
   严格遵守所选 skill 的 `How` 章节。若 skill 内容与用户要求冲突，**以用户要求为准**，并把冲突登记到 distill-candidates。

6. **收集可沉淀信号**（关键）
   在整个执行过程中，心里维护一个 `distill-candidates` 清单。触发登记的典型事件：
   - **新坑**：遇到 skill 未预警的报错/歧义。
   - **新最佳实践**：找到比 skill 记载更优的做法。
   - **缺口**：没有任何 skill 命中，靠临场推理完成的成熟套路。
   - **冲突**：skill 之间/skill 与现实冲突。
   - **修正**：skill 某一步骤描述不准确。

7. **结束前运行 `post` hooks**（见 `AGENT.md` §10.4–§10.5）
   - **始终**先评估默认的 `should-distill`：若 `distill-candidates` 非空，建议走 `distill`。
   - 再按声明顺序运行已声明的 `post` hooks。`require-validator` 必须严格执行：`scripts/validate.py` 失败就阻断任务回报。

8. **结束回报**
   - 交付结果。
   - 总结本次触发的所有 hook（name + 结果）。
   - 若 hooks 建议走 `distill` / `guide` 且用户同意，相应切入。

9. **出错时** — 若上述任何步骤抛错，先运行 `on_error` hooks，再把错误上报。

## Examples

### 例 1：命中已有 skill
```
用户：帮我用 Go 写一个带 context 的 HTTP client
→ 路由表匹配到 skills/go-http-client/
→ 读该 SKILL.md 的 How，按步骤交付
→ 无新信号，任务结束不建议 distill
```

### 例 2：发现缺口
```
用户：帮我调一个 CUDA OOM
→ 路由表无匹配
→ 临场推理完成
→ distill-candidates += { "CUDA OOM 排查 5 步法" }
→ 结束时建议用户沉淀为新 skill
```

## Pitfalls

- **P1**：贪心加载所有 skill，浪费上下文 → 严格 ≤ 3 个候选。
- **P2**：执行中忘记登记信号，导致经验流失 → 把"登记"视为第一类动作，与代码编辑同等优先级。
- **P3**：擅自修改 skill → Execute **只读** skill，禁止写；写是 `distill` 的职责。
- **P4**：认为"这次没啥大事"就跳过默认的 `should-distill` → 每次都必须诚实评估，静默跳过违反 §10.4。
- **P5**：把 `warn` 当 `skip` 处理 → `warn` 必须继续执行，只有 `skip` 才中止。

## Changelog
- 2026-05-01 v0.2.0 — SOP 中加入 pre/post/on_error hook 阶段；强制默认 `should-distill`。
- 2026-05-01 v0.1.0 — 初版。
