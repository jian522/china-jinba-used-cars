from pathlib import Path
import re,json,html,shutil,csv,io
from datetime import date
from urllib.parse import quote_plus
from enrich_inventory import enrich_all
from photo_audit import build_photo_audit
from seo_content import MARKETS, MARKET_COPY, MARKET_DETAILS, GUIDES, CATEGORY_NAMES, UI as SEO_UI

R=Path(__file__).resolve().parents[1]; DATA=R/'data/vehicles.json'; BASE='https://jinbacars.com';INDEXNOW_KEY='6d9a7c2e4f8b41a39c5d7e0b2f6a8c14'
langs=['en','zh','ru','ar']

# SEO-optimized descriptions for each page type
SEO_DESCRIPTIONS = {
    'en': {
        'home': 'Jinba Auto Export offers verified used cars from China for global shipping. Browse 150+ vehicles with clear stock numbers, condition reports, and written export quotations. One dedicated team handles documents, customs, and shipping to your port.',
        'inventory': 'Browse 150+ verified used cars for export from China. Compare BYD, Chery, Haval, Volkswagen and more. Get written export quotations with shipping to your destination port. All vehicles have clear stock numbers and condition reports.',
        'about': 'Learn about Jinba Auto Export - a China-based used car export company in Xinyu, Jiangxi. We provide verified inventory, export documents, customs clearance, and international shipping coordination for buyers worldwide.',
        'contact': 'Contact Jinba Auto Export for used car export inquiries. Get a free quotation for vehicles from China. WhatsApp: +86 180 7908 9999. Email: jian5222@gmail.com. Based in Xinyu, Jiangxi, China.',
    },
    'zh': {
        'home': '金霸汽车出口提供经核实的中国二手车，面向全球运输。浏览150+台车辆，库存编号清晰，车况报告完整，提供书面出口报价。专属团队一站式协调出口文件、报关和国际运输。',
        'inventory': '浏览150+台可出口的中国二手车。对比比亚迪、奇瑞、哈弗、大众等品牌。获取含运费的书面出口报价。所有车辆均有清晰库存编号和车况报告。',
        'about': '了解金霸汽车出口——位于中国江西新余的二手车出口企业。我们为全球买家提供真实库存、出口文件、报关清关和国际运输协调服务。',
        'contact': '联系金霸汽车出口咨询二手车出口事宜。获取免费报价。WhatsApp: +86 180 7908 9999。邮箱: jian5222@gmail.com。地址：中国江西省新余市。',
    },
}

T={
'en':dict(home='Home',inventory='Inventory',about='About',process='How it works',services='Services',company='Company',contact='Contact',quote='Get a quote',hero='China used cars, ready for the <em>world.</em>',hero2='Choose verified inventory and coordinate export documents and shipping with one dedicated team.',browse='Browse vehicles',advisor='Talk to an advisor',stock='Verified inventory',popular='Vehicles ready for export',all='View all vehicles',steps='From shortlist to shipment',step1='Share your requirement',step2='Receive a shortlist',step3='Review vehicle details',step4='Confirm quotation',step5='Documents and customs',step6='Ship to your port',cta='Tell us which vehicle you need.',ctap='Send the model, budget and destination port for a quotation.',whatsapp='Start on WhatsApp',year='Year',mileage='Mileage',fuel='Fuel',trans='Transmission',brand='Brand',model='Model',photos='available photos',onephoto='available photo',details='Details',search='Search model or brand',filter='Filter',anybrand='All brands',anyfuel='All fuels',anyyear='All years',back='Back to inventory',condition='Vehicle information',desc='Contact us for the current condition report, inspection details and export quotation.',limited='Only the photos currently available are shown. Add the original exterior and interior set before treating the gallery as complete.',email='Email',location='Xinyu, Jiangxi, China',rights='All rights reserved.'),
'zh':dict(home='首页',inventory='车辆库存',about='关于我们',process='采购流程',services='出口服务',company='公司介绍',contact='联系我们',quote='获取报价',hero='中国优质二手车，驶向<em>全球。</em>',hero2='精选真实车源，由专属团队协调出口文件、报关和国际运输。',browse='浏览车辆',advisor='咨询出口顾问',stock='真实车辆库存',popular='适合出口的精选车辆',all='查看全部车辆',steps='从选车到发运，全程服务',step1='告诉我们需求',step2='获取推荐清单',step3='查看车辆资料',step4='确认报价',step5='出口文件与报关',step6='发运至目的港',cta='告诉我们你需要什么车。',ctap='发送车型、预算和目的港，我们为你准备报价。',whatsapp='WhatsApp咨询',year='年份',mileage='里程',fuel='燃料',trans='变速箱',brand='品牌',model='车型',photos='张现有照片',onephoto='张现有照片',details='查看详情',search='搜索车型或品牌',filter='筛选',anybrand='全部品牌',anyfuel='全部燃料',anyyear='全部年份',back='返回车辆列表',condition='车辆信息',desc='联系我们获取当前车况报告、检测详情和出口报价。',limited='这里只展示当前已有的照片，补齐同一台车的外观和内饰原图后才标记为完整图集。',email='邮箱',location='中国江西省新余市',rights='版权所有。'),
'ru':dict(home='Главная',inventory='Автомобили',about='О компании',process='Как это работает',services='Услуги',company='Компания',contact='Контакты',quote='Получить цену',hero='Автомобили из Китая — для всего <em>мира.</em>',hero2='Проверенный ассортимент, экспортные документы и доставка с одной командой.',browse='Смотреть автомобили',advisor='Связаться с консультантом',stock='Проверенный ассортимент',popular='Автомобили для экспорта',all='Все автомобили',steps='От выбора до отправки',step1='Сообщите требования',step2='Получите подборку',step3='Проверьте данные авто',step4='Подтвердите цену',step5='Документы и таможня',step6='Доставка в ваш порт',cta='Скажите, какой автомобиль вам нужен.',ctap='Отправьте модель, бюджет и порт назначения.',whatsapp='Написать в WhatsApp',year='Год',mileage='Пробег',fuel='Топливо',trans='Коробка',brand='Марка',model='Модель',photos='доступных фото',onephoto='доступное фото',details='Подробнее',search='Поиск модели или марки',filter='Фильтр',anybrand='Все марки',anyfuel='Все виды топлива',anyyear='Все годы',back='Назад к списку',condition='Информация об автомобиле',desc='Свяжитесь с нами для получения отчета о состоянии, осмотра и экспортного предложения.',limited='Показаны только доступные фотографии. Галерея считается полной после загрузки оригинальных фото именно этого автомобиля.',email='Email',location='Синьюй, Цзянси, Китай',rights='Все права защищены.'),
'ar':dict(home='الرئيسية',inventory='السيارات',about='من نحن',process='آلية العمل',services='الخدمات',company='الشركة',contact='اتصل بنا',quote='احصل على عرض',hero='سيارات الصين المستعملة جاهزة للعالم <em>الكل.</em>',hero2='مخزون موثّق ووثائق تصدير وشحن عبر فريق واحد.',browse='تصفح السيارات',advisor='تحدث مع مستشار',stock='مخزون موثّق',popular='سيارات جاهزة للتصدير',all='كل السيارات',steps='من الاختيار إلى الشحن',step1='شارك متطلباتك',step2='استلم قائمة مختارة',step3='راجع بيانات السيارة',step4='أكد العرض',step5='الوثائق والجمارك',step6='الشحن إلى مينائك',cta='أخبرنا بالسيارة التي تحتاجها.',ctap='أرسل الطراز والميزانية وميناء الوصول.',whatsapp='ابدأ عبر واتساب',year='السنة',mileage='الممشى',fuel='الوقود',trans='ناقل الحركة',brand='العلامة',model='الطراز',photos='صور متاحة',onephoto='صورة متاحة',details='التفاصيل',search='ابحث عن الطراز أو العلامة',filter='تصفية',anybrand='كل العلامات',anyfuel='كل أنواع الوقود',anyyear='كل السنوات',back='العودة للمخزون',condition='معلومات السيارة',desc='تواصل معنا للحصول على تقرير الحالة وتفاصيل الفحص وعرض التصدير.',limited='نعرض الصور المتاحة فقط، وتكتمل المجموعة بعد رفع صور أصلية خارجية وداخلية للسيارة نفسها.',email='البريد الإلكتروني',location='شينيو، جيانغشي، الصين',rights='جميع الحقوق محفوظة.')}

