---
name: skillmesh
description: SkillMesh 的总入口技能，用于判断当前任务应该进入推荐、盘点，还是 Codex 插件构建流程。
---

# SkillMesh

## Overview

把 SkillMesh 当成这个插件的总入口，而不是具体执行细节的终点。

当用户说的是：

- “我现在该用哪个 skill / plugin / MCP”
- “帮我看看这个仓库里现在有哪些技能能力”
- “我要做一个像 Codex 内置插件那样的插件”

先用这个技能收束目标，再立刻路由到更具体的技能。

## Routing

1. 如果重点是“当前任务该用什么”，转到 `../skillmesh-advisor/SKILL.md`
2. 如果重点是“当前仓库或本地环境里已经有什么能力”，转到 `../skill-inventory-audit/SKILL.md`
3. 如果重点是“把项目做成 Codex 插件”，转到 `../codex-plugin-architect/SKILL.md`

## Working rules

- 先确认用户要的是线程内插件能力，还是独立可视化应用
- 如果两者都提到了，优先把插件边界讲清楚，再决定是否保留外部 app 作为辅助手段
- 不要把“有一个 dashboard 原型”误判成“已经有插件”
- 不要停留在泛泛建议，必须落到当前仓库要改哪些文件

## Output

默认输出四段：

### 当前目标

一句话收束用户真正要的东西。

### 应走哪条路

说明应该进入哪个具体技能，为什么。

### 当前证据

列出仓库里已经存在的插件、skills、MCP、app 结构。

### 下一步

给出马上要改的文件或要运行的命令。
