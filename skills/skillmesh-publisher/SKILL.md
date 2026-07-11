---
name: skillmesh-publisher
description: 校验、打包并准备发布 SkillMesh 这样的 Codex 插件。适用于用户要做本地安装、生成 release zip、校验插件结构、产出 SHA256 校验值，或梳理 GitHub Release 分发路径的场景。
---

# SkillMesh Publisher

## Overview

用这个技能把“仓库里的插件代码”变成“可以验证、可以打包、可以发出去的插件产物”。

优先调用仓库自带的发版脚本，而不是手工压缩目录。

## Workflow

### 1. 校验插件结构

先跑官方插件校验器：

```powershell
python C:\Users\Administrator\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py .
```

如果只是在检查 release 包内容，优先调用 `scripts/validate-release.py`。

### 2. 构建 release 包

调用：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-release.ps1
```

这个脚本应该完成：

- 清理旧产物
- 复制插件所需文件
- 再次校验 staged plugin
- 生成 zip
- 生成 SHA256

### 3. 本地安装验证

如果目标是本地 Codex 调试，调用：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-local-plugin.ps1
```

确认新的 cachebuster 版本已写入，并使用输出的 deeplink 在 Codex 里查看插件。

### 4. GitHub 分发准备

如果用户要公开发布，补齐这些信息：

- `.codex-plugin/plugin.json` 里的仓库元信息
- release zip 文件名与版本号
- SHA256 校验文件
- GitHub Release 文案

## Working rules

- 不要把工作区里的测试库、缓存和 `__pycache__` 打进 release 包
- release 包必须包含 `.codex-plugin`、`skills`、`assets`、`scripts`、`config`、`README.md`
- 如果官方校验器不过，先修 manifest 或 skill，再谈发布
- 如果用户问“能不能上线给别人用”，要区分本地 personal marketplace、仓库分发和官方生态上架

## Output

默认输出四段：

### 校验结果

说明官方验证器和 release 验证是否通过。

### 产物

列出 zip、SHA256 和版本号。

### 分发路径

说明这是本地安装、GitHub 下载，还是未来可公开上架。

### 下一步

给出继续发版、打 tag、发 GitHub Release 或重新安装到 Codex 的第一步。
