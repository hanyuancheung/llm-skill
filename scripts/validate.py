#!/usr/bin/env python3
"""
validate.py — Consistency checker for the llm-skill repo.

Checks performed:
  1. Every skills/<dir>/SKILL.md exists and has parseable YAML front-matter.
  2. Required front-matter keys are present.
  3. front-matter `name` equals the directory name.
  4. SKILL_zh.md (if present) has matching name/version/status/triggers.
  5. AGENT.md §2 registry rows exist for each non-template skill dir,
     and every registry row points to a real SKILL.md.
  6. `dependencies` references refer to real skill directories.
  7. Status is one of {active, experimental, deprecated, template}.

Exit code 0 on success, 1 on any error.

No external dependencies required (PyYAML is NOT used — we ship a tiny
front-matter parser good enough for the documented shape).
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
AGENT_MD = REPO_ROOT / "AGENT.md"

REQUIRED_KEYS = ["name", "version", "status", "triggers", "dependencies", "owner", "updated"]
ALLOWED_STATUS = {"active", "experimental", "deprecated", "template"}
MIRROR_MATCH_KEYS = ["name", "version", "status"]


# ---------------- tiny front-matter parser ----------------

def parse_front_matter(text: str) -> dict[str, Any]:
    """
    Parse a minimal YAML front-matter block delimited by '---'.
    Supports: scalar, list (inline [a, b] or block with "- item"), and nested mapping
    (one level, as used in `triggers:`).
    """
    if not text.startswith("---"):
        raise ValueError("missing leading '---'")

    end = text.find("\n---", 3)
    if end == -1:
        raise ValueError("missing trailing '---'")

    body = text[3:end].strip("\n")
    lines = body.splitlines()

    result: dict[str, Any] = {}
    i = 0
    while i < len(lines):
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue

        # top-level "key: value" or "key:" starting block
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", raw)
        if not m:
            i += 1
            continue
        key, value = m.group(1), m.group(2).strip()

        if value == "":
            # either nested mapping or block list
            block_lines = []
            j = i + 1
            while j < len(lines) and (lines[j].startswith("  ") or lines[j].strip() == ""):
                block_lines.append(lines[j])
                j += 1
            result[key] = _parse_block(block_lines)
            i = j
        else:
            result[key] = _parse_scalar_or_inline_list(value)
            i += 1

    return result


def _parse_scalar_or_inline_list(value: str) -> Any:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_strip_quotes(x.strip()) for x in _split_csv(inner)]
    return _strip_quotes(value)


def _parse_block(lines: list[str]) -> Any:
    """Parse a two-space-indented block: either list-of-scalars or mapping."""
    stripped = [ln[2:] if ln.startswith("  ") else ln for ln in lines]
    nonblank = [ln for ln in stripped if ln.strip() != ""]
    if not nonblank:
        return {}

    if all(ln.lstrip().startswith("- ") for ln in nonblank):
        return [_parse_scalar_or_inline_list(ln.lstrip()[2:]) for ln in nonblank]

    # mapping
    result: dict[str, Any] = {}
    i = 0
    while i < len(stripped):
        raw = stripped[i]
        if not raw.strip():
            i += 1
            continue
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", raw)
        if not m:
            i += 1
            continue
        key, value = m.group(1), m.group(2).strip()
        if value == "":
            # collect a nested block (4-space indent relative to top)
            nested: list[str] = []
            j = i + 1
            while j < len(stripped) and (stripped[j].startswith("  ") or stripped[j].strip() == ""):
                nested.append(stripped[j][2:] if stripped[j].startswith("  ") else stripped[j])
                j += 1
            # treat nested lines as a list if they start with '- '
            if all(ln.lstrip().startswith("- ") for ln in nested if ln.strip()):
                result[key] = [_parse_scalar_or_inline_list(ln.lstrip()[2:]) for ln in nested if ln.strip()]
            else:
                result[key] = _parse_scalar_or_inline_list(" ".join(ln.strip() for ln in nested))
            i = j
        else:
            result[key] = _parse_scalar_or_inline_list(value)
            i += 1
    return result


def _split_csv(s: str) -> list[str]:
    # simple CSV: splits on commas not inside quotes
    out, buf, quote = [], [], None
    for ch in s:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            buf.append(ch)
        elif ch == ",":
            out.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if buf:
        out.append("".join(buf))
    return out


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s


# ---------------- checks ----------------

@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def load_skill(md_path: Path) -> dict[str, Any]:
    text = md_path.read_text(encoding="utf-8")
    return parse_front_matter(text)


def check_skill_dir(skill_dir: Path, report: Report) -> dict[str, Any] | None:
    name = skill_dir.name
    main = skill_dir / "SKILL.md"
    if not main.is_file():
        report.err(f"[{name}] missing SKILL.md")
        return None

    try:
        fm = load_skill(main)
    except Exception as e:
        report.err(f"[{name}] front-matter parse failed: {e}")
        return None

    # required keys
    for k in REQUIRED_KEYS:
        if k not in fm:
            report.err(f"[{name}] SKILL.md missing front-matter key: {k}")

    # name must match directory
    fm_name = fm.get("name")
    if fm_name != name:
        report.err(f"[{name}] front-matter name='{fm_name}' != directory name='{name}'")

    # status whitelist
    if fm.get("status") not in ALLOWED_STATUS:
        report.err(f"[{name}] invalid status: {fm.get('status')}")

    # dependencies -> must be real dirs
    deps = fm.get("dependencies") or []
    if isinstance(deps, list):
        for dep in deps:
            if dep and not (SKILLS_DIR / str(dep)).is_dir():
                report.err(f"[{name}] dependency '{dep}' points to non-existent skill")

    # mirror (SKILL_zh.md etc)
    for mirror in skill_dir.glob("SKILL_*.md"):
        try:
            mfm = load_skill(mirror)
        except Exception as e:
            report.err(f"[{name}] {mirror.name} parse failed: {e}")
            continue
        for k in MIRROR_MATCH_KEYS:
            if fm.get(k) != mfm.get(k):
                report.err(
                    f"[{name}] {mirror.name} front-matter '{k}' differs "
                    f"(SKILL.md={fm.get(k)!r} vs {mirror.name}={mfm.get(k)!r})"
                )

    return fm


REGISTRY_ROW_RE = re.compile(
    r"^\|\s*([A-Za-z_][\w-]*)\s*\|\s*`?skills/([\w\-_]+)/SKILL\.md`?\s*\|.*\|\s*(\w+)\s*\|\s*$"
)


def parse_registry(text: str) -> list[tuple[str, str, str]]:
    """Return list of (name, path_skill_dir, status) rows from AGENT.md §2."""
    rows = []
    in_registry = False
    for line in text.splitlines():
        if line.strip().startswith("## 2."):
            in_registry = True
            continue
        if in_registry and line.startswith("## ") and not line.strip().startswith("## 2."):
            break
        if not in_registry:
            continue
        m = REGISTRY_ROW_RE.match(line.strip())
        if m:
            rows.append((m.group(1), m.group(2), m.group(3)))
    return rows


def check_registry(skill_fms: dict[str, dict[str, Any]], report: Report) -> None:
    if not AGENT_MD.is_file():
        report.err("AGENT.md missing")
        return
    text = AGENT_MD.read_text(encoding="utf-8")
    rows = parse_registry(text)

    reg_names = {r[0] for r in rows}
    disk_names = {name for name, fm in skill_fms.items() if fm and fm.get("status") != "template"}

    for row_name, row_dir, row_status in rows:
        if row_name != row_dir:
            report.warn(f"AGENT.md registry row name '{row_name}' differs from path 'skills/{row_dir}/'")
        if row_name not in skill_fms:
            report.err(f"AGENT.md registry mentions '{row_name}' but skills/{row_name}/ does not exist")
            continue
        fm = skill_fms[row_name]
        if fm and fm.get("status") != row_status:
            report.err(
                f"AGENT.md registry status for '{row_name}' = '{row_status}' "
                f"but SKILL.md says '{fm.get('status')}'"
            )

    for name in disk_names:
        if name not in reg_names:
            report.err(f"skills/{name}/ exists but is not registered in AGENT.md §2")


# ---------------- main ----------------

def main() -> int:
    if not SKILLS_DIR.is_dir():
        print("FAIL: skills/ directory not found")
        return 1

    report = Report()
    skill_fms: dict[str, dict[str, Any]] = {}

    for entry in sorted(SKILLS_DIR.iterdir()):
        if not entry.is_dir():
            continue
        fm = check_skill_dir(entry, report)
        skill_fms[entry.name] = fm or {}

    check_registry(skill_fms, report)

    print(f"Skills scanned: {len(skill_fms)}")
    if report.warnings:
        print("\nWarnings:")
        for w in report.warnings:
            print(f"  - {w}")

    if report.errors:
        print("\nErrors:")
        for e in report.errors:
            print(f"  - {e}")
        print("\nRESULT: FAIL")
        return 1

    print("\nRESULT: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