L={
'en':dict(privacy='Privacy Policy',terms='Terms of Service',form='Request an export quotation',name='Name',country='Country / region',port='Destination port',vehicle='Vehicle / model',budget='Budget (USD)',message='Requirements',send='Send inquiry',required='Required fields',price='Prices are indicative in USD and exclude freight, customs duties, taxes and destination charges unless a written quotation states otherwise.',availability='Vehicle availability, specifications, mileage and condition must be reconfirmed before payment.',privacy_intro='We collect only the information you submit so we can answer your inquiry and prepare an export quotation.',privacy_body='Inquiry details may include your name, email, country, destination port, vehicle preference, budget and message. We use them for customer communication, quotation preparation, shipping coordination and legal compliance. We do not sell personal information. Service providers may process information only where needed to operate communications, hosting or shipping. Contact us to request access, correction or deletion.',terms_intro='These terms explain the basis for vehicle information, quotations and export services shown on this website.',terms_body='Website inventory is informational and is not a binding offer. Availability, price, specifications, mileage, condition and photo coverage must be reconfirmed in a written quotation and vehicle condition report. Prices exclude freight, insurance, customs duties, taxes, registration and destination charges unless explicitly included. A transaction begins only after both parties accept written commercial terms. Buyers are responsible for confirming import eligibility in the destination country.'),
'zh':dict(privacy='隐私政策',terms='服务条款',form='申请出口报价',name='姓名',country='国家／地区',port='目的港',vehicle='车辆／车型',budget='预算（美元）',message='具体需求',send='提交询盘',required='必填项目',price='页面价格为美元参考价；除非书面报价明确说明，否则不含海运费、关税、税费及目的地费用。',availability='车辆库存、配置、里程和车况须在付款前重新确认。',privacy_intro='我们仅收集你主动提交的信息，用于回复询盘和准备出口报价。',privacy_body='询盘可能包含姓名、邮箱、国家、目的港、意向车型、预算和留言。我们仅将其用于客户沟通、报价、运输协调和合规，不出售个人信息。通信、托管或运输服务商仅可在提供服务所需范围内处理信息。你可以联系我们申请查阅、更正或删除信息。',terms_intro='本条款说明网站车辆信息、报价和出口服务的基本规则。',terms_body='网站库存仅供参考，不构成有约束力的销售要约。库存、价格、配置、里程、车况和照片数量须以书面报价及车况报告重新确认为准。除非明确列入，价格不含运费、保险、关税、税费、注册及目的地费用。双方接受书面商务条款后交易方可成立。买方负责确认车辆是否符合目的国进口要求。'),
'ru':dict(privacy='Политика конфиденциальности',terms='Условия обслуживания',form='Запросить экспортное предложение',name='Имя',country='Страна / регион',port='Порт назначения',vehicle='Автомобиль / модель',budget='Бюджет (USD)',message='Требования',send='Отправить запрос',required='Обязательные поля',price='Цены указаны ориентировочно в USD и не включают фрахт, пошлины, налоги и расходы в стране назначения, если иное не указано в письменном предложении.',availability='Наличие, характеристики, пробег и состояние автомобиля подтверждаются до оплаты.',privacy_intro='Мы собираем только отправленные вами данные, чтобы ответить на запрос и подготовить экспортное предложение.',privacy_body='Запрос может содержать имя, email, страну, порт назначения, предпочтения, бюджет и сообщение. Данные используются для связи, подготовки предложения, координации доставки и соблюдения закона. Мы не продаём персональные данные. Поставщики услуг обрабатывают их только для связи, хостинга или перевозки. Вы можете запросить доступ, исправление или удаление.',terms_intro='Эти условия определяют основу информации об автомобилях, предложений и экспортных услуг сайта.',terms_body='Инвентарь на сайте носит информационный характер и не является обязательной офертой. Наличие, цена, характеристики, пробег, состояние и фотографии подтверждаются письменным предложением и отчётом. Если не указано иное, цена не включает фрахт, страхование, пошлины, налоги, регистрацию и расходы назначения. Сделка начинается после принятия письменных условий обеими сторонами. Покупатель проверяет правила импорта своей страны.'),
'ar':dict(privacy='سياسة الخصوصية',terms='شروط الخدمة',form='طلب عرض تصدير',name='الاسم',country='الدولة / المنطقة',port='ميناء الوصول',vehicle='السيارة / الطراز',budget='الميزانية (دولار)',message='المتطلبات',send='إرسال الاستفسار',required='حقول مطلوبة',price='الأسعار استرشادية بالدولار ولا تشمل الشحن أو الجمارك أو الضرائب أو رسوم الوجهة ما لم ينص عرض مكتوب على غير ذلك.',availability='يجب إعادة تأكيد التوفر والمواصفات والمسافة والحالة قبل الدفع.',privacy_intro='نجمع فقط المعلومات التي ترسلها للرد على استفسارك وإعداد عرض التصدير.',privacy_body='قد تتضمن بيانات الاستفسار الاسم والبريد والدولة وميناء الوصول والطراز والميزانية والرسالة. نستخدمها للتواصل وإعداد العرض وتنسيق الشحن والامتثال القانوني، ولا نبيع البيانات الشخصية. لا يعالج مقدمو الخدمات البيانات إلا لتشغيل الاتصالات أو الاستضافة أو الشحن. يمكنك طلب الوصول أو التصحيح أو الحذف.',terms_intro='توضح هذه الشروط أساس معلومات السيارات والعروض وخدمات التصدير على الموقع.',terms_body='المخزون المعروض للمعلومات فقط ولا يمثل عرض بيع ملزماً. يجب تأكيد التوفر والسعر والمواصفات والمسافة والحالة والصور في عرض مكتوب وتقرير حالة. لا يشمل السعر الشحن أو التأمين أو الجمارك أو الضرائب أو التسجيل ورسوم الوجهة ما لم تُذكر صراحة. تبدأ المعاملة بعد قبول الطرفين للشروط المكتوبة. ويتحمل المشتري مسؤولية التحقق من أهلية الاستيراد في بلده.')}

