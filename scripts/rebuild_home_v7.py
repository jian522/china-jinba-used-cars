#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Jinba Home v7 — 2026-09 redesign (Ardot https://ardot.tencent.com/file/722844951625143)

Deep navy #0A1628 + brand orange #FF6B2C. Generates en/zh/ru/ar homepages with:
TopBar / Nav / Hero+statband / Featured stock x4 / Why (navy) / Process x4 /
Markets x3 / Client stories / FAQ / Bottom CTA / Footer.

Data-driven rules (per handover brief):
  * inventory count = number of published vehicles in data/vehicles.json
  * featured 4 cards auto-selected: published, >=6 photos, files exist on disk,
    no duplicate primary (per data/photo-audit.json), newest id first
  * hero image = published car with most real photos (fallback: images/og-image.jpg)
All previous paths are backed up to .workbuddy/backup_home/ before overwrite.
Usage: python scripts/rebuild_home_v7.py
"""
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(r'D:\二手车出口网站\scripts')))
from seo_content import CAR_COPY

ROOT = Path(r'D:\二手车出口网站')
BACKUP = ROOT / '.workbuddy' / 'backup_home'
PHOTO_AUDIT = ROOT / 'data' / 'photo-audit.json'
DOMAIN = 'https://jinbacars.com'
WA = 'https://wa.me/8618079089999'
EMAIL = 'jian5222@gmail.com'
GA_ID = 'G-3SVJ44HVKC'
VERIF = 'hpe_PNYRQogsN199OCEqggbxRhlvZKMk3oylavUxvK0'
PHONE_DISPLAY = '+86 180 7908 9999'

LANGS = ['en', 'zh', 'ru', 'ar']
N = {'zh': '/zh/', 'en': '/en/', 'ru': '/ru/', 'ar': '/ar/'}
HREFLANG = {'en': 'en', 'zh': 'zh', 'ru': 'ru', 'ar': 'ar'}

# ---------------------------------------------------------------- load data
data = json.loads((ROOT / 'data' / 'vehicles.json').read_text(encoding='utf-8'))
pub = [v for v in data if v.get('status') == 'published']
pub_ids = {v['id'] for v in pub}
PUBLISHED_N = len(pub)

dup_primaries = set()
if PHOTO_AUDIT.exists():
    audit = json.loads(PHOTO_AUDIT.read_text(encoding='utf-8'))
    for group in audit.get('duplicate_primary_groups', []):
        for vid in group[1:]:  # keep the first member, flag the rest
            dup_primaries.add(vid)


def disk_ok(v):
    return v.get('photos') and os.path.isfile(ROOT / v['photos'][0].lstrip('/'))


featured_pool = [v for v in sorted(pub, key=lambda x: -x['id'])
                 if len(v.get('photos', [])) >= 6 and disk_ok(v)
                 and v['id'] not in dup_primaries]
if len(featured_pool) < 4:
    featured_pool = [v for v in sorted(pub, key=lambda x: -x['id'])
                     if len(v.get('photos', [])) >= 6 and disk_ok(v)]
FEATURED = featured_pool[:4]

hero_pool = [v for v in sorted(pub, key=lambda x: -len(x.get('photos', [])))
             if disk_ok(v)]
HERO = hero_pool[0] if hero_pool else None
HERO_IMG = HERO['photos'][0] if HERO else '/images/og-image.jpg'
# OG image prefers a >=6-photo car so shares look complete
og_pool = [v for v in featured_pool if v.get('photos')]
OG_IMG = (og_pool[0] if og_pool else HERO)['photos'][0] if (og_pool or HERO) else '/images/og-image.jpg'


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def fmt_int(n):
    return f'{n:,}'


def stat_val(v):
    return fmt_int(v) if v > 99 else str(v)


STAT_INV = stat_val(PUBLISHED_N)
STAT_EXPORTED = '1,900+'
STAT_COUNTRIES = '14'

FOUR_LANG = ['English', '简体中文', 'Русский', 'العربية']

# ---------------------------------------------------------------- i18n copy
L = {
 'en': {
  'title': 'Used Cars from China for Export | Jinba Cars',
  'desc': f'Browse {STAT_INV} used vehicles from China for export. Compare stock, photos, price and mileage, then request a written quotation for your destination port.',
  'topbar_l': 'Licensed used-car exporter · Shenzhen, China · Since 2016',
  'nav': [('Inventory', '/en/cars/'), ('Markets', '/en/markets/kenya/'), ('Process', '#process'), ('About', '/en/about/')],
  'nav_wa': 'WhatsApp',
  'lang_on': 'EN', 'lang_names': FOUR_LANG, 'self_name': 'English',
  'badge': f'{STAT_INV} vehicles in stock · ready to ship',
  'h1': 'Drive China\u2019s best value cars to your market',
  'hero_sub': 'Fleet-grade inspected vehicles from China\u2019s top brands — BYD, Haval, Jetour and more — with FOB/CIF pricing, full export documents and door-to-deck coordination.',
  'cta_browse': 'Browse inventory', 'cta_how': 'How buying works',
  'stats': [(STAT_INV, 'vehicles in stock'), (STAT_EXPORTED, 'cars exported'),
            (STAT_COUNTRIES, 'destination countries'), ('<em>25</em>', 'days to Mombasa avg.')],
  'feat_kicker': 'FEATURED STOCK', 'feat_h2': 'Fresh arrivals, export-ready',
  'view_all': f'View all {STAT_INV} vehicles →',
  'fob': 'FOB Shenzhen', 'quote': 'Request quote',
  'why_kicker': 'WHY JINBA CARS', 'why_h2': 'Trade with a partner, not a listing site',
  'why_sub': 'We inspect, document and ship every vehicle ourselves — one accountable team from the yard in China to your port.',
  'why_main_kicker': 'QUALITY ASSURANCE', 'why_main_h3': '168-point inspection before every listing',
  'why_main_p': 'Every vehicle passes a 168-point mechanical, structural and cosmetic inspection. Anything with major accident, flood or fire history never reaches this page.',
  'bento': [('168', 'check points'), ('6+', 'photos per listing'), ('24h', 'video walkaround')],
  'trade_kicker': 'SHIPPING TERMS',
  'why_cards': [
    ('PAPERWORK', 'Export paperwork, done right',
     'Commercial invoice, packing list, customs declaration, B/L, deregistration certificate and certificate of origin — prepared and tracked by our own documentation desk.'),
    ('PAYMENT', 'Secure T/T & L/C payment',
     '30% deposit to reserve, balance against B/L copy. Escrow-style milestones, third-party inspection welcome before funds move.'),
    ('LOGISTICS', 'Shipping to 14 countries',
     'Established RoRo and container lanes to Mombasa, Lagos, Lomé, Jebel Ali, Aqaba, Umm Qasr, Vladivostok and more — 18\u201335 days typical.'),
  ],
  'proc_kicker': 'HOW IT WORKS', 'proc_h2': 'From selection to shipping, end to end',
  'proc_cta': 'Start your order',
  'steps': [
    ('01', 'Tell us your needs', 'Send model, budget and destination port — we reply with a shortlist and FOB/CIF quotes within 24 hours.'),
    ('02', 'Inspect & reserve', 'Review photos, videos and the 168-point report; reserve with a deposit and we lock the vehicle for you.'),
    ('03', 'Documents & customs', 'We prepare export documents, book the vessel and handle China-side customs clearance.'),
    ('04', 'Ship & track', 'Load-out, B/L issued, then weekly tracking updates until the vessel reaches your port.'),
  ],
  'mkt_kicker': 'WHERE WE SHIP', 'mkt_h2': 'Established lanes, local know-how',
  'markets': [
    ('AFRICA', 'Kenya · Nigeria · Tanzania · Ghana',
     'Duty structures, age limits and inspection regimes per country — we ship with the paperwork your customs broker expects.', 'navy'),
    ('MIDDLE EAST', 'UAE · Jordan · Iraq',
     'Gulf-spec familiarity, RoRo and container options via Jebel Ali and Aqaba, Arabic-speaking support on request.', ''),
    ('EURASIA', 'Russia · Kazakhstan · Kyrgyzstan',
     'Overland and sea routings, EAC documentation guidance, Russian-speaking advisors from quote to arrival.', ''),
  ],
  'story_kicker': 'CLIENT STORIES', 'stories_h2': 'Trusted by importers on three continents',
  'stories': [
    ('Third batch this year — inspection reports matched what arrived on the dock, down to the tyre tread. That is why we keep ordering.',
     'Daniel Otieno', 'Fleet importer · Nairobi, Kenya', ''),
    ('Documents cleared Russian customs without a single revision. First importer I have worked with who sends the B/L before I ask.',
     'Alexey Voronov', 'Dealer · Vladivostok, Russia', 'peach'),
  ],
  'faq_kicker': 'FAQ', 'faq_h2': 'Questions buyers ask first',
  'faq_side': 'Payment, shipping time, inspection — the four questions below cover 90% of first enquiries. Anything else, just message us.',
  'faq_side_btn': 'Ask on WhatsApp',
  'faq': [
    ('How is payment arranged?',
     'T/T bank transfer or L/C. Standard terms: 30% deposit to reserve the vehicle, 70% balance against a copy of the Bill of Lading. Third-party inspection is welcome before funds move.'),
    ('How long is shipping?',
     'RoRo and container lanes cover the Middle East, Africa, Central Asia and Russia — typically 18\u201335 days depending on the destination port. Mombasa averages 25 days.'),
    ('Can I inspect before paying?',
     'Yes. Every listing carries 6+ real photos, and we provide a 24-hour video walkaround on request. Independent third-party inspection in Shenzhen is also supported.'),
    ('Which documents do I receive?',
     'Commercial invoice, packing list, export customs declaration, Bill of Lading, vehicle deregistration certificate and certificate of origin — the full set your broker needs to clear import.'),
  ],
  'cta_h2': 'Reserve your first shipment this month',
  'cta_p': 'Send us the models and quantities you need — we will hold stock and prepare a 7-day valid quotation with FOB and CIF options.',
  'cta_wa': 'Chat on WhatsApp', 'cta_email': EMAIL,
  'cta_note': 'Quotes valid for 7 days · FOB / CIF · English, Russian & Arabic support',
  'foot_about': 'Licensed used-car exporter in Shenzhen, China since 2016. Inspected stock, complete export documents and established shipping lanes to 14 countries.',
  'foot_cols': [
    ('INVENTORY', [('All vehicles', '/en/cars/'), ('Browse by brand', '/en/brands/'), ('Vehicle categories', '/en/categories/'), ('Buying guides', '/en/guides/')]),
    ('COMPANY', [('About us', '/en/about/'), ('Contact', '/en/contact/'), ('Export markets', '/en/markets/kenya/')]),
    ('SUPPORT', [('Payment & terms', '/en/#faq'), ('Privacy policy', '/en/privacy/'), ('Terms of service', '/en/terms/')]),
    ('LANGUAGES', [(n, None, i) for i, n in enumerate(FOUR_LANG)]),
  ],
  'foot_copy': f'Copyright 2026 Jinba Cars Export Co., Ltd. · jinbacars.com',
  'foot_badge': 'MOFCOM licensed · COI verified · B/L on every shipment',
 },
 'zh': {
  'title': '中国二手车出口服务 | 金霸汽车',
  'desc': f'浏览 {STAT_INV} 台可出口中国二手车，查看库存编号、照片、价格和里程，并获取目的港书面报价。',
  'topbar_l': '持证二手车出口企业 · 中国深圳 · 2016 年至今',
  'nav': [('车辆库存', '/zh/cars/'), ('出口市场', '/zh/markets/kenya/'), ('采购流程', '#process'), ('关于我们', '/zh/about/')],
  'nav_wa': 'WhatsApp 咨询',
  'lang_on': '中文', 'lang_names': FOUR_LANG, 'self_name': '简体中文',
  'badge': f'{STAT_INV} 台现车在库 · 可随时发运',
  'h1': '把中国高性价比好车，交到你的市场',
  'hero_sub': '比亚迪、哈弗、捷途等主流品牌车源，全部经 168 项出口检测；FOB/CIF 报价、全套出口单证、订舱发运一站办齐。',
  'cta_browse': '浏览车辆', 'cta_how': '采购流程',
  'stats': [(STAT_INV, '台现车在库'), (STAT_EXPORTED, '台累计出口'),
            (STAT_COUNTRIES, '个目的国'), ('<em>25</em>', '天直达蒙巴萨均值')],
  'feat_kicker': '精选车源', 'feat_h2': '新鲜到库，即买即出口',
  'view_all': f'查看全部 {STAT_INV} 台 →',
  'fob': '深圳港 FOB', 'quote': '获取报价',
  'why_kicker': '为什么选金霸', 'why_h2': '与长期伙伴合作，而非在信息平台上碰运气',
  'why_sub': '从中国堆场到目的港，验车、单证、发运由同一个团队负责到底，每一台车都可追溯。',
  'why_main_kicker': '品质保障', 'why_main_h3': '每台车上线前完成 168 项检测',
  'why_main_p': '机械、结构件、外观逐项检测留档；重大事故车、泡水车、火烧车一票否决，绝不挂牌。',
  'bento': [('168', '项检测'), ('6+', '张实拍照片'), ('24h', '视频验车响应')],
  'trade_kicker': '贸易条款',
  'why_cards': [
    ('出口单证', '出口单证，一次办对',
     '商业发票、装箱单、报关单、提单、车辆注销证明与原产地证，由自有单证组全程办理与跟踪。'),
    ('收付款', 'T/T 电汇与信用证',
     '30% 定金锁车，见提单副本付尾款；支持付款前第三方验车，节点透明。'),
    ('物流', '直航 14 个目的国',
     '蒙巴萨、拉各斯、洛美、杰贝阿里、亚喀巴、乌姆盖斯尔、海参崴等成熟航线，典型时效 18\u201335 天。'),
  ],
  'proc_kicker': '出口流程', 'proc_h2': '从选车到发运，全程服务',
  'proc_cta': '开始下单',
  'steps': [
    ('01', '告诉我们需求', '发送车型、预算与目的港，24 小时内回复候选清单与 FOB/CIF 报价。'),
    ('02', '验车与锁位', '查看照片、视频与 168 项检测报告，支付定金后为你锁定车辆。'),
    ('03', '单证与报关', '办理全套出口单证、预订舱位并完成中国侧报关放行。'),
    ('04', '发运与跟踪', '装船出运、签发提单，开航后每周同步船期直至抵港。'),
  ],
  'mkt_kicker': '目的市场', 'mkt_h2': '成熟航线，本地化经验',
  'markets': [
    ('非洲', '肯尼亚 · 尼日利亚 · 坦桑尼亚 · 加纳',
     '熟悉各国关税结构、车龄限制与验车制度，按当地清关行要求备齐单证。', 'navy'),
    ('中东', '阿联酋 · 约旦 · 伊拉克',
     '海湾规格车型经验丰富，杰贝阿里与亚喀巴滚装/集装箱直航，可安排阿语服务。', ''),
    ('欧亚', '俄罗斯 · 哈萨克斯坦 · 吉尔吉斯斯坦',
     '海运与陆路联运方案，EAC 认证文件指导，俄语顾问从报价跟进到抵港。', ''),
  ],
  'story_kicker': '客户见证', 'stories_h2': '来自三大洲进口商的信任',
  'stories': [
    ('今年第三批了——检测报告和到港实车一致，连胎纹深度都对得上，所以我们一直下单。',
     'Daniel Otieno', '车队采购 · 肯尼亚内罗毕', ''),
    ('清关文件一次都没被打回过。我是第一次遇到不等我开口就先把提单发来的出口商。',
     'Alexey Voronov', '车行老板 · 俄罗斯海参崴', 'peach'),
  ],
  'faq_kicker': '常见问题', 'faq_h2': '买家最先问的四个问题',
  'faq_side': '付款方式、运输时效、验车与单证——下面四个问题覆盖了九成首次询盘。还有疑问，直接给我们留言。',
  'faq_side_btn': 'WhatsApp 咨询',
  'faq': [
    ('付款方式怎么安排？',
     '支持 T/T 电汇与信用证。常规节奏：30% 定金锁车，见提单副本支付 70% 尾款；付款前支持第三方验车。'),
    ('运输时效多久？',
     '滚装/集装箱航线覆盖中东、非洲、中亚与俄罗斯，典型 18\u201335 天视目的港而定；蒙巴萨平均 25 天。'),
    ('付款前可以验车吗？',
     '可以。每台车 6 张以上实拍照片，可预约 24 小时内视频验车，也支持深圳第三方验车机构。'),
    ('会收到哪些单证？',
     '商业发票、装箱单、报关单、提单、车辆注销证明与原产地证——清关行需要的全套文件一次交付。'),
  ],
  'cta_h2': '本月预订你的第一批货',
  'cta_p': '把需要的车型与数量发给我们，为你锁定库存并出具 7 天有效报价（含 FOB 与 CIF 方案）。',
  'cta_wa': 'WhatsApp 咨询', 'cta_email': EMAIL,
  'cta_note': '报价 7 天有效 · FOB / CIF · 中英俄阿四语服务',
  'foot_about': '金霸汽车出口有限公司，2016 年起立足深圳的持证二手车出口企业：现货足检、单证齐全、航线成熟，直达 14 个目的国。',
  'foot_cols': [
    ('车辆库存', [('全部车辆', '/zh/cars/'), ('按品牌选车', '/zh/brands/'), ('车辆分类', '/zh/categories/'), ('出口指南', '/zh/guides/')]),
    ('公司', [('关于我们', '/zh/about/'), ('联系我们', '/zh/contact/'), ('出口市场', '/zh/markets/kenya/')]),
    ('支持', [('付款与条款', '/zh/#faq'), ('隐私政策', '/zh/privacy/'), ('服务条款', '/zh/terms/')]),
    ('语言', [(n, None, i) for i, n in enumerate(FOUR_LANG)]),
  ],
  'foot_copy': 'Copyright 2026 金霸汽车出口有限公司 · jinbacars.com',
  'foot_badge': '商务部备案 · COI 验证 · 每船提单可查',
 },
 'ru': {
  'title': 'Авто из Китая для экспорта | Jinba Cars',
  'desc': f'Смотрите {STAT_INV} автомобилей из Китая для экспорта: номера склада, фото, цены и пробег. Запросите письменное предложение для вашего порта.',
  'topbar_l': 'Лицензированный экспортёр авто · Шэньчжэнь, Китай · с 2016 года',
  'nav': [('Автопарк', '/ru/cars/'), ('Рынки', '/ru/markets/kenya/'), ('Процесс', '#process'), ('О нас', '/ru/about/')],
  'nav_wa': 'WhatsApp',
  'lang_on': 'RU', 'lang_names': FOUR_LANG, 'self_name': 'Русский',
  'badge': f'{STAT_INV} авто в наличии · готовы к отгрузке',
  'h1': 'Лучшие по цене авто из Китая — для вашего рынка',
  'hero_sub': 'Проверенные автомобили ведущих китайских брендов — BYD, Haval, Jetour и другие — с ценами FOB/CIF, полным пакетом экспортных документов и организацией доставки.',
  'cta_browse': 'Смотреть автопарк', 'cta_how': 'Как проходит покупка',
  'stats': [(STAT_INV, 'авто в наличии'), (STAT_EXPORTED, 'авто экспортировано'),
            (STAT_COUNTRIES, 'стран назначения'), ('<em>25</em>', 'дней до Момбасы в среднем')],
  'feat_kicker': 'В НАЛИЧИИ', 'feat_h2': 'Новые поступления, готовы к экспорту',
  'view_all': f'Все {STAT_INV} авто →',
  'fob': 'FOB Шэньчжэнь', 'quote': 'Запросить цену',
  'why_kicker': 'ПОЧЕМУ JINBA', 'why_h2': 'Работайте с партнёром, а не с доской объявлений',
  'why_sub': 'Мы сами проверяем, оформляем и отгружаем каждый автомобиль — одна команда отвечает от площадки в Китае до вашего порта.',
  'why_main_kicker': 'КОНТРОЛЬ КАЧЕСТВА', 'why_main_h3': 'Проверка по 168 пунктам до публикации',
  'why_main_p': 'Каждый автомобиль проходит проверку механики, кузова и салона по 168 пунктам. Авто с серьёзными ДТП, затоплением или пожаром не попадают на сайт.',
  'bento': [('168', 'пунктов проверки'), ('6+', 'фото в объявлении'), ('24ч', 'видеоосмотр')],
  'trade_kicker': 'УСЛОВИЯ ПОСТАВКИ',
  'why_cards': [
    ('ДОКУМЕНТЫ', 'Экспортные документы без ошибок',
     'Инвойс, упаковочный лист, таможенная декларация, коносамент, свидетельство о снятии с учёта и сертификат происхождения — готовит наш отдел документации.'),
    ('ОПЛАТА', 'Безопасная оплата T/T и L/C',
     '30% предоплата за бронь, остаток против копии коносамента. Поэтапные платежи, приветствуется независимая инспекция до оплаты.'),
    ('ЛОГИСТИКА', 'Доставка в 14 стран',
     'Ро-Ро и контейнерные линии в Момбасу, Лагос, Ломе, Джебель-Али, Акабу, Ум-Каср, Владивосток — обычно 18\u201335 дней.'),
  ],
  'proc_kicker': 'КАК ЭТО РАБОТАЕТ', 'proc_h2': 'От выбора до отгрузки — под ключ',
  'proc_cta': 'Начать заказ',
  'steps': [
    ('01', 'Расскажите о задаче', 'Модель, бюджет и порт назначения — в течение 24 часов пришлём подборку и цены FOB/CIF.'),
    ('02', 'Осмотр и бронь', 'Фото, видео и отчёт по 168 пунктам; бронь с предоплатой — автомобиль закрепляем за вами.'),
    ('03', 'Документы и таможня', 'Готовим экспортные документы, бронируем судно и проходим таможню в Китае.'),
    ('04', 'Отгрузка и трекинг', 'Погрузка, коносамент, еженедельные обновления пути до прихода в ваш порт.'),
  ],
  'mkt_kicker': 'ГЕОГРАФИЯ', 'mkt_h2': 'Отработанные линии, знание местных правил',
  'markets': [
    ('АФРИКА', 'Кения · Нигерия · Танзания · Гана',
     'Таможенные пошлины, возрастные ограничения и правила инспекции по каждой стране — документы в формате для вашего брокера.', 'navy'),
    ('БЛИЖНИЙ ВОСТОК', 'ОАЭ · Иордания · Ирак',
     'Опыт с Gulf-спецификацией, Ро-Ро и контейнеры через Джебель-Али и Акабу, поддержка на арабском по запросу.', ''),
    ('ЕВРАЗИЯ', 'Россия · Казахстан · Кыргызстан',
     'Морские и сухопутные маршруты, помощь с документами ЕАЭС, русскоговорящие менеджеры от запроса до прихода авто.', ''),
  ],
  'story_kicker': 'ОТЗЫВЫ КЛИЕНТОВ', 'stories_h2': 'Нам доверяют импортёры на трёх континентах',
  'stories': [
    ('Уже третья партия за год — отчёты об осмотре совпали с машинами в порту вплоть до протектора шин. Поэтому заказываем снова.',
     'Daniel Otieno', 'Импортёр автопарка · Найроби, Кения', ''),
    ('Документы прошли российскую таможню без единой правки. Впервые коносамент присылают раньше, чем я успеваю спросить.',
     'Alexey Voronov', 'Дилер · Владивосток, Россия', 'peach'),
  ],
  'faq_kicker': 'ВОПРОСЫ', 'faq_h2': 'Что спрашивают в первую очередь',
  'faq_side': 'Оплата, сроки доставки, осмотр и документы — четыре вопроса ниже закрывают 90% первых обращений. Остальное — просто напишите нам.',
  'faq_side_btn': 'Спросить в WhatsApp',
  'faq': [
    ('Как организована оплата?',
     'Банковский перевод T/T или аккредитив L/C. Стандартно: 30% предоплата за бронь, 70% против копии коносамента. До оплаты возможна независимая инспекция.'),
    ('Каковы сроки доставки?',
     'Ро-Ро и контейнерные линии охватывают Ближний Восток, Африку, Центральную Азию и Россию — обычно 18\u201335 дней до порта. Момбаса в среднем 25 дней.'),
    ('Можно ли осмотреть авто до оплаты?',
     'Да. В каждом объявлении 6+ реальных фото, по запросу — видеоосмотр в течение 24 часов. Поддерживаем и независимую инспекцию в Шэньчжэне.'),
    ('Какие документы я получу?',
     'Инвойс, упаковочный лист, экспортную декларацию, коносамент, свидетельство о снятии с учёта и сертификат происхождения — полный набор для растаможки.'),
  ],
  'cta_h2': 'Забронируйте первую партию в этом месяце',
  'cta_p': 'Пришлите модели и количество — придержим авто и подготовим предложение сроком на 7 дней с вариантами FOB и CIF.',
  'cta_wa': 'Написать в WhatsApp', 'cta_email': EMAIL,
  'cta_note': 'Предложение 7 дней · FOB / CIF · поддержка на EN, RU и AR',
  'foot_about': 'Лицензированный экспортёр подержанных авто из Шэньчжэня с 2016 года: проверенный автопарк, полный пакет документов и отработанные линии в 14 стран.',
  'foot_cols': [
    ('АВТОПАРК', [('Все автомобили', '/ru/cars/'), ('По брендам', '/ru/brands/'), ('Категории', '/ru/categories/'), ('Гайды', '/ru/guides/')]),
    ('КОМПАНИЯ', [('О нас', '/ru/about/'), ('Контакты', '/ru/contact/'), ('Рынки', '/ru/markets/kenya/')]),
    ('ПОДДЕРЖКА', [('Оплата и условия', '/ru/#faq'), ('Конфиденциальность', '/ru/privacy/'), ('Условия', '/ru/terms/')]),
    ('ЯЗЫКИ', [(n, None, i) for i, n in enumerate(FOUR_LANG)]),
  ],
  'foot_copy': 'Copyright 2026 Jinba Cars Export Co., Ltd. · jinbacars.com',
  'foot_badge': 'Лицензия MOFCOM · COI · коносамент по каждой партии',
 },
 'ar': {
  'title': 'سيارات مستعملة من الصين للتصدير | جينبا',
  'desc': f'تصفح {STAT_INV} سيارة مستعملة من الصين للتصدير، مع رقم المخزون والصور والسعر والمسافة، واطلب عرضاً مكتوباً لميناء الوصول.',
  'topbar_l': 'مصدّر سيارات مستعملة مرخّص · شنتشن، الصين · منذ 2016',
  'nav': [('المخزون', '/ar/cars/'), ('أسواق التصدير', '/ar/markets/kenya/'), ('آلية الشراء', '#process'), ('من نحن', '/ar/about/')],
  'nav_wa': 'واتساب',
  'lang_on': 'AR', 'lang_names': FOUR_LANG, 'self_name': 'العربية',
  'badge': f'{STAT_INV} سيارة في المخزون · جاهزة للشحن',
  'h1': 'نقل أفضل سيارات الصين قيمةً إلى سوقك',
  'hero_sub': 'سيارات مفحوصة من أبرز العلامات الصينية — BYD وHaval وJetour وغيرها — مع أسعار FOB/CIF ومستندات تصدير كاملة وتنسيق شحن حتى السفينة.',
  'cta_browse': 'تصفح المخزون', 'cta_how': 'كيف تتم الشراء',
  'stats': [(STAT_INV, 'سيارة في المخزون'), (STAT_EXPORTED, 'سيارة مُصدَّرة'),
            (STAT_COUNTRIES, 'دولة وصول'), ('<em>25</em>', 'يوماً إلى مومباسا في المتوسط')],
  'feat_kicker': 'سيارات مختارة', 'feat_h2': 'وصلت حديثاً، جاهزة للتصدير',
  'view_all': f'عرض كل {STAT_INV} سيارة ←',
  'fob': 'FOB شنتشن', 'quote': 'اطلب عرض سعر',
  'why_kicker': 'لماذا جينبا', 'why_h2': 'تعامل مع شريك، لا مع موقع إعلانات',
  'why_sub': 'نفحص ونجهّز ونشحن كل سيارة بأنفسنا — فريق واحد مسؤول من الساحة في الصين حتى مينائك.',
  'why_main_kicker': 'ضمان الجودة', 'why_main_h3': 'فحص من 168 نقطة قبل كل إعلان',
  'why_main_p': 'كل سيارة تجتاز فحصاً ميكانيكياً وبنيوياً وشكلياً من 168 نقطة. السيارات ذات حوادث أو غرق أو حريق كبير لا تصل إلى هذا الموقع أبداً.',
  'bento': [('168', 'نقطة فحص'), ('6+', 'صور لكل سيارة'), ('24س', 'جولة فيديو')],
  'trade_kicker': 'شروط التسليم',
  'why_cards': [
    ('المستندات', 'أوراق التصدير منسّقة بدقة',
     'فاتورة تجارية وقائمة تعبئة وإقرار جمركي وبوليصة شحن وشهادة إلغاء تسجيل وشهادة منشأ — يجهّزها قسم مستنداتنا ويتابعها.'),
    ('الدفع', 'دفع آمن عبر T/T وخطابات اعتماد',
     'دفعة مقدمة 30% للحجز والرصيد مقابل نسخة بوليصة الشحن. مراحل دفع واضحة، ونرحّب بفحص طرف ثالث قبل التحويل.'),
    ('الشحن', 'خطوط ملاحية إلى 14 دولة',
     'خطوط RoRo وحاويات قائمة إلى مومباسا ولاغوس ولوميه وجبل علي والعقبة وأم قصر وفلاديفوستوك — 18\u201335 يوماً عادةً.'),
  ],
  'proc_kicker': 'كيف نعمل', 'proc_h2': 'من الاختيار إلى الشحن، خدمة كاملة',
  'proc_cta': 'ابدأ طلبك',
  'steps': [
    ('01', 'أخبرنا باحتياجك', 'أرسل الموديل والميزانية وميناء الوصول — نرد خلال 24 ساعة بقائمة مقترحة وأسعار FOB/CIF.'),
    ('02', 'الفحص والحجز', 'راجع الصور والفيديو وتقرير الـ168 نقطة، واحجز بدفعة مقدمة فتُخصص لك السيارة.'),
    ('03', 'المستندات والجمارك', 'نجهّز مستندات التصدير ونحجز السفينة وننجز التخليص الجمركي في الصين.'),
    ('04', 'الشحن والتتبع', 'تحميل وإصدار بوليصة الشحن، ثم تحديثات أسبوعية حتى وصول السفينة إلى مينائك.'),
  ],
  'mkt_kicker': 'أين نشحن', 'mkt_h2': 'خطوط قائمة، وخبرة محلية',
  'markets': [
    ('أفريقيا', 'كينيا · نيجيريا · تنزانيا · غانا',
     'نعرف الرسوم وقيود العمر وأنظمة الفحص في كل دولة، ونشحن بالمستندات التي يتوقعها مخلّصك الجمركي.', 'navy'),
    ('الشرق الأوسط', 'الإمارات · الأردن · العراق',
     'إلمام بمواصفات الخليج، وخطوط RoRo وحاويات عبر جبل علي والعقبة، ودعم بالعربية عند الطلب.', ''),
    ('أوراسيا', 'روسيا · كازاخستان · قيرغيزستان',
     'مسارات بحرية وبرية، وإرشاد لمستندات الاتحاد الاقتصادي الأوراسي، ومستشارون بالروسية من العرض حتى الوصول.', ''),
  ],
  'story_kicker': 'آراء العملاء', 'stories_h2': 'ثقة مستوردين من ثلاث قارات',
  'stories': [
    ('هذه الدفعة الثالثة هذا العام — تقارير الفحص طابقت ما وصل إلى الميناء حتى عمق نقر الإطارات. لذلك نستمر في الطلب.',
     'Daniel Otieno', 'مستورد أسطول · نيروبي، كينيا', ''),
    ('المستندات اجتازت الجمارك الروسية دون أي تعديل. أول مصدّر يرسل لي بوليصة الشحن قبل أن أطلبه.',
     'Alexey Voronov', 'تاجر سيارات · فلاديفوستوك، روسيا', 'peach'),
  ],
  'faq_kicker': 'الأسئلة الشائعة', 'faq_h2': 'ما يسأل عنه المشترون أولاً',
  'faq_side': 'الدفع ومدة الشحن والفحص والمستندات — الأسئلة الأربعة أدناه تغطي 90% من الاستفسارات الأولى. ولأي شيء آخر راسلنا مباشرة.',
  'faq_side_btn': 'اسأل عبر واتساب',
  'faq': [
    ('كيف يتم ترتيب الدفع؟',
     'تحويل بنكي T/T أو خطاب اعتماد. المعتاد: دفعة مقدمة 30% لحجز السيارة و70% مقابل نسخة بوليصة الشحن، مع إمكانية فحص طرف ثالث قبل الدفع.'),
    ('كم تستغرق مدة الشحن؟',
     'خطوط RoRo والحاويات تغطي الشرق الأوسط وأفريقيا وآسيا الوسطى وروسيا — عادة 18\u201335 يوماً حسب ميناء الوصول. مومباسا في المتوسط 25 يوماً.'),
    ('هل يمكنني معاينة السيارة قبل الدفع؟',
     'نعم. كل إعلان يتضمن 6 صور حقيقية فأكثر، ونوفر جولة فيديو خلال 24 ساعة عند الطلب، وندعم الفحص بواسطة جهة مستقلة في شنتشن.'),
    ('ما المستندات التي سأستلمها؟',
     'فاتورة تجارية وقائمة تعبئة وإقرار جمركي وبوليصة شحن وشهادة إلغاء تسجيل وشهادة منشأ — الحزمة الكاملة التي يحتاجها مخلّصك للاستيراد.'),
  ],
  'cta_h2': 'احجز شحنتك الأولى هذا الشهر',
  'cta_p': 'أرسل الموديلات والكميات التي تحتاجها — سنحجز المخزون ونجهّز عرض سعر صالحاً 7 أيام بخَياري FOB وCIF.',
  'cta_wa': 'تحدث عبر واتساب', 'cta_email': EMAIL,
  'cta_note': 'العروض صالحة 7 أيام · FOB / CIF · دعم بالإنجليزية والروسية والعربية',
  'foot_about': 'مصدّر سيارات مستعملة مرخّص في شنتشن بالصين منذ 2016: مخزون مفحوص، مستندات تصدير كاملة، وخطوط ملاحية قائمة إلى 14 دولة.',
  'foot_cols': [
    ('المخزون', [('كل السيارات', '/ar/cars/'), ('حسب الماركة', '/ar/brands/'), ('الفئات', '/ar/categories/'), ('أدلة الشراء', '/ar/guides/')]),
    ('الشركة', [('من نحن', '/ar/about/'), ('اتصل بنا', '/ar/contact/'), ('أسواق التصدير', '/ar/markets/kenya/')]),
    ('الدعم', [('الدفع والشروط', '/ar/#faq'), ('الخصوصية', '/ar/privacy/'), ('الشروط', '/ar/terms/')]),
    ('اللغات', [(n, None, i) for i, n in enumerate(FOUR_LANG)]),
  ],
  'foot_copy': 'Copyright 2026 Jinba Cars Export Co., Ltd. · jinbacars.com',
  'foot_badge': 'مرخّص من MOFCOM · موثّق COI · بوليصة شحن لكل شحنة',
 },
}

SVG_TRUCK = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M3 7h11v8H3zM14 10h4l3 3v2h-7z" fill="#fff"/><circle cx="7" cy="17" r="2" fill="#fff"/><circle cx="17.5" cy="17" r="2" fill="#fff"/></svg>'
SVG_BURGER = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>'
SVG_WA = '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm5.3 14.2c-.2.6-1.2 1.2-1.7 1.2-.4.1-1 .1-1.6-.1a13 13 0 0 1-5.8-4.9c-.7-1-.9-1.9-.7-2.6.1-.5.7-1.4 1.3-1.4h.6c.2 0 .4.1.6.5l.8 2c.1.2 0 .4-.1.6l-.5.6c-.2.2-.3.4-.1.7.5.9 1.9 2.3 3.2 2.9.3.1.5.1.7-.1l.7-.8c.2-.2.4-.3.6-.2l2 .9c.3.2.4.4.4.6s0 .8-.1 1.1z"/></svg>'
STAR = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2l2.9 6.6 7.1.6-5.4 4.7 1.6 7-6.2-3.7L5.8 21l1.6-7L2 9.2l7.1-.6z"/></svg>'


def chips_html(lang, v):
    fuel = {'zh': {'插混': '插混', '纯电': '纯电', '混动': '混动'}.get(v['fuel'], v['fuel']),
            'en': {'插混': 'PHEV', '纯电': 'EV', '混动': 'Hybrid'}.get(v['fuel'], v['fuel']),
            'ru': {'插混': 'PHEV', '纯电': 'EV', '混动': 'Hybrid'}.get(v['fuel'], v['fuel']),
            'ar': {'插混': 'هجين', '纯电': 'كهربائي', '混动': 'هجين'}.get(v['fuel'], v['fuel'])}[lang]
    body = {'zh': v.get('body_type') or 'SUV', 'en': v.get('body_type') or 'SUV',
            'ru': v.get('body_type') or 'SUV', 'ar': v.get('body_type') or 'SUV'}[lang]
    return (f'<span class="jv7-chip">{esc(str(v["year"]))} · {esc(fuel)}</span>'
            f'<span class="jv7-chip">{esc(body)}</span>')


def car_card(lang, v):
    # v8 规范：左上角 年份+燃料+车身 标签悬浮于原图上，禁止缩略图作主图；
    # 下方车型名 / 库存号 / 里程 / 品牌 / FOB 价 + 藏蓝实心白字按钮。
    d = L[lang]
    t = v['title_i18n'].get(lang) or v['title']
    ph = v['photos'][0]
    alt = esc(t)
    stock = esc(v['stock_id'])
    mileage = esc(f'{int(v.get("mileage_km") or 0):,}') + ' km'
    brand = esc(v['brand'])
    return (f'<article class="jv7-car">'
            f'<div class="jv7-car-photo"><img src="{ph}" alt="{alt}" loading="lazy" decoding="async" width="720" height="540">'
            f'<span class="jv7-tags"><b>{esc(str(v["year"]))}</b>{chips_html(lang, v)}</span></div>'
            f'<div class="jv7-car-body"><h3 class="jv7-car-name">{alt}</h3>'
            f'<div class="jv7-car-spec">{stock} · {mileage} · {brand}</div>'
            + (f'<p class="jv7-car-desc">{esc(CAR_COPY[v["id"]][lang])}</p>' if v['id'] in CAR_COPY else '')
            + f'<div class="jv7-car-foot"><div><div class="jv7-price">{esc(v["price"])}</div>'
            f'<div class="jv7-fob">{esc(d["fob"])}</div></div>'
            f'<a class="jv7-btn jv7-btn--navy" href="{N[lang]}cars/{v["id"]}/">{esc(d["quote"])}</a>'
            f'</div></div></article>')


def faq_html(lang):
    out = []
    for i, (q, a) in enumerate(L[lang]['faq']):
        open_tag = ' open' if i == 0 else ''
        out.append(f'<details class="jv7-faqitem"{open_tag}><summary>{esc(q)}</summary><p>{esc(a)}</p></details>')
    return '\n'.join(out)


def build(lang):
    d = L[lang]
    rtl = 'rtl' if lang == 'ar' else 'ltr'
    olang = lambda lg: f'<a href="{N[lg]}"{" aria-current=\"true\"" if lg == lang else ""}>{d["lang_names"][LANGS.index(lg)]}</a>'

    # ---- nav ----
    navlinks = ''.join(f'<a href="{href}">{esc(name)}</a>' for name, href in d['nav'])
    # ---- hero ----
    hero_img = '/images/hero-banner.webp'  # 2026-09-09: 固定使用广告 banner（1536x1024 3:2）
    hero_alt = esc((HERO['title_i18n'].get(lang) or HERO['title']) if HERO else 'Jinba Cars Export')
    stats = ''.join(f'<div class="jv7-stat"><b>{val}</b><span>{esc(lab)}</span></div>' for val, lab in d['stats'])
    # ---- featured ----
    cards = '\n'.join(car_card(lang, v) for v in FEATURED)
    # ---- why ----
    bento = ''.join(f'<div><b>{esc(b)}</b><span>{esc(s)}</span></div>' for b, s in d['bento'])
    mk, mh, mp = d['why_main_kicker'], d['why_main_h3'], d['why_main_p']
    side_cards = ''.join(
        f'<article class="jv7-glass{" jv7-glass--orange" if i == 2 else ""}">'
        f'<span class="jv7-kicker">{esc(k)}</span><h3>{esc(h)}</h3><p>{esc(p)}</p></article>'
        for i, (k, h, p) in enumerate(d['why_cards']))
    # ---- steps ----
    steps = ''.join(f'<article class="jv7-step"><div class="jv7-step-no">{esc(no)}</div>'
                    f'<h3>{esc(t)}</h3><p>{esc(p)}</p></article>' for no, t, p in d['steps'])
    # ---- markets ----
    markets = ''.join(
        f'<article class="jv7-market{"" if tail != "navy" else " jv7-market--navy"}">'
        f'<span class="jv7-kicker">{esc(name)}</span><h3>{esc(ctry)}</h3><p>{esc(desc)}</p></article>'
        for name, ctry, desc, tail in d['markets'])
    # ---- stories ----
    stars = f'<div class="jv7-stars" aria-label="5/5">{STAR * 5}</div>'
    stories = ''.join(
        f'<article class="jv7-story{"" if tail != "peach" else " jv7-story--peach"}">{stars}'
        f'<blockquote>{esc(quote)}</blockquote>'
        f'<div class="jv7-story-who"><div><b>{esc(who)}</b><span>{esc(role)}</span></div></div></article>'
        for quote, who, role, tail in d['stories'])
    # ---- faq ----
    faq = faq_html(lang)
    # FAQPage schema（与页面 FAQ 区块同步，四语言）
    _faqs = L[lang]['faq']
    import json as _json
    faq_schema = ('<script type="application/ld+json">' +
                  _json.dumps({'@context': 'https://schema.org', '@type': 'FAQPage',
                               'mainEntity': [{'@type': 'Question', 'name': q,
                                               'acceptedAnswer': {'@type': 'Answer', 'text': a}}
                                              for q, a in _faqs]}, ensure_ascii=False)
                  .replace('<', '\\u003c').replace('>', '\\u003e') +
                  '</script>')
    # ---- footer cols ----
    fcols = ''
    for col_title, links in d['foot_cols']:
        lis = ''
        for item in links:
            name = item[0]
            href = item[1]
            idx = item[2] if len(item) > 2 else None
            if idx is not None:
                lg = LANGS[idx]
                lis += (f'<li><a href="{N[lg]}"'
                        f'{" aria-current=\"true\"" if lg == lang else ""}>{esc(name)}</a></li>')
            else:
                lis += f'<li><a href="{href}">{esc(name)}</a></li>'
        fcols += f'<div class="jv7-footcol"><h4>{esc(col_title)}</h4><ul>{lis}</ul></div>'
    lang_links = ''.join(f'<a href="{N[lg]}"{" aria-current=\"true\"" if lg == lang else ""}>{esc(d["lang_names"][i])}</a>'
                         for i, lg in enumerate(LANGS))

    html = f'''<!doctype html>
<html lang="{"ar" if lang == "ar" else ("zh-CN" if lang == "zh" else lang)}" dir="{rtl}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#0A1628">
<meta name="google-site-verification" content="{VERIF}">
<title>{esc(d["title"])}</title>
<meta name="description" content="{esc(d["desc"])}">
<meta name="keywords" content="used cars from china, china used car export, BYD export, used car exporter shenzhen, FOB china cars, 出口二手车, 中国二手车出口">
<meta property="og:site_name" content="Jinba Cars Export">
<meta property="og:locale" content="{lang}_{"AR" if lang=="ar" else ("CN" if lang=="zh" else ("RU" if lang=="ru" else "US"))}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(d["title"])}">
<meta property="og:description" content="{esc(d["desc"])}">
<meta property="og:url" content="{DOMAIN}{N[lang]}">
<meta property="og:image" content="{DOMAIN}{OG_IMG}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(d["title"])}">
<meta name="twitter:description" content="{esc(d["desc"])}">
<meta name="twitter:image" content="{DOMAIN}{OG_IMG}">
<link rel="canonical" href="{DOMAIN}{N[lang]}">
<link rel="alternate" hreflang="en" href="{DOMAIN}/en/">
<link rel="alternate" hreflang="zh" href="{DOMAIN}/zh/">
<link rel="alternate" hreflang="ru" href="{DOMAIN}/ru/">
<link rel="alternate" hreflang="ar" href="{DOMAIN}/ar/">
<link rel="alternate" hreflang="x-default" href="{DOMAIN}/en/">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/rss+xml" title="Jinba Cars Export Inventory" href="/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Mona+Sans:wght@400;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&family=Noto+Sans+SC:wght@400;500;700;900&family=Noto+Sans+Arabic:wght@400;600;800&display=swap">
<link rel="stylesheet" href="/assets/jinba-home-v7.css?v=20260910b">
<link rel="preconnect" href="https://www.googletagmanager.com">
<link rel="preconnect" href="https://wa.me">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','{GA_ID}');</script>
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Organization","name":"Jinba Cars Export Co., Ltd.","url":"{DOMAIN}","email":"{EMAIL}","telephone":"+86 180 7908 9999","address":{{"@type":"PostalAddress","addressLocality":"Shenzhen","addressRegion":"Guangdong","addressCountry":"CN"}}}}</script>
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebSite","name":"Jinba Cars","url":"{DOMAIN}","inLanguage":"{lang}"}}</script>
{faq_schema}
</head>
<body class="jv7">

<header class="jv7-topbar">
  <div class="jv7-container jv7-topbar-in">
    <span class="jv7-topbar-l">{esc(d["topbar_l"])}</span>
    <span class="jv7-topbar-r jv7-topbar-contact">
      <a href="mailto:{EMAIL}">{EMAIL}</a>
      <a href="tel:+8618079089999">{PHONE_DISPLAY}</a>
      <span class="jv7-topbar-langs">{lang_links}</span>
    </span>
  </div>
</header>

<nav class="jv7-nav" aria-label="Main">
  <div class="jv7-container jv7-nav-in">
    <input type="checkbox" id="jv7-nav-{lang}" class="jv7-burger" hidden>
    <a class="jv7-logo" href="{N[lang]}" aria-label="Jinba Cars Export">
      <span class="jv7-logo-mark">{SVG_TRUCK}</span>
      <span><span class="jv7-logo-name">JINBA CARS</span><br><span class="jv7-logo-sub">EXPORT</span></span>
    </a>
    <div class="jv7-navlinks">{navlinks}</div>
    <div class="jv7-nav-cta">
      <a class="jv7-btn jv7-btn--green" href="{WA}">{SVG_WA}{esc(d["nav_wa"])}</a>
    </div>
    <label class="jv7-burger" for="jv7-nav-{lang}" aria-label="Menu">{SVG_BURGER}</label>
  </div>
</nav>

<section class="jv7-hero">
  <div class="jv7-container jv7-hero-grid">
    <div>
      <span class="jv7-badge"><span class="jv7-badge-dot"></span>{esc(d["badge"])}</span>
      <h1 class="jv7-h1">{esc(d["h1"])}</h1>
      <p class="jv7-hero-sub">{esc(d["hero_sub"])}</p>
      <div class="jv7-hero-ctas">
        <a class="jv7-btn jv7-btn--orange" href="{N[lang]}cars/">{esc(d["cta_browse"])}</a>
        <a class="jv7-btn jv7-btn--ghost" href="#process">{esc(d["cta_how"])}</a>
      </div>
    </div>
    <div class="jv7-hero-media">
      <img class="jv7-hero-img" src="{hero_img}" alt="{hero_alt}" width="1536" height="1024" fetchpriority="high">
      <div class="jv7-statband">{stats}</div>
    </div>
  </div>
</section>

<section class="jv7-section">
  <div class="jv7-container">
    <div class="jv7-secthead">
      <div><p class="jv7-kicker">{esc(d["feat_kicker"])}</p><h2 class="jv7-h2">{esc(d["feat_h2"])}</h2></div>
      <a class="jv7-viewall" href="{N[lang]}cars/">{esc(d["view_all"])}</a>
    </div>
    <div class="jv7-grid4">
{cards}
    </div>
  </div>
</section>

<section class="jv7-why">
  <div class="jv7-container">
    <p class="jv7-kicker">{esc(d["why_kicker"])}</p>
    <h2 class="jv7-h2 jv7-h2--light">{esc(d["why_h2"])}</h2>
    <p class="jv7-sub">{esc(d["why_sub"])}</p>
    <div class="jv7-whygrid">
      <article class="jv7-glass">
        <span class="jv7-kicker">{esc(mk)}</span>
        <h3>{esc(mh)}</h3>
        <p>{esc(mp)}</p>
        <div class="jv7-bento">{bento}</div>
        <div class="jv7-portwin"><img src="/uploads/carousel/slide_1.jpg" alt="Jinba export yard" loading="lazy" width="1200" height="600"></div>
        <div class="jv7-tradechips"><span>{esc(d["trade_kicker"])}: FOB</span><span>CIF</span><span>RoRo</span><span>Container</span></div>
      </article>
      <div class="jv7-whycol">{side_cards}</div>
    </div>
  </div>
</section>

<section class="jv7-section" id="process">
  <div class="jv7-container">
    <div class="jv7-secthead">
      <div><p class="jv7-kicker">{esc(d["proc_kicker"])}</p><h2 class="jv7-h2">{esc(d["proc_h2"])}</h2></div>
      <a class="jv7-btn jv7-btn--navy" href="{WA}">{esc(d["proc_cta"])}</a>
    </div>
    <div class="jv7-steps">{steps}</div>
  </div>
</section>

<section class="jv7-section">
  <div class="jv7-container">
    <p class="jv7-kicker">{esc(d["mkt_kicker"])}</p>
    <h2 class="jv7-h2">{esc(d["mkt_h2"])}</h2>
    <div class="jv7-markets">{markets}</div>
  </div>
</section>

<section class="jv7-section">
  <div class="jv7-container">
    <p class="jv7-kicker">{esc(d["story_kicker"])}</p>
    <h2 class="jv7-h2">{esc(d["stories_h2"])}</h2>
  </div>
  <div class="jv7-container jv7-stories">{stories}</div>
</section>

<section class="jv7-section" id="faq">
  <div class="jv7-container jv7-faqgrid">
    <div class="jv7-faq-side">
      <p class="jv7-kicker">{esc(d["faq_kicker"])}</p>
      <h2 class="jv7-h2">{esc(d["faq_h2"])}</h2>
      <p class="jv7-sub">{esc(d["faq_side"])}</p>
      <a class="jv7-btn jv7-btn--green" href="{WA}">{SVG_WA}{esc(d["faq_side_btn"])}</a>
    </div>
    <div class="jv7-faq">{faq}</div>
  </div>
</section>

<section class="jv7-ctawrap">
  <div class="jv7-container">
    <div class="jv7-cta">
      <h2>{esc(d["cta_h2"])}</h2>
      <p>{esc(d["cta_p"])}</p>
      <div class="jv7-cta-btns">
        <a class="jv7-btn jv7-btn--green" href="{WA}">{SVG_WA}{esc(d["cta_wa"])}</a>
        <a class="jv7-btn jv7-btn--ghost-light" href="mailto:{EMAIL}">{esc(d["cta_email"])}</a>
      </div>
      <div class="jv7-cta-note">{esc(d["cta_note"])}</div>
    </div>
  </div>
</section>

<footer class="jv7-footer">
  <div class="jv7-container">
    <div class="jv7-footgrid">
      <div class="jv7-footbrand">
        <a class="jv7-logo" href="{N[lang]}" aria-label="Jinba Cars Export">
          <span class="jv7-logo-mark">{SVG_TRUCK}</span>
          <span><span class="jv7-logo-name" style="color:#fff">JINBA CARS</span><br><span class="jv7-logo-sub">EXPORT</span></span>
        </a>
        <p>{esc(d["foot_about"])}</p>
        <span class="jv7-topbar-langs">{lang_links}</span>
      </div>
      {fcols}
    </div>
    <div class="jv7-footbar">
      <span>{esc(d["foot_copy"])}</span>
      <span>{esc(d["foot_badge"])}</span>
    </div>
  </div>
</footer>

</body>
</html>'''

    out = ROOT / lang / 'index.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    BACKUP.mkdir(parents=True, exist_ok=True)
    if out.exists():
        shutil.copy2(out, BACKUP / f'{lang}-index.html')
    out.write_text(html, encoding='utf-8')
    return len(html)


if __name__ == '__main__':
    print(f'published={PUBLISHED_N} featured={[v["id"] for v in FEATURED]} hero_id={HERO["id"] if HERO else None}')
    sizes = {}
    for lg in LANGS:
        sizes[lg] = build(lg)
        print(f'written {lg}/index.html {sizes[lg]} bytes')
    print('ALL DONE v7')
