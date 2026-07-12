# SkillMesh 真实线程验收记录

这份模板用来记录新开 Codex 任务后的真实输出。

## 环境

- 日期：
- Codex 插件已启用：是 / 否
- 工作区：`D:\Code\SkillMesh`
- 线程类型：新开任务

## 测试语 1：advisor

输入：

```text
使用 $skillmesh-advisor 推荐这个 Codex 插件仓库接下来该做什么
```

实际输出：

```text
（把真实输出贴这里）
```

判定：

- 是否出现 `skillmesh-advisor / skill-inventory-audit / skillmesh-publisher`：
- 是否出现 `nature-*` 或无关 domain：
- 是否固定四段输出：
- 是否有重复段落：

## 测试语 2：inventory

输入：

```text
使用 $skill-inventory-audit 盘点当前仓库里的 skills、插件结构和缺口
```

实际输出：

```text
（把真实输出贴这里）
```

判定：

- 是否识别出 Codex 插件仓库：
- 是否识别出 6 个内置 skills：
- 是否引用了 `.codex-plugin/plugin.json`、`skills/`、`scripts/`：

## 测试语 3：publisher

输入：

```text
使用 $skillmesh-publisher 校验并构建这个插件的发布产物
```

实际输出：

```text
（把真实输出贴这里）
```

判定：

- 是否提到插件校验：
- 是否提到 release zip：
- 是否提到 SHA256：
- 是否提到 GitHub Actions / release：

## 测试语 4：observer

输入：

```text
使用 $skillmesh-observer 看一下这个仓库最近的推荐和运行统计
```

实际输出：

```text
（把真实输出贴这里）
```

判定：

- 是否把重点放在反馈、运行记录、统计：
- 是否误答成插件构建建议：
- 是否出现无关 domain：

## 最终结论

- advisor 稳定性：通过 / 不通过
- inventory 稳定性：通过 / 不通过
- publisher 稳定性：通过 / 不通过
- observer 稳定性：通过 / 不通过
- 是否发生串台：是 / 否
- 是否达到真实线程验收通过标准：是 / 否
