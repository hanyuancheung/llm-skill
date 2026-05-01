# Changelog

All notable changes to this project will be documented in this file.
This file is **append-only** — never edit or remove past entries; add a new entry on top instead.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · SemVer.

---

## [0.2.0] — 2026-05-01

### Added
- Bilingual SKILL files: every skill now ships `SKILL.md` (English, default) + `SKILL_zh.md` (Chinese mirror) with identical front-matter.
- Runtime entrypoints: `AGENTS.md` (Codex), `CLAUDE.md` (Claude Code), `HERMES.md` (HERMES) — thin shells deferring to `AGENT.md`.
- `README.md` (English default) and `README_zh.md` (Chinese).
- `install.sh` — one-shot layout check + validator invocation.
- `scripts/validate.py` — front-matter & routing consistency checker.
- `CHANGELOG.md` (this file).

### Changed
- `AGENT.md` rewritten as bilingual schema with explicit §8 Runtime entrypoints and §9 Chinese notes.

---

## [0.1.0] — 2026-05-01

### Added
- Initial Execute → Distill → Guide closed loop.
- `AGENT.md` schema: routing table, SKILL contract, lifecycle state machine, anti-patterns.
- Meta-skills: `skills/execute/`, `skills/distill/`, `skills/guide/`.
- `skills/_template/` as the scaffold for new domain skills.
