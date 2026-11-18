# Telegram 每日发车 — 交接给 WorkBuddy

> 交接日期：2026-11-19。Koda 原来的云端定时任务（每天 18:00 发一辆车到 4 个 Telegram 频道）连着失败 7 次，主频道最容易失败。现把任务交给 WorkBuddy（九鼎电脑本地）执行。WorkBuddy 跑通后，Koda 停掉自己那边的定时任务，以后每天由 WorkBuddy 发。

## 任务

每天 18:00（北京时间）往 4 个 Telegram 频道各发一辆车（4 张照片 + 文案），从官网 jinbacars.com 选下一辆没发过的车，优先最新的。

## 4 个频道

- 主频道（双语）：@usedcarsdealer99（Used car supermarket），归属老账号 @ChinaUsedCarExpert
- 英文：@JinbaUsedCars（China Used Cars Export），归属新账号 @KinbaAutoExport
- 俄文：@KitayAvtoExport（Авто из Китая — экспорт），归属新账号 @KinbaAutoExport
- 中文：@ZhongGuoErShouChe（中国二手车出口），归属新账号 @KinbaAutoExport
- 投稿机器人：@JinbaCarsBot（id 9202018191），是 4 个频道的管理员（仅发帖 + 编辑权限）

## 发帖方式（优先 Bot API）

机器人是 4 个频道的管理员，所以最可靠的方式是用 Bot API（sendMediaGroup）一次发 4 张照片，不用打开 Telegram 网页，不怕登录掉线。

- 需要 Bot Token：向用户要（用户在手机 Telegram 的 BotFather 里能查到 @JinbaCarsBot 的 token）。Token 只存在电脑本地（例如 .env 或配置文件），绝不要写进仓库、不要提交到 git。
- 用 Bot API 发到 4 个频道：chat_id 直接用 @usedcarsdealer99、@JinbaUsedCars、@KitayAvtoExport、@ZhongGuoErShouChe。
- 备用方式：如果 Bot API 暂时不可用，用电脑浏览器打开 Telegram Web（web.telegram.org），用已登录的 @KinbaAutoExport 发 3 个新频道，用 @ChinaUsedCarExpert 发主频道。如果浏览器没登录，让用户在电脑上扫码登录，不要代填密码、验证码。

## 选车

- 读共享状态文件 `collab/telegram-posting-state.json`（git pull 后最新版），里面 `posted` 列了已发过的库存号。选一辆没在里面的车，优先官网最新的。
- 官网车列表：https://jinbacars.com/en/cars/（英文站），点进车型页拿年份、型号、库存号（JB-xxxxx）、里程（km）、照片（primary + 3 张，共 4 张，地址形如 https://jinbacars.com/uploads/cars/<id>/primary.webp 等）。
- 已发过的（不要重发）：JB-10889、JB-10879、JB-10869、JB-10859、JB-10858、JB-10848、JB-11611、JB-11681。最新发的是 JB-11681（2026-11-18）。下一辆从官网最新里挑没发过的。
- 照片：下载 4 张到电脑本地（建议 `D:\telegram-posting\<JB号>\`），webp 转 jpg（ffmpeg）再发，Telegram 对 webp 有时发不出去。
- 如果官网打不开、没有没发过的车了，就不要发，告诉用户原因，不要重发旧车。

## 文案（每频道一种语言，绝不写价格数字）

- 主频道 @usedcarsdealer99：双语（英文在前，空一行，再俄文）。
- @JinbaUsedCars：只英文。@KitayAvtoExport：只俄文。@ZhongGuoErShouChe：只中文。
- 英文：🚗 <年份> <型号> — Stock <JB-xxxxx> / <里程> km | Full inspection before shipment / 💰 FOB Price on Request — tell us your destination country and we'll quote you / 📲 WhatsApp: +86 18079089999 / 🌐 jinbacars.com / #usedcars #carexport
- 俄文：🚗 <年份> <型号> — Складской № <JB-xxxxx> / <里程，千分位空格，如 26 000> км | Полная проверка перед отправкой / 💰 Цена FOB — по запросу, напишите страну назначения, и мы сделаем предложение / 📲 WhatsApp: +86 18079089999 / 🌐 jinbacars.com / #usedcars #carexport
- 中文：🚗 <年份> <型号> — 库存号 <JB-xxxxx> / <里程> 公里 | 发货前全面检查 / 💰 FOB 价格请询价 — 告诉我们目的地国家，我们给您报价 / 📲 WhatsApp: +86 18079089999 / 🌐 jinbacars.com / #usedcars #carexport
- 铁律：任何帖子都不写价格数字，只写 FOB Price on Request / 价格请询价。
- 只发这 4 个自己的频道，不发别的群、频道，不私聊任何人，不加人。

## 发完之后

- 更新 `collab/telegram-posting-state.json`：在 `posted` 里加一条（stock、model、mileage_km、posted_at、channels 四个频道），并更新 `last_run`，然后 git push 到仓库。
- 告诉用户：发了哪辆车、几点发的、4 个频道各多少订阅者（发完看一眼频道信息）。
- 定时：每天 18:00 发一次。电脑上设个每天 18:00 的定时任务（Windows 任务计划程序）跑这个发帖脚本；或者每天手动跑一次也行，先保证能跑通。

## 试运行与交接条件

- 先手动跑一次（发一辆车到 4 个频道），确认 4 个频道都收到、照片和文案都对，再设每天定时。
- 跑通后在任务单里写清：用的哪种方式（Bot API 还是网页）、几点发的、4 个频道订阅数，并告诉用户。用户确认后，Koda 会停掉自己那边的定时任务（telegram-channel-post-every-2-days），以后就由 WorkBuddy 每天发。
- 如果 Bot API 和网页都发不出去，不要硬试，把报错和截图告诉用户，等用户决定。

## 已知坑（Koda 这边踩过的）

- Telegram 网页（web.telegram.org）经常白屏打不开、登录掉线，Koda 的定时任务连着失败 7 次，主频道最容易失败。Bot API 最稳。
- 主频道 @usedcarsdealer99 归属老账号 @ChinaUsedCarExpert，网页端登录容易掉；Bot API 不用登录，直接发。
- 4 个频道现在都只有 2 个订阅者，发完看一眼订阅数就行，不用管。

## 约定

- 密码、密钥、验证码一律不代填，等用户亲自做。Bot Token 只存电脑本地，绝不进仓库。
- 只改任务单里写明的文件；部署官网仍走 一键部署官网.bat（这个任务不涉及官网部署）。
