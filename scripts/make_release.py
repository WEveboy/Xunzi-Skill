#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""构建第一版全部发行资产到 dist/。

产物：
    xunzi-perspective-1.0.0-source.zip        仓库源码（不含 dist/ 与底本）
    xunzi-perspective-Codex-1.0.0.zip          Codex 安装包（安装器 + skill + 教程）
    dsh-xunzi-perspective-1.0.0.tgz            DeepSeek Harness 插件（npm 结构：package/）
    xunzi-perspective-DeepSeek-1.0.0.zip       DS 完整包（TGZ + 两份教程 + 说明）
    SHA256SUMS.txt                             上面四项的校验值

写包用固定时间戳，保证同样的输入产出同样的字节（可复现构建）。
"""
import gzip
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "xunzi-perspective"
DIST = ROOT / "dist"
STAGE = DIST / "stage"
VERSION = "1.0.0"
STAMP = (2026, 10, 30, 0, 0, 0)

EXCLUDE_DIRS = {".git", "dist", "__pycache__", ".venv", "node_modules", "xunzi-pages", ".idea", ".vscode"}
EXCLUDE_SUFFIX = {".pyc", ".pyo", ".png", ".pdf"}          # pdf 单独放行（只放行教程）
ALLOW_PDF = {"docs/tutorial/Codex-First-Edition.pdf", "docs/tutorial/DeepSeek-First-Edition.pdf"}


def rel_files(base: Path):
    out = []
    for p in sorted(base.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(base).as_posix()
        if any(part in EXCLUDE_DIRS for part in p.relative_to(base).parts):
            continue
        if p.suffix in EXCLUDE_SUFFIX and rel not in ALLOW_PDF:
            continue
        out.append(p)
    return out


def add_file(zf: zipfile.ZipFile, src: Path, arcname: str):
    info = zipfile.ZipInfo(arcname, date_time=STAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    zf.writestr(info, src.read_bytes())


def build_zip(path: Path, entries):
    """entries: [(源文件, 归档内路径)]"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for src, arc in entries:
            add_file(zf, src, arc)
    return path


def build_tgz(path: Path, entries):
    """tar + gzip 都要确定性：tar 头用固定 mtime，gzip 头 mtime 必须显式给 0。

    注意：tarfile.open(mode="w:gz") 会把当前时间写进 gzip 头，导致同样的输入
    每次构建出不同字节。必须自己套一层 GzipFile(mtime=0)。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as tf:
        for src, arc in entries:
            data = src.read_bytes()
            info = tarfile.TarInfo(arc)
            info.size = len(data)
            info.mtime = 1790000000
            info.mode = 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            tf.addfile(info, io.BytesIO(data))
    with open(path, "wb") as f:
        # filename="" 很关键：GzipFile 默认会把输出文件名写进 gzip 头（FNAME 字段），
        # 那样同样的内容换个文件名就产出不同字节。
        with gzip.GzipFile(filename="", fileobj=f, mode="wb", compresslevel=9, mtime=0) as gz:
            gz.write(raw.getvalue())
    return path


def check_edition():
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "rebuild_skill.py"), "--check"],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit("版本清单与实际文件不一致，先跑 rebuild_skill.py：\n" + proc.stdout + proc.stderr)
    print("  ✓ EDITION.json 与文件一致")


def main():
    print("== 预检 ==")
    check_edition()
    if not (ROOT / "docs/tutorial/Codex-First-Edition.pdf").is_file():
        sys.exit("缺 Codex 教程 PDF")
    if not (ROOT / "docs/tutorial/DeepSeek-First-Edition.pdf").is_file():
        sys.exit("缺 DeepSeek 教程 PDF")

    if DIST.exists():
        shutil.rmtree(DIST)
    STAGE.mkdir(parents=True)

    # ---- 1 源码包 ----
    src_entries = [(p, f"xunzi-perspective-{VERSION}/" + p.relative_to(ROOT).as_posix())
                   for p in rel_files(ROOT) if p != ROOT / "README.md" or True]
    p_source = build_zip(DIST / f"xunzi-perspective-{VERSION}-source.zip", src_entries)
    print(f"  ✓ {p_source.name}  ({len(src_entries)} 文件)")

    # ---- 2 Codex 包 ----
    codex_root = f"xunzi-perspective-Codex-{VERSION}"
    codex_entries = [
        (ROOT / "scripts" / "install_codex.py", f"{codex_root}/install_codex.py"),
        (ROOT / "platforms" / "codex-INSTALL.md", f"{codex_root}/INSTALL.md"),
        (ROOT / "docs/tutorial/Codex-First-Edition.pdf", f"{codex_root}/Codex-First-Edition.pdf"),
    ]
    for p in rel_files(SKILL):
        codex_entries.append((p, f"{codex_root}/xunzi-perspective/" + p.relative_to(SKILL).as_posix()))
    p_codex = build_zip(DIST / f"xunzi-perspective-Codex-{VERSION}.zip", codex_entries)
    print(f"  ✓ {p_codex.name}  ({len(codex_entries)} 文件)")

    # ---- 3 DeepSeek TGZ（npm 结构 package/） ----
    pkg = STAGE / "package"
    pkg.mkdir()
    for f in ("index.mjs", "cordis.patch.yml", "package.json", "README.md"):
        shutil.copyfile(ROOT / "platforms" / "deepseek" / f, pkg / f)
    shutil.copytree(SKILL, pkg / "skills" / "xunzi-perspective")
    tgz_entries = [(p, "package/" + p.relative_to(pkg).as_posix()) for p in rel_files(pkg)]
    p_tgz = build_tgz(DIST / f"dsh-xunzi-perspective-{VERSION}.tgz", tgz_entries)
    print(f"  ✓ {p_tgz.name}  ({len(tgz_entries)} 文件)")

    # ---- 4 DeepSeek 完整包 ----
    ds_root = f"xunzi-perspective-DeepSeek-{VERSION}"
    ds_entries = [
        (p_tgz, f"{ds_root}/dsh-xunzi-perspective-{VERSION}.tgz"),
        (ROOT / "platforms" / "deepseek" / "README.md", f"{ds_root}/README.md"),
        (ROOT / "docs/tutorial/DeepSeek-First-Edition.pdf", f"{ds_root}/DeepSeek-First-Edition.pdf"),
        (ROOT / "docs/tutorial/Codex-First-Edition.pdf", f"{ds_root}/Codex-First-Edition.pdf"),
    ]
    p_ds = build_zip(DIST / f"xunzi-perspective-DeepSeek-{VERSION}.zip", ds_entries)
    print(f"  ✓ {p_ds.name}")

    shutil.rmtree(STAGE)

    # ---- 5 SHA256SUMS ----
    assets = [p_source, p_codex, p_tgz, p_ds]
    lines = []
    for p in assets:
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        lines.append(f"{h}  {p.name}")
    sums = DIST / "SHA256SUMS.txt"
    sums.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"\n  ✓ SHA256SUMS.txt")
    for line in lines:
        print("    " + line)

    print("\n== dist ==")
    for p in sorted(DIST.iterdir()):
        print(f"  {p.name:44s} {p.stat().st_size/1024:10.1f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