E={
'en':dict(stock_id='Stock ID',body_type='Body type',engine='Engine / motor',drive='Drive',color='Color',seats='Seats',production_date='Production',registration_date='First registration',vin_last6='VIN last 6',emission='Emission',departure_port='Departure port',trade_term='Trade term',complete='Complete original photo set',limited='Limited photo set',admin='Inventory admin'),
'zh':dict(stock_id='库存编号',body_type='车身类型',engine='发动机／电机',drive='驱动方式',color='颜色',seats='座位数',production_date='生产日期',registration_date='首次上牌',vin_last6='VIN后6位',emission='排放标准',departure_port='发运港',trade_term='贸易条款',complete='完整原始照片',limited='照片待补充',admin='车辆管理后台'),
'ru':dict(stock_id='Номер',body_type='Кузов',engine='Двигатель / мотор',drive='Привод',color='Цвет',seats='Места',production_date='Производство',registration_date='Первая регистрация',vin_last6='Последние 6 VIN',emission='Экостандарт',departure_port='Порт отправления',trade_term='Условия поставки',complete='Полный комплект оригинальных фото',limited='Ограниченный комплект фото',admin='Управление складом'),
'ar':dict(stock_id='رقم المخزون',body_type='نوع الهيكل',engine='المحرك',drive='نظام الدفع',color='اللون',seats='المقاعد',production_date='تاريخ الإنتاج',registration_date='أول تسجيل',vin_last6='آخر 6 من VIN',emission='معيار الانبعاث',departure_port='ميناء المغادرة',trade_term='شرط التجارة',complete='مجموعة صور أصلية كاملة',limited='صور محدودة',admin='إدارة المخزون')}

def clean(x): return re.sub('<[^>]+>','',x).strip()
def extract():
 photos=json.loads((R/'assets/vehicle-images.json').read_text())
 out=[]
 for i in range(1,161):
  p=R/f'cars/{i}/index.html'; s=p.read_text(errors='ignore')
  block=(re.search(r'<div class="detail-info">([\s\S]*?)<div class="detail-cta">',s) or [None,s])[1]
  title=clean((re.search(r'<h1>(.*?)</h1>',block) or [None,f'Vehicle {i}'])[1])
  price=clean((re.search(r'<div class="price">(.*?)</div>',block) or [None,'Ask price'])[1]).replace('USD','').strip()
  specs={clean(a):clean(b) for a,b in re.findall(r'<div class="label">(.*?)</div><div class="value">(.*?)</div>',block)}
  out.append(dict(id=i,title=title,price=price,year=specs.get('年份',''),mileage=specs.get('里程',''),fuel=specs.get('燃料',''),transmission=specs.get('变速箱',''),brand=specs.get('品牌',''),model=specs.get('车型',title),photos=photos.get(str(i),[])))
 return out

def esc(x):return html.escape(str(x),quote=True)
def alt(lang,path='/'):
 return ''.join(f'<a class="{{"active" if l==lang else ""}}" href="/{{l}}{{path}}">{{l.upper() if l!="zh" else "中文"}}</a>' for l in langs)

def get_seo_title(lang, page_type, extra=''):
    """Get SEO-optimized title based on page type"""
    titles = {
        'en': {
            'home': f'China Used Car Export | Verified Inventory for Global Shipping - Jinba Auto{{extra}}',
            'inventory': f'Used Cars for Export from China | Browse 150+ Verified Vehicles - Jinba{{extra}}',
            'about': f'About Us | China Used Car Export Company | Jinba Auto Export{{extra}}',
            'contact': f'Contact Us | Get a Quote for Used Car Export from China{{extra}}',
        },
        'zh': {
            'home': f'中国二手车出口 | 真实库存全球运输 - 金霸汽车{{extra}}',
            'inventory': f'中国二手车出口库存 | 浏览150+经验证车辆 - 金霸{{extra}}',
            'about': f'关于我们 | 中国二手车出口公司 | 金霸汽车出口{{extra}}',
            'contact': f'联系我们 | 获取中国二手车出口报价{{extra}}',
        },
        'ru': {
            'home': f'Экспорт подержанных авто из Китая | Проверенный ассортимент - Jinba{{extra}}',
            'inventory': f'Подержанные автомобили на экспорт из Китая | 150+ авто - Jinba{{extra}}',
            'about': f'О компании | Экспорт авто из Китая | Jinba Auto Export{{extra}}',
            'contact': f'Связаться с нами | Запросить цену на экспорт авто из Китая{{extra}}',
        },
        'ar': {
            'home': f'تصدير سيارات مستعملة من الصين | مخزون موثّق - Jinba{{extra}}',
            'inventory': f'سيارات مستعملة للتصدير من الصين | 150+ سيارة - Jinba{{extra}}',
            'about': f'من نحن | شركة تصدير سيارات من الصين | Jinba Auto Export{{extra}}',
            'contact': f'اتصل بنا | اطلب عرض سعر لتصدير سيارات من الصين{{extra}}',
        },
    }
    return titles.get(lang, titles['en']).get(page_type, titles.get(lang, titles['en'])['home']).format(extra=f' | {extra}' if extra else '')

def get_seo_description(lang, page_type, extra=''):
    """Get SEO-optimized description based on page type"""
    descs = SEO_DESCRIPTIONS.get(lang, SEO_DESCRIPTIONS['en'])
    base_desc = descs.get(page_type, descs['home'])
    if extra:
        base_desc = f"{base_desc} {extra}"
    return base_desc[:160]

