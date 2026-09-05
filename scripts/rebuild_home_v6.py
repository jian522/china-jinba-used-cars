# -*- coding: utf-8 -*-
"""重建 zh/en/ru/ar 四语首页 —— 按《金霸二手车出口独立站改版设计》版式
Hero(左文右图+4项数据) + 6张真图车卡 + 出口排行(合规公开数据) + 资质信任区(素材图)
+ 8市场网格 + 6步流程 + FAQ + CTA + 四栏Footer
"""
import json
import os
from pathlib import Path

ROOT = Path(r'D:\二手车出口网站')
data = json.load(open(ROOT / 'data' / 'vehicles.json', encoding='utf-8'))
pub = {v['id']: v for v in data if v.get('status') == 'published'}
pub_list = list(pub.values())

# ---------------- 站点统计 ----------------
published_n = len(pub_list)
photo_n = sum(len(v['photos']) for v in pub_list)

# ---------------- 首页6张车卡 ----------------
# 前3台对齐设计稿主推实车：秦PLUS/哈弗H6/唐DM-i；后3台保留原精选（海豹/宋PLUS/瑞虎8L）
CARD_IDS = [11, 9, 12, 60, 144, 13]

# ---------------- 出口排行榜（9席，公开行业数据 + 本站在售现货） ----------------
# 数据源：Autostat/ Izvestia 2025（俄罗斯TOP车型）、特易资讯白皮书2024-2025（市场结构）、
# 中国汽车流通协会（2024出口43.6万辆）。每席链接本站在售现货。
RANK = [
    # (car_id, rank_no, zh_reason, en_reason, ru_reason, ar_reason, zh_src, en_src)
    (112, 1, '俄联邦2025年自华进口二手车最畅销车型',
     'Top used-car model imported from China to Russia, 2025',
     'Самая популярная модель б/у из Китая в России, 2025',
     'الطراز الأكثر استيراداً من الصين إلى روسيا 2025',
     '来源：Autostat 2025', 'Source: Autostat 2025'),
    (110, 2, '俄联邦2025全年自华进口量第一（3,912台）',
     'No.1 China-to-Russia used import by volume 2025 (3,912 units)',
     'Импорт №1 из Китая в Россию, 2025 (3 912 шт.)',
     'الأول في الاستيراد من الصين إلى روسيا 2025 (3,912 وحدة)',
     '来源：Autostat 2025', 'Source: Autostat 2025'),
    (113, 3, '中东与俄罗斯硬派越野常青款，残值坚挺',
     'Evergreen off-roader for Middle East & Russia, strong resale',
     'Вечная классика для Ближнего Востока и России',
     'سيارة دفع رباعي خالدة للشرق الأوسط وروسيا',
     '来源：行业公开报道', 'Source: public industry reports'),
    (9, 4, '2024出口热点：哈弗H6列出口热门SUV榜前位',
     '2024 export hotspot: Haval H6 among top exported SUVs',
     'Экспортный хит 2024: Haval H6 в топе SUV',
     'نقطة ساخنة للتصدير 2024: هافل H6',
     '来源：行业公开报道', 'Source: public industry reports'),
    (135, 5, '俄市场自华热门：高尔夫列大众系前列',
     'Hot China-to-Russia model: Golf leads VW segment',
     'Популярная модель из Китая: Golf лидирует у VW',
     'طراز رائج من الصين: غولف في مقدمة فولكس واجن',
     '来源：Autostat 2025', 'Source: Autostat 2025'),
    (126, 6, '俄市场自华热门：途观系大众SUV主力',
     'Hot China-to-Russia model: Tiguan, VW SUV mainstay',
     'Популярная модель из Китая: Tiguan — основной SUV VW',
     'طراز رائج من الصين: تيغوان ركيزة SUV',
     '来源：Autostat 2025', 'Source: Autostat 2025'),
    (13, 7, '奇瑞系出海代表，中东非洲SUV需求旺盛',
     'Chery flagship export; strong ME & Africa SUV demand',
     'Флагман Chery; спрос на Ближнем Востоке и в Африке',
     'نجم تصدير تشيري؛ طلب مرتفع في الشرق الأوسط وأفريقيا',
     '来源：行业公开报道', 'Source: public industry reports'),
    (22, 8, '长城风骏皮卡：非洲/中亚工程物流刚需',
     'Great Wall Wingle pickup: Africa/Central Asia workhorse',
     'Great Wall Wingle: рабочая лошадка Африки и Азии',
     'بيكاب غريت وول: الأكثر طلباً في أفريقيا وآسيا',
     '来源：行业公开报道', 'Source: public industry reports'),
    (265, 9, '新能源出口主力：比亚迪元PLUS全球热销',
     'NEV export champion: BYD Yuan PLUS sells worldwide',
     'Лидер NEV-экспорта: BYD Yuan PLUS',
     'بطل تصدير السيارات الكهربائية: BYD Yuan PLUS',
     '来源：行业公开报道', 'Source: public industry reports'),
]

