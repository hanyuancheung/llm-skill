#!/usr/bin/env python3
"""
validate.py — Consistency checker for the llm-skill repo.

Checks performed:
  1. Every skills/<dir>/SKILL.md exists and has parseable YAML front-matter.
  2. Required front-matter keys are present.
  3. front-matter `name` equals the directory name.
  4. SKILL_<locale>.md (if present) has matching name/version/status.
  5. AGENT.md §2 registry rows exist for each non-template skill dir,
     and every registry row points to a real SKILL.md.
  6. `dependencies` references refer to real skill directories.
  7. Status is one of {active, experimental, deprecated, template}.
  8. Hook declarations (if present) are well-formed:
     - phases limited to {pre, post, on_error}
     - each entry is a mapping with required `name` and `action`
     - `action` value is in the whitelist (including `run-script:<relpath>`)
     - referenced scripts exist and are executable

Exit code 0 on success, 1 on any error.

No external dependencies required (PyYAML is NOT used — we ship a small
indent-based YAML subset parser covering the documented shape, including
lists of mappings as used by the `hooks` field).
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

ALLOWED_HOOK_PHASES = {"pre", "post", "on_error"}
ALLOWED_HOOK_ACTIONS_LITERAL = {
    "proceed",
    "skip",
    "warn",
    "propose-distill",
    "propose-guide",
    "require-validator",
}
RUN_SCRIPT_PREFIX = "run-script:"
HOOK_ENTRY_REQUIRED = {"name", "action"}


# ============================================================
# Minimal YAML-subset parser (indent-based)
# ------------------------------------------------------------
# Supports, in a strict subset:
#   - scalars:         key: value
#   - inline lists:    key: [a, b, "c"]
#   - block lists of scalars:
#        key:
#          - a
#          - b
#   - block lists of mappings:
#        key:
#          - name: foo
#            action: bar
#   - nested mappings (arbitrary depth):
#        key:
#          sub1: x
#          sub2:
#            deeper: y
#   - comments (`# ...`) and blank lines are ignored.
#
# This is NOT a general YAML parser. It is intentionally restricted to
# the shape documented in AGENT.md §3.1 / §10.
# ============================================================

KV_RE = re.compile(r"^([A-Za-z_][\w\-]*)\s*:\s*(.*)$")


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s


def _split_csv(s: str) -> list[str]:
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


def _parse_scalar_or_inline_list(value: str) -> Any:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_strip_quotes(x.strip()) for x in _split_csv(inner)]
    return _strip_quotes(value)


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _normalize_lines(body: str) -> list[tuple[int, str]]:
    """Strip comments and blanks; return list of (indent, content)."""
    out: list[tuple[int, str]] = []
    for raw in body.splitlines():
        if not raw.strip():
            continue
        stripped = raw.split("#", 1)[0].rstrip() if raw.lstrip().startswith("#") else raw.rstrip()
        # preserve in-line trailing comments too
        if "#" in stripped and not stripped.lstrip().startswith("#"):
            # naive: only strip if not inside quotes
            in_q: str | None = None
            idx = -1
            for i, ch in enumerate(stripped):
                if in_q:
                    if ch == in_q:
                        in_q = None
                elif ch in ("'", '"'):
                    in_q = ch
                elif ch == "#":
                    idx = i
                    break
            if idx != -1:
                stripped = stripped[:idx].rstrip()
        if not stripped.strip():
            continue
        out.append((_indent_of(stripped), stripped))
    return out


def _parse_mapping(lines: list[tuple[int, str]], i: int, base_indent: int) -> tuple[dict[str, Any], int]:
    """Parse a mapping block at indent >= base_indent. Returns (dict, next_index)."""
    result: dict[str, Any] = {}
    while i < len(lines):
        indent, content = lines[i]
        if indent < base_indent:
            break
        if indent > base_indent:
            # unexpected indent: treat as end of this mapping to be safe
            break
        m = KV_RE.match(content.strip())
        if not m:
            i += 1
            continue
        key, raw_value = m.group(1), m.group(2).strip()
        if raw_value == "":
            # block under this key
            # peek next line to decide: list-of-* vs mapping
            j = i + 1
            if j < len(lines) and lines[j][0] > indent:
                child_indent = lines[j][0]
                if lines[j][1].lstrip().startswith("- "):
                    value, i = _parse_list(lines, j, child_indent)
                else:
                    value, i = _parse_mapping(lines, j, child_indent)
                result[key] = value
            else:
                # empty block -> empty list or empty dict; choose []
                result[key] = []
                i = j
        else:
            result[key] = _parse_scalar_or_inline_list(raw_value)
            i += 1
    return result, i


def _parse_list(lines: list[tuple[int, str]], i: int, base_indent: int) -> tuple[list[Any], int]:
    """Parse a block list where every item starts with '- '."""
    items: list[Any] = []
    while i < len(lines):
        indent, content = lines[i]
        if indent < base_indent:
            break
        if indent > base_indent:
            break
        stripped = content.strip()
        if not stripped.startswith("- "):
            break
        rest = stripped[2:].rstrip()

        inline_kv = KV_RE.match(rest)
        if inline_kv and rest and not rest.startswith("["):
            # list item is a mapping: first kv is on the dash line,
            # remaining kvs sit at base_indent + 2 (or more) on next lines.
            item: dict[str, Any] = {}
            key, raw_value = inline_kv.group(1), inline_kv.group(2).strip()
            if raw_value == "":
                # first key has sub-block
                j = i + 1
                if j < len(lines) and lines[j][0] > indent:
                    sub_indent = lines[j][0]
                    if lines[j][1].lstrip().startswith("- "):
                        value, j = _parse_list(lines, j, sub_indent)
                    else:
                        value, j = _parse_mapping(lines, j, sub_indent)
                    item[key] = value
                    i = j
                else:
                    item[key] = []
                    i += 1
            else:
                item[key] = _parse_scalar_or_inline_list(raw_value)
                i += 1

            # collect continuation keys that are indented past the '- '
            cont_indent = indent + 2
            while i < len(lines) and lines[i][0] >= cont_indent:
                if lines[i][1].lstrip().startswith("- "):
                    break
                m = KV_RE.match(lines[i][1].strip())
                if not m:
                    i += 1
                    continue
                ckey, cval = m.group(1), m.group(2).strip()
                if cval == "":
                    j = i + 1
                    if j < len(lines) and lines[j][0] > lines[i][0]:
                        sub_indent = lines[j][0]
                        if lines[j][1].lstrip().startswith("- "):
                            value, j = _parse_list(lines, j, sub_indent)
                        else:
                            value, j = _parse_mapping(lines, j, sub_indent)
                        item[ckey] = value
                        i = j
                    else:
                        item[ckey] = []
                        i = j
                else:
                    item[ckey] = _parse_scalar_or_inline_list(cval)
                    i += 1
            items.append(item)
        else:
            # scalar list item (possibly inline list)
            items.append(_parse_scalar_or_inline_list(rest) if rest else None)
            i += 1
    return items, i


def parse_front_matter(text: str) -> dict[str, Any]:
    """Parse a minimal YAML front-matter block delimited by '---'."""
    if not text.startswith("---"):
        raise ValueError("missing leading '---'")
    end = text.find("\n---", 3)
    if end == -1:
        raise ValueError("missing trailing '---'")
    body = text[3:end].strip("\n")
    lines = _normalize_lines(body)
    result, _ = _parse_mapping(lines, 0, 0)
    return result


# ============================================================
# Reports & checks
# ============================================================

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


def _validate_hook_action(action: Any, skill_dir: Path, skill_name: str, hook_name: str, report: Report) -> None:
    if not isinstance(action, str):
        report.err(f"[{skill_name}] hook '{hook_name}' has non-string action: {action!r}")
        return
    if action in ALLOWED_HOOK_ACTIONS_LITERAL:
        return
    if action.startswith(RUN_SCRIPT_PREFIX):
        rel = action[len(RUN_SCRIPT_PREFIX):].strip()
        if not rel:
            report.err(f"[{skill_name}] hook '{hook_name}' uses empty run-script path")
            return
        target = (skill_dir / rel).resolve()
        try:
            target.relative_to(skill_dir.resolve())
        except ValueError:
            report.err(f"[{skill_name}] hook '{hook_name}' script '{rel}' escapes skill directory")
            return
        if not target.is_file():
            report.err(f"[{skill_name}] hook '{hook_name}' references missing script: {rel}")
            return
        if not os.access(target, os.X_OK):
            report.err(f"[{skill_name}] hook '{hook_name}' script '{rel}' is not executable (chmod +x)")
            return
        return
    report.err(f"[{skill_name}] hook '{hook_name}' has unknown action: {action!r}")


def _validate_hooks(fm: dict[str, Any], skill_dir: Path, skill_name: str, report: Report) -> None:
    hooks = fm.get("hooks")
    if hooks is None:
        return  # hooks are optional
    if not isinstance(hooks, dict):
        report.err(f"[{skill_name}] `hooks` must be a mapping, got {type(hooks).__name__}")
        return

    for phase, entries in hooks.items():
        if phase not in ALLOWED_HOOK_PHASES:
            report.err(f"[{skill_name}] unknown hook phase '{phase}' (allowed: {sorted(ALLOWED_HOOK_PHASES)})")
            continue
        if entries is None or entries == []:
            continue
        if not isinstance(entries, list):
            report.err(f"[{skill_name}] hook phase '{phase}' must be a list, got {type(entries).__name__}")
            continue
        for idx, entry in enumerate(entries):
            if not isinstance(entry, dict):
                report.err(f"[{skill_name}] {phase}[{idx}] must be a mapping with 'name' and 'action'")
                continue
            missing = HOOK_ENTRY_REQUIRED - set(entry.keys())
            if missing:
                report.err(f"[{skill_name}] {phase}[{idx}] missing keys: {sorted(missing)}")
                continue
            hook_name = entry.get("name")
            if phase == "pre" and entry.get("action") in {"propose-distill", "propose-guide", "require-validator"}:
                report.err(f"[{skill_name}] pre-hook '{hook_name}' cannot use post-only action '{entry['action']}'")
            if phase != "pre" and entry.get("action") == "skip":
                report.err(f"[{skill_name}] '{phase}' hook '{hook_name}' cannot use 'skip' (pre-only)")
            _validate_hook_action(entry.get("action"), skill_dir, skill_name, str(hook_name), report)


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

    for k in REQUIRED_KEYS:
        if k not in fm:
            report.err(f"[{name}] SKILL.md missing front-matter key: {k}")

    fm_name = fm.get("name")
    if fm_name != name:
        report.err(f"[{name}] front-matter name='{fm_name}' != directory name='{name}'")

    if fm.get("status") not in ALLOWED_STATUS:
        report.err(f"[{name}] invalid status: {fm.get('status')}")

    deps = fm.get("dependencies") or []
    if isinstance(deps, list):
        for dep in deps:
            if dep and not (SKILLS_DIR / str(dep)).is_dir():
                report.err(f"[{name}] dependency '{dep}' points to non-existent skill")

    _validate_hooks(fm, skill_dir, name, report)

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


# ============================================================
# AGENT.md registry consistency
# ============================================================

REGISTRY_ROW_RE = re.compile(
    r"^\|\s*([A-Za-z_][\w-]*)\s*\|\s*`?skills/([\w\-_]+)/SKILL\.md`?\s*\|.*\|\s*(\w+)\s*\|\s*$"
)


def parse_registry(text: str) -> list[tuple[str, str, str]]:
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


# ============================================================
# main
# ============================================================

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
