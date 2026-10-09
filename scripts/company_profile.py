"""Shared public business identity and buyer-focused search content.

Address confirmed by the owner on 2026-10-09. No unverified legal name,
opening hours, coordinates or ratings are inferred from the address.
"""
import html
import json

BASE = 'https://jinbacars.com'
BUYER_PATH = '/guides/buy-used-cars-from-china/'
ADDRESS = {
    'en': 'Building 11, Jiuding Automobile Market, Xinyu, Jiangxi, China',
    'zh': '江西省新余市九鼎汽车市场11栋',
    'ru': 'Корпус 11, автомобильный рынок Цзюдин, Синьюй, Цзянси, Китай',
    'ar': 'المبنى 11، سوق جيودينغ للسيارات، شينيو، جيانغشي، الصين',
}
BUYER_LABEL = {
    'en': 'Buy used cars from China', 'zh': '中国二手车采购指南',
    'ru': 'Покупка б/у авто из Китая', 'ar': 'شراء سيارات مستعملة من الصين',
}
HOME = {
    'en': ('Used Cars from China & Export Inquiries | JINBA CARS',
           'Browse used cars from China with JINBA CARS in Xinyu. Compare vehicle details and request export quotations on WhatsApp.'),
    'zh': ('中国汽车与二手车出口询价 | 金霸汽车 JINBA CARS',
           '金霸汽车位于江西新余九鼎汽车市场11栋，提供中国汽车与二手车采购咨询。浏览车型、照片和挂牌参考价，通过 WhatsApp 获取出口书面报价。'),
    'ru': ('Подержанные авто из Китая: запрос на экспорт | JINBA CARS',
           'JINBA CARS в Синьюе: подержанные автомобили из Китая, сведения о машинах и письменное экспортное предложение через WhatsApp.'),
    'ar': ('سيارات مستعملة من الصين وعروض التصدير | JINBA CARS',
           'تصفح السيارات المستعملة من الصين مع JINBA CARS في شينيو، وراجع تفاصيل السيارة واطلب عرض تصدير مكتوباً عبر واتساب.'),
}
META = {
    'en': {
        '/cars/': ('Used Cars from China: Vehicle Listings | JINBA CARS', 'Explore used cars from China by brand, year, fuel and price. View photos and mileage, then confirm availability and export terms with JINBA CARS.'),
        '/about/': ('About JINBA CARS | Used-Car Sourcing in Xinyu, China', 'Meet JINBA CARS at Jiuding Automobile Market in Xinyu, Jiangxi. Learn how we handle China used-car inquiries, vehicle checks and export quotations.'),
        '/contact/': ('Contact JINBA CARS | WhatsApp & Xinyu Company Address', 'Contact JINBA CARS on WhatsApp +86 180 7908 9999 or by email. Find our Xinyu address and request a used-car export quotation from China.'),
        BUYER_PATH: ('Buy Used Cars from China: Buyer Guide | JINBA CARS', 'Learn how to source used cars from China, compare vehicle evidence, prepare an inquiry and review a written export quotation with JINBA CARS.'),
    },
    'zh': {
        '/cars/': ('中国二手车车源、车型与参考价 | 金霸汽车 JINBA CARS', '浏览中国二手车信息，按品牌、年份、能源和价格筛选，查看车辆照片与里程。联系新余金霸汽车核实可售状态、车况及出口报价。'),
        '/about/': ('关于金霸汽车 | 中国新余二手车采购咨询 JINBA CARS', '金霸汽车 JINBA CARS 位于江西省新余市九鼎汽车市场11栋，协调中国来源二手车采购询盘、车辆核验及出口书面报价。'),
        '/contact/': ('联系金霸汽车 | 新余地址与 WhatsApp JINBA CARS', '金霸汽车地址：江西省新余市九鼎汽车市场11栋。WhatsApp：+86 180 7908 9999。发送车型、预算、数量与目的港，咨询中国二手车出口报价。'),
        BUYER_PATH: ('中国二手车采购与出口询价指南 | 金霸汽车 JINBA CARS', '了解从中国采购二手车的步骤、车辆资料核验、询价所需信息与费用比较方法，联系江西新余金霸汽车获取针对具体车辆的书面报价。'),
    },
}
SHORT_GUIDE_TITLES = {
    'import-china-cars-to-kenya': {'en': 'China Used Cars to Kenya: Buyer Checklist', 'ru': 'Б/у авто из Китая в Кению: проверка перед покупкой', 'ar': 'سيارات الصين المستعملة إلى كينيا: دليل المشتري'},
    'import-china-cars-to-nigeria': {'en': 'China Used Cars to Nigeria: Buyer Checklist', 'ru': 'Б/у авто из Китая в Нигерию: проверка перед покупкой', 'ar': 'سيارات الصين المستعملة إلى نيجيريا: دليل المشتري'},
    'used-ev-export-china-byd': {'en': 'Used EVs from China: BYD Buyer Checklist', 'ru': 'Б/у электромобили BYD из Китая: проверка', 'ar': 'سيارات BYD الكهربائية المستعملة من الصين'},
}

