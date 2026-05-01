# HERMES.md — HERMES entrypoint

> This is the **HERMES runtime boot file** for the `llm-skill` project.
> It is a thin shell. All routing, contract, and lifecycle rules live in [`AGENT.md`](./AGENT.md).
> Do not add domain knowledge here.

## What HERMES should do on load

1. **Single source of truth**: `AGENT.md`. Read it first.
2. **Routing**: use `AGENT.md` §2 to match `triggers`; pick ≤ 3 candidates; lazy-load.
3. **Loop**: Execute → Distill → Guide (`AGENT.md` §1). Three meta-skills have strictly disjoint write rights:
   - Execute: read-only on skills.
   - Distill: writes `skills/<name>/SKILL.md`.
   - Guide: writes `AGENT.md` registry & changelog only.
4. **Language**: default `SKILL.md` is English; fall back to `SKILL_zh.md` when user input is Chinese.

## Install (HERMES)

```bash
# Option A: use this repo as the project root
git clone <this-repo-url> .

# Option B: mount into an existing project
git clone <this-repo-url> .hermes-skills
ln -s .hermes-skills/AGENT.md  ./AGENT.md
ln -s .hermes-skills/HERMES.md ./HERMES.md
ln -s .hermes-skills/skills    ./skills
```

Validate:

```bash
bash install.sh
python3 scripts/validate.py
```

## HERMES-specific guidance

- HERMES tends to run multi-agent graphs. Treat each meta-skill as a **node with a strict interface**:
  - `execute(user_input) -> (deliverable, distill_candidates)`
  - `distill(distill_candidates) -> (skill_diffs)`
  - `guide(skill_diffs) -> (agent_md_diff)`
- Persist `distill-candidates` across steps as first-class state, not scratchpad.
- On every graph tick, re-read `AGENT.md` §2 so routing is never cached stale.

## Minimal contract

- **Read**: `AGENT.md`, chosen `SKILL.md` (lazy).
- **Write**: skills only via `distill`; `AGENT.md` only via `guide`.
- **Never**: mix loop phases; never let Execute write.

## Pointers

- Schema → [`AGENT.md`](./AGENT.md)
- Meta-skills → `skills/execute/`, `skills/distill/`, `skills/guide/`
- Changelog → [`CHANGELOG.md`](./CHANGELOG.md)
