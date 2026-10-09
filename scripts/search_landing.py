"""Buyer intent content, contextual links and truthful sitemap dates.

Published listings are inquiry candidates, not independently verified stock.
No search-volume, transaction, inspection or shipping claims are invented.
"""
import hashlib
import html
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.parse import quote, urlencode
import xml.etree.ElementTree as ET

BASE = 'https://jinbacars.com'
PATHS = ('/chinese-cars/', '/wholesale-used-cars/')
EDITED = '2026-10-09'
LABELS = {
 'en': ('Chinese cars for export', 'Wholesale used cars from China', 'Compare brands', 'Compare powertrains', 'Related buying resources', 'Ask for a quote on WhatsApp', 'Browse vehicle listings'),
 'zh': ('中国汽车采购与出口', '中国二手车批量采购', '按品牌比较', '按能源比较', '相关采购资料', '通过 WhatsApp 询价', '浏览车辆信息'),
 'ru': ('Китайские автомобили на экспорт', 'Оптовая покупка авто из Китая', 'Сравнить марки', 'Сравнить двигатели', 'Материалы для покупателя', 'Запросить цену в WhatsApp', 'Смотреть объявления'),
 'ar': ('السيارات الصينية للتصدير', 'شراء سيارات مستعملة من الصين بالجملة', 'مقارنة العلامات', 'مقارنة أنواع الوقود', 'أدلة الشراء ذات الصلة', 'اطلب عرضاً عبر واتساب', 'تصفح قوائم السيارات'),
}
COPY = {
 '/chinese-cars/': {
  'en': {
   'title': 'Chinese Cars for Export: Brands & Used Listings | JINBA CARS',
   'desc': 'Compare Chinese cars for export, including BYD, Geely, Chery, Haval and Changan. Browse used listings and ask JINBA CARS for a WhatsApp quotation.',
   'intro': 'Looking to buy Chinese cars from China? Start with the vehicle type, destination and budget. JINBA CARS in Xinyu, Jiangxi handles inquiries for used cars sourced in China. Browse published listings, compare specifications and ask us to reconfirm the selected vehicle before ordering.',
   'sections': [
    ('Chinese brands and cars sourced in China', 'Chinese cars can mean Chinese brands such as BYD, Geely, Chery, Haval and Changan, or vehicles offered in the Chinese domestic market. Check both the brand and the market specification when comparing cars. Our brand pages show the published listings for each make; a listing does not establish manufacturer authorization or destination-market certification.'),
    ('Choose petrol, electric or hybrid', 'For petrol cars, compare engine, gearbox, fuel use and parts support. For used electric vehicles, request battery-condition evidence, charging-connector details and the onboard language options. For plug-in hybrids, review both the combustion and electric systems. Domestic-market specifications can differ from the version sold locally in your country.'),
    ('Compare model names and specifications', 'Use the model name together with year, trim, drivetrain and stock number when requesting a quote. Export-market names may differ from the name used in China; confirm the actual specification rather than assuming two similar names identify the same car. Photos and listed mileage are starting points for vehicle checks.'),
    ('Turn a shortlist into a written quote', 'Send the stock numbers or models, acceptable years, quantity, budget, country and destination port on WhatsApp. Ask for current availability, vehicle identity, condition evidence and the proposed trade term. Separate freight, insurance and destination charges when comparing offers. Check local import and registration eligibility before reserving a car.'),
   ],
  },
  'zh': {
   'title': '中国汽车采购与出口：品牌及二手车信息 | 金霸 JINBA CARS',
   'desc': '比较比亚迪、吉利、奇瑞、哈弗及长安等中国汽车品牌，浏览中国二手车信息，通过 WhatsApp 联系新余金霸汽车核实车况与出口报价。',
   'intro': '采购中国汽车，先明确车型、目的地和预算。金霸汽车位于江西新余，处理中国来源二手车采购询价。浏览已发布信息、比较配置，选定车辆后再逐车核实。',
   'sections': [('中国品牌与中国来源汽车', '中国汽车既可能指比亚迪、吉利、奇瑞、哈弗、长安等中国品牌，也可能指在中国市场出售的其他品牌车辆。品牌页面展示当前已发布信息，不代表厂家授权或目的国认证。'), ('比较汽油、纯电和混动', '汽油车比较发动机、变速箱及配件支持；二手电动车需确认电池资料、充电接口和车机语言；插混车需同时检查燃油和电气系统。中国国内版本可能与目的国版本不同。'), ('核对车型名称与实际配置', '询价时提供车型、年份、配置、驱动形式和库存编号。海外车型名称可能与国内不同，不能仅凭类似名称判断是同一款。图片和标注里程是核验起点。'), ('从选车到书面报价', '通过 WhatsApp 发送编号或车型、年份范围、数量、预算、目的国及目的港。核实可售状态、车辆身份与车况资料，分开比较车价、运费、保险和目的地费用。预订前确认进口和上牌资格。')],
  },
  'ru': {
   'title': 'Китайские автомобили на экспорт: марки и б/у авто | JINBA CARS',
   'desc': 'Сравните китайские автомобили BYD, Geely, Chery, Haval и Changan. Смотрите объявления о б/у авто из Китая и запрашивайте цену через WhatsApp.',
   'intro': 'Хотите купить китайский автомобиль? Начните с типа машины, страны назначения и бюджета. JINBA CARS в Синьюе, Цзянси принимает запросы на подержанные авто из Китая. По выбранной машине наличие и характеристики подтверждаются отдельно.',
   'sections': [('Китайские марки и автомобили из Китая', 'Китайские автомобили могут означать марки BYD, Geely, Chery, Haval и Changan либо машины других марок, продаваемые в Китае. Страницы марок показывают опубликованные объявления. Они не подтверждают авторизацию производителя или сертификацию для вашей страны.'), ('Бензин, электричество или гибрид', 'У бензиновой машины сравните двигатель, коробку и поддержку запчастей. Для электромобиля запросите данные батареи, разъёма зарядки и языков системы. У PHEV проверяют и электрическую, и бензиновую часть. Китайская версия может отличаться от местной.'), ('Название модели и комплектация', 'Укажите модель, год, комплектацию, привод и номер объявления. Название модели за рубежом может отличаться от китайского: похожие названия не гарантируют одинаковую машину. Фото и заявленный пробег требуют последующей проверки.'), ('От выбора к письменной цене', 'Отправьте модели или номера, годы, количество, бюджет, страну и порт в WhatsApp. Подтвердите наличие, идентичность и состояние. Сравнивайте цену машины, фрахт, страховку и расходы назначения отдельно. До бронирования уточните возможность ввоза и регистрации.')],
  },
  'ar': {
   'title': 'السيارات الصينية للتصدير: العلامات والمستعمل | JINBA CARS',
   'desc': 'قارن سيارات BYD وجيلي وشيري وهافال وشانجان الصينية. تصفح قوائم السيارات المستعملة من الصين واطلب عرضاً من JINBA CARS عبر واتساب.',
   'intro': 'هل تريد شراء سيارة صينية؟ ابدأ بنوع السيارة والوجهة والميزانية. تستقبل JINBA CARS في شينيو، جيانغشي استفسارات السيارات المستعملة من الصين. قارن المواصفات ثم أكد التوافر والحالة للسيارة المختارة.',
   'sections': [('العلامات الصينية والسيارات من الصين', 'قد تعني السيارات الصينية علامات مثل BYD وجيلي وشيري وهافال وشانجان، أو سيارات من علامات أخرى تُباع في السوق الصينية. تعرض صفحات العلامات القوائم المنشورة ولا تثبت تفويض المصنع أو اعتماد السيارة في بلدك.'), ('بنزين أم كهربائية أم هجينة', 'قارن المحرك وناقل الحركة ودعم القطع في سيارات البنزين. للكهربائية اطلب بيانات حالة البطارية ومنفذ الشحن ولغات النظام. للهجينة القابلة للشحن افحص نظامي الوقود والكهرباء. قد تختلف النسخة المحلية الصينية عن نسخة بلدك.'), ('تأكيد اسم الطراز والمواصفات', 'أرسل الطراز والسنة والفئة ونظام الدفع ورقم المخزون. قد تختلف أسماء الطرازات خارج الصين، وتشابه الاسم لا يضمن تطابق السيارة. الصور والمسافة المنشورة نقطة بداية للتحقق.'), ('من القائمة المختصرة إلى عرض مكتوب', 'أرسل الطرازات أو الأرقام والسنوات والكمية والميزانية والبلد وميناء الوصول عبر واتساب. أكد التوافر وهوية السيارة وحالتها. قارن سعر السيارة والشحن والتأمين ورسوم الوجهة منفصلة، وتأكد من أهلية الاستيراد والتسجيل قبل الحجز.')],
  },
 },
 '/wholesale-used-cars/': {
  'en': {
   'title': 'Wholesale Used Cars from China for Dealers | JINBA CARS',
   'desc': 'Source wholesale used cars from China for your dealership or fleet. Compare listings, prepare a batch inquiry and request a written quote on WhatsApp.',
   'intro': 'Buying for a dealership, resale business or fleet requires a shortlist that matches your customers and destination. JINBA CARS handles China used-car sourcing inquiries for single vehicles and proposed batches. Quantity, availability, export eligibility and shipping options are confirmed for each request.',
   'sections': [
    ('Build a dealer buying brief', 'List the models your customers need, acceptable years, mileage limits, steering position, powertrain, budget per car and target quantity. Include must-have specifications and acceptable alternatives. Separate an immediate order from an estimated future purchasing volume so the quote reflects the actual request.'),
    ('Check every car in a proposed batch', 'A batch is a group of individual vehicles. Ask for a separate stock number, identity details, current photos and condition information for each unit. Agree which checks or independent inspections will be available before payment. For EVs and hybrids, include battery-condition evidence and charging compatibility in your requirements.'),
    ('Compare unit prices and batch costs', 'Request an itemized written quotation. Distinguish vehicle prices, domestic collection, inspections, export services, freight, insurance and destination costs. Do not assume a quantity discount or container saving: the result depends on the vehicles, locations, carrier and route. Compare the same inclusions and trade term across suppliers.'),
    ('Confirm the proposed shipment', 'Ask which departure port, transport method, loading plan and carrier acceptance apply to the selected cars. Mixed models may need a different arrangement from identical models. Shipment timing and required documents must be confirmed for that order; your destination broker should check import and registration eligibility.'),
    ('Send a wholesale inquiry on WhatsApp', 'Send your company name, models or stock numbers, quantity, budget and destination port. We can discuss a shortlist and written quotation against those requirements. A published listing is not a reservation; availability and the payment beneficiary should be reconfirmed before purchase.'),
   ],
  },
  'zh': {
   'title': '中国二手车批量采购：经销商与车队询价 | 金霸 JINBA CARS',
   'desc': '为经销商和车队采购中国二手车，比较车型信息、准备批量需求，通过 WhatsApp 联系金霸汽车获取逐车与运输费用分明的书面报价。',
   'intro': '经销商、转售商和车队采购应匹配客户需求与目的地要求。金霸汽车处理单车和拟定批次的采购询价；数量、可售状态、出口资格与运输方案需按每笔询价确认。',
   'sections': [('准备经销商需求单', '列明车型、年份范围、里程上限、方向盘位置、能源、单车预算及本次数量。注明必要配置与可接受替代车型，将即时订单与未来预计采购量分开。'), ('每台车分别核验', '批次由具体车辆组成。逐车索取编号、身份资料、当前照片及车况，约定付款前能提供哪些核验或独立验车。新能源车补充电池及充电兼容要求。'), ('比较单车与批次费用', '要求书面报价分列车价、国内集运、验车、出口服务、运费、保险及目的地费用。不能默认批量折扣或装柜节省金额：费用取决于车型、所在地、承运人和路线。'), ('确认运输方案', '逐单确认出港口、运输方式、装载方案及承运人接收条件。混装与同款车可能需要不同方案。时效与文件按具体订单确认，进口和上牌资格交目的地清关行核实。'), ('通过 WhatsApp 发需求', '发送公司名、车型或编号、数量、预算和目的港。我们据此讨论车源与书面报价。发布信息不代表已预留，付款前再次核对可售状态与收款主体。')],
  },
  'ru': {
   'title': 'Б/у авто из Китая оптом для дилеров | JINBA CARS',
   'desc': 'Подбор б/у автомобилей из Китая для дилеров и автопарков. Сравните объявления, подготовьте запрос на партию и получите письменную цену в WhatsApp.',
   'intro': 'Для дилера или автопарка подбор должен соответствовать клиентам и стране назначения. JINBA CARS принимает запросы на отдельные машины и предполагаемые партии. Количество, наличие, возможность экспорта и доставка подтверждаются по каждому запросу.',
   'sections': [('Требования дилера', 'Укажите модели, годы, предел пробега, расположение руля, топливо, бюджет за машину и количество. Разделите текущий заказ и ожидаемые будущие закупки. Укажите обязательные опции и допустимые альтернативы.'), ('Проверка каждой машины', 'Партия состоит из отдельных автомобилей. Для каждого запросите номер, данные идентичности, актуальные фото и состояние. Согласуйте доступные проверки до оплаты, а для EV и гибридов — данные батареи и зарядки.'), ('Цена автомобиля и затраты партии', 'Запросите отдельные суммы за машины, сбор по Китаю, осмотр, экспортные услуги, фрахт, страховку и расходы назначения. Скидка за количество и экономия контейнера не предполагаются автоматически: они зависят от машины, перевозчика и маршрута.'), ('План перевозки', 'Подтвердите порт, способ перевозки, план загрузки и приёмку перевозчиком. Разные модели могут требовать отдельного плана. Сроки и документы согласуются по заказу; брокер назначения проверяет ввоз и регистрацию.'), ('Запрос через WhatsApp', 'Отправьте название компании, модели или номера, количество, бюджет и порт. По ним обсудим подборку и письменную цену. Объявление не означает резерв: до покупки повторно проверьте наличие и получателя платежа.')],
  },
  'ar': {
   'title': 'سيارات مستعملة من الصين بالجملة للتجار | JINBA CARS',
   'desc': 'توريد سيارات مستعملة من الصين للتجار والأساطيل. قارن القوائم وجهز طلب الدفعة واطلب عرضاً مكتوباً يوضح التكاليف عبر واتساب.',
   'intro': 'يتطلب الشراء للتجارة أو الأسطول قائمة تناسب العملاء والوجهة. تستقبل JINBA CARS طلبات سيارات منفردة ودفعات مقترحة. تؤكد الكمية والتوافر وأهلية التصدير وخيارات النقل لكل طلب.',
   'sections': [('متطلبات التاجر', 'حدد الطرازات والسنوات وحد المسافة وجهة المقود والوقود والميزانية لكل سيارة والكمية المطلوبة الآن. اذكر المواصفات الأساسية والبدائل المقبولة وافصل الطلب الحالي عن توقعات الشراء المستقبلية.'), ('تحقق من كل سيارة', 'تتكون الدفعة من سيارات منفردة. اطلب لكل سيارة رقم المخزون والهوية والصور الحالية وبيانات الحالة. اتفق على الفحص المتاح قبل الدفع، وأضف متطلبات البطارية والشحن للكهربائية والهجينة.'), ('سعر الوحدة وتكاليف الدفعة', 'اطلب عرضاً يفصل أسعار السيارات والتجميع المحلي والفحص وخدمات التصدير والشحن والتأمين ورسوم الوجهة. لا تفترض خصماً للكمية أو توفيراً بالحاوية، فذلك يعتمد على السيارات والمواقع والناقل والمسار.'), ('خطة النقل', 'أكد ميناء المغادرة وطريقة النقل وخطة التحميل وقبول الناقل. قد تحتاج الطرازات المختلطة إلى ترتيب مختلف. تؤكد المدة والمستندات لكل طلب، ويتحقق مخلص الوجهة من الاستيراد والتسجيل.'), ('أرسل طلبك عبر واتساب', 'أرسل اسم الشركة والطرازات أو الأرقام والكمية والميزانية وميناء الوصول لمناقشة قائمة وعرض مكتوب. نشر السيارة لا يعني حجزها؛ أعد تأكيد التوافر والمستفيد من الدفع قبل الشراء.')],
  },
 },
}

