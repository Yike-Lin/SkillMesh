---
name: codex-plugin-architect
description: 把一个项目收敛成像 Codex 内置插件那样的结构，明确插件边界、技能组织和本地安装路径。
---

# Codex Plugin Architect

## Use this skill when

- 用户明确说要做 Codex 插件，而不是独立大屏
- 当前仓库已经有原型 app，但插件形态还不完整
- 需要决定 `.codex-plugin`、`skills/`、`.mcp.json`、`.app.json` 的边界
- 需要给出本地安装或迭代更新路径

## Plugin-first boundary

先把下面四件事做对，再谈额外 UI：

1. `.codex-plugin/plugin.json`
2. `skills/`
3. `assets/`
4. 本地 marketplace / 安装闭环

只有当插件真的需要：

- 外部系统连接时，再补 `.app.json`
- 工具后端时，再补 `.mcp.json`

## Working rules

- 优先做线程内能力，而不是独立 dashboard
- 能用现有 skill 组合表达的，不要急着造外部 UI
- 任何插件结构改动后，都要用官方验证器校验
- 如果要进入本地安装链路，优先走个人 marketplace，而不是手改散乱配置

## Expected output

### 当前插件形态

- 已有的 manifest、skills、assets
- 缺失的 companion files

### 结构判断

- 这是合格插件、半成品插件，还是仍然主要是 app 原型

### 改造顺序

- 先改哪些文件
- 哪些组件先不要做

### 安装路径

- 如何把仓库内容同步到本地插件目录
- 如何让 Codex 重新识别更新