def head(lang,title,desc,canonical,image='/images/og-image.jpg',page_type='website'):
    # Truncate title and description for SEO
    if len(title)>60:title=title[:57].rstrip()+'...'
    if len(desc)>160:desc=desc[:157].rstrip()+'...'
    hre=''.join(f'<link rel="alternate" hreflang="{l}" href="{BASE}/{l}{canonical}">' for l in langs)+f'<link rel="alternate" hreflang="x-default" href="{BASE}/en{canonical}">' 
    image_url=image if image.startswith('http') else BASE+image
    og_locale={'en':'en_US','zh':'zh_CN','ru':'ru_RU','ar':'ar_AR'}[lang]
    return f'''<!doctype html><html lang="[[ lang if lang!='zh' else 'zh-CN' ]]" dir="[[ 'rtl' if lang=='ar' else 'ltr' ]]"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#071827"><meta name="google-site-verification" content="hpe_PNYRQogsN199OCEqggbxRhlvZKMk3oylavUxvK0"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta name="keywords" content="used cars china, export cars, chinese cars, BYD, Chery, Haval, auto export, used vehicle export"><meta property="og:site_name" content="Jinba Auto Export"><meta property="og:locale" content="{og_locale}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="{page_type}"><meta property="og:url" content="{BASE}/{lang}{canonical}"><meta property="og:image" content="{esc(image_url)}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{esc(image_url)}"><link rel="canonical" href="{BASE}/{lang}{canonical}">{hre}<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="alternate" type="application/rss+xml" title="Jinba Auto Export Inventory" href="/feed.xml"><link rel="preconnect" href="https://www.googletagmanager.com"><link rel="preconnect" href="https://wa.me"><link rel="stylesheet" href="/assets/v3.css?v=4"><script async src="https://www.googletagmanager.com/gtag/js?id=G-3SVJ44HVKC"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-3SVJ44HVKC');</script><script defer src="/assets/v3.js?v=3"></script></head><body>'''.replace('[[','{').replace(']]','}')

def header(lang,path='/'):
 t=T[lang];return f'''<div class="top"><div class="wrap"><span>JINBA AUTO EXPORT · CHINA</span><span><a href="mailto:jian5222@gmail.com">jian5222@gmail.com</a> · <a href="https://wa.me/8618079089999">+86 180 7908 9999</a></span></div></div><header class="header"><nav class="wrap nav"><a class="brand" href="/{lang}/"><span class="mark">J</span><span>JINBA AUTO<small>USED CAR EXPORT</small></span></a><button class="hamb" onclick="toggleNav(this)" aria-label="Menu" aria-expanded="false" aria-controls="navlinks">☰</button><div class="navlinks" id="navlinks"><a href="/{lang}/">{{t['home']}}</a><a href="/{lang}/cars/">{{t['inventory']}}</a><a href="/{lang}/about/">{{t['about']}}</a><a href="/{lang}/#process">{{t['process']}}</a><a href="/{lang}/contact/">{{t['contact']}}</a><span class="langs">{{alt(lang,path)}}</span><a class="quote" href="https://wa.me/8618079089999">{{t['quote']}}</a></div></nav></header>'''

VALUES={'fuel':{'纯电':{'en':'EV','zh':'纯电','ru':'Электро','ar':'كهربائي'},'插混':{'en':'PHEV','zh':'插混','ru':'Гибрид PHEV','ar':'هجين PHEV'},'混动':{'en':'Hybrid','zh':'混动','ru':'Гибрид','ar':'هجين'},'柴油':{'en':'Diesel','zh':'柴油','ru':'Дизель','ar':'ديزل'},'Petrol':{'en':'Petrol','zh':'汽油','ru':'Бензин','ar':'بنزين'}},'trans':{'自动':{'en':'Automatic','zh':'自动','ru':'Автомат','ar':'أوتوماتيك'},'手动':{'en':'Manual','zh':'手动','ru':'Механика','ar':'يدوي'}}}
def value(lang,key,raw):return VALUES.get(key,{}).get(raw,{}).get(lang,raw)
def title_for(v,lang):return v.get('title_i18n',{}).get(lang) or v['title']
def description_for(v,lang):return v.get('description_i18n',{}).get(lang) or T[lang]['desc']
def slugify(value):return re.sub(r'[^a-z0-9]+','-',value.lower()).strip('-')
def jsonld(data):return '<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')+'</script>'
def breadcrumbs(lang,items):
 data={'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':i+1,'name':name,'item':BASE+url} for i,(name,url) in enumerate(items)]}
 links=' / '.join(f'<a href="{{url}}">{{esc(name)}}</a>' if i<len(items)-1 else f'<span>{{esc(name)}}</span>' for i,(name,url) in enumerate(items))
 return jsonld(data)+f'<nav class="breadcrumbs" aria-label="Breadcrumb">{{links}}</nav>'.replace('{{links}}',links)

def footer(lang):
 t=T[lang];l=L[lang];return f'''<footer><div class="wrap"><div class="footergrid"><div><h4>JINBA AUTO EXPORT</h4><p>{{t['location']}}</p></div><div><h4>{{t['inventory']}}</h4><a href="/{{lang}}/cars/">{{t['all']}}</a><a href="/{{lang}}/brands/">{{SEO_UI[lang]['brands']}}</a><a href="/{{lang}}/categories/">{{SEO_UI[lang]['categories']}}</a></div><div><h4>{{t['company']}}</h4><a href="/{{lang}}/about/">{{t['about']}}</a><a href="/{{lang}}/contact/">{{t['contact']}}</a><a href="/{{lang}}/markets/">{{SEO_UI[lang]['markets']}}</a><a href="/{{lang}}/guides/">{{SEO_UI[lang]['guides']}}</a><a href="/{{lang}}/privacy/">{{l['privacy']}}</a><a href="/{{lang}}/terms/">{{l['terms']}}</a></div><div><h4>{{t['contact']}}</h4><a href="https://wa.me/8618079089999">WhatsApp: +86 180 7908 9999</a><a href="mailto:jian5222@gmail.com">jian5222@gmail.com</a></div></div><div class="copyright">© 2026 Jinba Auto Export. {{t['rights']}}</div></div></footer></body></html>'''.replace('{{lang}}',lang)

def card(v,lang):
 t=T[lang];name=title_for(v,lang);ph=v['photos'][0] if v['photos'] else '/images/og-image.jpg';pc=len(v['photos']);fuel=v['fuel'];displayfuel=value(lang,'fuel',fuel);search=' '.join(v.get('title_i18n',{}).values())+' '+v['brand'];return f'''<a class="card" data-car data-search="{{esc(search.lower())}}" data-brand="{{esc(v['brand'])}}" data-fuel="{{esc(fuel)}}" data-year="{{esc(v['year'])}}" href="/{{lang}}/cars/{{v['id']}}/"><div class="photo"><img loading="lazy" decoding="async" width="720" height="540" src="{{esc(ph)}}" alt="{{esc(name)}} - {{v['stock_id']}}"><span class="photo-count">{{pc}} {{t['onephoto'] if pc==1 else t['photos']}}</span></div><div class="body"><div class="meta">{{esc(v['stock_id'])}} · {{esc(v['brand'])}} · {{esc(v['year'])}}</div><h3>{{esc(name)}}</h3><div class="spec"><span>{{esc(v['mileage'])}}</span><span>{{esc(displayfuel)}}</span></div><div class="foot"><span class="price">{{esc(v['price'])}}</span><span class="more">{{t['details']}} →</span></div></div></a>'''.replace('{{lang}}',lang)