def esc(s):
    return html.escape(str(s), quote=True)

def wa_url(lang, topic, stock=''):
    stock = stock or {'en':'the requirements below','zh':'下列需求','ru':'указанным ниже требованиям','ar':'المتطلبات أدناه'}[lang]
    templates = {
      'en': 'Hello JINBA CARS, I found {topic}. Please quote {stock}. Model: __; year: __; quantity: __; budget (USD): __; country / destination port: __.',
      'zh': '您好金霸汽车，我通过{topic}联系。请为{stock}报价。车型：__；年份：__；数量：__；美元预算：__；目的国/目的港：__。',
      'ru': 'Здравствуйте JINBA CARS! Я на странице {topic}. Запрос по {stock}. Модель: __; год: __; количество: __; бюджет USD: __; страна / порт: __.',
      'ar': 'مرحباً JINBA CARS، وصلت من {topic}. أطلب عرضاً لـ {stock}. الطراز: __؛ السنة: __؛ الكمية: __؛ الميزانية USD: __؛ البلد / الميناء: __.',
    }
    return 'https://wa.me/8618079089999?' + urlencode({'text': templates[lang].format(topic=topic, stock=stock)})

def resource_links(lang):
    return ''.join(f'<p><a href="/{lang}{path}">{esc(LABELS[lang][i])}</a></p>' for i, path in enumerate(PATHS))

