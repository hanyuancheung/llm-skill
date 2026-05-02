---
name: distill
version: 0.2.0
status: active
triggers:
  keywords: [distill, retrospective, remember this, always do this, summarize, write a skill]
  intents:
    - Turn traces from an execution into a reusable skill
    - Revise an existing skill
    - Merge or deprecate skills
dependencies: [guide]
owner: agent
updated: 2026-05-01
hooks:
  pre:
    - name: have-candidates
      when: "distill-candidates list is empty"
      action: skip
  post:
    - name: propose-guide
      when: "any SKILL.md was created, merged, or deprecated"
      action: propose-guide
    - name: validate-skills
      when: "any skill front-matter was modified"
      action: require-validator
  on_error: []
---

# distill — Distillation Meta-Skill

## What
Turn Raw-layer traces (conversation, pitfalls, best practices) into Wiki-layer skills, or CRUD existing ones, then notify `guide` to update the routing table.

## When to use
- ✅ `execute` reports a non-empty `distill-candidates`.
- ✅ User says "distill / remember / write it as a skill".
- ✅ Two skills overlap or conflict and need merging.

## When NOT to use
- ❌ One-off incidents judged "won't recur".
- ❌ A tiny correction does not warrant a new skill (update the existing one).

## How (SOP)

### Phase 1: classify
For each candidate:

| Situation | Action |
|---|---|
| No routing hit + reusable | **Create** a new skill |
| Hit exists but record is inaccurate/incomplete | **Update** |
| Two skills overlap in responsibility | **Merge**, deprecate the loser |
| Not matched for 2 cycles | **Deprecate** |
| One-off, non-generalizable | **Discard** |

### Phase 2: write/revise (follow Schema)

Adhere to `AGENT.md` §3 `SKILL.md` contract. Core requirements:

1. **Naming**: `kebab-case`, verb-domain or domain-action, e.g. `review-go-pr`, `debug-cuda-oom`.
2. **Complete front-matter**: `name/version/status/triggers/dependencies/owner/updated` — all required.
3. **Six required sections**: What / When / How / Examples / Pitfalls / Changelog.
4. **Every Pitfall must come from a real trace**, never fabricated.
5. **If > 500 lines**, spill references into `references/`.

### Phase 3: version & status

- New: `version: 0.1.0`, `status: experimental`.
- Revision:
  - Minor fix → patch (`0.1.0 → 0.1.1`)
  - New How step → minor (`0.1.0 → 0.2.0`)
  - Contract/trigger change → major (`0.1.0 → 1.0.0`), document migration in Changelog.
- After the 2nd independent reuse, `experimental → active`.

### Phase 4: notify Guide

**After distillation**, trigger `guide` to:
- Update `AGENT.md` §2.2 registry.
- Check dependency fan-in for ripple changes.

## Distill Quality Bar

Before a candidate lands as a skill, self-check:

1. **Reusable**: will a similar task genuinely reach for this again?
2. **Teachable**: can `How` be stated in ≤ 10 lines?
3. **Falsifiable**: can every Pitfall be stated as "if A then B"?
4. **Orthogonal**: non-overlapping with existing skills?

All four Yes → land. Otherwise Discard or Merge.

## Examples

### From candidate to new skill

**Input (logged by Execute)**:
> "Triaging CUDA OOM: check `nvidia-smi` for zombie processes, then batch size, then unreleased tensors. Became an ad-hoc 5-step."

**Distill output**:
```
skills/debug-cuda-oom/SKILL.md
---
name: debug-cuda-oom
version: 0.1.0
status: experimental
triggers:
  keywords: [CUDA, OOM, VRAM, out of memory]
...
---
# debug-cuda-oom
## How
1. nvidia-smi for zombie processes
2. ...
```

**Linkage**: notify guide to append a row in the registry.

## Pitfalls

- **P1**: Cramming multiple topics into one distill → one topic per pass; keep the rest for next time.
- **P2**: Treating project-specific context as universal → before distilling, ask "does it still hold without the project name/path?"
- **P3**: Creating when something overlapping exists → `grep triggers` first; overlap forces Merge.
- **P4**: Forgetting to bump version + Changelog → final check before saving.

## Changelog
- 2026-05-01 v0.2.0 — declared `pre.have-candidates` (skip if nothing to distill), `post.propose-guide`, `post.validate-skills`.
- 2026-05-01 v0.1.0 — Initial release: four-phase SOP and quality bar.
