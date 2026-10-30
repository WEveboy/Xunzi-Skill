# dsh-xunzi-perspective

Xunzi-Skill 第一版（1.0.0）的 DeepSeek Harness 原生插件包。

## 它做什么

把 `skills/xunzi-perspective/SKILL.md` 注册为一个名为 `xunzi-perspective` 的技能，并把资源目录（`references/`、`scripts/`）指给宿主，使模型可以按需读取调研记录与渲染脚本。

**注册名**：`dsh-xunzi-perspective`（装/卸/列表时用）
**技能名**：`xunzi-perspective`（对话中调用时用）

## 前置

- Node.js `^22.19.0 || >=24.0.0`
- 已安装 dsh 宿主：`npm install -g @deepseek-ai/dsh@0.2.1-rc.2`
- **已安装仓颉 cangjie-skill 插件**。本插件通过 `inject: ['skills']` 依赖宿主的 skills 服务，没有仓颉时注册会失败。

## 安装

```powershell
dsh plugin --profile web add .\dsh-xunzi-perspective-1.0.0.tgz
dsh web
```

安装后**新开一个任务**验收。`web` 是示例 profile；桌面宿主请换成它实际使用的 profile——装到 web 不等于 desktop 也加载了。

## 不装 Harness 也能查看内容

```powershell
tar -xzf .\dsh-xunzi-perspective-1.0.0.tgz -C C:\SkillLab\xunzi
```

解压后内容在 `C:\SkillLab\xunzi\package\`，`skills\xunzi-perspective\references\quickstart.md` 可直接阅读。

## 契约

`index.mjs` 导出 `name`、`inject = ['skills']`、`apply(context)`，调用 `context.skills.register({...})`，其中：

- `content`：`SKILL.md` 剥离 YAML frontmatter 后的正文；frontmatter 缺失时导入即抛错。
- `resourceBase`：`{ kind: 'directory', path: <包内 skills/xunzi-perspective> }`
- `invocation`：`{ modelInvocable: true, userInvocable: true }`
- `provider`：`dsh-xunzi-perspective`；`source`：`bundled`

契约测试：`node --test tests/test_deepseek.mjs`（5 项）。

## 完整教程

见包内 `DeepSeek-First-Edition.pdf`。