def home_discovery(lang):
    cards = ''.join(f'<article style="padding:24px;border:1px solid #dce3ec;border-radius:16px"><h3><a href="/{lang}{path}">{esc(LABELS[lang][i])}</a></h3><p>{esc(COPY[path][lang]["desc"])}</p></article>' for i,path in enumerate(PATHS))
    return f'<section class="jv7-section"><div class="jv7-container"><div class="jv7-secthead"><h2 class="jv7-h2">{esc(LABELS[lang][4])}</h2></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr));gap:24px">{cards}</div></div></section>'

def related(lang, brand='', fuel=''):
    labels = LABELS[lang]
    links = [(labels[0], PATHS[0]), (labels[1], PATHS[1])]
    if brand:
        links.insert(0, (brand, '/brands/' + re.sub(r'[^a-z0-9]+', '-', brand.lower()).strip('-') + '/'))
    slug = {'EV': 'ev', 'PHEV': 'phev', 'Petrol': 'petrol', 'Diesel': 'diesel'}.get(fuel)
    if slug:
        links.insert(1, (fuel, f'/categories/{slug}/'))
    guide = {'en': 'Buy used cars from China', 'zh': '中国二手车采购指南', 'ru': 'Как купить авто из Китая', 'ar': 'دليل شراء السيارات من الصين'}[lang]
    links.append((guide, '/guides/buy-used-cars-from-china/'))
    return '<aside class="checkpanel"><h2>' + esc(labels[4]) + '</h2><ul>' + ''.join(f'<li><a href="/{lang}{path}">{esc(label)}</a></li>' for label, path in links) + '</ul></aside>'

