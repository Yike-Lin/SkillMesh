---
name: skill-inventory-audit
description: 盘点当前仓库或本地环境里的 skills、plugins、MCP 和 app 映射，并指出缺口、冲突和下一步。
---

# Skill Inventory Audit

## Use this skill when

- 用户想知道当前仓库已经具备哪些 Codex 能力
- 用户在判断“这是 skill、plugin，还是单独 app”
- 用户需要找缺失依赖、结构错误、重复能力或安装阻塞点

## Audit scope

优先检查这些位置：

- `.codex-plugin/plugin.json`
- `skills/**/SKILL.md`
- `skills/**/agents/openai.yaml`
- `.mcp.json`
- `.app.json`
- `hooks/`
- `assets/`
- repo 内的 marketplace 文件

## What to produce

1. 能力清单：
   - 有哪些 skills
   - 是否已经是合法插件
   - 是否带 MCP 或 app 映射
2. 结构判断：
   - 这是插件主工程，还是只有原型 app
   - 有没有把 dashboard 误当插件
3. 缺口清单：
   - 缺哪些必须文件
   - 哪些文件存在但没有接进 manifest
   - 哪些安装路径还没有闭环
4. 下一步：
   - 最小可行改动顺序

## Rules

- 只基于当前仓库证据下结论
- 不要把“将来要做的 UI”算成“现在已有插件能力”
- 如果用户目标是插件优先，就把可视化台面降级为外部 surface 或后续阶段
