# 荀子 · 思维操作系统（xunzi-perspective）

一个可运行的人物思维框架 Skill。用荀子（约前 310—前 235，名况，又称荀卿、孙卿）的心智模型、决策启发式与表达方式，审事、断人、设计制度、拆解诡辩。

第一版（public version 1.0.0）。

## 装好之后先读这两个文件

| 想知道 | 读 |
|---|---|
| 怎么确认装对了、怎么问第一句、三种问法 | `references/quickstart.md` |
| 没反应 / 不像荀子 / 引文对不上 / 脚本报错 | `references/troubleshooting.md` |

## 目录结构

```
xunzi-perspective/
├── SKILL.md                    # 入口：6 心智模型 + 9 启发式 + 示例对话 + 表达 DNA + 跑偏自检
│                               #       + 6 对张力 + 诚实边界 + 首次使用指针
├── README.md                   # 本文件
├── EDITION.json                # 版本号 + 每个文件的 SHA256（安装器据此校验完整性）
├── BUILD_MANIFEST.json         # 构建清单
├── scripts/
│   └── render_pages.py         # 底本扫描件渲染脚本（书页 → PNG），底本不随包分发
└── references/
    ├── quickstart.md           # 快速上手
    ├── troubleshooting.md      # 故障排查
    └── research/               # 7 份调研记录，约 29 万字节，逐条标书页与原话
        ├── 01a-writings-cultivation.md   # 劝学/修身/不苟/荣辱/非相/非十二子/仲尼/儒效
        ├── 01b-writings-politics.md      # 王制/富国/王霸/君道/臣道/致士/议兵/强国
        ├── 01c-writings-philosophy.md    # 天论/正论/礼论/乐论/解蔽/正名/性恶/君子
        ├── 03-expression-dna.md          # 句式模板库、排比组织法、词汇、节奏、可执行规则
        ├── 04-external-views.md          # 历代评价谱系、四组学术争议、盲区清单
        ├── 05-decisions.md               # 11 个生平决策 + 8 组史料分歧
        └── 06-timeline.md                # 生平 / 文本形成史 / 影响史 / 当代研究
```

## 底本与回原书核对

底本为中华书局「全本全注全译」本《荀子》，方勇、李波 译注，2010。**纯扫描件，无文字层**（每页仅一张图），必须渲染成图片后阅读。

**底本受版权保护，不随本 skill 分发。** 三个放置办法任选其一：

1. 放到 `references/sources/books/` 下（任意 `*.pdf` 会被自动识别）
2. 设环境变量 `XUNZI_PDF=<绝对路径>`
3. 运行时加 `--pdf <绝对路径>`

```bash
python scripts/render_pages.py --list-chapters          # 篇名 ↔ 书页 ↔ PDF 页
python scripts/render_pages.py --chapter 天论 --span 3 --out ./pages
```

页码换算：`PDF 页索引 = 书页 + 13`。版式是「原文页 → 注释+译文页」交替，**只取原文页**可省一半配额。

没有底本也能正常使用——所有被引用的原文都已在 `references/research/` 里逐字抄录并标注书页。

## 诚实边界（摘）

- 精读约 100 页，非全书通读。未取到原文的段落已在 SKILL.md 点名（最重要三处：「涂之人可以为禹」整段、《乐论》「以道制欲」对偶句、《正论》八条驳文中的六条）。
- 生卒年无确考，异说相差三十年；「年五十」还是「年十五」游齐未决。
- 《性恶》作者仍有「性朴论」一派挑战；八篇疑非自著。
- 注释本里的「人定胜天」「朴素唯物主义」是 2010 年编者的现代范畴，不是荀子原话。
- 秩序论证是功能主义的（「否则会乱」），不是价值论证。等级化是结构性盲区。

## 生成方式

由 [女娲 · Skill造人术](https://github.com/alchaincyf/nuwa-skill) 的流程生成：5 个并行 agent 分工精读底本（逐字抄录原文并标书页）+ 1 个 agent 做外部考据 → 提炼心智模型（三重验证：跨域复现 / 生成力 / 排他性）→ 构建 → quality_check 6/6 → 独立 agent 盲测 4 题（3 已知立场 + 1 边缘）并据反馈修订。