def collection_schema(lang, path, title, cars):
    return {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': title,
      'url': BASE + '/' + lang + path, 'inLanguage': lang,
      'publisher': {'@id': BASE + '/#organization'},
      'mainEntity': {'@type': 'ItemList', 'numberOfItems': len(cars), 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'url': f'{BASE}/{lang}/cars/{v["id"]}/'} for i, v in enumerate(cars)]}}

def landing(lang, path, vehicles, head, header, footer, card, breadcrumbs, jsonld):
    c = COPY[path][lang]; labels = LABELS[lang]
    index = PATHS.index(path)
    # One listing per supplier source in this preview; no claim of stock counts.
    seen = set(); preview = []
    for v in vehicles:
        key = v.get('source') or v['stock_id']
        if key not in seen:
            seen.add(key); preview.append(v)
        if len(preview) == 8:
            break
    crumb = breadcrumbs(lang, [( {'en':'Home','zh':'首页','ru':'Главная','ar':'الرئيسية'}[lang], f'/{lang}/'), (labels[index], f'/{lang}{path}')])
    schema = collection_schema(lang, path, labels[index], preview)
    brands = sorted({v['brand'] for v in vehicles})
    brand_links = ''.join(f'<li><a href="/{lang}/brands/{re.sub(r"[^a-z0-9]+", "-", b.lower()).strip("-")}/">{esc(b)}</a></li>' for b in brands)
    fuels = [('ev','EV'),('phev','PHEV'),('petrol','Petrol'),('diesel','Diesel')]
    fuel_links = ''.join(f'<li><a href="/{lang}/categories/{s}/">{f}</a></li>' for s,f in fuels if any(v.get('fuel') == f for v in vehicles))
    body = ''.join(f'<section><h2>{esc(h)}</h2><p>{esc(p)}</p></section>' for h,p in c['sections'])
    cta = f'<div class="actions"><a class="btn primary" data-track="whatsapp" data-topic="{path.strip("/")}" href="{esc(wa_url(lang, labels[index]))}">{esc(labels[5])}</a><a class="btn" href="/{lang}/cars/">{esc(labels[6])}</a></div>'
    return head(lang,c['title'],c['desc'],path,extra_schema=jsonld(schema))+header(lang,path)+f'<section class="pagehead"><div class="wrap"><h1>{esc(labels[index])}</h1><p>{esc(c["intro"])}</p>{cta}</div></section><main><section class="section"><article class="wrap contentpage">{crumb}{body}<h2>{esc(labels[2])}</h2><ul class="seo-linklist">{brand_links}</ul><h2>{esc(labels[3])}</h2><ul>{fuel_links}</ul>{related(lang)}{cta}</article></section><section class="section alt"><div class="wrap"><h2>{esc(labels[6])}</h2><div class="grid">'+''.join(card(v,lang) for v in preview)+'</div></div></section></main>'+footer(lang)

