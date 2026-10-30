## 荀子思维操作系统 · 第一版（1.0.1）

> **本版修订（1.0.1）：修安装器两处缺陷。** 1.0.0 的 `install_codex.py` 存在两个问题——
> ① 目标已存在时 `--dry-run` 直接报错退出，"先干跑看一眼会装到哪"这个推荐动作在已装过的机器上用不了；
> ② 错误路径写成 `sys.exit(2, msg)`，`sys.exit` 只收一个参数，于是所有可读提示都变成 `TypeError` traceback。
> 两处均已修复，并新增 3 项测试（干跑在已装环境可用、错误路径退出码 2 且无 traceback）。
> **skill 本体（`SKILL.md` 与 7 份调研记录）与 1.0.0 完全一致，哈希未变**；只有安装器、版本号与教程里的包名变了。
> 已装 1.0.0 的用户：重新下载本版用 `--replace` 升级即可，不影响已有内容。

从中华书局《荀子》（方勇、李波 译注，2010）三十二篇蒸馏出的人物思维框架 Skill。用它审事、断人、设计制度、拆解诡辩——不是让 AI 复述荀子说了什么，而是让它按荀子的方式做判断。

### 这份 skill 里有什么

| 维度 | 内容 |
|---|---|
| 心智模型 6 个 | 本末（找唯一有效层级）· 分（划界先于一切秩序）· 伪（善是加工品）· 兼陈（两端皆蔽，取兼不取中）· 定档（分类即论证）· 两得（不把对立项做成零和） |
| 决策启发式 9 条 | 问「要」答「本」· 不给对方错只给对方低 · 先承认对方最强处再换尺子 · 判人看「当」不看「难」· 先把词钉死 · 验前提而非驳结论 · 挡来源再核验 · 一喻只证一理 · 不合则去 |
| 表达 DNA | 短句断言、分档带轴、《诗》曰 +「此之谓也」收束、反诘代驳斥、禁用缓和词 |
| 内在张力 6 对 | 法先王／法后王 · 不求知天／制天命而用之 · 有治人无治法／法制主张 · 性恶／涂之人可以为禹 · 王者制名／约定俗成 · 逐条驳／不与辩 |
| 诚实边界 9 条 | 含「未取到原文的句子不许当确凿证据」「生卒年无确考」「两种天不能混用」 |
| 调研记录 7 份 | 约 29 万字节，逐字抄录原文并标注书页 |

### 资产

| 文件 | 用途 |
|---|---|
| `xunzi-perspective-Codex-1.0.0.zip` | Codex 安装包：安装器 + skill + 教程 PDF |
| `dsh-xunzi-perspective-1.0.0.tgz` | DeepSeek Harness 插件（只想装插件就下这个） |
| `xunzi-perspective-DeepSeek-1.0.0.zip` | DS 完整包：TGZ + 两份教程 + 说明 |
| `xunzi-perspective-1.0.0-source.zip` | 源码（含两份教程 PDF、安装器、测试） |
| `SHA256SUMS.txt` | 上面四项的校验值 |

**校验值不能混用**：ZIP 的对应 ZIP，TGZ 的对应 TGZ。

### Codex 安装（三步）

```bat
cd <解压目录>
python install_codex.py --dry-run     :: 先看会装到哪，一个字节都不写
python install_codex.py               :: 真装
```

成功标志：输出 `"status": "installed_and_verified"`。然后**新开一个任务**（Codex 只在任务启动时扫描 skills），输入「用荀子的视角看：……」。

### DeepSeek Harness 安装

需先装 dsh 与仓颉（cangjie-skill）插件，再添加本插件：

```powershell
npm install -g @deepseek-ai/dsh@0.2.1-rc.2
dsh plugin --profile web add .\dsh-cangjie-skill-2.5.0.tgz
dsh plugin --profile web add .\dsh-xunzi-perspective-1.0.0.tgz
dsh web
```

普通 DeepSeek 网页对话**没有**本地 skill 加载能力，网页版不能替代 Harness。

### 教程

两份保姆级 PDF 都在资产与仓库里：`Codex-First-Edition.pdf` 与 `DeepSeek-First-Edition.pdf`。覆盖前置检查 → 安装（脚本法 + 手工法）→ 验证加载 → 首跑四例 → 四段式验收 → 跑偏自检 → 常见错误 → 升级回滚卸载。

### 已知限制

- 底本精读约 100 页（全书 526 页），非通读；未取到原文的 8 处已在 SKILL.md 列明。
- 生卒年、游齐年龄、《性恶》作者归属均有学术争议，SKILL.md 如实并列而不裁断。
- 秩序论证为功能主义（「否则会乱」），非价值论证；等级化默认值是结构性盲区。
- 底本 PDF 受版权保护，不随本仓库与任何资产分发；缺底本不影响使用。

### 验证

安装器 10 项单元测试、DeepSeek 适配器 5 项契约测试、发行包 20 项烟测、SKILL.md 静态质检 6/6 全部通过。

### 贡献者

WEveboy（发起、语料、流程与发布）· DeepSeek-V4.1（精读、提炼、撰写、验证）
