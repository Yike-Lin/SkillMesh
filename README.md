# SkillMesh

> 面向 Codex 的插件化 Skill OS

<p align="left">
  <a href="https://github.com/Yike-Lin/SkillMesh/stargazers"><img src="https://img.shields.io/github/stars/Yike-Lin/SkillMesh?style=flat-square&color=2563eb&label=%E6%98%9F%E6%A0%87" alt="星标" /></a>
  <a href="https://github.com/Yike-Lin/SkillMesh/commits/main"><img src="https://img.shields.io/github/last-commit/Yike-Lin/SkillMesh?style=flat-square&color=0ea5e9&label=%E6%9C%80%E8%BF%91%E6%8F%90%E4%BA%A4" alt="最近提交" /></a>
  <img src="https://img.shields.io/badge/Codex-%E6%8F%92%E4%BB%B6-1d4ed8?style=flat-square" alt="Codex 插件" />
  <img src="https://img.shields.io/badge/%E7%8A%B6%E6%80%81-%E6%9C%AC%E5%9C%B0%E5%BC%80%E5%8F%91%E4%B8%AD-0f766e?style=flat-square" alt="状态：本地开发中" />
  <img src="https://img.shields.io/badge/%E5%88%86%E5%8F%91-%E4%B8%AA%E4%BA%BA%20Marketplace-334155?style=flat-square" alt="分发：个人 Marketplace" />
</p>

SkillMesh 是一个 **Codex 插件项目**。

天下Skills如过江之鲫,SkillMesh专注在线程内解决一件事：把分散的 `skills / plugins / MCP` 组织成可推荐、可解释、可安装的能力层。

## 它能做什么

- 推荐当前任务最合适的 `skill / plugin / MCP`
- 解释为什么推荐它
- 盘点仓库里已有的插件能力
- 帮你把项目收敛成真正的 Codex 插件
- 把本地安装、staging、验证流程串起来

## 内置 Skills

- `skillmesh`：总入口，负责路由任务
- `skillmesh-advisor`：推荐最合适的能力组合
- `skill-inventory-audit`：盘点当前仓库的插件能力
- `codex-plugin-architect`：把项目收敛成 Codex 插件结构

## 快速开始

### 1. 验证插件结构

```powershell
python C:\Users\Administrator\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py .
```

### 2. 安装到本地 Codex

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-local-plugin.ps1
```

这个脚本会：

1. 准备 `%USERPROFILE%\plugins\skillmesh`
2. 更新个人 marketplace 条目
3. 写入新的 cachebuster 版本
4. 验证 staged plugin
5. 输出 Codex app deeplink

### 3. 在 Codex 中启用

如果你当前的 `codex` CLI 还不支持 `plugin add`，直接用脚本输出的 Codex app deeplink 打开并启用即可。

建议之后新开一个 Codex 线程，确保最新 skills 被正确加载。

## 使用示例

在 Codex 线程里直接这样说：

- `用 SkillMesh 盘点这个仓库里已经具备哪些插件能力`
- `根据当前任务，推荐最合适的 skills / plugins / MCP 组合`
- `帮我把这个项目收敛成真正的 Codex 插件`
- `告诉我在安装或执行之前，还缺哪些前置条件`

## 文档

- [PRD-lite](./docs/PRD-lite.md)
- [Schema draft](./docs/schema.sql)

## 当前状态

SkillMesh 当前已经可以作为 **本地 Codex 插件** 使用，项目接下来会继续补强推荐逻辑和分发路径。