BRAND_TEXT = {
 'en': 'Compare used {brand} cars from China by model, year, mileage and powertrain. The names below come from the published listings. Open a vehicle to review its photos and indicative price, then ask us to reconfirm availability and specification. For an EV or hybrid, include battery and charging requirements. Your destination and selected vehicle determine import eligibility and export terms.',
 'zh': '按车型、年份、里程和能源比较中国来源的{brand}二手车。下列名称来自已发布信息。打开详情查看图片及参考价，再核实可售情况与配置。新能源车还需提供电池及充电要求。进口资格与出口条款按目的地和具体车辆确认。',
 'ru': 'Сравните б/у {brand} из Китая по модели, году, пробегу и двигателю. Названия ниже взяты из объявлений. Откройте машину для просмотра фото и ориентировочной цены, затем подтвердите наличие и комплектацию. Для EV и гибрида уточните батарею и зарядку. Возможность ввоза и условия экспорта зависят от машины и страны.',
 'ar': 'قارن سيارات {brand} المستعملة من الصين حسب الطراز والسنة والمسافة ونوع الوقود. الأسماء أدناه من القوائم المنشورة. افتح السيارة لمراجعة الصور والسعر الاسترشادي ثم أكد التوافر والمواصفات. للكهربائية والهجينة حدد متطلبات البطارية والشحن. تعتمد أهلية الاستيراد وشروط التصدير على السيارة والوجهة.',
}

