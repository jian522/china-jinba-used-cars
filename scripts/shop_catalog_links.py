"""Crawlable, attributed links from the independent site to export listings."""
from html import escape
from urllib.parse import urlencode

BASE = 'https://shop.jinbacars.com'
COPY = {
    'en': ('Export catalogue', 'Compare export listings', 'Explore these models and request a destination-specific quote. Availability and vehicle details are confirmed per enquiry.'),
    'zh': ('出口商品目录', '比较出口车型并询价', '查看以下车型，按目的地获取人工报价。每条挂牌的可售情况和车辆信息须单独确认。'),
    'ru': ('Каталог для экспорта', 'Сравнить модели для экспорта', 'Посмотрите модели и запросите расчёт для вашей страны. Наличие и данные каждой машины уточняются по запросу.'),
    'ar': ('كتالوج التصدير', 'قارن طرازات السيارات للتصدير', 'تصفح الطرازات واطلب عرضاً حسب وجهتك. يتم تأكيد التوافر وبيانات كل سيارة عند الاستفسار.'),
}
MODELS = (
    ('2023 Geely Coolray (Binyue) 1.5T', '2023-geely-coolray-binyue-1-5t-compact-suv-export-ready-lhd'),
    ('2024 Chery Tiggo 8 PRO 390T', 'chery-tiggo-8-pro-2024-390t-suv-export-ready-lhd'),
    ('2021 Haval H6 1.5T', 'haval-h6-2021-1-5t-suv-export-ready-lhd-2'),
    ('2023 BYD Atto 3 (Yuan Plus) 510km', '2023-byd-yuan-plus-atto-3-510km-flagship-electric-suv-export-ready-lhd'),
    ('2023 BYD Dolphin 420km', '2023-byd-dolphin-420km-free-edition-electric-hatchback-export-lhd'),
)

def destination(path, lang, placement):
    params = urlencode({'utm_source': 'jinbacars', 'utm_medium': 'referral',
                        'utm_campaign': 'shop_catalog_20261009',
                        'utm_content': f'{lang}_{placement}'})
    return escape(f'{BASE}{path}?{params}', quote=True)

def catalog_link(lang, placement, class_name=''):
    cls = f' class="{escape(class_name, quote=True)}"' if class_name else ''
    return f'<a{cls} href="{destination("/collections/all", lang, placement)}">{escape(COPY[lang][0])}</a>'

def model_links(lang, placement):
    label, heading, note = COPY[lang]
    links = ''.join(
        f'<a href="{destination("/products/" + handle, lang, placement + "_" + str(i))}" '
        f'style="display:block;flex:1 1 210px;padding:12px 16px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;color:#0a1628;text-decoration:none;overflow-wrap:anywhere">{escape(name)} →</a>'
        for i, (name, handle) in enumerate(MODELS, 1))
    return (f'<section data-shop-catalog="{escape(placement)}" style="margin:24px auto;padding:24px;max-width:1170px;border-radius:12px;background:#f1f5f9;color:#0a1628">'
            f'<h2 style="margin:0 0 12px;font-size:24px;line-height:1.3">{escape(heading)}</h2>'
            f'<p style="margin:0 0 16px">{escape(note)}</p>'
            f'<div style="display:flex;flex-wrap:wrap;gap:12px">{links}</div>'
            f'<p style="margin:16px 0 0">{catalog_link(lang, placement + "_all")}</p></section>')