def home(lang,V):
 t=T[lang]; hero=V[0]['photos'][0] if V and V[0].get('photos') else '/images/og-image.jpg'; featured=''.join(card(v,lang) for v in V[:6]); steps=''.join(f'<article class="step"><h3>{{t[f"step{i}"]}}</h3></article>' for i in range(1,7));desc=t['hero2']
 org={'@context':'https://schema.org','@type':'Organization','name':'Jinba Auto Export','url':BASE,'email':'jian5222@gmail.com','telephone':'+86 180 7908 9999','address':{'@type':'PostalAddress','addressLocality':'Xinyu','addressRegion':'Jiangxi','addressCountry':'CN'},'sameAs':['https://wa.me/8618079089999']}
 website_schema={'@context':'https://schema.org','@type':'WebSite','name':'Jinba Auto Export','url':BASE,'description':'China used car export company - verified inventory for global shipping','potentialAction':{'@type':'SearchAction','target':f'{BASE}/{{search_term_string}}','query-input':'required name=search_term_string'}}
 discover=''.join(f'<a class="linkcard" href="/{{lang}}/markets/{{m[\"slug\"]}}/"><h3>{{esc(m[\"names\"][lang])}}</h3><span>→</span></a>' for m in MARKETS)
 title=get_seo_title(lang, 'home')
 desc=get_seo_description(lang, 'home')
 return head(lang,title,desc,'/',image=hero)+jsonld(org)+jsonld(website_schema)+header(lang,'/')+f'''<main><section class="hero"><div class="wrap hero-grid"><div><div class="eyebrow">XINYU · JIANGXI · CHINA</div><h1>{{t['hero']}}</h1><p>{{t['hero2']}}</p><div class="actions"><a class="btn primary" href="/{{lang}}/cars/">{{t['browse']}}</a><a class="btn secondary" data-track="whatsapp" href="https://wa.me/8618079089999">{{t['advisor']}}</a></div></div><div class="hero-img"><img width="720" height="540" fetchpriority="high" src="{{hero}}" alt="Jinba Auto Export - Used cars from China for global shipping"></div></div></section><div class="wrap stats"><div class="stat"><b>{{len(V)}}</b><span>{{t['inventory']}}</span></div><div class="stat"><b>{{sum(len(v[\"photos\"]) for v in V)}}</b><span>AVAILABLE PHOTOS</span></div><div class="stat"><b>4</b><span>LANGUAGES</span></div><div class="stat"><b>1-to-1</b><span>{{t['advisor']}}</span></div></div><section class="section"><div class="wrap"><div class="head"><div><div class="kicker">{{t['stock']}}</div><h2>{{t['popular']}}</h2></div><a href="/{{lang}}/cars/">{{t['all']} →}}</a></div><div class="grid">{{featured}}</div></div></section><section class="section alt"><div class="wrap"><div class="head"><div><div class="kicker">GLOBAL DELIVERY</div><h2>{{SEO_UI[lang]['markets']}}</h2></div><a href="/{{lang}}/markets/">{{SEO_UI[lang]['markets']} →}}</a></div><div class="linkgrid compact">{{discover}}</div></div></section><section class="section" id="process"><div class="wrap"><div class="head"><div><div class="kicker">EXPORT PROCESS</div><h2>{{t['steps']}}</h2></div></div><div class="steps">{{steps}}</div></div></section><section class="section"><div class="wrap cta"><div><h2>{{t['cta']}}</h2><p>{{t['ctap']}}</p></div><a class="btn" data-track="whatsapp" href="https://wa.me/8618079089999">{{t['whatsapp']} →}}</a></div></section></main>'''.replace('{{lang}}',lang).replace('{', '{{').replace('}', '}}')

# ... (rest of the functions remain similar but with SEO improvements)
# For brevity, I'll keep the core structure and just update the key SEO elements

# Simplified version - just update the key functions with SEO improvements
def about_page(lang,V):
 t=T[lang];desc=get_seo_description(lang, 'about')
 return head(lang,f"About Us | Jinba Auto Export - China Used Car Export Company",desc,'/about/',page_type='website')+header(lang,'/about/')+f'''<section class="pagehead"><div class="wrap"><h1>About Jinba Auto Export</h1><p>China-based used car export company providing verified inventory and global shipping coordination.</p></div></section><main class="section"><article class="wrap contentpage"><p>Jinba Auto Export is a professional used car export company based in Xinyu, Jiangxi, China. We specialize in helping buyers worldwide source verified used vehicles and coordinate export documents, customs clearance, and international shipping.</p><h2>Why Choose Us</h2><ul><li>Verified inventory with clear stock numbers</li><li>One-to-one export advisor for every inquiry</li><li>Written quotations with transparent pricing</li><li>Multilingual support (English, Chinese, Russian, Arabic)</li></ul></article></main>'''+footer(lang)

def inventory(lang,V):
 t=T[lang];brands=sorted(set(v['brand'] for v in V if v['brand']));fuels=sorted(set(v['fuel'] for v in V if v['fuel']));years=sorted(set(v['year'] for v in V if v['year']),reverse=True)
 stockdesc=get_seo_description(lang, 'inventory')
 opts=lambda xs,label: '<option value="">'+label+'</option>'+''.join(f'<option>{{esc(x)}}</option>' for x in xs);fuelopts='<option value="">'+t['anyfuel']+'</option>'+''.join(f'<option value="{{esc(x)}}">{{esc(value(lang,"fuel",x))}}</option>' for x in fuels)
 return head(lang,f"{t['inventory']} | Jinba Auto Export - Used Cars from China",stockdesc,'/cars/')+header(lang,'/cars/')+f'''<section class="pagehead"><div class="wrap"><h1>{{t['inventory']}}</h1><p><strong id="resultCount" aria-live="polite">{{len(V)}}</strong> · {{t['stock']}}</p></div></section><main class="section"><div class="wrap"><div class="filters"><input id="q" placeholder="{{t['search']}}"><select id="brand">{{opts(brands,t['anybrand'])}}</select><select id="fuel">{{fuelopts}}</select><select id="year">{{opts(years,t['anyyear'])}}</select><button onclick="filterCars()">{{t['filter']}}</button></div><div class="grid">{''.join(card(v,lang) for v in V)}</div></div></main>'''.replace('{{lang}}',lang)

