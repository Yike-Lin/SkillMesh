---
name: skillmesh-observer
description: 记录 SkillMesh 的推荐反馈、Skill 执行结果与统计报告。适用于用户想追踪某次推荐是否命中、某个 skill 执行是否成功、查看 workspace 级别的推荐/运行数据，或给插件补可观测能力的场景。
---

# SkillMesh Observer

## Overview

用这个技能把“推荐得对不对、执行有没有用、最近哪些能力最常被命中”落到本地数据库，而不是只停留在口头判断。

优先调用 `scripts/skillmesh.py` 里的观测命令。

## Workflow

### 1. 记录推荐反馈

当用户已经拿到 `recommend` 的结果，并且知道某个推荐是否命中时，调用：

```powershell
python .\scripts\skillmesh.py feedback <recommendation_id> <skill-slug> helpful
```

如果是误判，调用：

```powershell
python .\scripts\skillmesh.py feedback <recommendation_id> <skill-slug> misfire --reason "<原因>"
```

### 2. 记录一次 Skill 执行开始

在真正执行某个 skill、脚本或操作前，先创建一条运行记录：

```powershell
python .\scripts\skillmesh.py observe-start <skill-slug> --workspace . --command "<执行命令>"
```

记下返回的 `run_id`。

### 3. 记录执行完成结果

执行结束后，用同一个 `run_id` 补结果：

```powershell
python .\scripts\skillmesh.py observe-finish <run_id> --outcome success --feedback helpful
```

失败时补充错误摘要：

```powershell
python .\scripts\skillmesh.py observe-finish <run_id> --outcome failed --feedback misfire --error "<错误摘要>"
```

### 4. 输出统计报告

看全局统计：

```powershell
python .\scripts\skillmesh.py report --json
```

只看当前仓库：

```powershell
python .\scripts\skillmesh.py report --workspace . --json
```

## Working rules

- 优先使用当前工作区路径，避免把别的仓库数据混进来
- 反馈和运行记录都要尽量绑定真实的 `recommendation_id` 或 `run_id`
- 观测结果只用于事实记录，不替用户做价值判断
- 如果用户问“现在已经做了哪些功能、还差哪些功能”，要基于统计能力和 schema 说明当前已实现范围

## Output

默认输出三段：

### 已记录什么

说明本次写入了哪类记录：推荐反馈、运行结果或统计查询。

### 当前数据怎么看

给出关键数字，例如推荐次数、采纳数、成功数、误判数、高频 skill。

### 下一步

如果数据太少，建议继续记录反馈；如果已经有明显模式，指出该优化推荐规则还是补新的 skill。
