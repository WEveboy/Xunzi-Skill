#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""渲染《荀子》扫描底本的指定页面为 PNG，供视觉模型逐页阅读。

底本（方勇、李波 译注，中华书局 2010）是纯扫描件，每页只有一张图、没有文字层，
所以只能渲染成图片再读。本脚本只负责「书页号 → PNG」。

## 底本从哪里找（按顺序）

1. `--pdf <路径>` 显式指定
2. 环境变量 `XUNZI_PDF`
3. `<本脚本目录>/../references/sources/books/` 下任意 *.pdf
4. 桌面上的 `荀子*.pdf`（仅本机已放置时命中）

底本受版权保护，不随 skill 分发。没有底本时本脚本给出获取与放置说明后退出，
**不影响 skill 的其余功能**（调研记录已逐字抄录引用原文并标注书页）。

## 页码换算

    pdf_index = book_page + 13

目录在 pdf_index 12/13；正文「劝学」从 book_page 1 起 = pdf_index 14。

## 用法

    python render_pages.py --list-chapters
    python render_pages.py --chapter 天论 --span 3 --out ./pages
    python render_pages.py --book 265 266 267 --out ./pages
    python render_pages.py --pdfpage 278 279 --out ./pages
    python render_pages.py --pdf /path/to/荀子.pdf --chapter 解蔽 --span 2 --out ./pages

`--span` 从每个起始页向后连续渲染 N 页；`--scale` 默认 3.0（约 1233x1706 px）。
版式提示：正文是「原文页 → 注释+译文页」交替，只取原文页可省一半配额。

退出码：0 成功；2 用法或底本缺失。
"""
import argparse
import glob
import os
import sys

OFFSET = 13

CHAPTERS = {
    "劝学": 1, "修身": 13, "不苟": 25, "荣辱": 37, "非相": 53, "非十二子": 68,
    "仲尼": 81, "儒效": 90, "王制": 114, "富国": 138, "王霸": 162, "君道": 189,
    "臣道": 209, "致士": 220, "议兵": 227, "强国": 250, "天论": 265, "正论": 277,
    "礼论": 300, "乐论": 325, "解蔽": 336, "正名": 357, "性恶": 375, "君子": 391,
    "成相": 397, "赋": 420, "大略": 428, "宥坐": 472, "子道": 483, "法行": 490,
    "哀公": 495, "尧问": 504,
}

HERE = os.path.dirname(os.path.abspath(__file__))


def find_pdf(explicit=None):
    """按 --pdf → $XUNZI_PDF → skill 内 books/ → 桌面常见名 的顺序定位底本。"""
    if explicit:
        return explicit if os.path.isfile(explicit) else None
    env = os.environ.get("XUNZI_PDF")
    if env:
        return env if os.path.isfile(env) else None
    for pat in (
        os.path.join(HERE, "..", "references", "sources", "books", "*.pdf"),
        os.path.join(HERE, "..", "..", "references", "sources", "books", "*.pdf"),
    ):
        hits = sorted(glob.glob(os.path.normpath(pat)))
        if hits:
            return hits[0]
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    hits = sorted(glob.glob(os.path.join(desktop, "荀子*.pdf")))
    if hits:
        return hits[0]
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="渲染《荀子》扫描底本指定页为 PNG")
    ap.add_argument("--pdf", help="底本 PDF 路径（优先于自动查找）")
    ap.add_argument("--book", nargs="*", type=int, default=[], help="书页号，可多个")
    ap.add_argument("--pdfpage", nargs="*", type=int, default=[], help="PDF 页索引（0 起），可多个")
    ap.add_argument("--chapter", nargs="*", default=[], help="篇名，如 天论（可多个）")
    ap.add_argument("--span", type=int, default=1, help="从每个起始页向后连续取几页，默认 1")
    ap.add_argument("--scale", type=float, default=3.0, help="渲染倍率，默认 3.0")
    ap.add_argument("--out", help="输出目录，默认 ./xunzi-pages")
    ap.add_argument("--list-chapters", action="store_true", help="列出篇名与书页，然后退出")
    a = ap.parse_args(argv)

    if a.list_chapters:
        for name, page in CHAPTERS.items():
            print(f"{name}\t书页 {page}\tpdf {page + OFFSET}")
        return 0

    try:
        import pypdfium2 as pdfium
    except ImportError:
        print("缺少 pypdfium2。请用带该库的 Python 运行，或先执行：", file=sys.stderr)
        print("  python -m pip install pypdfium2", file=sys.stderr)
        print(r"WorkBuddy 托管环境示例：C:\Users\<你>\.workbuddy\binaries\python\envs\default\Scripts\python.exe",
              file=sys.stderr)
        return 2

    pdf_path = find_pdf(a.pdf)
    if not pdf_path:
        print("找不到底本 PDF。", file=sys.stderr)
        print("底本受版权保护，不随本 skill 分发。请自行取得《荀子》（方勇、李波 译注，中华书局 2010）",
              file=sys.stderr)
        print("扫描件后，任选其一：", file=sys.stderr)
        print("  1) 放到  <skill目录>/references/sources/books/   下（任意 *.pdf 均可识别）", file=sys.stderr)
        print("  2) 设置环境变量  XUNZI_PDF=<绝对路径>", file=sys.stderr)
        print("  3) 运行时加  --pdf <绝对路径>", file=sys.stderr)
        print("提示：不装底本也能正常使用本 skill——调研记录已逐字抄录引用原文并标注书页。", file=sys.stderr)
        return 2

    starts = []
    for name in a.chapter:
        if name not in CHAPTERS:
            print(f"未知篇名：{name}", file=sys.stderr)
            print("可用篇名：" + "、".join(CHAPTERS), file=sys.stderr)
            return 2
        starts.append(CHAPTERS[name])

    idx = list(a.pdfpage)
    idx.extend(b + OFFSET for b in a.book)
    for s in starts:
        base = s + OFFSET
        idx.extend(range(base, base + max(1, a.span)))
    if not idx:
        print("没有指定页面。用 --chapter / --book / --pdfpage 指定，或 --list-chapters 看篇名。",
              file=sys.stderr)
        return 2

    out = a.out or os.path.join(os.getcwd(), "xunzi-pages")
    os.makedirs(out, exist_ok=True)

    doc = pdfium.PdfDocument(pdf_path)
    total = len(doc)
    written = 0
    for i in sorted(set(idx)):
        if i < 0 or i >= total:
            print(f"跳过越界页 pdf {i}（底本共 {total} 页）", file=sys.stderr)
            continue
        path = os.path.join(out, f"p{i:03d}_book{i - OFFSET}.png")
        doc[i].render(scale=a.scale).to_pil().save(path)
        print(path)
        written += 1
    print(f"完成：{written} 页 → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
