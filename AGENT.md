# AGENT.md — Schema Layer (single source of truth)

> Karpathy's LLM-Wiki analogy applied to skills:
> **Raw layer** = interaction traces (chat, tool output, logs, pitfalls)
> **Wiki layer** = `skills/<name>/SKILL.md` (reusable experience packs)
> **Schema layer** = this file (metadata, routing rules, lifecycle contract)
>
> This file describes **only "when to use what, how they collaborate"** — never domain knowledge.
> All domain knowledge MUST sink into the corresponding skill.
>
> 中文说明见 [`AGENT.md` §9](#9-chinese-notes-中文说明)。

---

## 1. Core loop: Execute → Distill → Guide

```
   ┌────────────────────────────────────────────────┐
   │                                                │
   ▼                                                │
[Execute] ──traces──► [Distill] ──skill CRUD──► [Guide]
  run                 refine                    route
  reads Guide                                    edits this file
   ▲                                                │
   │                                                │
   └──────── next task routed by new rules ◄────────┘
```

| Meta-skill | Trigger | Action | Output |
|---|---|---|---|
| `execute` | Any user-facing task starts | Read Guide → pick skills → run → log distillable signals | Deliverable + `distill-candidates` |
| `distill` | End of task or explicit "distill this" | Turn traces into skill CRUD | `skills/<name>/SKILL.md` changes |
| `guide` | Skill set changed / periodic review | Update routing table + contract | This file changes |

**Hard constraint**: the three meta-skills communicate **only through this file (Schema)**. Bypassing the routing table to grep skills directly is forbidden.

---

## 2. Skill registry (routing table)

> This is the **only authoritative source** that `execute` consults.
> `guide` is responsible for keeping it in sync.

### 2.1 Meta-skills (operate on the skill system itself)

| Skill | Path | Triggers (keywords / intent) | Status |
|---|---|---|---|
| execute | `skills/execute/SKILL.md` | implicit on any actionable task | active |
| distill | `skills/distill/SKILL.md` | "distill / retrospective / remember / write as skill" | active |
| guide   | `skills/guide/SKILL.md`   | "update AGENT / routing / organize / register" | active |

### 2.2 Domain skills (user-authored, append here)

| Skill | Path | Triggers (keywords / intent) | Status |
|---|---|---|---|
| _(placeholder)_ | `skills/_template/SKILL.md` | template for new skills | template |

> When adding a domain skill, append one row here. When removing, mark `deprecated` first, wait one cycle, then delete.

---

## 3. SKILL file contract

Each skill is a directory `skills/<kebab-case-name>/` containing at least `SKILL.md`.
If a translation is provided, put it alongside as `SKILL_zh.md` (or `SKILL_<locale>.md`) with identical front-matter values.

### 3.1 Required front-matter

```yaml
---
name: <kebab-case-name>          # matches directory name
version: <semver>                # start at 0.1.0; breaking bumps major
status: active | experimental | deprecated
triggers:
  keywords: [kw1, kw2]
  file_globs: ["**/*.go"]        # optional: trigger by file type
  intents: [one-line intent description, ...]
dependencies: []                 # other skill names this depends on
owner: <human or agent>
updated: <YYYY-MM-DD>
hooks:                           # optional; see §10 Hook protocol
  pre: []
  post: []
  on_error: []
---
```

### 3.2 Required sections in SKILL.md

1. **What** — one-line problem statement (≤ 2 lines).
2. **When to use / When NOT to use** — ≥ 2 positive + ≥ 2 negative examples.
3. **How** — step-by-step SOP (numbered, executable).
4. **Examples** — at least one minimum viable example.
5. **Pitfalls** — real pitfalls + mitigation (fed by Execute).
6. **Changelog** — `YYYY-MM-DD vX.Y.Z — summary`.

### 3.3 Suggested layout

```
skills/<name>/
├── SKILL.md          # required (English default)
├── SKILL_zh.md       # optional Chinese mirror
├── references/       # long-form references
├── scripts/          # helper scripts
└── examples/         # extra examples
```

---

## 4. Lifecycle state machine

```
  (new trace)──distill──► experimental ──validated──► active
                              │                          │
                              └──2 misses──► deprecated ◄─┘
                                                          │
                                                          └──1 cycle──► removed
```

- **experimental**: new, not yet reused by ≥ 2 independent tasks. Execute may use it with an "experimental" notice.
- **active**: stable, safe to depend on.
- **deprecated**: kept on disk, but `triggers` should be emptied/narrowed so routing misses it on purpose.

---

## 5. Execute loading protocol (agent instruction)

At the start of every task the agent MUST:

1. **Read only §2 of this file** (routing table). Do NOT batch-read all `SKILL.md` files.
2. Match `triggers` against user input; select up to **3** candidates.
3. Lazy-load only the chosen `SKILL.md`; expand `references/` on demand.
4. **Run `pre` hooks** (see §10). If any hook resolves to `skip`, drop this skill before executing its `How`. If `warn`, proceed but surface the warning.
5. Execute the skill's `How`. While executing, maintain a `distill-candidates` list (mental or written) for:
   - new pitfalls
   - better practices
   - gaps (no skill hit)
   - conflicts
   - corrections
6. **Before declaring the task done, run `post` hooks** (see §10). The default post-hook (`should-distill`) is always active: if `distill-candidates` is non-empty, propose invoking `distill`. Skill-declared post-hooks run in declared order.
7. If an error is raised anywhere above, run `on_error` hooks (see §10) before surfacing the failure.

---

## 6. Anti-patterns

- ❌ Writing domain knowledge into this file (sinks to skills).
- ❌ Bypassing the routing table and grepping `skills/`.
- ❌ Skills importing each other's internals (use explicit `dependencies`).
- ❌ A single SKILL.md > 500 lines without splitting into `references/`.
- ❌ The same knowledge duplicated across skills (merge or extract shared skill).

---

## 7. Changelog (this file)

- 2026-05-01 v0.1.0 — bootstrapped the Execute-Distill-Guide loop and skill contract.
- 2026-05-01 v0.2.0 — bilingual SKILL files; added AGENTS/CLAUDE/HERMES entrypoints.
- 2026-05-01 v0.3.0 — introduced Hook protocol (§10) with `pre`/`post`/`on_error` phases and default `should-distill` post-hook.

---

## 8. Runtime entrypoints

Agent runtimes mount this system via a thin shell file that points here:

| Runtime | Entrypoint file | Purpose |
|---|---|---|
| Codex | `AGENTS.md` | Instruction boot for Codex CLI / agents |
| Claude Code | `CLAUDE.md` | Instruction boot for Claude Code |
| HERMES | `HERMES.md` | Instruction boot for HERMES |
| Generic / custom | this `AGENT.md` | Default schema & routing |

All entrypoints MUST defer concrete routing/contract rules to this file, and MUST NOT carry domain knowledge.

---

## 9. Chinese notes（中文说明）

- 本文件是 **Schema 层**，只谈"何时用什么、怎么协作"；领域知识一律下沉到 `skills/<name>/SKILL.md`。
- `SKILL.md` 为英文默认版本；中文镜像保存为 `SKILL_zh.md`，front-matter 与英文版完全一致。
- `AGENTS.md` / `CLAUDE.md` / `HERMES.md` 是不同 Agent 运行时的入口薄壳，最终都回指本文件。
- 新增领域 skill 只需：(a) 从 `skills/_template/` 复制目录；(b) 填写 `SKILL.md`（及 `SKILL_zh.md`）；(c) 在 §2.2 追加一行。
- Hook 协议（§10）允许 skill 声明执行前/后/出错时的判定与动作；其中默认的 `should-distill` post-hook 对所有 skill 自动生效，**保证每次任务结束前都会判断是否需要走 distill**。

---

## 10. Hook protocol

Hooks let a skill declare checks that **must** fire at specific lifecycle moments.
They are the mechanism that answers "before I finish, do I still need to do something?"

### 10.1 Phases

| Phase | When it fires | Typical purpose |
|---|---|---|
| `pre` | After the skill is routed-in, **before** its `How` runs | Guard conditions; decide `skip` / `warn` / `proceed` |
| `post` | **Before** Execute declares the task done | Distill judgement, validator runs, side-effect checks |
| `on_error` | If any step raises / user aborts | Cleanup, rollback, log extraction |

### 10.2 Declaration shape (inside front-matter)

```yaml
hooks:
  pre:
    - name: needs-go-toolchain
      when: "target language is Go"
      action: warn                       # skip | warn | proceed
  post:
    - name: should-distill               # conventional name
      when: "distill-candidates is non-empty"
      action: propose-distill
    - name: run-validator
      when: "any skill file was modified"
      action: require-validator
    - name: custom-check
      when: "always"
      action: run-script:hooks/post.sh
  on_error:
    - name: cleanup
      action: run-script:hooks/on_error.sh
```

Every hook entry MUST have `name` and `action`. `when` is a free-form human-readable predicate the agent evaluates; if omitted it defaults to `"always"`.

### 10.3 Built-in actions (agent-native; no script needed)

| Action | Semantics |
|---|---|
| `proceed` | Continue (no-op; default). |
| `skip` | Abort this skill's `How` without error. Only valid in `pre`. |
| `warn` | Continue but surface a warning to the user. |
| `propose-distill` | At the end, propose invoking `distill` skill. |
| `propose-guide` | At the end, propose invoking `guide` skill. |
| `require-validator` | Before finishing, run `scripts/validate.py`; non-zero exit blocks the report. |
| `run-script:<relpath>` | Execute `<relpath>` (relative to the skill dir); non-zero exit = hook violated. |

### 10.4 Default hooks (apply to every skill, no declaration required)

```yaml
post:
  - name: should-distill
    when: "distill-candidates is non-empty"
    action: propose-distill
```

Skills MAY re-declare `should-distill` to customise its `when`, but MUST NOT weaken it to `proceed` or remove it entirely.

### 10.5 Execution order

1. All declared `pre` hooks run in declared order.
2. Any `pre` hook resolving to `skip` → abort skill immediately (subsequent `pre`/`How`/`post` do NOT run; `on_error` does NOT fire because this is not an error).
3. `How` runs.
4. **Default `should-distill` runs first**, then each declared `post` hook in order.
5. If any step from 1–4 raises, `on_error` hooks run, then the error propagates.

### 10.6 Evaluation contract for the agent

For each hook, the agent MUST:
- Print the hook `name` and chosen branch (`triggered` / `not-triggered`) to the task log.
- For `run-script:*`, verify the script exists and is executable; otherwise fail with a clear message.
- For `require-validator`, run `python3 scripts/validate.py` from the repo root.
- Never silently swallow a triggered hook.

### 10.7 Relation to meta-skills

- **Execute** is the only phase that **runs** hooks.
- **Distill** is the only phase that may **write** `hooks:` into a skill's front-matter.
- **Guide** checks hook-set consistency but does not modify them.

### 10.8 Pitfalls

- ❌ Using `pre.skip` for things that should just be a narrower `triggers` — prefer fixing triggers.
- ❌ Side-effectful scripts with no idempotency — `post` can run multiple times during debugging.
- ❌ Silencing `should-distill` to avoid "nagging" — that defeats the point of the loop.
