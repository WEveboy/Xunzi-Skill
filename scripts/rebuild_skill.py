#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""重建 EDITION.json 与 BUILD_MANIFEST.json（唯一真源是 skills/<name>/ 里的实际文件）。

改动 skill 内任何文件后必须重跑本脚本，否则安装器的完整性校验会拒绝安装——
这是有意设计的：宁可在安装时报错，也不要把内容与版本号对不上的包发出去。

用法： python scripts/rebuild_skill.py [--check]
  --check  只校验现存的 EDITION.json 是否与实际文件一致，不写盘；不一致时退出码 1。
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

NAME = "xunzi-perspective"
DISPLAY = "荀子·思维操作系统"
PUBLIC_VERSION = "1.0.1"
EDITION = 1
BASELINE = "1.0.1-dev"          # 第一版冻结时指向自身
ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / NAME

# 不写进 files 清单的文件：EDITION.json 无法包含自身哈希；清单文件本身也不自指
EXCLUDE = {"EDITION.json", "BUILD_MANIFEST.json"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def collect():
    files = {}
    for p in sorted(SKILL.rglob("*")):
        if not p.is_file():
            continue
        if "__pycache__" in p.parts or p.suffix in {".pyc", ".pyo"}:
            continue
        rel = p.relative_to(SKILL).as_posix()
        if rel in EXCLUDE:
            continue
        files[rel] = sha256(p)
    return files


def build_manifest(files):
    return {
        "skill": NAME,
        "display_name": DISPLAY,
        "edition": EDITION,
        "public_version": PUBLIC_VERSION,
        "frozen_baseline": BASELINE,
        "generated_by": "scripts/rebuild_skill.py",
        "file_count": len(files),
        "capabilities": {
            "mental_models": 6,
            "decision_heuristics": 9,
            "unresolved_tensions": 6,
            "research_documents": 7,
            "runtime_programs": 1,
        },
        "runtime": {
            "python": ">=3.9（仅 scripts/render_pages.py 需要；需 pypdfium2）",
            "node": None,
            "skill_core": "纯 Markdown，无运行时依赖",
        },
        "source_policy": "底本《荀子》（方勇、李波 译注，中华书局 2010）受版权保护，不随包分发。",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    if not SKILL.is_dir():
        sys.exit(f"找不到 skill 目录：{SKILL}")

    files = collect()
    manifest = build_manifest(files)

    if a.check:
        ed = json.loads((SKILL / "EDITION.json").read_text(encoding="utf-8"))
        old = ed.get("files", {})
        missing = sorted(set(old) - set(files))
        extra = sorted(set(files) - set(old))
        changed = sorted(k for k in set(old) & set(files) if old[k] != files[k])
        if missing or extra or changed:
            print("EDITION.json 与实际文件不一致：")
            for k in missing:
                print("  缺失:", k)
            for k in extra:
                print("  新增:", k)
            for k in changed:
                print("  已改:", k)
            print("→ 运行 python scripts/rebuild_skill.py 重建")
            return 1
        print(f"一致：{len(files)} 个文件")
        return 0

    edition = {
        "project": "Xunzi Perspective Skill",
        "display_name": DISPLAY,
        "public_version": PUBLIC_VERSION,
        "edition": EDITION,
        "frozen_baseline": BASELINE,
        "capabilities": manifest["capabilities"],
        "files": files,
    }
    (SKILL / "EDITION.json").write_text(
        json.dumps(edition, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    (SKILL / "BUILD_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"已重建：{len(files)} 个文件")
    for k in files:
        print("  ", k)
    return 0


if __name__ == "__main__":
    sys.exit(main())
