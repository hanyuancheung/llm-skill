# CLAUDE.md — Claude Code entrypoint

> This is the **Claude Code runtime boot file** for the `llm-skill` project.
> It is a thin shell. All routing, contract, and lifecycle rules live in [`AGENT.md`](./AGENT.md).
> Do not add domain knowledge here.

## What Claude Code should do on load

1. **Treat `AGENT.md` as the single source of truth.** Read it first; do not read the whole `skills/` tree.
2. **Route via `AGENT.md` §2 Skill Registry.** Pick ≤ 3 candidate skills by `triggers`, then lazy-load.
3. **Respect the Execute → Distill → Guide loop** (`AGENT.md` §1). Claude Code does NOT edit skills while executing; writes go through `distill`, routing edits go through `guide`.
4. **Language**: default `SKILL.md` is English. If the user writes in Chinese, prefer `SKILL_zh.md` when it exists.
5. **Proactive distill**: at task end, if reusable signals were observed, surface a short proposal to invoke `distill`.

## Install (Claude Code)

Claude Code auto-loads `CLAUDE.md` from the workspace root.

```bash
# Option A: use this repo as the project root
git clone <this-repo-url> .

# Option B: mount into an existing project
git clone <this-repo-url> .claude-skills
ln -s .claude-skills/AGENT.md  ./AGENT.md
ln -s .claude-skills/CLAUDE.md ./CLAUDE.md
ln -s .claude-skills/skills    ./skills
```

Validate:

```bash
bash install.sh
python3 scripts/validate.py
```

## Minimal contract

- **Read**: `AGENT.md`, chosen `skills/<name>/SKILL.md` (lazy).
- **Write**: skills only via `distill`; `AGENT.md` only via `guide`.
- **Never**: dump domain knowledge into this file.

## Tips for Claude Code specifically

- Prefer **parallel tool calls** when loading multiple skills chosen by the routing step.
- When reporting "done", include: (a) deliverable, (b) whether a distill proposal is attached.
- If a skill's `How` conflicts with user intent, user wins; the conflict must be logged as a distill candidate.

## Pointers

- Schema and routing → [`AGENT.md`](./AGENT.md)
- Meta-skills → `skills/execute/`, `skills/distill/`, `skills/guide/`
- New skill scaffold → `skills/_template/`
- Changelog → [`CHANGELOG.md`](./CHANGELOG.md)