# ---------------- FAQ ----------------
FAQ = {
    'zh': [
        ('付款方式怎么安排？', '支持 TT 电汇与信用证，30% 定金排产、尾款见提单副本；全程可视频验车、第三方验车陪同。'),
        ('出口单证谁来办理？', '商业发票、装箱单、报关单、提单、车辆注销证明与原产地证由我司一站式办理，买家仅需提供收货人资料。'),
        ('发运时效多久？', '滚装/集装箱航线覆盖中东、非洲、中亚与俄罗斯方向，典型时效 18-35 天视目的港而定。'),
        ('车况如何保障？', '全部车辆经 96 项出口检测，实拍照片与视频交付；重大事故车、泡水车、火烧车一票否决。'),
    ],
    'en': [
        ('How is payment arranged?', 'T/T bank transfer or L/C: 30% deposit to reserve, balance against B/L copy. Video inspection and third-party inspection supported.'),
        ('Who handles export documents?', 'We handle commercial invoice, packing list, customs declaration, B/L, deregistration certificate and certificate of origin end-to-end.'),
        ('How long is shipping?', 'RoRo and container routes cover the Middle East, Africa, Central Asia and Russia — typically 18-35 days depending on destination port.'),
        ('How is vehicle condition guaranteed?', 'Every vehicle passes a 96-point export inspection with real photos and videos. Major accident, flood or fire damaged vehicles are rejected.'),
    ],
    'ru': [
        ('Как организована оплата?', 'Банковский перевод T/T или аккредитив: 30% предоплата, остаток против копии коносамента. Возможен видеоосмотр и независимая инспекция.'),
        ('Кто оформляет экспортные документы?', 'Мы оформляем инвойс, упаковочный лист, таможенную декларацию, коносамент, свидетельство о снятии с учёта и сертификат происхождения.'),
        ('Каковы сроки доставки?', 'Ро-Ро и контейнерные линии охватывают Ближний Восток, Африку, Центральную Азию и Россию — обычно 18-35 дней до порта назначения.'),
        ('Как гарантируется состояние авто?', 'Каждый автомобиль проходит 96-пунктовую проверку на экспорт с реальными фото и видео. Авто с серьёзными ДТП не допускаются.'),
    ],
    'ar': [
        ('كيف يتم الترتيب للدفع؟', 'تحويل بنكي T/T أو خطاب اعتماد: دفعة مقدمة 30% للحجز، والرصيد مقابل نسخة بوليصة الشحن. مع فحص بالفيديو وفحص من طرف ثالث.'),
        ('من يتولى مستندات التصدير؟', 'نتولى الفاتورة التجارية وقائمة التعبئة والإقرار الجمركي وبوليصة الشحن وشهادة إلغاء التسجيل وشهادة المنشاء بالكامل.'),
        ('ما هي مدة الشحن؟', 'خطوط RoRo والحاويات تغطي الشرق الأوسط وأفريقيا وآسيا الوسطى وروسيا — عادة 18-35 يوماً حسب ميناء الوصول.'),
        ('كيف تضمنون حالة السيارة؟', 'كل سيارة تجتاز فحص تصدير من 96 نقطة مع صور وفيديوهات حقيقية. السيارات المتضررة من حوادث كبرى مرفوضة.'),
    ],
}

