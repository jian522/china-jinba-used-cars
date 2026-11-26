# Koda ↔ WorkBuddy 协作任务单

> 用途：Koda（云端）与 WorkBuddy（九鼎电脑本地）协作的任务交接单。
> Koda 把需要在电脑上做的事写在这里，WorkBuddy 在电脑上执行，执行完把结果写回这里（或直接提交到仓库）。
> 使用方法：WorkBuddy 每次开始工作前先读这个文件；Koda 有新任务时更新它并告诉用户。

## 进行中的任务

### 3. Threads 补发 4 台车（2026-11-26 新增，Koda 核实后交办）
- 背景：Koda 核实了 11 月 21、23、24、25 日的 Threads 发帖。WorkBuddy 每天 18:30 都在发，但因为仓库里的状态文件是旧的（Koda 的 18:00 定时任务只更新本地文件，没推到仓库），你没看到当天 Telegram 发的是哪台车，所以按自己的主题轮换挑了别的车；11 月 24 日那天还因为 Chrome 没登录而没发成。已核实：11 月 21 日发了 JB-11529（和当天 Telegram 同车）；11 月 23 日发了 JB-11723（不是当天 Telegram 车 JB-11774，那台是 11 月 22 日发的）；11 月 24 日没发；11 月 25 日发了 JB-11898（不是当天 Telegram 车 JB-11919）；11 月 26 日发了 JB-11930（不是当天 Telegram 车 JB-11744）。
- 补发清单（以下 4 台还没上过 Threads，从 11 月 27 日 18:30 开始，每天发一台，不要一天发多台，按顺序）：
  1. JB-11764 — 2025 BYD Seagull 305km Edition，20,000 km（11 月 22 日 Telegram 车，网站 car 687）
  2. JB-11754 — 2021 BYD Dolphin 405km Fashion，44,000 km（11 月 24 日 Telegram 车，网站 car 686）
  3. JB-11919 — 2025 BYD Seagull 305km Vitality，51,000 km（11 月 25 日 Telegram 车）
  4. JB-11744 — 2022 BYD Yuan PLUS 430KM Premium，74,000 km（11 月 26 日 Telegram 车，网站 car 685）
- 每台的文案（英文，4 张图 + 这段文案，不写任何价格数字，FOB Price on Request）：
  - JB-11764：🔥 EV Series / 🚗 2025 BYD Seagull 305km Edition — Stock JB-11764 / 20,000 km | Full inspection before shipment / 💰 FOB Price on Request — tell us your destination country and we'll quote you / 📲 WhatsApp: +86 18079089999 / 🌐 jinbacars.com / #usedcars #carexport
  - JB-11754：🔥 EV Series / 🚗 2021 BYD Dolphin 405km Fashion — Stock JB-11754 / 44,000 km | Full inspection before shipment / 💰 FOB Price on Request — tell us your destination country and we'll quote you / 📲 WhatsApp: +86 18079089999 / 🌐 jinbacars.com / #usedcars #carexport
  - JB-11919：🔥 EV Series / 🚗 2025 BYD Seagull 305km Vitality — Stock JB-11919 / 51,000 km | Full inspection before shipment / 💰 FOB Price on Request — tell us your destination country and we'll quote you / 📲 WhatsApp: +86 18079089999 / 🌐 jinbacars.com / #usedcars #carexport
  - JB-11744：🔥 EV Series / 🚗 2022 BYD Yuan PLUS 430KM Premium — Stock JB-11744 / 74,000 km | Full inspection before shipment / 💰 FOB Price on Request — tell us your destination country and we'll quote you / 📲 WhatsApp: +86 18079089999 / 🌐 jinbacars.com / #usedcars #carexport
- 照片：从 jinbacars.com 该车详情页取 primary + photo-02/03/04（和平时一样，发前核对详情页 + 图片能打开）。
- 发完每台：先 git pull，再把记录写进 collab/telegram-posting-state.json 的 threads_posted（带帖子链接），再 push。不要重复发已在 threads_posted 里的车：JB-11661、JB-11549、JB-11529、JB-11774、JB-11723、JB-11898、JB-11930。
- 状态文件已由 Koda 合并并推回仓库（2026-11-26 21:00 左右，本地 + 仓库两边合一）。以后每天 18:30 前先 git pull 再读状态文件，就能看到当天 Telegram 的车。

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
