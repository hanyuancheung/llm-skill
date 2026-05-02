---
name: guide
version: 0.2.0
status: active
triggers:
  keywords: [update AGENT, routing, organize skills, register skill, skill index]
  intents:
    - Maintain AGENT.md after the skill set changes
    - Periodic skill-health review (overlap, staleness, experimental promotion)
dependencies: []
owner: agent
updated: 2026-05-01
hooks:
  pre: []
  post:
    - name: validate-after-guide
      when: "AGENT.md was modified"
      action: require-validator
  on_error: []
---

# guide — Guidance Meta-Skill

## What
Maintain the single Schema file `AGENT.md` so that `execute` always routes to the right skill with the **minimum information** possible.

> Guide **does not create** domain knowledge; it organizes and routes.

## When to use
- ✅ `distill` has just done Create / Merge / Deprecate.
- ✅ User asks to "tidy up skills / find merge candidates".
- ✅ Periodic review (e.g. every N completed tasks).

## When NOT to use
- ❌ Domain questions themselves (those belong to `execute`).
- ❌ Internal edits to a single `SKILL.md` (those belong to `distill`).

## How (SOP)

### 1. Scan the skill set
```
ls skills/*/SKILL.md
```
Parse **only the front-matter** of each file (skip the body). Collect:
`name, status, triggers, dependencies, updated`.

### 2. Consistency checks (Schema guard)

| Check | Action |
|---|---|
| Missing front-matter field | Mark as `malformed`, notify distill to fix |
| `name` differs from directory name | Error, require fix |
| `triggers` fully overlap another skill | Suggest Merge |
| `status: experimental` for > 2 reuse cycles with no promotion | Suggest promote or deprecate |
| `status: deprecated` kept for > 1 cycle | Suggest deletion |
| `dependencies` point to a non-existent skill | Error |

### 3. Update `AGENT.md`
May edit **only**:

- §2.1 / §2.2 registry (add/remove/modify rows).
- §7 changelog (append a line).

All other sections (loop definition, contract, anti-patterns) are stable; changes require explicit user confirmation.

### 4. Produce a diff summary
After each guide run, report to user:
```
Added:       skills/xxx   (from distill, experimental)
Promoted:    skills/yyy   experimental → active
Deprecated:  skills/zzz   (90 days cold)
```

### 5. Reverse-notify
If a skill has weak `triggers` (never matches), **reverse-suggest** distill to rewrite them.

## Examples

### After distill creates `debug-cuda-oom`

1. Scan finds a new directory `skills/debug-cuda-oom`.
2. Front-matter is valid.
3. Append to `AGENT.md` §2.2:
   ```
   | debug-cuda-oom | skills/debug-cuda-oom/SKILL.md | CUDA, OOM, VRAM | experimental |
   ```
4. Append to `AGENT.md` §7:
   `- 2026-05-02 — registered debug-cuda-oom (experimental)`
5. Report to user.

## Pitfalls

- **P1**: Smuggling domain knowledge into `AGENT.md` → strictly forbidden; push back into the SKILL.md.
- **P2**: One run touches too many sections → only the registry and changelog; the rest is contract.
- **P3**: Trusting raw text match for triggers → plan A/B evaluation against real query history (future).
- **P4**: Guide becoming "another big index" → registry holds minimal routing info only, not descriptions.

## Changelog
- 2026-05-01 v0.2.0 — declared `post.validate-after-guide` (AGENT.md edits must pass the validator).
- 2026-05-01 v0.1.0 — Initial release.
