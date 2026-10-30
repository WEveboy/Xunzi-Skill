#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""用 GitHub API 创建 edition-v1.0.0 发行并上传 dist/ 资产，然后逐个下载核验 SHA256。

令牌只从环境变量读，不接受命令行参数（避免进 shell 历史），也绝不打印。

用法（Git Bash）：
    export GH_TOKEN=<你的 fine-grained PAT>
    python scripts/publish_release.py                 # 建发行 + 上传 + 核验
    python scripts/publish_release.py --dry-run       # 只检查令牌与资产，不发请求
    python scripts/publish_release.py --verify-only   # 只下载核验已有资产

所需令牌权限：Contents: Read and write（含 Releases 需要 repo 级 Contents 写权限）。
"""
import argparse
import hashlib
import json
import os
import subprocess
import time
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

OWNER = "WEveboy"
REPO = "Xunzi-Skill"
TAG = "edition-v1.0.0"
TITLE = "荀子思维操作系统 · 第一版 1.0.0"
ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
API = "https://api.github.com"
UA = "Xunzi-Skill-release-script/1.0"


def token():
    """优先环境变量，其次向 git 凭据管理器要（令牌已在 GCM 里时不经过磁盘与日志）。"""
    for k in ("GH_TOKEN", "GITHUB_TOKEN"):
        v = os.environ.get(k)
        if v and v.strip():
            return v.strip()
    try:
        p = subprocess.run(
            ["git", "credential", "fill"],
            input=f"protocol=https\nhost=github.com\nusername={OWNER}\n\n",
            capture_output=True, text=True, timeout=30,
        )
        for line in p.stdout.splitlines():
            if line.startswith("password=") and len(line) > 12:
                print("（令牌来源：git 凭据管理器）")
                return line[len("password="):].strip()
    except (OSError, subprocess.SubprocessError):
        pass
    sys.exit("缺少令牌：export GH_TOKEN=<PAT>（需 Contents: Read and write），"
             "或先用 git push 让凭据管理器存一次")


def api(method, path, tok, data=None, raw=None, ctype="application/json", tries=5):
    """带重试：代理偶发 502/SSL EOF 时不要整个发布流程前功尽弃。"""
    url = path if path.startswith("http") else API + path
    headers = {
        "Authorization": f"Bearer {tok}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    }
    if raw is not None:
        body = raw
        headers["Content-Type"] = ctype
    elif data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    else:
        body = None
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=300) as r:
                payload = r.read()
                return r.status, (json.loads(payload) if payload else {})
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:600]
            return e.code, {"error": detail}
        except Exception as e:  # 网络层抖动（502 / SSL EOF / 超时）
            last = e
            print(f"    重试 {i + 1}/{tries}（{type(e).__name__}）")
            time.sleep(4 * (i + 1))
    return 0, {"error": f"连续失败：{last}"}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def assets():
    order = [
        f"xunzi-perspective-Codex-1.0.0.zip",
        f"dsh-xunzi-perspective-1.0.0.tgz",
        f"xunzi-perspective-DeepSeek-1.0.0.zip",
        f"xunzi-perspective-1.0.0-source.zip",
        "SHA256SUMS.txt",
    ]
    out = [DIST / n for n in order]
    missing = [p.name for p in out if not p.is_file()]
    if missing:
        sys.exit("dist/ 缺文件：" + ", ".join(missing) + "\n先运行 python scripts/make_release.py")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--draft", action="store_true", help="建为草稿，不公开")
    a = ap.parse_args()

    tok = token()
    files = assets()

    if a.dry_run:
        code, me = api("GET", "/user", tok)
        print("令牌可用：" if code == 200 else f"令牌不可用（{code}）")
        if code == 200:
            print("  身份：", me.get("login"))
        code, repo = api("GET", f"/repos/{OWNER}/{REPO}", tok)
        print("仓库：", f"{code} " + (repo.get("full_name", repo.get("error", "")) if code == 200 else repo.get("error", "")))
        if code == 200:
            print("  权限：", repo.get("permissions"))
        print("待上传资产：")
        for p in files:
            print(f"  {p.name:44s} {p.stat().st_size/1024:9.1f} KB  {sha256(p)[:16]}…")
        return 0

    if not a.verify_only:
        # 1. 建发行（已存在则复用）
        body = (ROOT / "docs" / "RELEASE_NOTES-v1.0.0.md").read_text(encoding="utf-8")
        code, rel = api("POST", f"/repos/{OWNER}/{REPO}/releases", tok, data={
            "tag_name": TAG, "name": TITLE, "body": body,
            "draft": a.draft, "prerelease": False,
        })
        if code == 422:  # 已存在
            code, rel = api("GET", f"/repos/{OWNER}/{REPO}/releases/tags/{TAG}", tok)
            print("发行已存在，复用：", rel.get("html_url"))
        elif code not in (200, 201):
            sys.exit(f"创建发行失败 {code}: {rel.get('error')}")
        else:
            print("已创建发行：", rel.get("html_url"))

        upload_url = rel["upload_url"].split("{")[0]
        existing = {x["name"] for x in rel.get("assets", [])}

        # 2. 上传资产
        for p in files:
            if p.name in existing:
                print(f"  跳过（已存在）：{p.name}")
                continue
            with open(p, "rb") as f:
                payload = f.read()
            ctype = "application/zip" if p.suffix == ".zip" else (
                "application/gzip" if p.suffix == ".tgz" else "text/plain; charset=utf-8")
            code, res = api("POST", f"{upload_url}?name={urllib.parse.quote(p.name)}", tok,
                            raw=payload, ctype=ctype)
            if code in (200, 201):
                print(f"  ✓ 已上传 {p.name}  ({res.get('size', 0)/1024:.1f} KB)")
            else:
                sys.exit(f"上传 {p.name} 失败 {code}: {res.get('error')}")

    # 3. 逐个下载核验
    code, rel = api("GET", f"/repos/{OWNER}/{REPO}/releases/tags/{TAG}", tok)
    if code != 200:
        sys.exit(f"读取发行失败 {code}: {rel.get('error')}")
    remote = {x["name"]: x for x in rel.get("assets", [])}
    print(f"\n== 下载核验（{len(remote)} 个资产）==")
    bad = 0
    for p in files:
        info = remote.get(p.name)
        if not info:
            print(f"  ✗ 远端缺 {p.name}")
            bad += 1
            continue
        req = urllib.request.Request(info["browser_download_url"], headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=300) as r:
            data = r.read()
        local, got = sha256(p), hashlib.sha256(data).hexdigest()
        if local == got and len(data) == p.stat().st_size:
            print(f"  ✓ {p.name}  {len(data)/1024:.1f} KB  哈希一致")
        else:
            print(f"  ✗ {p.name}  哈希或大小不符（local {local[:12]} vs remote {got[:12]}）")
            bad += 1
    print(f"\n发行页：{rel.get('html_url')}")
    print("结果：", "全部核验通过" if bad == 0 else f"{bad} 项未通过")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
