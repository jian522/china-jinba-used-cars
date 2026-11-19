# Koda ↔ WorkBuddy 协作任务单

> 用途：Koda（云端）与 WorkBuddy（九鼎电脑本地）协作的任务交接单。
> Koda 把需要在电脑上做的事写在这里，WorkBuddy 在电脑上执行，执行完把结果写回这里（或直接提交到仓库）。
> 使用方法：WorkBuddy 每次开始工作前先读这个文件；Koda 有新任务时更新它并告诉用户。

## 进行中的任务

### 3. 电报频道页脚卡片式改版部署（2026-11-19，待部署）
- 详见：`workbuddy-telegram-footer-redesign.md`（同一目录，含完整说明与核对清单）
- 改动（已推送到 main，commit 924dc38c）：页脚 TELEGRAM 列由 5 行纯文字链接改成卡片式（4 频道 + 橙色投稿卡，带图标/@handle/语言标签），桌面端列内纵向、手机端通栏可点；改了 `scripts/telegram_config.json`、`scripts/telegram_block.py`、`assets/telegram.css`、`scripts/rebuild_home_v7.py`。
- 请 WorkBuddy：拉取最新 main → 一键部署官网.bat 重建全站并部署 → 核对四语首页与内页页脚 TELEGRAM 列为卡片式、链接正确、手机端通栏可点。

## 已完成的任务

### 1. 官网 Telegram 收尾部署（2026-11-18，已完成）
- 详见：`workbuddy-deploy-task.md`（同一目录，含完整执行记录）
- 结果：git pull（`-s ours` 同步分叉历史）→ 4 个新文件已 git add → rebuild_home_v7.py 四语 foot_cols 加 TELEGRAM 列（4 频道 + @JinbaCarsBot）→ 重建四语首页（页脚 5 列）→ 部署 CF Pages（Uploaded 6 files）。
- 线上核对：assets/telegram.css 从 404 → HTTP 200；en/zh/ru/ar 首页页脚均 5 列含 TELEGRAM（4 频道各 1 次 + Bot 2 次），jb-tg 横幅 + 页脚卡片条齐全。
- 已单独提交 `a6142a338`，并备份到 GitHub（merge commit `91c2b7d8b`）。

### 2. 车型页/列表页加 TELEGRAM 列（2026-11-18 21:20 新增，已完成）
- 详见：`workbuddy-deploy-task.md` 末尾「新增任务」段
- 结果：4 频道 + Bot 收进集中配置 `scripts/telegram_config.json`（footer_channels 字段）；共享模块 `telegram_block.py` 新增 `inner_footer_channels(lang)`；`build_v2.py` 共用 footer 模板插入第 5 列（一次生效全站）。
- 重建：全站内页（1660 车型页 + 列表页），抽样四语 cars 列表页 + 车型页 8 处均含 TELEGRAM 列（4 频道 + Bot）且 jb-tg 卡片在；三闸全过（verify_ui 62/62、photo_check 0 违规、validate_inventory 0/0）。
- 部署：CF Pages 上传成功（Deployment complete，https://82527b60.jinba-cars.pages.dev）。修复 `deploy_pages.py` 直连重试触发条件（`Failed to upload files` / `UND_ERR_SOCKET` 未匹配导致代理失败后不重试，全站 1.1 万文件上传必挂）。
- 线上核对：en/cars/、en/cars/675/、zh/cars/、ar/cars/ 页脚均含 TELEGRAM 列（4 频道各 1 + Bot 1 + placement 追踪），jb-tg 卡片正常；真实访客请求 cf-cache-status MISS 拿到新内容。
- ⚠️ 缓存清理仍 HTTP 401（cfut_ token 无 Zone:Cache Purge 权限，项目已知限制），不影响上线。
- 待提交：本次源码改动（build_v2.py / telegram_config.json / telegram_block.py / deploy_pages.py / collab/*.md）尚未 commit（用户未要求提交）。

## 约定

- Koda 只写任务，不直接改电脑上的文件；WorkBuddy 只改任务单里写明的文件。
- 部署一律走电脑上的 一键部署官网.bat（Cloudflare Pages 项目 jinba-cars），不要从仓库部署。
- 涉及密码、密钥、验证码的步骤，WorkBuddy 停下来等用户亲自做，不要代填。
- 每次执行完，在“已完成的任务”里写清：做了什么、结果、线上核对情况。