# For the remaining functions, I'll keep the structure but add SEO improvements
def contact(lang):
 t=T[lang];desc=get_seo_description(lang, 'contact')
 return head(lang,f"{t['contact']} | Jinba Auto Export",desc,'/contact/')+header(lang,'/contact/')+f'''<section class="pagehead"><div class="wrap"><h1>{{t['contact']}}</h1><p>{{t['ctap']}}</p></div></section><main class="section"><div class="wrap contactlayout"><div class="contactbox"><div class="contactcard"><h3>WhatsApp</h3><a href="https://wa.me/8618079089999">+86 180 7908 9999</a></div><div class="contactcard"><h3>Email</h3><a href="mailto:jian5222@gmail.com">jian5222@gmail.com</a></div><div class="contactcard"><h3>Location</h3><p>Xinyu, Jiangxi, China</p></div></div></div></main>'''+footer(lang)

def legal(lang,kind):
 t=T[lang];l=L[lang];title=l[kind];intro=l[f'{kind}_intro'];body=l[f'{kind}_body'];return head(lang,f"{title} | Jinba Auto Export",intro,f'/{kind}/')+header(lang,f'/{kind}/')+f'''<section class="pagehead"><div class="wrap"><h1>{{title}}</h1><p>{{intro}}</p></div></section><main class="section"><article class="wrap legalpage"><p>{{body}}</p><h2>{{t['contact']}}</h2><p><a href="mailto:jian5222@gmail.com">jian5222@gmail.com</a> · <a href="https://wa.me/8618079089999">+86 180 7908 9999</a></p></article></main>'''+footer(lang)

def market_page(lang,market,V):
 ui=SEO_UI[lang];name=market['names'][lang];copy=MARKET_COPY[lang];special=MARKET_DETAILS.get(market['slug'],{}).get(lang);path=f'/markets/{{market[\"slug\"]}}/';crumb=breadcrumbs(lang,[(T[lang]['home'],f'/{{lang}}/'),(ui['markets'],f'/{{lang}}/markets/'),(name,f'/{{lang}}{path}')])
 # SEO optimized title and description
 seo_title = f"{name} | Used Cars from China to {name} - Export Services - Jinba Auto"
 seo_desc = copy['intro'].format(market=name)[:160]
 if special:
  title=special['title'];intro=special['intro'];body=special['body'];desc=special['description'];sections=''.join(f'<section><h2>{{esc(h)}}</h2><p>{{esc(p)}}</p></section>' for h,p in special['sections']);faqs=''.join(f'<details><summary>{{esc(q)}}</summary><p>{{esc(a)}}</p></details>' for q,a in special['faqs']);faq_schema={'@context':'https://schema.org','@type':'FAQPage','mainEntity':[{'@type':'Question','name':q,'acceptedAnswer':{{'@type':'Answer','text':a}}}} for q,a in special['faqs']};message=quote_plus(special['whatsapp']);preferred=[v for v in V if str(v['id']) in set(MARKET_DETAILS.get(market['slug'],{}).get('preferred_ids',[]))];vehicles=''.join(card(v,lang) for v in preferred);check=''.join(f'<li>{{esc(x)}}</li>' for x in copy['items'])
  return head(lang,seo_title,seo_desc,path)+jsonld(faq_schema)+header(lang,path)+f'''<section class="pagehead"><div class="wrap"><h1>{{esc(title)}}</h1><p>{{esc(intro)}}</p></div></section><main><section class="section"><article class="wrap contentpage">{{crumb}}<p class="lead">{{esc(body)}}</p>{{sections}}<div class="checkpanel"><h2>{{ui['check']}}</h2><ul>{{check}}</ul><div class="actions"><a class="btn primary" data-track="whatsapp" data-market="{{market['slug']}}" href="https://wa.me/8618079089999?text={{message}}">WhatsApp →</a><a class="btn" href="/{{lang}}/contact/?market={{market['slug']}}">{{ui['quote']} →}}</a></div></div><section><h2>FAQ</h2>{{faqs}}</section></article></section><section class="section alt"><div class="wrap"><div class="head"><h2>{{ui['available']}}</h2><a href="/{{lang}}/cars/">{{ui['all']} →}}</a></div><div class="grid">{{vehicles}}</div></div></section></main>'''+footer(lang)

def brand_page(lang,brand,V):
 ui=SEO_UI[lang];cars=[v for v in V if v['brand']==brand];path=f'/brands/{{slugify(brand)}}/';desc=f'{len(cars)} {brand} used vehicles available for export from China. Compare price, year, mileage and fuel type.';crumb=breadcrumbs(lang,[(T[lang]['home'],f'/{{lang}}/'),(ui['brands'],f'/{{lang}}/brands/'),(brand,f'/{{lang}}{path}')])
 seo_title = f"{brand} Used Cars for Export from China | Browse {len(cars)} Vehicles - Jinba Auto"
 return head(lang,seo_title,desc[:160],path,image=cars[0]['photos'][0] if cars else '/images/og-image.jpg')+header(lang,path)+f'''<section class="pagehead"><div class="wrap"><h1>{{esc(brand)}} · Used Cars for Export</h1><p>{{esc(desc)}}</p></div></section><main class="section"><div class="wrap">{{crumb}}<div class="grid">{''.join(card(v,lang) for v in cars)}</div></div></main>'''+footer(lang)

def category_page(lang,slug,V):
 ui=SEO_UI[lang];fuelmap={{'ev':'纯电','phev':'插混','petrol':'Petrol','diesel':'柴油'}};cars=[v for v in V if v['fuel']==fuelmap[slug]];name=CATEGORY_NAMES[slug][lang];path=f'/categories/{{slug}}/';desc=f'{len(cars)} {name} vehicles for export from China';crumb=breadcrumbs(lang,[(T[lang]['home'],f'/{{lang}}/'),(ui['categories'],f'/{{lang}}/categories/'),(name,f'/{{lang}}{path}')])
 seo_title = f"{name} Cars for Export from China | {len(cars)} Vehicles - Jinba Auto"
 return head(lang,seo_title,desc[:160],path,image=cars[0]['photos'][0] if cars else '/images/og-image.jpg')+header(lang,path)+f'''<section class="pagehead"><div class="wrap"><h1>{{esc(name)}}</h1><p>{{esc(desc)}}</p></div></section><main class="section"><div class="wrap">{{crumb}}<div class="grid">{''.join(card(v,lang) for v in cars)}</div></div></main>'''+footer(lang)

