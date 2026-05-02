---
name: execute
version: 0.2.0
status: active
triggers:
  keywords: [execute, run task, implement, fix bug, debug, do it]
  intents:
    - User proposes a concrete, actionable task
    - An existing skill's triggers match the intent
dependencies: [guide]
owner: agent
updated: 2026-05-01
hooks:
  pre: []
  post: []
  on_error: []
---

# execute — Execution Meta-Skill

## What
Select the right domain skill from the `AGENT.md` routing table, complete the task, and **passively collect distillable signals** as raw material for the next `distill` pass.

## When to use
- ✅ User gives a concrete task (write code, fix a bug, research, answer a question).
- ✅ An existing skill's `triggers` match the intent.

## When NOT to use
- ❌ The discussion is about the skill system itself (hand off to `distill` or `guide`).
- ❌ Pure small talk with no executable action.

## How (SOP)

1. **Read the Schema, not the whole library.**
   Open section 2 of `AGENT.md`. **Do NOT** `ls skills/` or batch-read all `SKILL.md` files.

2. **Pick ≤ 3 candidates.**
   Match `keywords`, `file_globs`, `intents` against the user input. Prefer `status: active` over `experimental` on ties.

3. **Lazy load.**
   `read_file` only the chosen `SKILL.md`. If it links to `references/*.md`, load on demand.

4. **Run `pre` hooks** (see `AGENT.md` §10).
   For each hook in declared order, evaluate `when`; apply `action`:
   - `skip` → drop this skill silently, try next candidate.
   - `warn` → surface to user, continue.
   - `proceed` → continue.
   - `run-script:<path>` → execute; non-zero exit = violation, treat as hook failure.

5. **Execute the task.**
   Follow the chosen skill's `How` section strictly. If a skill conflicts with user intent, **user wins**, and log the conflict into distill-candidates.

6. **Collect distillable signals (key).**
   Maintain a `distill-candidates` list during execution. Log entries for:
   - **New pitfall**: an error/ambiguity the skill did not warn about.
   - **Better practice**: a superior approach beyond what is recorded.
   - **Gap**: no skill matched; you solved it with ad-hoc reasoning that felt reusable.
   - **Conflict**: skill-vs-skill or skill-vs-reality.
   - **Correction**: a step in the skill turned out to be inaccurate.

7. **Run `post` hooks before finishing** (see `AGENT.md` §10.4–§10.5).
   - **Always** evaluate the default `should-distill`: if `distill-candidates` is non-empty, propose invoking `distill`.
   - Then run declared `post` hooks in order. Enforce `require-validator` strictly: a failing `scripts/validate.py` blocks the task report.

8. **Closing report.**
   - Deliver results.
   - Summarise every hook that fired (name + outcome).
   - If hooks proposed `distill` / `guide` and the user agrees, hand off accordingly.

9. **On error** — if any step above raises, run `on_error` hooks before surfacing the failure.

## Examples

### 1. Hit an existing skill
```
User: Write a Go HTTP client with context support
→ Routing matches skills/go-http-client/
→ Read its SKILL.md "How", deliver step-by-step
→ No new signals, end without suggesting distill
```

### 2. Gap detected
```
User: Help me debug a CUDA OOM
→ No match in routing table
→ Solved via ad-hoc reasoning
→ distill-candidates += { "CUDA OOM triage 5-step" }
→ Suggest distillation at the end
```

## Pitfalls

- **P1**: Greedy loading burns context → strict ≤ 3 candidates.
- **P2**: Forgetting to log signals mid-flight → treat "logging" as first-class, equal to code edits.
- **P3**: Editing a skill in place → Execute is **read-only** on skills; writing belongs to `distill`.
- **P4**: Skipping the default `should-distill` post-hook because "nothing big happened" → evaluate honestly every time; silent skipping is forbidden by §10.4.
- **P5**: Treating `warn` as `skip` → `warn` must still proceed; only `skip` aborts.

## Changelog
- 2026-05-01 v0.2.0 — added hook phases (pre/post/on_error) to the SOP; enforce default `should-distill`.
- 2026-05-01 v0.1.0 — Initial release.
