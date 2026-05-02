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
  # 可选。不用的阶段整段删除即可。
  # 默认的 `should-distill` post-hook 对所有 skill 自动生效，无需在此声明。
  pre: []
  # - name: needs-go
  #   when: "目标语言是 Go"
  #   action: warn                  # skip | warn | proceed
  post: []
  # - name: run-unit-tests
  #   when: "源文件有改动"
  #   action: run-script:hooks/post.sh
  on_error: []
---

# <skill-name> — <一句话定位>

> 复制此目录为 `skills/<your-skill-name>/`，按注释填写即可。
> 写完后通知 `guide` 更新 AGENT.md 注册表。

## What
<一句话说明 skill 解决什么问题，不超过 2 行。>

## When to use
- ✅ <正例 1>
- ✅ <正例 2>

## When NOT to use
- ❌ <反例 1>
- ❌ <反例 2>

## How
1. <步骤 1>
2. <步骤 2>
3. ...

## Examples

### 例 1：<场景名>
```
<最小可运行示例>
```

## Pitfalls
- **P1**：<坑的触发条件> → <规避方式>
- **P2**：...

## Changelog
- <YYYY-MM-DD> v0.1.0 — 初版。
