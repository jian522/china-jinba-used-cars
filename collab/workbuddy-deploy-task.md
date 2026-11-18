任务：把 jinbacars.com 官网的 Telegram 推广收尾并部署上线。

背景：
- 你今天已经做了 Telegram 推广模块（jb-tg）：新文件 scripts/telegram_config.json、scripts/telegram_block.py、assets/telegram.css、images/telegram-qr-placeholder.svg；改了 scripts/build_v2.py、scripts/rebuild_home_v7.py、assets/inquiry.js。线上已有这套设计，但 assets/telegram.css 线上 404，因为这 4 个新文件还没 git add，deploy_pages.py 是按 git ls-files 挑文件上传的，漏掉了。
- 另外要在页脚加一列 TELEGRAM（4 个新频道 + 投稿机器人），这是 Koda 那边补的，不在你今天的改动里。

要做的事（按顺序）：
1. git pull（先拉取。Koda 已把他那份 telegram.css 从仓库删掉，现在拉取不会冲突）。
2. git add scripts/telegram_config.json scripts/telegram_block.py assets/telegram.css images/telegram-qr-placeholder.svg（4 个新文件必须进 Git，否则部署漏传）。
3. 在 scripts/rebuild_home_v7.py 里，每个语言的 foot_cols 中 LANGUAGES 那一项后面加一行（注意：你今天改过这个脚本的结构，先核对 LANGUAGES 那行的位置，不要硬套行号）：
en：
    ('TELEGRAM', [('Used car supermarket', 'https://t.me/usedcarsdealer99'), ('China Used Cars Export', 'https://t.me/JinbaUsedCars'), ('Авто из Китая — экспорт', 'https://t.me/KitayAvtoExport'), ('中国二手车出口', 'https://t.me/ZhongGuoErShouChe'), ('List your car — @JinbaCarsBot', 'https://t.me/JinbaCarsBot')]),
zh：
    ('电报频道', [('Used car supermarket', 'https://t.me/usedcarsdealer99'), ('China Used Cars Export', 'https://t.me/JinbaUsedCars'), ('Авто из Китая — экспорт', 'https://t.me/KitayAvtoExport'), ('中国二手车出口', 'https://t.me/ZhongGuoErShouChe'), ('发车投稿 — @JinbaCarsBot', 'https://t.me/JinbaCarsBot')]),
ru：
    ('TELEGRAM', [('Used car supermarket', 'https://t.me/usedcarsdealer99'), ('China Used Cars Export', 'https://t.me/JinbaUsedCars'), ('Авто из Китая — экспорт', 'https://t.me/KitayAvtoExport'), ('中国二手车出口', 'https://t.me/ZhongGuoErShouChe'), ('Разместить авто — @JinbaCarsBot', 'https://t.me/JinbaCarsBot')]),
ar：
    ('تيليغرام', [('Used car supermarket', 'https://t.me/usedcarsdealer99'), ('China Used Cars Export', 'https://t.me/JinbaUsedCars'), ('Авто из Китая — экспорт', 'https://t.me/KitayAvtoExport'), ('中国二手车出口', 'https://t.me/ZhongGuoErShouChe'), ('اعرض سيارتك — @JinbaCarsBot', 'https://t.me/JinbaCarsBot')]),
（4 个语言的频道链接都一样，只有列标题和机器人那行的文案不同。）
4. 重新生成四个首页（en/zh/ru/ar），核对页脚有 TELEGRAM 列（5 列）且 jb-tg 推广还在。
5. 运行 一键部署官网.bat（scripts/deploy_pages.py）部署到 Cloudflare Pages 项目 jinba-cars 并清缓存。
6. 核对线上 https://jinbacars.com/{en,zh,ru,ar}/：页脚有 TELEGRAM 列（4 频道 + Bot），jb-tg 推广板块有样式（assets/telegram.css 能打开，不再 404）。

注意：不要改动其他文件；不要从仓库部署（仓库版是旧的）；部署前确认第 2 步的 git add 已做；如果 rebuild_home_v7.py 里的 foot_cols 结构和上面说的不一样，先按实际结构加。
