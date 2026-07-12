---
name: skillmesh-advisor
description: 在当前 Codex 线程内推荐最合适的 skills、plugins 与 MCP 组合，并说明原因、前置依赖和下一步执行顺序。适用于用户询问“现在该用什么能力”、想根据仓库和任务做自动推荐，或想把推荐结果写入 SkillMesh 数据库的场景。
---

# SkillMesh Advisor

## Workflow

1. 收集上下文：
   - 用户当前任务和交付物
   - 工作区路径与仓库结构
   - 是否允许写库、写文件、联网或调用外部命令
2. 优先调用本仓库的推荐引擎，而不是手工拍脑袋：

```powershell
python .\scripts\skillmesh.py recommend "<用户任务>" --workspace . --limit 3 --json
```

3. 从返回结果里提炼：
   - 推荐顺序
   - 每个 Skill 的命中原因
   - `preflight` 里缺失的依赖
4. 如果用户确认推荐有效，提示记录反馈：

```powershell
python .\scripts\skillmesh.py feedback <recommendation_id> <skill-slug> helpful
```

如果推荐失准，则记录：

```powershell
python .\scripts\skillmesh.py feedback <recommendation_id> <skill-slug> misfire --reason "<原因>"
```

## Working rules

- 优先推荐现成能力，再建议新建能力
- 推荐组合，不只推荐单点
- 把线程内插件和外部 app 的边界说清楚
- 如果用户只是要结论，可以不展示命令，但推荐理由必须来自脚本输出或仓库证据
- 只允许基于当前线程目标和当前工作区输出结论，不要引用别的任务、别的文档或别的 domain 里的建议
- 如果当前工作区是 Codex 插件仓库，优先输出插件相关 skills、安装链路、发布链路和仓库盘点结果
- 除非用户当前任务明确点名某个无关 skill，否则不要把 `nature-*`、文档写作或其他外部 domain 的能力混进插件仓库推荐里

## Output

默认只输出四段，且每段只出现一次，不要重复标题，不要混入别的任务背景：

- 标题必须严格使用：`推荐组合`、`为什么是它`、`前置与风险`、`下一步`
- 不要把标题缩成“为什么”或“风险”

### 推荐组合

- 列出 1-3 个最合适的 skill、plugin 或 MCP
- 给出建议顺序
- 每项只写一句用途，不展开成长段

### 为什么是它

- 只引用当前线程任务和当前工作区里的证据
- 说明命中的关键词、仓库信号、文件证据
- 假设最多写 1-2 条，避免重复解释

### 前置与风险

- 列出缺失依赖、所需权限、认证和可能失败点
- 不要重复上一段已经说过的仓库证据

### 下一步

- 只给一个最先该做的动作
- 如果用户目标是做插件，优先引到插件结构、安装链路或发布链路