# ---------------- 文案 ----------------
L = {
 'zh': {
  'title': '金霸汽车出口 | 中国优质二手车出口全球',
  'desc': '精选真实车源，96项出口检测，一站式办理出口单证、报关与国际运输，直航中东、非洲、中亚与俄罗斯。',
  'eyebrow': 'XINYU · JIANGXI · CHINA',
  'h1a': '中国优质二手车，驶向', 'h1em': '全球。',
  'sub': '精选真实车源，96项出口检测，一站式办理单证、报关与国际运输。',
  'btn_browse': '浏览车辆', 'btn_advisor': '咨询出口顾问',
  'stat_inv': '车辆库存', 'stat_photo': '张实拍照片', 'stat_lang': '语言服务', 'stat_11': '专属顾问',
  'inv_kicker': '真实车辆库存', 'inv_h2': '适合出口的精选车辆', 'inv_more': '查看全部车辆 →',
  'photo_fmt': '{} 张现有照片', 'detail': '查看详情 →',
  'rank_kicker': 'EXPORT HOT MODELS', 'rank_h2': '中国二手车出口热门排行',
  'rank_sub': '基于 Autostat、海关总署公开数据与行业公开报道整理，点击查看本站在售现货。',
  'rank_src': '数据来源：Autostat 2025 · 海关总署 · 中国汽车流通协会（2024年出口43.6万辆）',
  'trust_kicker': 'LICENSED & VERIFIED', 'trust_h2': '资质与单证，清关无忧',
  'mk_kicker': 'GLOBAL DELIVERY', 'mk_h2': '出口市场',
  'pc_kicker': 'EXPORT PROCESS', 'pc_h2': '从选车到发运，全程服务',
  'steps': ['告诉我们需求', '获取推荐清单', '查看车辆资料', '确认报价', '出口文件与报关', '发运至目的港'],
  'faq_kicker': 'FAQ', 'faq_h2': '常见问题',
  'cta_h2': '告诉我们你需要什么车。', 'cta_p': '发送车型、预算和目的港，我们为你准备报价。', 'cta_btn': 'WhatsApp咨询 →',
  'f_inv': '车辆库存', 'f_all': '查看全部车辆', 'f_brand': '按品牌选车', 'f_cat': '车辆分类',
  'f_co': '公司介绍', 'f_about': '关于我们', 'f_contact': '联系我们', 'f_mk': '出口市场', 'f_guide': '出口指南', 'f_priv': '隐私政策', 'f_term': '服务条款',
  'f_addr': '中国江西省新余市', 'f_copy': '© 2026 Jinba Auto Export. 版权所有。',
  'nav': ['首页', '车辆库存', '关于我们', '采购流程', '联系我们'], 'nav_quote': '获取报价',
  'lang_on': '中文',
 },
 'en': {
  'title': 'Jinba Auto Export | Quality Used Cars from China, Exported Worldwide',
  'desc': 'Verified inventory, 96-point export inspection, export documents, customs and shipping to the Middle East, Africa, Central Asia and Russia.',
  'eyebrow': 'XINYU · JIANGXI · CHINA',
  'h1a': 'China used cars, ready for the ', 'h1em': 'world.',
  'sub': 'Verified inventory, 96-point export inspection, one-stop documents, customs and shipping.',
  'btn_browse': 'Browse vehicles', 'btn_advisor': 'Talk to an advisor',
  'stat_inv': 'Inventory', 'stat_photo': 'real photos', 'stat_lang': 'languages', 'stat_11': 'dedicated advisor',
  'inv_kicker': 'Verified inventory', 'inv_h2': 'Vehicles ready for export', 'inv_more': 'View all vehicles →',
  'photo_fmt': '{} available photos', 'detail': 'Details →',
  'rank_kicker': 'EXPORT HOT MODELS', 'rank_h2': 'China Used-Car Export Rankings',
  'rank_sub': 'Compiled from Autostat, China customs public data and industry reports — every entry links to live stock.',
  'rank_src': 'Sources: Autostat 2025 · China Customs · CADA (436,000 units exported in 2024)',
  'trust_kicker': 'LICENSED & VERIFIED', 'trust_h2': 'Licensed, documented, cleared',
  'mk_kicker': 'GLOBAL DELIVERY', 'mk_h2': 'Export markets',
  'pc_kicker': 'EXPORT PROCESS', 'pc_h2': 'From selection to shipping, end to end',
  'steps': ['Tell us your needs', 'Get a shortlist', 'Review vehicle files', 'Confirm quotation', 'Export docs & customs', 'Ship to destination port'],
  'faq_kicker': 'FAQ', 'faq_h2': 'Frequently asked questions',
  'cta_h2': 'Tell us what car you need.', 'cta_p': 'Send model, budget and destination port — we will prepare a quotation.', 'cta_btn': 'WhatsApp us →',
  'f_inv': 'Inventory', 'f_all': 'View all vehicles', 'f_brand': 'Browse by brand', 'f_cat': 'Vehicle categories',
  'f_co': 'Company', 'f_about': 'About', 'f_contact': 'Contact', 'f_mk': 'Export markets', 'f_guide': 'Buying guides', 'f_priv': 'Privacy Policy', 'f_term': 'Terms of Service',
  'f_addr': 'Xinyu, Jiangxi, China', 'f_copy': '© 2026 Jinba Auto Export. All rights reserved.',
  'nav': ['Home', 'Inventory', 'About', 'Process', 'Contact'], 'nav_quote': 'Get a quote',
  'lang_on': 'EN',
 },
 'ru': {
  'title': 'Jinba Auto Export | Автомобили из Китая на экспорт',
  'desc': 'Проверенный автопарк, 96-пунктовая проверка, экспортные документы, таможня и доставка на Ближний Восток, в Африку, Центральную Азию и Россию.',
  'eyebrow': 'СИНЬЮ · ЦЗЯНСИ · КИТАЙ',
  'h1a': 'Авто из Китая — ', 'h1em': 'весь мир.',
  'sub': 'Проверенные авто, 96-пунктовая проверка, документы, таможня и доставка под ключ.',
  'btn_browse': 'Смотреть авто', 'btn_advisor': 'Связаться с экспертом',
  'stat_inv': 'авто в наличии', 'stat_photo': 'реальных фото', 'stat_lang': 'языка', 'stat_11': 'персональный эксперт',
  'inv_kicker': 'Проверенный автопарк', 'inv_h2': 'Авто, готовые к экспорту', 'inv_more': 'Все автомобили →',
  'photo_fmt': '{} доступных фото', 'detail': 'Подробнее →',
  'rank_kicker': 'ЭКСПОРТНЫЕ ХИТЫ', 'rank_h2': 'Рейтинг экспорта авто из Китая',
  'rank_sub': 'По данным Autostat, китайской таможни и отраслевых публикаций — каждая позиция в наличии.',
  'rank_src': 'Источники: Autostat 2025 · Таможня КНР · CADA (436 тыс. авто в 2024)',
  'trust_kicker': 'ЛИЦЕНЗИИ И ДОКУМЕНТЫ', 'trust_h2': 'Документы и растаможка без проблем',
  'mk_kicker': 'ГЛОБАЛЬНАЯ ДОСТАВКА', 'mk_h2': 'Рынки экспорта',
  'pc_kicker': 'ПРОЦЕСС ЭКСПОРТА', 'pc_h2': 'От выбора до отгрузки — полный сервис',
  'steps': ['Расскажите о задаче', 'Получите подборку', 'Изучите досье авто', 'Согласуйте цену', 'Документы и таможня', 'Отгрузка в порт'],
  'faq_kicker': 'ВОПРОСЫ', 'faq_h2': 'Частые вопросы',
  'cta_h2': 'Скажите, какой автомобиль нужен.', 'cta_p': 'Модель, бюджет и порт назначения — мы подготовим предложение.', 'cta_btn': 'WhatsApp →',
  'f_inv': 'Автопарк', 'f_all': 'Все автомобили', 'f_brand': 'По брендам', 'f_cat': 'Категории',
  'f_co': 'Компания', 'f_about': 'О нас', 'f_contact': 'Контакты', 'f_mk': 'Рынки', 'f_guide': 'Гайды', 'f_priv': 'Конфиденциальность', 'f_term': 'Условия',
  'f_addr': 'Синьюй, Цзянси, Китай', 'f_copy': '© 2026 Jinba Auto Export. Все права защищены.',
  'nav': ['Главная', 'Автопарк', 'О нас', 'Процесс', 'Контакты'], 'nav_quote': 'Запрос цены',
  'lang_on': 'RU',
 },
 'ar': {
  'title': 'جينبا لتصدير السيارات | سيارات مستعملة من الصين إلى العالم',
  'desc': 'مخزون موثوق، فحص تصدير من 96 نقطة، مستندات وتخليص جمركي وشحن دولي إلى الشرق الأوسط وأفريقيا وآسيا الوسطى وروسيا.',
  'eyebrow': 'شينيو · جيانغشي · الصين',
  'h1a': 'سيارات صينية مستعملة نحو ', 'h1em': 'العالم.',
  'sub': 'مخزون موثوق، فحص من 96 نقطة، مستندات وتخليص وشحن كامل.',
  'btn_browse': 'تصفح السيارات', 'btn_advisor': 'تحدث إلى مستشار',
  'stat_inv': 'سيارة متوفرة', 'stat_photo': 'صورة حقيقية', 'stat_lang': 'لغات', 'stat_11': 'مستشار خاص',
  'inv_kicker': 'مخزون موثوق', 'inv_h2': 'سيارات جاهزة للتصدير', 'inv_more': 'كل السيارات →',
  'photo_fmt': '{} صور متاحة', 'detail': 'التفاصيل →',
  'rank_kicker': 'الأكثر تصديراً', 'rank_h2': 'ترتيب سيارات التصدير من الصين',
  'rank_sub': 'بناءً على بيانات Autostat والجمارك الصينية والتقارير المهنية — كل طراز متوفر في المخزون.',
  'rank_src': 'المصادر: Autostat 2025 · الجمارك الصينية · CADA (436 ألف سيارة في 2024)',
  'trust_kicker': 'مرخّص ومعتمد', 'trust_h2': 'تراخيص ومستندات وتخليص بلا عناء',
  'mk_kicker': 'توصيل عالمي', 'mk_h2': 'أسواق التصدير',
  'pc_kicker': 'مسار التصدير', 'pc_h2': 'من الاختيار إلى الشحن، خدمة كاملة',
  'steps': ['أخبرنا باحتياجك', 'استلم قائمة مقترحة', 'راجع ملف السيارة', 'أكّد عرض السعر', 'المستندات والجمارك', 'الشحن إلى الميناء'],
  'faq_kicker': 'أسئلة شائعة', 'faq_h2': 'الأسئلة المتكررة',
  'cta_h2': 'أخبرنا بالسيارة التي تحتاجها.', 'cta_p': 'أرسل الموديل والميزانية وميناء الوصول وسنجهز عرض سعر.', 'cta_btn': 'واتساب →',
  'f_inv': 'المخزون', 'f_all': 'كل السيارات', 'f_brand': 'حسب الماركة', 'f_cat': 'الفئات',
  'f_co': 'الشركة', 'f_about': 'من نحن', 'f_contact': 'اتصل بنا', 'f_mk': 'أسواق التصدير', 'f_guide': 'أدلة الشراء', 'f_priv': 'الخصوصية', 'f_term': 'الشروط',
  'f_addr': 'شينيو، جيانغشي، الصين', 'f_copy': '© 2026 Jinba Auto Export. جميع الحقوق محفوظة.',
  'nav': ['الرئيسية', 'المخزون', 'من نحن', 'العملية', 'اتصل بنا'], 'nav_quote': 'اطلب سعراً',
  'lang_on': 'AR',
 },
}

