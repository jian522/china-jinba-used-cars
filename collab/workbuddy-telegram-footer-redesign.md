# 给 WorkBuddy 的任务：部署电报频道页脚卡片式改版

## 背景

用户要求把官网页脚的电报频道区重新排版：更美观、简洁、大气，方便使用，适配电脑端和手机端。
原先是 5 行纯文字链接（4 个频道 + 投稿机器人），现已改成卡片式。

## 已完成（在仓库 main，commit 924dc38c）

改了 4 个文件，均已推送并逐字节校验通过（rebuild_home_v7.py 仅行尾 CRLF→LF，内容一致）：

1. `scripts/telegram_config.json` — `footer_channels` 增加：
   - 每个频道加 `handle`（@用户名）与 `tag`（语言标签，四语）
   - 新增 `subtitle`（列副标题，四语）
   - 机器人加 `bot_name` / `bot_handle` / `bot_tag`（四语）；`bot_label` 保留作兼容
2. `scripts/telegram_block.py` — 新增 `footer_channels_html(lang)`（卡片式渲染，首页与内页共用），
   `inner_footer_channels()` 改为委托给它；新增 `_fc_text` / `_channel_attrs` 辅助函数。
   链接、点击追踪（`data-track="telegram_click"`）、新标签页、无障碍标注全部保留。
3. `assets/telegram.css` — 新增 `.jb-tg-col` / `.jb-tg-channels` / `.jb-tg-ch` 等卡片样式：
   深色页脚半透明卡片、Telegram 蓝图标圆章、语言标签 pill、投稿机器人橙色强调、
   悬停上浮、键盘焦点橙色描边；手机端（≤600px）卡片通栏、点按区加高；RTL 适配。
4. `scripts/rebuild_home_v7.py` — 首页 `foot_cols` 循环里特殊处理 TELEGRAM 列：
   检测到 `t.me` 链接时调用 `_tg.footer_channels_html(lang)`，不再输出纯文字 `<ul>`。
   其余列渲染完全不动。`foot_cols` 里硬编码的 Telegram 元组仍在，但不再被渲染（留作备用）。

## 新版效果（预览）

预览页在 `~/workspace/goals/jinba-cars-used-car-export-customer-development/hidden_files/telegram-redesign/preview.html`
（已发给用户看效果；它是独立预览文件，不参与构建）：
- 电脑端：页脚五列网格中的 TELEGRAM 列，纵向 5 张卡片（4 频道 + 橙色投稿卡）
- 手机端：单列堆叠，卡片通栏，点按区 56px
- 每张卡：Telegram 图标 + 频道名 + @handle + 语言标签（双语/英文/俄文/中文；机器人为“车商投稿”）

## 请 WorkBuddy 在电脑上做

1. 拉取最新 main（commit 924dc38c 及之后）。
2. 运行一键部署（`一键部署官网.bat` / `scripts/deploy_pages.py`，Cloudflare Pages 项目 `jinba-cars`），
   即 `build_v2.py`（内页）与 `rebuild_home_v7.py`（首页）重建全站。
3. 部署后核对四语首页与任一内页页脚：TELEGRAM 列应为卡片式（不是纯文字链接），
   5 张卡片链接正确（4 个频道 + @JinbaCarsBot），手机端打开页脚卡片通栏可点。
4. 若构建报错，先不要强行上线，把报错贴回 `collab/koda-workbuddy-tasks.md`，等 Koda 修。

## 注意

- 只改页脚 Telegram 列与相关样式；首页引流大横幅（jb-tg banner）与蓝色页脚条（jb-tg-footstrip）未动，
  仍指向旧频道 `t.me/chinausedcarexport`（用户先前决定保留该宣传）。
- 不要从仓库/虚拟机直接部署（仓库可能滞后于电脑，虚拟机 Cloudflare token 看不到 zone 无法清缓存）。
- 二维码仍是占位图，未换真实码。