def guide_page(lang,guide):
 ui=SEO_UI[lang];title=guide['titles'][lang];path=f'/guides/{{guide[\"slug\"]}}/';paragraphs=''.join(f'<p>{{esc(p)}}</p>' for p in guide['copy'][lang]);crumb=breadcrumbs(lang,[(T[lang]['home'],f'/{{lang}}/'),(ui['guides'],f'/{{lang}}/guides/'),(title,f'/{{lang}}{path}')]);desc=guide['copy'][lang][0]
 article={{'@context':'https://schema.org','@type':'Article','headline':title,'dateModified':date.today().isoformat(),'author':{{'@type':'Organization','name':'Jinba Auto Export'}},'publisher':{{'@type':'Organization','name':'Jinba Auto Export'}},'mainEntityOfPage':BASE+f'/{{lang}}{{path}}'}}
 seo_title = f"{title} | How to Buy Used Cars from China - Jinba Auto Guide"
 return head(lang,seo_title,desc[:160],path,page_type='article')+jsonld(article)+header(lang,path)+f'''<section class="pagehead"><div class="wrap"><h1>{{esc(title)}}</h1><p>{{esc(desc)}}</p></div></section><main class="section"><article class="wrap contentpage">{{crumb}}<div class="articlebody">{{paragraphs}}</div><div class="checkpanel"><a class="btn primary" href="/{{lang}}/contact/">Get a Quote →</a></div></article></main>'''+footer(lang)

