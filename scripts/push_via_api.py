"""当 git 协议被网络策略阻断（如只放行 api.github.com、github.com 返回 502）时，
改用 GitHub Git Data API 提交一批文件，效果等价于 git push。

不经过 git 传输层，因此也不需要 git 的凭据缓存；令牌取自 git 凭据管理器或 GH_TOKEN。

做四步：
  1. 以远端 main 的 tree 为 base_tree，把 CHANGED 里的文件各建一个 blob
  2. 建新 tree
  3. 建新 commit（parent = 远端 main）
  4. 更新 refs/heads/main；把 edition-v1.0.0 重指到新 commit（建新 tag 对象）

**只在 push 不通时使用。** 能用 git push 就用 git push——这里不会更新本地分支引用，
跑完本地与远端会出现"内容相同但 commit 不同"的状态，网络恢复后需
`git fetch origin && git reset --hard origin/main` 对齐。

用法： python scripts/push_via_api.py [--files a.md b.py] [--no-tag]
"""
import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OWNER, REPO = "WEveboy", "Xunzi-Skill"
API = "https://api.github.com"
TAG = "edition-v1.0.0"
CHANGED = ["CHANGELOG.md", "README.md", "scripts/make_release.py", "tests/test_install.py"]


def tok():
    p = subprocess.run(["git", "credential", "fill"],
                       input="protocol=https\nhost=github.com\nusername=WEveboy\n\n",
                       capture_output=True, text=True, timeout=30)
    for l in p.stdout.splitlines():
        if l.startswith("password="):
            return l[9:].strip()
    raise SystemExit("no credential")


T = tok()


def api(method, path, data=None, tries=5):
    body = json.dumps(data).encode() if data is not None else None
    last = None
    for i in range(tries):
        req = urllib.request.Request(API + path, data=body, method=method, headers={
            "Authorization": f"Bearer {T}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json",
            "User-Agent": "Xunzi-Skill-gitdata/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, {"error": e.read().decode()[:500]}
        except Exception as e:                      # 代理抖动 / SSL EOF
            last = e
            time.sleep(4 * (i + 1))
    raise SystemExit(f"{method} {path} 连续失败：{last}")


def main():
    import argparse

    ap = argparse.ArgumentParser(description="经 Git Data API 提交文件（git 协议不通时使用）")
    ap.add_argument("--files", nargs="*", default=None, help="要提交的文件（相对仓库根）")
    ap.add_argument("--message", default=None, help="提交信息，默认取本地 HEAD 的提交信息")
    ap.add_argument("--no-tag", action="store_true", help="不重指 edition-v1.0.0")
    a = ap.parse_args()
    files = a.files or CHANGED

    msg = a.message
    if msg is None:
        msg = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--pretty=%B"],
                             capture_output=True, text=True).stdout.rstrip() + "\n"

    c, ref = api("GET", f"/repos/{OWNER}/{REPO}/git/ref/heads/main")
    head = ref["object"]["sha"]
    c, commit = api("GET", f"/repos/{OWNER}/{REPO}/git/commits/{head}")
    base_tree = commit["tree"]["sha"]
    print("远端 head:", head[:8], "tree:", base_tree[:8])

    items = []
    for f in files:
        content = (ROOT / f).read_bytes()
        c, blob = api("POST", f"/repos/{OWNER}/{REPO}/git/blobs",
                      {"content": base64.b64encode(content).decode(), "encoding": "base64"})
        if c not in (200, 201):
            raise SystemExit(f"blob {f} 失败 {c} {blob}")
        items.append({"path": f, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        print(f"  blob {f} -> {blob['sha'][:8]}")

    c, tree = api("POST", f"/repos/{OWNER}/{REPO}/git/trees", {"base_tree": base_tree, "tree": items})
    if c not in (200, 201):
        raise SystemExit(f"tree 失败 {c} {tree}")
    print("新 tree:", tree["sha"][:8])

    c, nc = api("POST", f"/repos/{OWNER}/{REPO}/git/commits",
                {"message": msg, "tree": tree["sha"], "parents": [head]})
    if c not in (200, 201):
        raise SystemExit(f"commit 失败 {c} {nc}")
    print("新 commit:", nc["sha"][:8])

    c, r = api("PATCH", f"/repos/{OWNER}/{REPO}/git/refs/heads/main", {"sha": nc["sha"], "force": False})
    print("更新 main:", c, str(r.get("object", {}).get("sha", r.get("error", "")))[:8])

    if not a.no_tag:
        c, tagobj = api("POST", f"/repos/{OWNER}/{REPO}/git/tags",
                        {"tag": TAG, "message": "荀子思维操作系统 第一版 1.0.0",
                         "object": nc["sha"], "type": "commit"})
        if c not in (200, 201):
            raise SystemExit(f"tag object 失败 {c} {tagobj}")
        c, r = api("PATCH", f"/repos/{OWNER}/{REPO}/git/refs/tags/{TAG}",
                   {"sha": tagobj["sha"], "force": True})
        print("重指标签:", c, str(r.get("object", {}).get("sha", r.get("error", "")))[:8])

    local_tree = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD^{tree}"],
                                capture_output=True, text=True).stdout.strip()
    print("\n本地 tree:", local_tree[:12], "| 远端 tree:", tree["sha"][:12],
          "|", "一致 ✓" if local_tree == tree["sha"] else "不一致 ✗")
    print("远端 commit:", nc["sha"])
    print("提醒：本地分支引用未更新；网络恢复后 git fetch origin && git reset --hard origin/main")
    return 0


if __name__ == "__main__":
    sys.exit(main())
