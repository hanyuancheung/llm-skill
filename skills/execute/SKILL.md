---
name: execute
version: 0.1.0
status: active
triggers:
  keywords: [execute, run task, implement, fix bug, debug, do it]
  intents:
    - User proposes a concrete, actionable task
    - An existing skill's triggers match the intent
dependencies: [guide]
owner: agent
updated: 2026-05-01
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

4. **Execute the task.**
   Follow the chosen skill's `How` section strictly. If a skill conflicts with user intent, **user wins**, and log the conflict into distill-candidates.

5. **Collect distillable signals (key).**
   Maintain a `distill-candidates` list during execution. Log entries for:
   - **New pitfall**: an error/ambiguity the skill did not warn about.
   - **Better practice**: a superior approach beyond what is recorded.
   - **Gap**: no skill matched; you solved it with ad-hoc reasoning that felt reusable.
   - **Conflict**: skill-vs-skill or skill-vs-reality.
   - **Correction**: a step in the skill turned out to be inaccurate.

6. **Closing report.**
   - Deliver results.
   - If `distill-candidates` is non-empty and worth "would reuse next time", **proactively** ask: "I found X worth distilling — enter distill?"
   - Drop if rejected; otherwise hand off to `distill`.

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

## Changelog
- 2026-05-01 v0.1.0 — Initial release.
