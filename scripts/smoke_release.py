#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""发行包烟测：解压 → 真装 → 校验 → 探针。不复用仓库工作区里的任何东西。

检查项：
  1. Codex ZIP 解压后能直接跑安装器，输出 installed_and_verified；装上来的文件哈希与 EDITION.json 一致。
  2. DeepSeek TGZ 解压后是 npm 结构（package/），含 skills/xunzi-perspective/SKILL.md。
  3. 用 node 探针对解压后的插件做注册烟测（register 被调用、frontmatter 已剥离、resourceBase 正确）。
  4. SHA256SUMS.txt 里每个值都与 dist/ 下的实际文件相符。

用法： python scripts/smoke_release.py
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
VERSION = "1.0.0"
ok = 0
fail = 0


def check(name, cond, detail=""):
    global ok, fail
    if cond:
        ok += 1
        print(f"  ✓ {name}")
    else:
        fail += 1
        print(f"  ✗ {name}  {detail}")


def main():
    if not DIST.is_dir():
        sys.exit("dist/ 不存在，先运行 python scripts/make_release.py")

    tmp = Path(tempfile.mkdtemp(prefix="xz-smoke-"))
    try:
        # ---- 1 Codex ----
        print("== Codex 包 ==")
        z = DIST / f"xunzi-perspective-Codex-{VERSION}.zip"
        check("Codex ZIP 存在", z.is_file(), str(z))
        ex = tmp / "codex"
        with zipfile.ZipFile(z) as zf:
            zf.extractall(ex)
        root = ex / f"xunzi-perspective-Codex-{VERSION}"
        check("解压后含安装器", (root / "install_codex.py").is_file())
        check("解压后含教程 PDF", (root / "Codex-First-Edition.pdf").is_file())
        dest = tmp / "skills"
        proc = subprocess.run([sys.executable, str(root / "install_codex.py"), "--destination", str(dest)],
                              capture_output=True, text=True)
        check("安装器退出码 0", proc.returncode == 0, proc.stderr[-300:])
        try:
            res = json.loads(proc.stdout)
        except json.JSONDecodeError:
            res = {}
            check("安装器输出可解析", False, proc.stdout[:200])
        check("状态为 installed_and_verified", res.get("status") == "installed_and_verified", str(res.get("status")))
        target = Path(res.get("target", dest / "xunzi-perspective"))
        check("目标 SKILL.md 存在", (target / "SKILL.md").is_file())
        ed = json.loads((target / "EDITION.json").read_text(encoding="utf-8"))
        bad = [r for r, d in ed["files"].items()
               if not (target / r).is_file() or hashlib.sha256((target / r).read_bytes()).hexdigest() != d]
        check(f"落盘 {len(ed['files'])} 个文件哈希全部相符", not bad, str(bad[:3]))

        # ---- 2/3 DeepSeek ----
        print("== DeepSeek 包 ==")
        t = DIST / f"dsh-xunzi-perspective-{VERSION}.tgz"
        check("TGZ 存在", t.is_file(), str(t))
        dx = tmp / "ds"
        dx.mkdir()
        with tarfile.open(t, "r:gz") as tf:
            names = tf.getnames()
            try:
                tf.extractall(dx, filter="data")
            except TypeError:            # Python < 3.12 没有 filter 参数
                tf.extractall(dx)
        check("TGZ 为 npm 结构（package/ 前缀）", all(n.startswith("package/") for n in names), str(names[:2]))
        pkg = dx / "package"
        for f in ("index.mjs", "package.json", "cordis.patch.yml", "README.md"):
            check(f"含 {f}", (pkg / f).is_file())
        check("含 skills/xunzi-perspective/SKILL.md", (pkg / "skills/xunzi-perspective/SKILL.md").is_file())
        node = shutil.which("node")
        if node:
            proc = subprocess.run([node, str(ROOT / "scripts" / "probe_plugin.mjs"), str(pkg)],
                                  capture_output=True, text=True)
            check("node 探针通过（注册合同）", proc.returncode == 0,
                  (proc.stderr or proc.stdout)[-300:])
        else:
            print("  - 跳过 node 探针（未找到 node）")

        # ---- 4 SHA ----
        print("== 校验值 ==")
        sums = (DIST / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
        check("SHA256SUMS.txt 非空", bool(sums))
        for line in sums:
            digest, name = line.split("  ", 1)
            p = DIST / name
            good = p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == digest
            check(f"{name} 校验通过", good)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n结果：{ok} 通过，{fail} 失败")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
