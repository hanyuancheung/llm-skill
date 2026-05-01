# AGENTS.md — Codex entrypoint

> This is the **Codex runtime boot file** for the `llm-skill` project.
> It is a thin shell. All routing, contract, and lifecycle rules live in [`AGENT.md`](./AGENT.md).
> Do not add domain knowledge here.

## What Codex should do on load

1. **Treat `AGENT.md` as the single source of truth.** Read it first.
2. **Route via `AGENT.md` §2 Skill Registry.** Do not scan `skills/` directly.
3. **Respect the Execute → Distill → Guide loop** defined in `AGENT.md` §1.
4. **Language**: the default `SKILL.md` is English. If the user writes in Chinese, prefer `SKILL_zh.md` when it exists.

## Install (Codex CLI)

The repo is drop-in for Codex. From the target workspace:

```bash
# Option A: use this repo as the project root
git clone <this-repo-url> .

# Option B: mount into an existing project
git clone <this-repo-url> .codex-skills
ln -s .codex-skills/AGENT.md ./AGENT.md
ln -s .codex-skills/AGENTS.md ./AGENTS.md
ln -s .codex-skills/skills    ./skills
```

Then validate:

```bash
bash install.sh           # verifies layout
python3 scripts/validate.py
```

Codex will pick up `AGENTS.md` automatically at session start.

## Minimal contract for Codex

- **Read**: `AGENT.md`, chosen `skills/<name>/SKILL.md` (lazy).
- **Write**: `skills/<name>/SKILL.md` **only via `distill`**; `AGENT.md` **only via `guide`**.
- **Never**: write domain knowledge into `AGENTS.md` itself.

## Pointers

- Schema and routing → [`AGENT.md`](./AGENT.md)
- Meta-skills → `skills/execute/`, `skills/distill/`, `skills/guide/`
- New skill scaffold → `skills/_template/`
- Changelog → [`CHANGELOG.md`](./CHANGELOG.md)