FUEL_DISP = {
    'zh': {'Petrol': '汽油', '插混': '插混', '纯电': '纯电', 'PHEV': '插混', 'EV': '纯电', 'Diesel': '柴油'},
    'en': {'Petrol': 'Petrol', '插混': 'PHEV', '纯电': 'EV', 'Diesel': 'Diesel'},
    'ru': {'Petrol': 'Бензин', '插混': 'Гибрид PHEV', '纯电': 'Электро', 'Diesel': 'Дизель'},
    'ar': {'Petrol': 'بنزين', '插混': 'هجين PHEV', '纯电': 'كهربائي', 'Diesel': 'ديزل'},
}

MARKETS = [
    ('uae', '阿联酋', 'UAE', 'ОАЭ', 'الإمارات'),
    ('saudi-arabia', '沙特阿拉伯', 'Saudi Arabia', 'Саудовская Арабия', 'السعودية'),
    ('kazakhstan', '哈萨克斯坦', 'Kazakhstan', 'Казахстан', 'كازاخستان'),
    ('uzbekistan', '乌兹别克斯坦', 'Uzbekistan', 'Узбекистан', 'أوزبكستان'),
    ('nigeria', '尼日利亚', 'Nigeria', 'Нигерия', 'نيجيريا'),
    ('iraq', '伊拉克', 'Iraq', 'Ирак', 'العراق'),
    ('russia', '俄罗斯', 'Russia', 'Россия', 'روسيا'),
    ('kenya', '肯尼亚', 'Kenya', 'Кения', 'كينيا'),
]

