---
name: skillmesh-advisor
description: 在当前 Codex 线程内推荐最合适的 skills、plugins 与 MCP 组合，并说明原因、前置依赖和下一步执行顺序。
---

# SkillMesh Advisor

## Use this skill when

- 用户想知道当前任务该用哪个 skill、plugin 或 MCP
- 用户想盘点当前仓库或本地环境里已有的能力
- 用户想把一个任务拆成一条可执行的技能链
- 用户想确认缺失依赖、权限瓶颈或安装阻塞点

## Primary goal

把“我现在该用什么”回答清楚，并尽量给出可以立刻执行的下一步。

## Working rules

1. 先收集上下文：
   - 当前用户目标、约束和交付物
   - 仓库信号：技术栈、关键文件、已有插件、skills、MCP
   - 风险信号：是否需要联网、写文件、认证、远程权限
2. 先推荐现成能力，再建议新建能力：
   - 优先本地已安装
   - 其次 workspace 内已有定义
   - 最后才推荐远程安装或新建
3. 推荐组合，不只推荐单点：
   - 例如 `github -> gh-fix-ci -> yeet`
   - 或 `plugin-creator -> custom skill -> marketplace publish`
4. 始终解释原因：
   - 命中的关键词
   - 仓库或文件证据
   - 前置依赖
   - 失败时的退化路径
5. 把边界说清楚：
   - 线程内插件负责推荐、解释、桥接执行
   - 全局库管理、图谱、统计和批量配置属于后续 app surface

## Output format

默认按下面结构输出，除非用户要求别的格式：

### 推荐组合

- 列出 1-3 个最合适的 skill、plugin 或 MCP
- 给出建议顺序

### 为什么是它

- 说明命中的上下文证据
- 标注任何假设

### 前置与风险

- 缺失依赖
- 需要的权限或认证
- 可能失败点

### 下一步

- 给出马上可以执行的第一步
- 如果用户目标是“做插件”，优先收敛成 `.codex-plugin/plugin.json`、`skills/`，必要时再补 `.mcp.json` 或 `.app.json`

## Do not

- 不要把独立大屏或 marketing 页当成主交付
- 不要在没有证据时假设某个 skill 已安装
- 不要只给技能名，不解释 why、when、risk