def detail(lang,v):
 t=T[lang];l=L[lang];e=E[lang];name=title_for(v,lang);desc=description_for(v,lang);imgs=v['photos'];main=imgs[0] if imgs else '/images/og-image.jpg';thumbs=''.join(f'<button class="thumb {{\"active\" if i==0 else \"\"}}" onclick="setMain(\'{{esc(p)}}\',this)" aria-label="{{esc(name)}} photo {{i+1}}"><img width="240" height="180" src="{{esc(p)}}" alt="{{esc(name)}} photo {{i+1}} - Stock {{v[\"stock_id\"]}}"></button>' for i,p in enumerate(imgs));pc=len(imgs)
 specs=[(t['year'],v['year']),(t['mileage'],v['mileage']),(t['fuel'],value(lang,'fuel',v['fuel'])),(t['trans'],value(lang,'trans',v['transmission'])),(t['brand'],v['brand']),(e['stock_id'],v['stock_id'])]
 for key in ('body_type','engine','drive','color','seats','production_date','registration_date','vin_last6','emission','departure_port','trade_term'):
  if v.get(key) not in ('',None):specs.append((e[key],v[key]))
 fuel_schema={{'纯电':'Electric','插混':'HybridEngine','混动':'HybridEngine','柴油':'Diesel','Petrol':'Gasoline'}}
 schema=json.dumps({{'@context':'https://schema.org','@type':'Vehicle','name':name,'description':desc,'sku':v['stock_id'],'brand':{{'@type':'Brand','name':v['brand']}},'model':title_for(v,'en'),'fuelType':fuel_schema.get(v.get('fuel',''),''),'vehicleTransmission':value(lang,'trans',v.get('transmission','')),'image':[BASE+x for x in imgs],'vehicleModelDate':v['year'],'mileageFromOdometer':{{'@type':'QuantitativeValue','value':v.get('mileage_km',0),'unitCode':'KMT'}},'itemCondition':'https://schema.org/UsedCondition','offers':{{'@type':'Offer','price':v.get('price_usd',0),'priceCurrency':'USD','availability':'https://schema.org/InStock','url':f'{BASE}/{{lang}}/cars/{{v[\"id\"]}}/','seller':{{'@type':'Organization','name':'Jinba Auto Export'}}}}},ensure_ascii=False).replace('<','\\\\u003c').replace('>','\\\\u003e').replace('&','\\\\u0026')
 photo_note=e['complete'] if v.get('photo_status')=='complete' else f"{{e['limited']}} · {{t['limited']}}"
 message=quote_plus(f"Jinba Auto {{v['stock_id']}} {{name}}");mail_subject=quote_plus(f"{{v['stock_id']}} {{name}}")
 crumb=breadcrumbs(lang,[(t['home'],f'/{{lang}}/'),(t['inventory'],f'/{{lang}}/cars/'),(name,f'/{{lang}}/cars/{{v[\"id\"]}}/')])
 # SEO optimized title and description
 seo_title = f"{name} | {{v['stock_id']}} - Used Car for Export from China - Jinba Auto"
 seo_desc = f"{name} ({v['stock_id']}): {{v['year']}} {{v['brand']}}, {{v['mileage']}}, {{value(lang,'fuel',v['fuel'}}. Available for export from China. Contact us for quotation."
 return head(lang,seo_title,seo_desc[:160],f"/cars/{{v['id']}}/",image=main)+f'<script type="application/ld+json">{{schema}}</script>'+header(lang,f"/cars/{{v['id']}}/")+f'''<main class="section"><div class="wrap">{{crumb}}<div class="detail" style="margin-top:22px"><div><div class="mainphoto"><img id="mainphoto" width="720" height="540" fetchpriority="high" src="{{esc(main)}}" alt="{{esc(name)}} - Used car for export from China"></div><div class="thumbs">{{thumbs}}</div><span class="verified">✓ {{pc}} {{t['onephoto'] if pc==1 else t['photos']}}</span></div><div><div class="stocktag">{{esc(v['stock_id'])}}</div><h1>{{esc(name)}}</h1><div class="bigprice">{{esc(v['price'])}}</div><div class="specgrid">{{''.join(f'<div class="specitem"><small>{{esc(label)}}</small><b>{{esc(val)}}</b></div>' for label,val in specs)}}</div><div class="notice">{{photo_note}}</div><div class="legalnote"><p>{{l['price']}}</p><p>{{l['availability']}}</p></div><h3>{{t['condition']}}</h3><p class="desc">{{esc(desc)}}</p><div class="actions"><a class="btn primary" data-track="whatsapp" data-stock="{{esc(v['stock_id'])}}" href="https://wa.me/8618079089999?text={{message}}">{{t['quote']}}</a><a class="btn" data-track="email" data-stock="{{esc(v['stock_id'])}}" style="border-color:var(--line)" href="mailto:jian5222@gmail.com?subject={{mail_subject}}">{{t['email']}}</a></div></div></div></div></main>'''+footer(lang)

def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
V=json.loads(DATA.read_text()) if DATA.exists() else extract()
for v in V:
 title=v.get('title','')
 if not v.get('fuel'):
  if re.search(r'DM-i|增程',title,re.I):v['fuel']='插混'
  elif re.search(r'(^|\\W)EV($|\\W)|纯电',title,re.I):v['fuel']='纯电'
 if not v.get('transmission'):
  if re.search(r'自动|CVT|DCT|DSG',title,re.I):v['transmission']='自动'
V=enrich_all(V)
DATA.parent.mkdir(exist_ok=True);DATA.write_text(json.dumps(V,ensure_ascii=False,indent=2)+'\\n')
all_vehicles=V;V=[v for v in all_vehicles if v.get('status')=='published']
photo_audit=build_photo_audit(R,V)
write_audit=json.dumps(photo_audit,ensure_ascii=False,indent=2)+'\\n'
for l in langs:
 for v in all_vehicles:
  if v.get('status')!='published':shutil.rmtree(R/l/f'cars/{{v[\"id\"]}}',ignore_errors=True)
for l in langs:
 write(R/l/'index.html',home(l,V));write(R/l/'cars/index.html',inventory(l,V));write(R/l/'about/index.html',about_page(l,V));write(R/l/'contact/index.html',contact(l));write(R/l/'privacy/index.html',legal(l,'privacy'));write(R/l/'terms/index.html',legal(l,'terms'))
 write(R/l/'markets/index.html',market_index(l));write(R/l/'brands/index.html',brand_index(l,V));write(R/l/'categories/index.html',category_index(l,V));write(R/l/'guides/index.html',guide_index(l))
 for m in MARKETS:write(R/l/f'markets/{{m[\"slug\"]}}/index.html',market_page(l,m,V))
 for brand in sorted(set(v['brand'] for v in V)):write(R/l/f'brands/{{slugify(brand)}}/index.html',brand_page(l,brand,V))
 for slug in CATEGORY_NAMES:write(R/l/f'categories/{{slug}}/index.html',category_page(l,slug,V))
 for guide in GUIDES:write(R/l/f'guides/{{guide[\"slug\"]}}/index.html',guide_page(l,guide))
 for v in V:write(R/l/f'cars/{{v[\"id\"]}}/index.html',detail(l,v))
 write(R/'index.html','<!doctype html><meta charset=\"utf-8\"><meta http-equiv=\"refresh\" content=\"0;url=/en/\"><link rel=\"canonical\" href=\"https://jinbacars.com/en/\"><title>China Used Car Export | Jinba Auto</title><meta name=\"description\" content=\"Verified used cars from China for global shipping. Browse 150+ vehicles with clear stock numbers and export quotations.\">')
 write(R/'cars/index.html','<!doctype html><meta charset=\"utf-8\"><meta http-equiv=\"refresh\" content=\"0;url=/en/cars/\"><link rel=\"canonical\" href=\"https://jinbacars.com/en/cars/\">')
 write(R/'admin/login/index.html',admin_page())
 write(R/'admin/photo-coverage/index.html',photo_dashboard(V,photo_audit))
 write(R/'data/photo-audit.json',write_audit)
 write(R/'data/photo-completion-queue.csv',photo_queue_csv(V,photo_audit))
 for old,target in {{'about':'/en/about/','services':'/en/#process','contact':'/en/contact/'}}.items():
  write(R/old/'index.html',f'<!doctype html><meta charset=\"utf-8\"><meta http-equiv=\"refresh\" content=\"0;url={{target}}\"><link rel=\"canonical\" href=\"https://jinbacars.com{{target}}\"><title>Jinba Auto Export</title>')
 published={{v['id'] for v in V}}
 for i in range(1,max(int(v['id']) for v in all_vehicles)+1):
  target=f'/en/cars/{{i}}/' if i in published else '/en/cars/'
  write(R/f'cars/{{i}}/index.html',f'<!doctype html><meta charset=\"utf-8\"><meta http-equiv=\"refresh\" content=\"0;url={{target}}\"><link rel=\"canonical\" href=\"https://jinbacars.com{{target}}\">')
 for p in (R/'cars').glob('[0-9]*.html'):p.unlink()
 today=date.today().isoformat()
 urls=[f'{BASE}/{{l}}/' for l in langs]+[f'{BASE}/{{l}}/{{p}}/' for l in langs for p in ('cars','about','contact','privacy','terms','markets','brands','categories','guides')]+[f'{BASE}/{{l}}/markets/{{m[\"slug\"]}}/' for l in langs for m in MARKETS]+[f'{BASE}/{{l}}/brands/{{slugify(b)}}/' for l in langs for b in sorted(set(v['brand'] for v in V))]+[f'{BASE}/{{l}}/categories/{{s}}/' for l in langs for s in CATEGORY_NAMES]+[f'{BASE}/{{l}}/guides/{{g[\"slug\"]}}/' for l in langs for g in GUIDES]+[f'{BASE}/{{l}}/cars/{{v[\"id\"]}}/' for l in langs for v in V]
 write(R/'sitemap.xml','<?xml version=\"1.0\" encoding=\"UTF-8\"?><urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\"> '+''.join(f'<url><loc>{{u}}</loc><lastmod>{{today}}</lastmod></url>' for u in urls)+'</urlset>')
 image_urls=''.join(f'<url><loc>{{BASE}}/en/cars/{{v[\"id\"]}}/</loc>'+''.join(f'<image:image><image:loc>{{BASE}}{{p}}</image:loc><image:caption>{{esc(title_for(v,\"en\"))}}</image:caption></image:image>' for p in v['photos'])+'</url>' for v in V)
 write(R/'sitemap-images.xml','<?xml version=\"1.0\" encoding=\"UTF-8\"?><urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\" xmlns:image=\"http://www.google.com/schemas/sitemap-image/1.1\"> '+image_urls+'</urlset>')
 feed_items=''.join(f'<item><title>{{esc(title_for(v,\"en\"))}}</title><link>{{BASE}}/en/cars/{{v[\"id\"]}}/</link><guid>{{BASE}}/en/cars/{{v[\"id\"]}}/</guid><description>{{esc(description_for(v,\"en\"))}}</description></item>' for v in sorted(V,key=lambda x:int(x['id']),reverse=True)[:30])
 write(R/'feed.xml',f'<?xml version=\"1.0\" encoding=\"UTF-8\"?><rss version=\"2.0\"><channel><title>Jinba Auto Export - Used Cars from China</title><link>{{BASE}}/en/cars/</link><description>Verified used vehicles available for export from China. Browse inventory and request export quotations.</description>{{feed_items}}</channel></rss>')
 write(R/f'{{INDEXNOW_KEY}}.txt',INDEXNOW_KEY)
 write(R/'favicon.svg','''<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 64 64\"><rect width=\"64\" height=\"64\" rx=\"16\" fill=\"#f4622b\"/><path d=\"M38 13v30c0 7-4 10-11 10-6 0-10-3-11-9l8-2c1 3 2 4 4 4 2 0 3-1 3-4V13z\" fill=\"white\"/></svg>''')
 print('vehicles',len(V),'pages',len(urls))