def brand_intro(lang, brand, cars):
    models = sorted({v.get('title_i18n', {}).get(lang) or v.get('title', '') for v in cars})
    return '<div class="articlebody"><p>' + esc(BRAND_TEXT[lang].format(brand=brand)) + '</p><ul>' + ''.join('<li>'+esc(m)+'</li>' for m in models[:6]) + '</ul><div class="actions"><a class="btn primary" data-track="whatsapp" data-topic="brand" href="'+esc(wa_url(lang,brand))+'">'+esc(LABELS[lang][5])+'</a></div></div>'

GUIDE_SECTIONS = {
 'vehicle-inspection-checklist': {
  'en': [('Identify the actual vehicle', 'Match the VIN, registration information, stock number and current exterior photos. Request available ownership and service records. Ask who performed the inspection, when it happened and which items were checked.'), ('Review condition and inspection scope', 'Discuss accident repairs, flood or fire history, corrosion, brakes, tyres, suspension, engine and gearbox. Agree on an independent inspection where needed. For EVs, request battery-condition evidence and explain the charging equipment used at your destination.'), ('Record exceptions before purchase', 'Keep the report, photos and agreed repairs with the written quotation. Listed mileage is not an independent mileage verification. A general checklist on this site does not mean that every published car has completed these checks.')],
  'zh': [('确认具体车辆身份', '将 VIN、登记资料、库存号与当前外观照片对应。索取可提供的权属和保养资料，确认检测人、检测时间及检查范围。'), ('核对车况与检测范围', '讨论事故维修、泡水、火烧、锈蚀、制动、轮胎、悬架、发动机和变速箱，必要时约定独立验车。新能源车索取电池资料并说明目的地充电设备。'), ('购买前记录例外', '将报告、照片及约定维修附在书面报价中。标注里程不等于独立核实里程，网站清单也不代表每台车已完成检查。')],
  'ru': [('Идентификация машины', 'Сопоставьте VIN, регистрацию, номер объявления и актуальные фото. Запросите доступные сведения о владельце и обслуживании. Уточните исполнителя, дату и объём осмотра.'), ('Состояние и объём проверки', 'Обсудите ДТП, затопление, пожар, коррозию, тормоза, шины, подвеску, двигатель и коробку. При необходимости согласуйте независимый осмотр. Для EV запросите данные батареи и уточните зарядное оборудование.'), ('Зафиксируйте исключения', 'Приложите отчёт, фото и согласованный ремонт к предложению. Заявленный пробег не равен независимой проверке. Общий список не означает, что все объявления прошли осмотр.')],
  'ar': [('هوية السيارة', 'طابق VIN والتسجيل ورقم المخزون والصور الحالية. اطلب بيانات الملكية والصيانة المتاحة وحدد منفذ الفحص وتاريخه ونطاقه.'), ('الحالة ونطاق الفحص', 'ناقش الحوادث والغرق والحريق والصدأ والفرامل والإطارات والتعليق والمحرك وناقل الحركة. اتفق على فحص مستقل عند الحاجة. للكهربائية اطلب بيانات البطارية ووضح معدات الشحن في الوجهة.'), ('توثيق الاستثناءات', 'أرفق التقرير والصور والإصلاحات المتفق عليها بالعرض. المسافة المنشورة ليست تحققاً مستقلاً، والقائمة العامة لا تعني فحص كل سيارة منشورة.')],
 },
 'export-documents-and-shipping': {
  'en': [('Agree the transport plan', 'Confirm the selected vehicle, departure port, destination port, proposed carrier and transport method. Ask about carrier acceptance and vehicle-specific loading requirements before booking; an estimated transit time is not a fixed delivery promise.'), ('Agree a document list', 'Ask the seller, freight provider and destination broker which invoice, packing, transport, export and vehicle-identity documents apply to this shipment. Match the beneficiary and vehicle details across the documents. Request available drafts for review before the agreed payment milestone.'), ('Define included costs and responsibilities', 'Write down the offered trade term and who arranges freight, insurance, loading, destination handling and clearance. Ask the destination broker to estimate local costs separately. Document requirements and route availability must be reconfirmed for the order.')],
  'zh': [('确认运输方案', '确认具体车辆、出港口、目的港、拟用承运人与运输方式。订舱前核对接收条件及装载要求，预计运输时间不是固定交付承诺。'), ('约定文件清单', '向卖方、物流方和目的地清关行确认本单所需发票、装箱、运输、出口及车辆身份文件。核对文件中的车辆与收款主体，在约定付款节点前审阅可提供的草稿。'), ('明确费用与责任', '写明贸易条款及运费、保险、装载、目的地处理与清关各由谁负责。目的地费用单独估算，文件与航线按订单重新确认。')],
  'ru': [('План перевозки', 'Подтвердите машину, порты, перевозчика и способ доставки. До бронирования уточните приёмку и требования погрузки. Оценка времени в пути не является обещанием фиксированной даты.'), ('Список документов', 'Согласуйте с продавцом, перевозчиком и брокером инвойс, упаковочные, транспортные, экспортные документы и идентификацию машины для данного заказа. Сопоставьте машину и получателя платежа; запросите доступные проекты до этапа оплаты.'), ('Расходы и ответственность', 'Запишите условие поставки и ответственных за фрахт, страховку, погрузку, обработку и таможню назначения. Местные расходы оцените отдельно; документы и маршрут подтверждаются по заказу.')],
  'ar': [('خطة النقل', 'أكد السيارة وميناءي المغادرة والوصول والناقل وطريقة النقل. تحقق من قبول الناقل ومتطلبات التحميل قبل الحجز. مدة العبور التقديرية ليست موعد تسليم مضموناً.'), ('قائمة المستندات', 'اتفق مع البائع والناقل ومخلص الوجهة على الفاتورة والتعبئة والنقل والتصدير وهوية السيارة المطلوبة لهذه الشحنة. طابق السيارة والمستفيد وراجع المسودات المتاحة قبل مرحلة الدفع المتفق عليها.'), ('التكاليف والمسؤوليات', 'حدد شرط التجارة والمسؤول عن الشحن والتأمين والتحميل والمناولة والتخليص في الوجهة. قدر رسوم الوجهة منفصلة وأعد تأكيد المستندات والمسار لكل طلب.')],
 },
 'safe-payment-and-quotation': {
  'en': [('Compare like-for-like quotations', 'Use the same vehicle, currency, trade term, departure port and included services when comparing offers. A listing price is indicative. Ask for quote validity and separately stated freight, insurance and destination expenses.'), ('Verify the contracting party and beneficiary', 'Request company details and check them against the contract and payment instructions. Independently verify an unexpected change of bank account using a contact you already know. Agree payment milestones and the vehicle evidence available at each stage.'), ('Keep a complete order record', 'Keep the stock number, vehicle identity, condition exceptions, document list, inspection scope and agreed responsibilities with the contract. Resolve inconsistencies before paying. Ask how cancellations, unavailable vehicles and disputed condition will be handled in the written agreement.')],
  'zh': [('统一报价比较口径', '以相同车辆、币种、贸易条款、出港口及服务范围比较报价。挂牌价是参考价，索取有效期并单列运费、保险和目的地费用。'), ('核实签约方与收款主体', '索取公司资料并与合同、付款信息核对。遇到收款账户突然变更，通过已有可信联系方式独立核实。约定付款节点及每阶段可提供的车辆资料。'), ('保存完整订单记录', '记录车辆编号、身份、车况例外、文件、验车范围与责任。付款前解决矛盾，并在书面协议中明确取消、车辆不可售及车况争议的处理。')],
  'ru': [('Сопоставимые цены', 'Сравнивайте одинаковую машину, валюту, условие поставки, порт и услуги. Цена объявления ориентировочная. Запросите срок действия цены и отдельные расходы на фрахт, страховку и назначение.'), ('Компания и получатель платежа', 'Сверьте данные компании с договором и платёжными инструкциями. Неожиданную смену счёта подтвердите независимо через известный контакт. Согласуйте этапы оплаты и доказательства по машине на каждом этапе.'), ('Запись заказа', 'Сохраните номер, идентичность, исключения по состоянию, документы, осмотр и обязанности с договором. До оплаты устраните противоречия; письменно согласуйте отмену, отсутствие машины и споры по состоянию.')],
  'ar': [('عروض قابلة للمقارنة', 'قارن السيارة نفسها والعملة وشرط التجارة والميناء والخدمات المشمولة. سعر القائمة استرشادي. اطلب صلاحية العرض وتكاليف الشحن والتأمين والوجهة منفصلة.'), ('الشركة والمستفيد', 'طابق بيانات الشركة مع العقد وتعليمات الدفع. تحقق مستقلاً عبر جهة اتصال معروفة عند تغيير الحساب فجأة. اتفق على مراحل الدفع وأدلة السيارة المتاحة في كل مرحلة.'), ('سجل الطلب', 'احتفظ بالرقم والهوية واستثناءات الحالة والمستندات ونطاق الفحص والمسؤوليات. عالج التناقضات قبل الدفع واتفق كتابة على الإلغاء وعدم التوافر والنزاع حول الحالة.')],
 },
}

