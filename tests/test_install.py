#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""安装器单元测试：完整性校验、拒覆盖、备份、干跑、符号链接防护。

运行： python -m unittest discover -s tests
"""
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import install_codex as installer  # noqa: E402

SKILL = ROOT / "skills" / "xunzi-perspective"


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="xz-install-"))
        self.root = self.tmp / "skills"
        self.addCleanup(shutil.rmtree, self.tmp, True)

    # ---- 正常路径 ----
    def test_install_copies_and_verifies(self):
        result = installer.install(self.root)
        self.assertEqual(result["status"], "installed_and_verified")
        target = Path(result["target"])
        self.assertTrue((target / "SKILL.md").is_file())
        self.assertTrue((target / "references" / "quickstart.md").is_file())
        self.assertTrue((target / "references" / "troubleshooting.md").is_file())
        self.assertTrue((target / "scripts" / "render_pages.py").is_file())
        edition = json.loads((SKILL / "EDITION.json").read_text(encoding="utf-8"))
        expected = sum(
            1
            for p in SKILL.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.suffix not in {".pyc", ".pyo"}
        )
        self.assertEqual(result["files"], expected)
        self.assertEqual(len(edition["files"]), expected - 2, "EDITION/BUILD 两个清单不计入 files")
        for rel, digest in edition["files"].items():
            self.assertEqual(hashlib.sha256((target / rel).read_bytes()).hexdigest(), digest, rel)

    def test_installed_skill_has_valid_frontmatter(self):
        installer.install(self.root)
        text = (self.root / installer.NAME / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        self.assertIn("name: xunzi-perspective", text.split("---")[1])

    # ---- 拒覆盖 ----
    def test_second_install_refused_without_replace(self):
        installer.install(self.root)
        marker = self.root / installer.NAME / "SKILL.md"
        before = marker.read_bytes()
        with self.assertRaises(ValueError) as ctx:
            installer.install(self.root)
        self.assertIn("--replace", str(ctx.exception))
        self.assertEqual(marker.read_bytes(), before, "被拒时不得改动已有安装")

    def test_replace_creates_backup(self):
        installer.install(self.root)
        (self.root / installer.NAME / "LOCAL_NOTE.txt").write_text("mine", encoding="utf-8")
        result = installer.install(self.root, replace=True)
        self.assertIsNotNone(result["backup"])
        backup = Path(result["backup"])
        self.assertTrue(backup.is_dir())
        self.assertTrue((backup / "LOCAL_NOTE.txt").is_file(), "备份应保留用户原有文件")
        self.assertFalse((self.root / installer.NAME / "LOCAL_NOTE.txt").exists())

    # ---- 干跑 ----
    def test_dry_run_writes_nothing(self):
        result = installer.install(self.root, dry_run=True)
        self.assertEqual(result["status"], "dry_run_ok")
        self.assertFalse(self.root.exists())

    # ---- 完整性 ----
    def test_source_tamper_detected(self):
        fake = self.tmp / "fake-skill"
        shutil.copytree(SKILL, fake)
        edition = json.loads((fake / "EDITION.json").read_text(encoding="utf-8"))
        (fake / "SKILL.md").write_text("tampered", encoding="utf-8")
        with self.assertRaises(ValueError) as ctx:
            installer.verify_source(fake, edition)
        self.assertIn("哈希", str(ctx.exception))

    def test_missing_source_file_detected(self):
        fake = self.tmp / "fake-skill2"
        shutil.copytree(SKILL, fake)
        edition = json.loads((fake / "EDITION.json").read_text(encoding="utf-8"))
        (fake / "references" / "troubleshooting.md").unlink()
        with self.assertRaises(ValueError) as ctx:
            installer.verify_source(fake, edition)
        self.assertIn("缺失", str(ctx.exception))

    # ---- 符号链接防护（Windows 无权限时跳过）----
    def test_symlink_target_refused(self):
        self.root.mkdir(parents=True, exist_ok=True)
        real = self.tmp / "real"
        real.mkdir()
        link = self.root / installer.NAME
        try:
            link.symlink_to(real, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("当前环境不能创建目录符号链接")
        with self.assertRaises(ValueError) as ctx:
            installer.install(self.root)
        self.assertIn("符号链接", str(ctx.exception))


class EditionConsistencyTests(unittest.TestCase):
    def test_edition_matches_files_on_disk(self):
        """EDITION.json 必须与 skills/ 下实际文件一致（改文件后要重跑 rebuild_skill.py）。"""
        import subprocess

        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "rebuild_skill.py"), "--check"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_declared_counts_match_content(self):
        edition = json.loads((SKILL / "EDITION.json").read_text(encoding="utf-8"))
        skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        caps = edition["capabilities"]
        self.assertEqual(skill_md.count("\n### 模型"), caps["mental_models"])
        research = list((SKILL / "references" / "research").glob("*.md"))
        self.assertEqual(len(research), caps["research_documents"])
        self.assertEqual(edition["public_version"], "1.0.0")


if __name__ == "__main__":
    unittest.main()
