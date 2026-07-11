---
name: skillmesh
description: SkillMesh 的总入口技能，用于把当前任务路由到推荐、盘点、观测或插件构建/分发流程。适用于用户想知道该用什么 skill、想审计当前插件能力、想记录推荐/执行效果，或想把项目做成并发布为 Codex 插件的场景。
---

# SkillMesh

## Overview

把 SkillMesh 当成这个插件的总入口，而不是具体执行细节的终点。

当用户说的是：

- “我现在该用哪个 skill / plugin / MCP”
- “帮我看看这个仓库里现在有哪些技能能力”
- “我要做一个像 Codex 内置插件那样的插件”
- “帮我记录这次 skill 推荐是否命中、执行结果怎么样”
- “帮我打包发布这个插件”

先用这个技能收束目标，再立刻路由到更具体的技能。

## Routing

1. 如果重点是“当前任务该用什么”，转到 `../skillmesh-advisor/SKILL.md`
2. 如果重点是“当前仓库或本地环境里已经有什么能力”，转到 `../skill-inventory-audit/SKILL.md`
3. 如果重点是“记录推荐反馈、执行结果或统计”，转到 `../skillmesh-observer/SKILL.md`
4. 如果重点是“打包、校验、分发插件”，转到 `../skillmesh-publisher/SKILL.md`
5. 如果重点是“把项目做成 Codex 插件”，转到 `../codex-plugin-architect/SKILL.md`

## Working rules

- 先确认用户要的是线程内插件能力，还是独立可视化应用
- 如果两者都提到了，优先把插件边界讲清楚，再决定是否保留外部 app 作为辅助手段
- 不要把“有一个 dashboard 原型”误判成“已经有插件”
- 不要停留在泛泛建议，必须落到当前仓库要改哪些文件或要运行的命令
- 需要落库或观测时，优先调用 `scripts/skillmesh.py`
- 需要打包或发版时，优先调用 `scripts/build-release.ps1` 与 `scripts/validate-release.py`

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