def guide_content(lang, slug):
    sections = GUIDE_SECTIONS.get(slug, {}).get(lang)
    if slug == 'used-ev-export-china-byd':
        sections = [COPY[PATHS[0]][lang]['sections'][1], GUIDE_SECTIONS['vehicle-inspection-checklist'][lang][0], GUIDE_SECTIONS['export-documents-and-shipping'][lang][0]]
    if slug in ('import-china-cars-to-kenya', 'import-china-cars-to-nigeria'):
        country = 'Kenya' if 'kenya' in slug else 'Nigeria'
        # Avoid unsourced legal limits; use a destination-specific buying brief.
        intro = {
         'en': f'For a shipment to {country}, send the destination port and ask your local broker to confirm the selected vehicle’s age, steering position, emissions, inspection requirements, taxes and registration eligibility. Compare a complete landed-cost estimate before ordering; this guide does not specify current legal limits or tax rates.',
         'zh': f'拟发往 {country} 的订单应提供目的港，请当地清关行逐车确认车龄、方向盘位置、排放、检验、税费和上牌资格。下单前比较完整到岸成本，本指南不提供未经核实的现行法规数值。',
         'ru': f'Для отправки в {country} укажите порт. Местный брокер должен подтвердить возраст, руль, выбросы, осмотр, налоги и регистрацию выбранной машины. До заказа сравните полную стоимость; здесь не приводятся непроверенные действующие ставки или ограничения.',
         'ar': f'للشحن إلى {country} أرسل ميناء الوصول. اطلب من مخلص محلي تأكيد العمر وجهة المقود والانبعاثات والفحص والضرائب والتسجيل للسيارة المختارة. قارن التكلفة الكاملة قبل الطلب؛ لا يحدد الدليل قيوداً أو معدلات قانونية حالية غير متحققة.',
        }[lang]
        sections = [(country, intro), GUIDE_SECTIONS['safe-payment-and-quotation'][lang][0], GUIDE_SECTIONS['export-documents-and-shipping'][lang][1]]
    if not sections:
        return ''
    body = ''.join(f'<section><h2>{esc(h)}</h2><p>{esc(p)}</p></section>' for h,p in sections)
    return body + related(lang) + '<div class="actions"><a class="btn primary" data-track="whatsapp" data-topic="'+esc(slug)+'" href="'+esc(wa_url(lang,slug))+'">'+esc(LABELS[lang][5])+'</a></div>'

