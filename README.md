# Xunzi-Skill · 荀子思维操作系统（第一版）

从中华书局「全本全注全译」本《荀子》（方勇、李波 译注，2010）三十二篇蒸馏出的人物思维框架 Skill：6 个心智模型、9 条决策启发式、完整表达 DNA、6 对未解张力，外加 7 份逐字标注书页的调研记录。

用它来审事、断人、设计制度、拆解诡辩——不是让 AI 复述荀子说了什么，而是让它按荀子的方式做判断。

## 安装与教程（保姆级，PDF）

| 平台 | 教程 | 安装包 |
|---|---|---|
| **Codex** | [Codex 安装版教程](docs/tutorial/Codex-First-Edition.pdf) | `xunzi-perspective-codex-v1.0.1.zip` |
| **DeepSeek Harness** | [DeepSeek 安装版教程](docs/tutorial/DeepSeek-First-Edition.pdf) | `xunzi-perspective-deepseek-v1.0.1.tgz` / `.zip` |

两份教程都从「零前置」开始，覆盖：前置检查 → 安装（脚本法 + 手工法）→ 验证加载成功 → 首跑三例 → 三种问法 → 退出角色 → 常见错误 → 升级/回滚/卸载。

**Codex 一行安装**（下载源码后）：

```bash
python scripts/install_codex.py            # 自动选 ~/.codex/skills 或 ~/.agents/skills
python scripts/install_codex.py --dry-run  # 只看会装到哪
```

**DeepSeek Harness**：需先装 dsh 与仓颉（cangjie）插件，再添加本项目的 TGZ 插件。普通 DeepSeek 网页对话**没有**本地 skill 加载能力，网页版不能替代 Harness。

发行资产与校验文件已发布在 [edition-v1.0.1 Release](https://github.com/WEveboy/Xunzi-Skill/releases/tag/edition-v1.0.1)（5 个资产，均已回下载核验 SHA256）。源码下载后也可按教程安装或自行打包。

## 这个 Skill 有什么

| 维度 | 内容 |
|---|---|
| 心智模型 6 个 | 本末（找唯一有效层级）· 分（划界先于一切秩序）· 伪（善是加工品）· 兼陈（两端皆蔽，取兼不取中）· 定档（分类即论证）· 两得（不把对立项做成零和） |
| 决策启发式 9 条 | 问「要」答「本」· 不给对方错只给对方低 · 先承认对方最强处再换尺子 · 判人看「当」不看「难」· 先把词钉死 · 验前提而非驳结论 · 挡来源再核验 · 一喻只证一理 · 不合则去 |
| 表达 DNA | 短句断言、分档带轴、只引《诗》与「此之谓也」收束、反诘代驳斥、禁用缓和词 |
| 内在张力 6 对 | 法先王／法后王 · 不求知天／制天命而用之 · 有治人无治法／法制主张 · 性恶／涂之人可以为禹 · 王者制名／约定俗成 · 逐条驳／不与辩 |
| 诚实边界 9 条 | 含「未取到原文的句子不许当确凿证据」「生卒年无确考」「两种天不能混用」等硬约束 |

## 从源码复现

Python 3.10+，skill 本体是纯 Markdown，无运行时依赖。仅 `scripts/render_pages.py` 需要 `pypdfium2`。

```bash
python scripts/rebuild_skill.py --check                       # 版本与内容是否一致
python -m unittest discover -s tests                          # 安装器与版本一致性
node --test tests/test_deepseek.mjs                           # DS 适配器契约
python scripts/make_release.py                                # 出 dist/ 全部资产
```

改了 `skills/` 下任何文件，都必须先跑 `python scripts/rebuild_skill.py` 重建 `EDITION.json`，否则安装器会按哈希拒绝安装——这是有意设计的，宁可在安装时报错，也不要把内容和版本号对不上的包发出去。

## 底本与版权

底本《荀子》（方勇、李波 译注，中华书局 2010）**受版权保护，不随本仓库分发**，也不在任何发行资产里。skill 的调研记录已逐字抄录所有被引用的原文并标注书页（`PDF 页 = 书页 + 13`），**不装底本也能完整使用本 skill**；只有想回原书核对时，才需要自备扫描件并放到 `skills/xunzi-perspective/references/sources/books/`（或设 `XUNZI_PDF`）。

本项目不新增 LICENSE：上游依赖按上游许可自行下载安装，不随本项目再分发。

## 贡献者

- **WEveboy** — 项目发起、语料获取、流程与发布
- **DeepSeek-V4.1** — 底本精读（5 个并行调研代理）、框架提炼、SKILL.md 撰写、盲测与修订

详见 [CONTRIBUTORS.md](CONTRIBUTORS.md)。

## 维护

发版与上传必须按 [上传与发布流程](docs/UPLOAD_WORKFLOW.md) 执行，变更记入 [CHANGELOG.md](CHANGELOG.md)。