N = {'zh': '/zh/', 'en': '/en/', 'ru': '/ru/', 'ar': '/ar/'}


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def _img_w(p):
    try:
        from PIL import Image as _PIL
        with _PIL.open(ROOT / str(p).lstrip('/')) as im:
            return im.width
    except Exception:
        return None


def thumb_src(p):
    t = p.rsplit('.', 1)[0] + '.th.webp'
    return t if (ROOT / t.lstrip('/')).is_file() else p


def srcset_attr(p):
    th = thumb_src(p)
    if th == p:
        return ''
    w, tw = _img_w(p), _img_w(th)
    if not w or not tw:
        return ''
    return ' srcset="' + esc(f'{th} {tw}w, {p} {w}w') + '"'


def card_html(lang, v):
    t = v['title_i18n'][lang]
    fuel = FUEL_DISP[lang].get(v['fuel'], v['fuel'])
    nph = len(v['photos'])
    search = esc(v['title'].lower()) + ' ' + esc(v['title_i18n']['en'].lower())
    data_fuel = 'EV' if '纯电' in v['fuel'] else ('PHEV' if ('插混' in v['fuel'] or 'PHEV' in v['fuel']) else 'Petrol')
    return (f'<a class="card" data-car data-search="{search}" data-brand="{esc(v["brand"])}" '
            f'data-fuel="{data_fuel}" data-year="{v["year"]}" href="{N[lang]}cars/{v["id"]}/">'
            f'<div class="photo"><img loading="lazy" decoding="async" width="720" height="540" '
            f'src="{v["photos"][0]}"{srcset_attr(v["photos"][0])} '
            f'sizes="(max-width:600px) 48vw, (max-width:1024px) 30vw, 300px" alt="{esc(t)}">'
            f'<span class="photo-count">{t["{}`".format()] if False else L[lang]["photo_fmt"].format(nph)}</span></div>'
            f'<div class="body"><div class="meta">{v["stock_id"]} · {esc(v["brand"])} · {v["year"]}</div>'
            f'<h3>{esc(t)}</h3>'
            f'<div class="spec"><span>{v["mileage"]}</span><span>{fuel}</span></div>'
            f'<div class="foot"><span class="price">{v["price"]}</span>'
            f'<span class="more">{L[lang]["detail"]}</span></div></div></a>')