def write_sitemap(root, urls):
    """Retain dates only for content observed changing; never reset at rebuild."""
    state_path = root / 'data/seo_page_state.json'
    previous = json.loads(state_path.read_text('utf-8')) if state_path.exists() else {}
    today = datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat()
    ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    xns = 'http://www.w3.org/1999/xhtml'
    ET.register_namespace('', ns); ET.register_namespace('xhtml', xns)
    tree = ET.Element('{'+ns+'}urlset'); state = {}
    for url in urls:
        content = (root / url.removeprefix(BASE).lstrip('/') / 'index.html').read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        old = previous.get(url, {})
        # Without historical content hashes, establish a baseline without guessing.
        modified = old.get('lastmod') if old.get('sha256') == digest else (today if old else None)
        state[url] = {'sha256':digest, 'lastmod':modified}
        item = ET.SubElement(tree, '{'+ns+'}url'); ET.SubElement(item, '{'+ns+'}loc').text = url
        if modified:
            ET.SubElement(item, '{'+ns+'}lastmod').text = modified
        path = '/' + url.removeprefix(BASE).lstrip('/').split('/',1)[1]
        for lang in ('en','zh','ru','ar','x-default'):
            ET.SubElement(item, '{'+xns+'}link', rel='alternate', hreflang=lang, href=BASE+'/'+('en' if lang=='x-default' else lang)+path)
    ET.ElementTree(tree).write(root/'sitemap.xml',encoding='utf-8',xml_declaration=True)
    state_path.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
