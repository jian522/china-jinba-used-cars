#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""金霸网站部署到 Cloudflare Pages（Direct Upload，替代 push_api.py 的 GitHub Pages 路线）。

用法：
    python scripts/deploy_pages.py            # 部署当前 git 已跟踪的静态文件
    python scripts/deploy_pages.py --skip-stage   # 跳过暂存，直接重传 _pages_deploy/site

前提：
  - Token 在 .workbuddy/cf_token.txt（Pages Write 权限，项目 jinba-cars）
  - 代理 127.0.0.1:7890 可用
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
STAGE = ROOT / "_pages_deploy" / "site"
TOKEN_FILE = ROOT / ".workbuddy" / "cf_token.txt"
NODE = r"C:/Users/Administrator/.workbuddy/binaries/node/versions/22.22.2-2/node.exe"
WRANGLER = r"C:/Users/Administrator/node_modules/wrangler/bin/wrangler.js"
ACCOUNT = "0cd64536d2bc18ae46651a0a2636e1ff"
PROJECT = "jinba-cars"


def stage() -> None:
    """按 null 分隔清单复制 git 已跟踪的部署文件（排除脚本/文档/缓存）。"""
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True)
    keep = []
    for rel in out.stdout.split(b"\0"):
        rel2 = rel.decode("utf-8", "ignore")
        low = rel2.lower()
        if not rel2 or rel2.startswith(("scripts/", ".workbuddy/", "ZCode_Workspacecacheuv/", "_pages_deploy/", "_preview/")) \
                or low.endswith((".md", ".py", ".pdf", ".pyc", ".sh", ".bat")):
            continue
        keep.append(rel2)
    print(f"STAGE {len(keep)} files", flush=True)

    import shutil
    if STAGE.exists():
        # 不删旧文件，直接按清单覆盖复制（Pages 部署以本次上传为准，多出的旧文件仅在文件删除时才需要清理）
        pass
    for rel in keep:
        src, dst = ROOT / rel, STAGE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    size = sum(f.stat().st_size for f in STAGE.rglob("*") if f.is_file())
    print(f"STAGED size={size/1024/1024:.1f}MB", flush=True)


def deploy() -> int:
    env = {"PATH": r"C:/Windows/System32",
           "CLOUDFLARE_API_TOKEN": TOKEN_FILE.read_text(encoding="utf-8").strip(),
           "CLOUDFLARE_ACCOUNT_ID": ACCOUNT,
           "HTTPS_PROXY": "http://127.0.0.1:7890", "HTTP_PROXY": "http://127.0.0.1:7890"}
    r = subprocess.run(
        [NODE, WRANGLER, "pages", "deploy", ".", "--project-name", PROJECT,
         "--branch", "main", "--commit-dirty=true"],
        cwd=STAGE, capture_output=True, text=True, env=env, timeout=3600)
    print((r.stdout or "")[-1500:], flush=True)
    if r.returncode != 0:
        print("ERR " + (r.stderr or "")[-800:], flush=True)
    return r.returncode


if __name__ == "__main__":
    if "--skip-stage" not in sys.argv:
        stage()
    sys.exit(deploy())