def rank_html(lang):
    out = []
    for car_id, no, rz, re_, rr, ra, srcz, srce in RANK:
        if car_id not in pub:
            continue  # 车辆下架/不存在时安全跳过，不中断首页构建
        v = pub[car_id]
        t = v['title_i18n'][lang]
        reason = {'zh': rz, 'en': re_, 'ru': rr, 'ar': ra}[lang]
        src = srcz if lang == 'zh' else srce
        data_fuel = 'EV' if '纯电' in v['fuel'] else ('PHEV' if ('插混' in v['fuel'] or 'PHEV' in v['fuel']) else 'Petrol')
        out.append(
            f'<a class="rankcard" data-car data-brand="{esc(v["brand"])}" data-fuel="{data_fuel}" '
            f'data-year="{v["year"]}" href="{N[lang]}cars/{v["id"]}/">'
            f'<div class="rank-no">#{no}</div>'
            f'<div class="rank-photo"><img loading="lazy" decoding="async" width="360" height="270" '
            f'src="{v["photos"][0]}"{srcset_attr(v["photos"][0])} sizes="96px" alt="{esc(t)}"></div>'
            f'<div class="rank-body"><h3>{esc(t)}</h3>'
            f'<p>{esc(reason)}</p>'
            f'<div class="rank-foot"><span class="price">{v["price"]}</span><span class="src">{esc(src)}</span></div>'
            f'</div></a>')
    return '\n'.join(out)


def faq_html(lang):
    out = []
    for i, (q, a) in enumerate(FAQ[lang], 1):
        out.append(f'<details class="faqitem"{" open" if i == 1 else ""}><summary>{esc(q)}</summary><p>{esc(a)}</p></details>')
    return '\n'.join(out)


