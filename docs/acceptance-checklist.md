# SkillMesh 最小验收清单

这份清单给两类场景用：

- 新装完插件后，快速确认 SkillMesh 能不能用
- 发布前，做一轮最小可复现验收

## 先决条件

- 插件已经在 Codex app 里启用
- 当前工作区是 `SkillMesh` 仓库
- 本地安装脚本已经成功跑过

## 新开任务怎么测

新开一个 Codex 任务，在 `D:\Code\SkillMesh` 工作区里先发这 3 句核心测试。

### 1. advisor

```text
使用 $skillmesh-advisor 推荐这个 Codex 插件仓库接下来该做什么
```

正常结果：

- 应该优先出现 `skillmesh-advisor` / `skill-inventory-audit` / `skillmesh-publisher`
- 不应该串进 `nature-*`、课程报告、论文写作之类的无关能力
- 输出结构应该是固定四段：`推荐组合`、`为什么是它`、`前置与风险`、`下一步`

### 2. inventory

```text
使用 $skill-inventory-audit 盘点当前仓库里的 skills、插件结构和缺口
```

正常结果：

- 应该识别出 6 个内置 skills
- 应该指出当前仓库是 Codex 插件仓库
- 应该基于 `.codex-plugin/plugin.json`、`skills/`、`scripts/` 给出判断

### 3. publisher

```text
使用 $skillmesh-publisher 校验并构建这个插件的发布产物
```

正常结果：

- 应该提到插件校验、release zip、SHA256
- 应该把 GitHub Actions / release 作为发布链路的一部分

## 第四句补测

真实线程验收如果要覆盖完整四条链路，再补这一句：

```text
使用 $skillmesh-observer 看一下这个仓库最近的推荐和运行统计
```

正常结果：

- 应该把重点放在反馈、运行记录、统计报告
- 不应该把它误答成插件构建建议或外部 domain 推荐

## 什么结果算通过

满足下面 5 条，就算这一轮真实线程验收通过：

1. `advisor` 没有串进无关 domain
2. `advisor` 输出结构稳定，没有重复段落
3. `inventory` 能认出插件仓库结构
4. `observer` 和 `publisher` 没有路由错位
5. 结果都能落回当前工作区证据，而不是泛泛而谈

## 发布前再看一眼

发布前额外确认：

- `python -m unittest discover -s tests -v` 通过
- `python .\scripts\validate-plugin-local.py . --json` 通过
- `powershell -ExecutionPolicy Bypass -File .\scripts\build-release.ps1` 通过
- `dist/` 下有 zip 和 SHA256
