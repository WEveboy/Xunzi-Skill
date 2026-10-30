#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Codex 安装器：把第一版荀子 skill 装进 Codex 的 skills 目录。

设计取向是「宁可拒绝，不要装坏」：
  - 装之前先按 EDITION.json 逐文件校验 SHA256，内容与版本号对不上就拒绝；
  - 目标已存在时默认拒绝，只有显式 --replace 才覆盖；
  - --replace 是**精确镜像**：先整份备份，再清空目标重铺，旧版残留文件不会留下来，
    被清掉的文件清单会打印在 removed_from_previous 里，备份目录可随时回滚；
  - 拒绝安装到符号链接目标，避免顺着链接写到别处；
  - 装完再校验一次落盘哈希，任何一项不一致就报错。

默认落点：优先 ~/.codex/skills（若那里已有同名 skill，说明是本机旧布局），
否则 ~/.agents/skills（Codex 新布局）。用 --destination 可显式指定。

用法：
    python scripts/install_codex.py                     # 装到默认落点
    python scripts/install_codex.py --destination D:/skills
    python scripts/install_codex.py --replace           # 有意升级，先备份
    python scripts/install_codex.py --dry-run           # 只检查，不写盘
"""
import argparse
import datetime
import hashlib
import json
import shutil
import sys
from pathlib import Path

NAME = "xunzi-perspective"
BASE = Path(__file__).resolve().parent


def source_directory():
    for p in (BASE / NAME, BASE.parent / "skills" / NAME):
        if (p / "EDITION.json").is_file():
            return p
    raise ValueError("找不到完整的第一版 skill 目录（需含 EDITION.json）")


def verify_source(source: Path, edition: dict):
    for rel, digest in edition["files"].items():
        p = source / rel
        if not p.is_file():
            raise ValueError("源文件缺失：" + rel)
        if p.resolve().is_relative_to(source.resolve()) is False:
            raise ValueError("源文件逃逸 skill 目录：" + rel)
        if hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            raise ValueError("源文件哈希与 EDITION.json 不符：" + rel)


def default_root():
    legacy = Path.home() / ".codex" / "skills"
    if (legacy / NAME).exists():
        return legacy
    return Path.home() / ".agents" / "skills"


def install(root=None, replace=False, dry_run=False):
    source = source_directory()
    edition = json.loads((source / "EDITION.json").read_text(encoding="utf-8"))
    verify_source(source, edition)

    root = Path(root).expanduser().resolve() if root else default_root().expanduser().resolve()
    target = root / NAME

    if target.is_symlink():
        raise ValueError("目标是指向别处的符号链接，拒绝写入；请用 --destination 指定独立目录")

    # 干跑必须走完所有检查再返回，否则「先跑 --dry-run 看看会装到哪」这条
    # 在已装过的机器上就永远失败——而这恰恰是最需要先看一眼的场景。
    if dry_run:
        return {
            "status": "dry_run_ok",
            "source": str(source),
            "target": str(target),
            "target_exists": target.exists(),
            "would_backup": target.exists(),
            "would_need_replace": target.exists(),
            "files": len(edition["files"]),
            "note": "未写盘。目标已存在时要真装请加 --replace（会先备份）。" if target.exists() else "未写盘。可直接安装。",
        }

    if target.exists() and not replace:
        raise ValueError(
            "目标已存在：" + str(target) + "\n"
            "  · 只想看是否装成功：读该目录下的 references/quickstart.md\n"
            "  · 确实要升级：加 --replace（会先备份）"
        )

    backup = None
    removed = []
    if target.exists():
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup = root / (NAME + ".backup-" + stamp)
        if backup.resolve().parent != root or target.resolve().parent != root:
            raise ValueError("备份/目标包含性检查失败")
        shutil.copytree(target, backup)
        # --replace 的语义是「精确镜像」：旧版残留文件必须清掉，否则会污染新版
        # （例如上一版有而本版已删的能力卡，会继续被路由表之外的东西引用）。
        # 全部内容已在 backup 里，且下面会把清掉的清单打印出来。
        owned = set(edition["files"]) | {"EDITION.json", "BUILD_MANIFEST.json"}
        removed = sorted(
            p.relative_to(target).as_posix()
            for p in target.rglob("*")
            if p.is_file() and p.relative_to(target).as_posix() not in owned
        )
        shutil.rmtree(target)

    target.mkdir(parents=True, exist_ok=True)
    copied = {}
    for p in source.rglob("*"):
        if not p.is_file() or "__pycache__" in p.parts or p.suffix in {".pyc", ".pyo"}:
            continue
        rel = p.relative_to(source)
        dest = target / rel
        if not dest.resolve().is_relative_to(target.resolve()):
            raise ValueError("目标子路径逃逸：" + rel.as_posix())
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dest)
        copied[rel.as_posix()] = hashlib.sha256(dest.read_bytes()).hexdigest()

    for rel, digest in edition["files"].items():
        if copied.get(rel) != digest:
            raise ValueError("落盘校验失败：" + rel)

    return {
        "status": "installed_and_verified",
        "edition": edition.get("display_name", NAME),
        "public_version": edition.get("public_version"),
        "target": str(target),
        "backup": str(backup) if backup else None,
        "removed_from_previous": removed,
        "files": len(copied),
        "next": "新开一个任务（不要在本会话里测），然后说：用荀子的视角看……",
        "help": str(target / "references" / "quickstart.md"),
    }


def main():
    p = argparse.ArgumentParser(description="安装第一版荀子 skill 到 Codex")
    p.add_argument("--destination", type=Path, help="skills 根目录，例如 ~/.agents/skills")
    p.add_argument("--replace", action="store_true", help="覆盖已存在的安装（先备份）")
    p.add_argument("--dry-run", action="store_true", help="只做校验，不写盘")
    a = p.parse_args()
    try:
        result = install(a.destination, a.replace, a.dry_run)
    except (ValueError, OSError) as e:
        # sys.exit 只接受一个参数；写成 sys.exit(2, msg) 会抛 TypeError，
        # 把「目标已存在，请加 --replace」这类本该可读的提示变成 traceback。
        sys.stderr.write("error: " + str(e) + "\n")
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
