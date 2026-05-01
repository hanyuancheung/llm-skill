---
name: guide
version: 0.1.0
status: active
triggers:
  keywords: [更新 AGENT, 路由, 整理 skill, 注册 skill, skill 目录]
  intents:
    - 在 skill 集合发生变动后维护 AGENT.md
    - 周期性审视 skill 健康度（重叠/失效/experimental 升级）
dependencies: []
owner: agent
updated: 2026-05-01
---

# guide — 指引层元技能

## What
维护唯一的 Schema 层文件 `AGENT.md`，让 Execute 始终能通过**最小信息**命中最合适的 skill。

> Guide **不创造**领域知识，只组织和路由。

## When to use
- ✅ `distill` 刚完成 Create / Merge / Deprecate。
- ✅ 用户要求"整理一下 skill / 看看哪些能合并"。
- ✅ 周期性回顾（比如每完成 N 次任务触发一次）。

## When NOT to use
- ❌ 领域问题本身（那属于 Execute）。
- ❌ 单个 SKILL.md 内部的修订（那属于 Distill）。

## How（SOP）

### 1. 扫描 skill 集合
```
ls skills/*/SKILL.md
```
读取每个文件的 **front-matter**（仅 front-matter，不读正文），收集：
`name, status, triggers, dependencies, updated`。

### 2. 一致性检查（Schema 守护）
对每个 skill 检查：

| 检查项 | 动作 |
|---|---|
| front-matter 缺字段 | 标记为 `malformed`，通知 distill 补齐 |
| name 与目录名不一致 | 报错，要求修正 |
| triggers 与其它 skill 完全重叠 | 建议 Merge |
| `status: experimental` 超 2 个复用周期未晋升 | 建议晋升或 deprecate |
| `status: deprecated` 已保留 > 1 周期 | 建议删除 |
| dependencies 指向不存在的 skill | 报错 |

### 3. 更新 AGENT.md
只能改以下区域，**禁止改其它**：

- 第 2.1 / 2.2 节注册表（增删改行）。
- 第 7 节变更日志（append 一行）。

其它章节（闭环定义、契约、反模式）属于稳定契约，变更需用户显式确认。

### 4. 产出 Diff 说明
每次 guide 执行后，向用户呈现：
```
新增：skills/xxx  （来自 distill，experimental）
晋升：skills/yyy  experimental → active
弃用：skills/zzz  （90 天未命中）
```

### 5. 反向通知
如果发现某个 skill 的 `triggers` 很弱（总是匹配不上），**反向建议** distill 重写其 triggers。

## Examples

### 例：distill 刚新建 `debug-cuda-oom`

1. 扫描发现新目录 `skills/debug-cuda-oom`。
2. front-matter 合法。
3. 在 AGENT.md 2.2 节追加：
   ```
   | debug-cuda-oom | skills/debug-cuda-oom/SKILL.md | CUDA, OOM, 显存 | experimental |
   ```
4. 在 AGENT.md 第 7 节追加：
   `- 2026-05-02 — 注册 debug-cuda-oom (experimental)`
5. 回报用户。

## Pitfalls

- **P1**：在 AGENT.md 里夹带领域知识 → 严禁；领域知识一律回退到 SKILL.md。
- **P2**：一次改动覆盖过多区域 → 只改注册表和 changelog，其它属于契约层。
- **P3**：盲信 triggers 的文本匹配 → 定期用真实历史查询做 A/B 评估（未来接入）。
- **P4**：把 guide 变成"另一个大目录" → 注册表只记最小路由信息，不记描述细节。

## Changelog
- 2026-05-01 v0.1.0 — 初版。
