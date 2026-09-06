#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""金霸二手车出口站 · 一键全自动管线（车源入库 → 构建 → 验收 → 提交 → 部署 → 索引提交）

覆盖四种场景（按 --mode）：
  ingest   车源采集入库：imports/<batch>/<stock_id>/*.jpg + CSV → vehicles.json + uploads/
           发布门槛（不可跳过）：图片 6–9 张（min-photos 可升不可降）、四语标题齐全、
           首图规范由 ingest_batch.py 校验；不达标自动置 unpublished（待补图/待翻译）。
  build    仅构建：make_thumbs → build_v2(自动补跑 rebuild_home_v7) → verify_ui 验收
  deploy   仅部署：git add/commit → push_api plan/upload/finish（finish 自动触发 IndexNow）
  all      采集入库 + 构建 + 部署 全流程

每一步失败立即退出非零，不进入下一步。用法示例：
  python scripts/auto_pipeline.py --mode ingest --batch 2026-09-che168 --csv imports/2026-09-che168/vehicles.csv
  python scripts/auto_pipeline.py --mode build
  python scripts/auto_pipeline.py --mode deploy --commit-msg "feat: 9月车源批次 + 首页v7"
  python scripts/auto_pipeline.py --mode all --batch <名> --csv <csv> --commit-msg "<msg>"
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable  # 必须由调度方用 Python 3.12.4 启动本脚本


def run(step, cmd, cwd=ROOT, allow_fail=False):
    print(f'\n===== [{step}] {" ".join(str(c) for c in cmd)} =====', flush=True)
    rc = subprocess.run([str(c) for c in cmd], cwd=str(cwd)).returncode
    if rc != 0 and not allow_fail:
        print(f'!! 步骤 {step} 失败（exit {rc}），管线中止。', flush=True)
        sys.exit(rc)
    return rc


def step_ingest(args):
    """车源入库（校验/翻译门槛内建于 ingest_batch.py，不达标自动 unpublished）"""
    run('ingest 预演', [PY, 'scripts/ingest_batch.py', '--batch', args.batch, '--csv', args.csv])
    if args.dry_run:
        print('（--dry-run：预演结束，未写入。去掉 --dry-run 正式入库。）')
        return
    run('ingest 入库', [PY, 'scripts/ingest_batch.py', '--batch', args.batch, '--csv', args.csv, '--commit'])
    if args.unpublish:
        run('ingest 下架旧车', [PY, 'scripts/ingest_batch.py', '--batch', args.batch,
                                '--csv', args.csv, '--commit', '--unpublish', args.unpublish])


def step_build():
    run('thumbs 缩略图', [PY, 'scripts/make_thumbs.py'])
    run('build 全站构建', [PY, 'scripts/build_v2.py'])   # 末尾自动补跑 rebuild_home_v7.py
    run('verify 验收', [PY, 'scripts/verify_ui.py'])


def step_deploy(args):
    # 1) 本地提交（push_api 以本地 HEAD 树为部署基准 —— 9/4 事故教训：资源必须先入 commit）
    run('git add', ['git', 'add', '-A'])
    run('git commit', ['git', 'commit', '-m', args.commit_msg], allow_fail=True)  # 无变更时非0可容忍
    run('git 核验', ['git', 'ls-tree', 'HEAD', 'data/vehicles.json'])
    # 2) GitHub API 部署（唯一通道；finish 成功后自动跑 submit_indexnow.py）
    run('push plan', [PY, 'scripts/push_api.py', 'plan'])
    up_rc = run('push upload', [PY, 'scripts/push_api.py', 'upload', str(args.upload_batch)], allow_fail=True)
    if up_rc != 0:
        run('push upload 重试', [PY, 'scripts/push_api.py', 'upload', str(args.upload_batch)])
    run('push finish', [PY, 'scripts/push_api.py', 'finish', args.commit_msg])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--mode', required=True, choices=['ingest', 'build', 'deploy', 'all'])
    ap.add_argument('--batch', help='imports/<batch> 批次目录名（ingest/all 必填）')
    ap.add_argument('--csv', help='车源 CSV 路径（ingest/all 必填）')
    ap.add_argument('--unpublish', help='可选：本次要下架的旧 stock_id 清单文件（每行一个）')
    ap.add_argument('--commit-msg', default='feat: pipeline update', help='git 提交与部署说明')
    ap.add_argument('--upload-batch', type=int, default=400, help='push_api 每批上传文件数')
    ap.add_argument('--dry-run', action='store_true', help='ingest 仅预演不写入')
    args = ap.parse_args()

    if args.mode in ('ingest', 'all') and not (args.batch and args.csv):
        ap.error('--mode ingest/all 需要 --batch 与 --csv')

    print(f'Python: {PY}')
    if args.mode in ('ingest', 'all'):
        step_ingest(args)
        step_build()
    elif args.mode == 'build':
        step_build()
    if args.mode in ('deploy', 'all'):
        step_deploy(args)
    print('\n===== 管线全部完成 =====')


if __name__ == '__main__':
    main()
