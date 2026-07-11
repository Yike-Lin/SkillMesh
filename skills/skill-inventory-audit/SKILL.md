---
name: skill-inventory-audit
description: 盘点当前仓库或本地环境里的 skills、plugins、MCP 和 app 映射，并指出缺口、冲突和下一步。适用于用户想确认一个项目现在到底是插件、skill 集合还是外部 app，或者想把清点结果写入 SkillMesh 数据库时。
---

# Skill Inventory Audit

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

## Workflow

1. 读取插件清单与 `skills/**/SKILL.md`
2. 必要时运行索引命令，把当前仓库 skills 写进本地库：

```powershell
python .\scripts\skillmesh.py index --workspace . --include-installed --json
```

3. 对照仓库证据回答四件事：
   - 现在有哪些 skills
   - 是否已经是合法插件
   - 是否存在 MCP 或 app 映射
   - 当前缺口和冲突是什么
4. 如果用户还想看统计，转到 `../skillmesh-observer/SKILL.md`

## Rules

- 只基于当前仓库证据下结论
- 不要把“将来要做的 UI”算成“现在已有插件能力”
- 如果用户目标是插件优先，就把可视化台面降级为外部 surface 或后续阶段
- 如果发现 `scripts/skillmesh.py`、`config/recommendation-rules.json`、`docs/schema.sql` 已存在，要把它们算作“可执行能力”，不是只说“有文档”

## Output

默认输出四段：

### 能力清单

列出已存在的 skills、插件 manifest、安装脚本、规则配置和数据层。

### 结构判断

说明它现在是完整插件、半成品插件，还是仍以 app 原型为主。

### 缺口

指出缺失文件、未接线能力和安装/分发断点。

### 下一步

给出最小可行改动顺序。