def organization():
    return {
        '@context': 'https://schema.org', '@type': 'Organization',
        '@id': BASE + '/#organization', 'name': 'JINBA CARS',
        'alternateName': ['Jinba Auto Export', '金霸汽车'], 'url': BASE + '/',
        'email': 'jian5222@gmail.com', 'telephone': '+8618079089999',
        'address': {'@type': 'PostalAddress', 'streetAddress': 'Building 11, Jiuding Automobile Market',
                    'addressLocality': 'Xinyu', 'addressRegion': 'Jiangxi', 'addressCountry': 'CN'},
        'contactPoint': {'@type': 'ContactPoint', 'contactType': 'sales inquiries',
                         'telephone': '+8618079089999', 'email': 'jian5222@gmail.com',
                         'url': 'https://wa.me/8618079089999'},
    }

def organization_script():
    return '<script type="application/ld+json">' + json.dumps(organization(), ensure_ascii=False).replace('<', '\\u003c') + '</script>'

def metadata(lang, path, title, desc):
    if path == '/':
        return HOME[lang]
    return META.get(lang, {}).get(path, (title, desc))

def buyer_link(lang):
    return f'<a href="/{lang}{BUYER_PATH}">{html.escape(BUYER_LABEL[lang])}</a>'

BUYER_SECTIONS = {
 'en': [
  ('Choose the right used cars from China', 'Start with your destination, intended use and budget. Browse Chinese brands such as BYD, Haval, Chery, Geely and Changan, or other vehicles listed in China. Use our vehicle filters to compare year, fuel type, mileage and indicative price. A published listing is an inquiry option; current availability must be reconfirmed.'),
  ('Send a clear buying inquiry', 'Include the model or stock number, acceptable years, steering position, preferred fuel type, quantity, budget in USD and destination country and port. State whether you are buying for resale, fleet use or personal use. If a listed model is unsuitable, explain your requirements so we can discuss alternatives.'),
  ('Check the specific vehicle before payment', 'Request current photos, a video if available, the VIN, ownership information, mileage and a written condition report. Discuss accident, flood and fire history, maintenance and an independent inspection. For a used EV, ask about battery health, charging connector and compatibility at your destination.'),
  ('Compare a written export quotation', 'Ask for vehicle price, domestic transport, departure port, freight, insurance and destination charges to be listed separately. Confirm what the offered trade term includes and excludes. Payment milestones, beneficiary details, document list and estimated timing should be agreed in writing for the selected vehicle.'),
  ('Confirm destination requirements', 'Check vehicle age, steering position, emissions, duties and registration with the destination authority or your customs broker before reserving a car. Requirements depend on the country and vehicle; a model shown on this website is not confirmation that it can be imported everywhere.'),
  ('Contact JINBA CARS in Xinyu', 'Our company address is Building 11, Jiuding Automobile Market, Xinyu, Jiangxi, China. WhatsApp: +86 180 7908 9999. Email: jian5222@gmail.com. Contact us with your requirements to request a vehicle-specific quotation; confirm an appointment before travelling.'),
 ],
 'zh': [
  ('选择适合您的中国二手车', '先明确目的地、用途和预算，再浏览比亚迪、哈弗、奇瑞、吉利、长安等中国品牌或其他中国来源车辆。按年份、能源、里程和挂牌参考价筛选。页面展示代表可以询价，当前可售状态需要重新确认。'),
  ('准备完整的采购询价', '发送车型或库存编号、可接受年份、方向盘位置、能源类型、数量、美元预算、目的国及目的港。说明用于经销、车队还是个人使用。如现有车型不合适，请说明必要配置以便讨论替代车源。'),
  ('付款前核验具体车辆', '索取当前照片、可提供的视频、VIN、权属信息、里程和书面车况资料，核查事故、泡水、火烧及保养情况，必要时讨论独立验车。采购二手新能源车，还需确认电池状态、充电接口及目的地适配。'),
  ('比较书面出口报价', '要求分别列明车价、国内运输、出发港、运费、保险及目的地费用。明确所报贸易条款包含及排除哪些费用，并逐笔书面约定付款节点、收款主体、文件清单和预计时效。'),
  ('核实目的国进口条件', '订车前向目的国主管部门或清关行核实车龄、方向盘位置、排放、税费和上牌条件。要求随目的地与车辆变化，网站展示车型并不代表其可出口至所有国家。'),
  ('联系中国新余金霸汽车', '公司地址：江西省新余市九鼎汽车市场11栋。WhatsApp：+86 180 7908 9999。邮箱：jian5222@gmail.com。发送具体需求以获取逐车书面报价，到访前请联系预约。'),
 ],
 'ru': [
  ('Выберите подержанный автомобиль из Китая', 'Определите страну назначения, назначение машины и бюджет. Сравните объявления BYD, Haval, Chery, Geely, Changan и других марок по году, топливу, пробегу и ориентировочной цене. Текущее наличие уточняется по каждой машине.'),
  ('Подготовьте запрос', 'Укажите модель или номер объявления, годы, расположение руля, топливо, количество, бюджет в долларах, страну и порт. Сообщите, нужна ли машина для перепродажи, автопарка или личного пользования.'),
  ('Проверьте машину до оплаты', 'Запросите актуальные фото, доступное видео, VIN, сведения о владельце, пробеге и состоянии. Обсудите аварии, затопление, пожар, обслуживание и независимый осмотр. Для электромобиля уточните состояние батареи и совместимость зарядки.'),
  ('Сравните письменное предложение', 'Разделите цену машины, перевозку по Китаю, порт отправления, фрахт, страховку и расходы назначения. Письменно согласуйте включённые расходы, этапы оплаты, получателя средств, документы и ориентировочные сроки.'),
  ('Проверьте правила импорта', 'До заказа уточните возраст, расположение руля, выбросы, пошлины и регистрацию у компетентного органа или брокера. Объявление не подтверждает допустимость импорта во все страны.'),
  ('Свяжитесь с JINBA CARS в Синьюе', 'Адрес: корпус 11, автомобильный рынок Цзюдин, Синьюй, Цзянси, Китай. WhatsApp: +86 180 7908 9999. Email: jian5222@gmail.com. Пришлите требования для расчёта; согласуйте визит заранее.'),
 ],
 'ar': [
  ('اختر سيارة مستعملة من الصين', 'حدد الوجهة والاستخدام والميزانية، ثم قارن قوائم BYD وهافال وشيري وجيلي وشانجان وغيرها حسب السنة والوقود والمسافة والسعر الاسترشادي. يجب إعادة تأكيد توافر السيارة المختارة.'),
  ('جهز استفسار الشراء', 'أرسل الطراز أو رقم المخزون والسنوات المقبولة وجهة المقود والوقود والكمية والميزانية بالدولار والبلد وميناء الوصول. وضح إن كان الشراء لإعادة البيع أو للأسطول أو للاستخدام الشخصي.'),
  ('تحقق من السيارة قبل الدفع', 'اطلب صوراً حديثة وفيديو إن توفر ورقم VIN ومعلومات الملكية والمسافة والحالة. ناقش الحوادث والغرق والحريق والصيانة والفحص المستقل. للسيارة الكهربائية، تحقق من البطارية وتوافق الشحن في وجهتك.'),
  ('قارن عرضاً مكتوباً', 'افصل سعر السيارة والنقل داخل الصين وميناء المغادرة والشحن والتأمين ورسوم الوجهة. اتفق كتابةً على التكاليف المشمولة ومراحل الدفع والمستفيد والمستندات والمدة المقدرة.'),
  ('أكد شروط الاستيراد', 'تحقق قبل الحجز من العمر وجهة المقود والانبعاثات والضرائب والتسجيل لدى الجهة المختصة أو مخلصك. ظهور السيارة على الموقع لا يؤكد إمكانية استيرادها إلى جميع البلدان.'),
  ('تواصل مع JINBA CARS في شينيو', 'العنوان: المبنى 11، سوق جيودينغ للسيارات، شينيو، جيانغشي، الصين. واتساب: +86 180 7908 9999. البريد: jian5222@gmail.com. أرسل متطلباتك لعرض خاص بالسيارة، ورتب موعداً قبل الزيارة.'),
 ],
}

def buyer_content(lang):
    sections = ''.join(f'<section><h2>{html.escape(h)}</h2><p>{html.escape(p)}</p></section>' for h, p in BUYER_SECTIONS[lang])
    labels = {'en': ('Browse used cars', 'Ask on WhatsApp'), 'zh': ('浏览中国二手车', 'WhatsApp 询价'),
              'ru': ('Смотреть автомобили', 'Написать в WhatsApp'), 'ar': ('تصفح السيارات', 'استفسر عبر واتساب')}[lang]
    return sections + f'<div class="actions"><a class="btn primary" href="/{lang}/cars/">{labels[0]}</a><a class="btn" href="https://wa.me/8618079089999">{labels[1]}</a></div>'