def build(lang):
    d = L[lang]
    hero_car = (pub.get(7) if pub.get(7, {}).get('photos') else
                next((x for x in pub_list if x['photos']), None))  # 默认 MG ZS，异常时回退首台有图
    hero_img = hero_car['photos'][0] if hero_car else '/images/og-image.jpg'

    cards = '\n'.join(card_html(lang, pub[cid]) for cid in CARD_IDS if cid in pub)

    market_links = '\n'.join(
        f'<a class="linkcard" href="{N[lang]}markets/{slug}/"><h3>{name[lang]}</h3><span>→</span></a>'
        for slug, zh_, en_, ru_, ar_ in MARKETS
        for name in [{'zh': zh_, 'en': en_, 'ru': ru_, 'ar': ar_}]
    )

    steps = '\n'.join(f'<article class="step"><h3>{esc(s)}</h3></article>' for s in d['steps'])

    langs = ''.join(
        f'<a class="{"active" if lg == lang else ""}" href="{N[lg]}">{L[lg]["lang_on"]}</a>'
        for lg in ['en', 'zh', 'ru', 'ar'])

    dirattr = ' rtl' if lang == 'ar' else ''
    html = f'''<!doctype html><html lang="{"ar" if lang=="ar" else ("zh-CN" if lang=="zh" else lang)}" dir="{"rtl" if lang=="ar" else "ltr"}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#0b2239"><meta name="google-site-verification" content="hpe_PNYRQogsN199OCEqggbxRhlvZKMk3oylavUxvK0"><title>{esc(d["title"])}</title><meta name="description" content="{esc(d["desc"])}"><meta name="keywords" content="used cars china, export cars, chinese cars, BYD, Chery, Haval, auto export, used vehicle export, used car from china"><meta property="og:site_name" content="Jinba Auto Export"><meta property="og:locale" content="{lang}"><meta property="og:title" content="{esc(d["title"])}"><meta property="og:description" content="{esc(d["desc"])}"><meta property="og:type" content="website"><meta property="og:url" content="https://jinbacars.com{N[lang]}"><meta property="og:image" content="https://jinbacars.com/uploads/cars/60/primary.jpg"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(d["title"])}"><meta name="twitter:description" content="{esc(d["desc"])}"><meta name="twitter:image" content="https://jinbacars.com/uploads/cars/60/primary.jpg"><link rel="canonical" href="https://jinbacars.com{N[lang]}"><link rel="alternate" hreflang="en" href="https://jinbacars.com/en/"><link rel="alternate" hreflang="zh" href="https://jinbacars.com/zh/"><link rel="alternate" hreflang="ru" href="https://jinbacars.com/ru/"><link rel="alternate" hreflang="ar" href="https://jinbacars.com/ar/"><link rel="alternate" hreflang="x-default" href="https://jinbacars.com/en/"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="alternate" type="application/rss+xml" title="Jinba Auto Export Inventory" href="/feed.xml"><link rel="preconnect" href="https://www.googletagmanager.com"><link rel="preconnect" href="https://wa.me"><link rel="stylesheet" href="/assets/design-system.css?v=1"><script async src="https://www.googletagmanager.com/gtag/js?id=G-3SVJ44HVKC"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-3SVJ44HVKC');</script><script defer src="/assets/app.js?v=1"></script><script type="application/ld+json">{{"@context": "https://schema.org", "@type": "Organization", "name": "Jinba Auto Export", "url": "https://jinbacars.com", "email": "jian5222@gmail.com", "telephone": "+86 180 7908 9999", "address": {{"@type": "PostalAddress", "addressLocality": "Xinyu", "addressRegion": "Jiangxi", "addressCountry": "CN"}}}}</script></head><body class="home"{dirattr}><header class="header"><nav class="wrap nav"><a class="brand" href="{N[lang]}"><span class="mark">J</span><span>JINBA AUTO<small>USED CAR EXPORT</small></span></a><button class="hamb" onclick="toggleNav(this)" aria-label="Menu" aria-expanded="false" aria-controls="navlinks">☰</button><div class="navlinks" id="navlinks"><a href="{N[lang]}">{d["nav"][0]}</a><a href="{N[lang]}cars/">{d["nav"][1]}</a><a href="{N[lang]}about/">{d["nav"][2]}</a><a href="{N[lang]}#process">{d["nav"][3]}</a><a href="{N[lang]}contact/">{d["nav"][4]}</a><span class="langs">{langs}</span><a class="quote" href="https://wa.me/8618079089999">{d["nav_quote"]}</a></div></nav></header><main><section class="hero"><div class="wrap hero-grid"><div><div class="eyebrow">{d["eyebrow"]}</div><h1>{esc(d["h1a"])}<em>{esc(d["h1em"])}</em></h1><p>{esc(d["sub"])}</p><div class="actions"><a class="btn primary" href="{N[lang]}cars/">{d["btn_browse"]}</a><a class="btn secondary" data-track="whatsapp" href="https://wa.me/8618079089999">{d["btn_advisor"]}</a></div></div><div class="hero-img"><img width="720" height="540" fetchpriority="high" src="{hero_img}" alt="Jinba Auto Export vehicle"></div></div></section><div class="wrap stats"><div class="stat"><b>{published_n}</b><span>{d["stat_inv"]}</span></div><div class="stat"><b>{photo_n}</b><span>{d["stat_photo"]}</span></div><div class="stat"><b>4</b><span>{d["stat_lang"]}</span></div><div class="stat"><b>1-to-1</b><span>{d["stat_11"]}</span></div></div><section class="section"><div class="wrap"><div class="head"><div><div class="kicker">{d["inv_kicker"]}</div><h2>{d["inv_h2"]}</h2></div><a href="{N[lang]}cars/">{d["inv_more"]}</a></div><div class="grid">{cards}</div></div></section><section class="section alt"><div class="wrap"><div class="head"><div><div class="kicker">{d["rank_kicker"]}</div><h2>{d["rank_h2"]}</h2></div></div><p class="lead" style="max-width:860px">{esc(d["rank_sub"])}</p><div class="rankgrid">{rank_html(lang)}</div><div class="ranknote">{esc(d["rank_src"])}</div></div></section><section class="section"><div class="wrap"><div class="head"><div><div class="kicker">{d["trust_kicker"]}</div><h2>{d["trust_h2"]}</h2></div><a href="{N[lang]}about/">{d["f_about"]} →</a></div><div class="trustgrid"><div class="trustcard"><img loading="lazy" decoding="async" width="640" height="440" src="/images/certs/certificates.svg" alt="Jinba Auto Export certificates"></div><div class="trustcard"><img loading="lazy" decoding="async" width="640" height="440" src="/images/certs/export-docs.svg" alt="Export documentation"></div><div class="trustcard"><img loading="lazy" decoding="async" width="640" height="440" src="/images/certs/markets-board.svg" alt="Destination markets"></div></div></div></section><section class="section alt"><div class="wrap"><div class="head"><div><div class="kicker">{d["mk_kicker"]}</div><h2>{d["mk_h2"]}</h2></div><a href="{N[lang]}markets/">{d["mk_h2"]} →</a></div><div class="linkgrid compact">{market_links}</div></div></section><section class="section" id="process"><div class="wrap"><div class="head"><div><div class="kicker">{d["pc_kicker"]}</div><h2>{d["pc_h2"]}</h2></div></div><div class="steps">{steps}</div></div></section><section class="section"><div class="wrap"><div class="head"><div><div class="kicker">{d["faq_kicker"]}</div><h2>{d["faq_h2"]}</h2></div></div><div class="faqwrap">{faq_html(lang)}</div></div></section><section class="section"><div class="wrap cta"><div><h2>{esc(d["cta_h2"])}</h2><p>{esc(d["cta_p"])}</p></div><a class="btn" data-track="whatsapp" href="https://wa.me/8618079089999">{esc(d["cta_btn"])}</a></div></section></main><footer><div class="wrap"><div class="footergrid"><div><h4>JINBA AUTO EXPORT</h4><p>{d["f_addr"]}</p></div><div><h4>{d["f_inv"]}</h4><a href="{N[lang]}cars/">{d["f_all"]}</a><a href="{N[lang]}brands/">{d["f_brand"]}</a><a href="{N[lang]}categories/">{d["f_cat"]}</a></div><div><h4>{d["f_co"]}</h4><a href="{N[lang]}about/">{d["f_about"]}</a><a href="{N[lang]}contact/">{d["f_contact"]}</a><a href="{N[lang]}markets/">{d["f_mk"]}</a><a href="{N[lang]}guides/">{d["f_guide"]}</a><a href="{N[lang]}privacy/">{d["f_priv"]}</a><a href="{N[lang]}terms/">{d["f_term"]}</a></div><div><h4>{"اتصل بنا" if lang=="ar" else ("Контакты" if lang=="ru" else ("Contact" if lang=="en" else "联系我们"))}</h4><a href="https://wa.me/8618079089999">WhatsApp: +86 180 7908 9999</a><a href="mailto:jian5222@gmail.com">jian5222@gmail.com</a></div></div><div class="copyright">{d["f_copy"]}</div><div class="footer-wm" aria-hidden="true">JINBA CARS</div></div></footer></body></html>'''
    out = ROOT / lang / 'index.html'
    out.write_text(html, encoding='utf-8')
    print('written', out, len(html))


for lg in ['en', 'zh', 'ru', 'ar']:
    build(lg)
print('ALL DONE')
