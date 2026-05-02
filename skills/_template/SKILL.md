---
name: _template
version: 0.0.0
status: template
triggers:
  keywords: []
  intents: []
dependencies: []
owner: <fill-me>
updated: <YYYY-MM-DD>
hooks:
  # Optional. Remove a phase entirely if unused.
  # The default `should-distill` post-hook is always active; no need to declare.
  pre: []
  # - name: needs-go
  #   when: "target language is Go"
  #   action: warn                  # skip | warn | proceed
  post: []
  # - name: run-unit-tests
  #   when: "source files changed"
  #   action: run-script:hooks/post.sh
  on_error: []
---

# <skill-name> — <one-line positioning>

> Copy this directory as `skills/<your-skill-name>/`, fill in per comments.
> When done, notify `guide` to update the `AGENT.md` registry.

## What
<One-line statement of what this skill solves, ≤ 2 lines.>

## When to use
- ✅ <positive example 1>
- ✅ <positive example 2>

## When NOT to use
- ❌ <negative example 1>
- ❌ <negative example 2>

## How
1. <step 1>
2. <step 2>
3. ...

## Examples

### 1. <scenario>
```
<minimal runnable example>
```

## Pitfalls
- **P1**: <trigger condition> → <mitigation>
- **P2**: ...

## Changelog
- <YYYY-MM-DD> v0.1.0 — Initial release.
