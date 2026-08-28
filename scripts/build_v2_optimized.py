from pathlib import Path
import re,json,html,shutil,csv,io
from datetime import date
from urllib.parse import quote_plus
from enrich_inventory import enrich_all
from photo_audit import build_photo_audit
from seo_content import MARKETS, MARKET_COPY, MARKET_DETAILS, GUIDES, CATEGORY_NAMES, UI as SEO_UI

R=Path(__file__).resolve().parents[1]; DATA=R/'data/vehicles.json'; BASE='https://jinbacars.com';INDEXNOW_KEY='6d9a7c2e4f8b41a39c5d7e0b2f6a8c14'
langs=['en','zh','ru','ar']

# SEO-optimized title templates
TITLE_TEMPLATES = {
    'en': {
        'home': 'China Used Car Export | Verified Inventory for Global Shipping - Jinba Auto',
        'inventory': 'Used Cars for Export from China | Browse Verified Inventory - Jinba Auto',
        'about': 'About Us | China Used Car Export Company - Jinba Auto Export',
        'contact': 'Contact Us | Get a Quote for Used Car Export from China',
        'market': '{market} | Used Cars from China to {market} - Export Services',
        'brand': '{brand} Used Cars for Export from China | Browse Inventory',
        'category': '{category} Cars for Export from China | {type} Vehicles',
        'guide': 'How to Buy Used Cars from China | Export Guide - Jinba Auto',
    },
    'zh': {
        'home': '中国二手车出口 | 真实库存全球运输 - 金霸汽车出口',
        'inventory': '中国二手车出口库存 | 浏览经验证的车辆 - 金霸汽车',
        'about': '关于我们 | 中国二手车出口公司 - 金霸汽车出口',
        'contact': '联系我们 | 获取中国二手车出口报价',
        'market': '{market} | 中国二手车出口到{market} - 出口服务',
        'brand': '{brand} 中国二手车出口 | 浏览库存',
        'category': '{category} 汽车出口中国 | {type} 车辆',
        'guide': '如何从中国购买二手车 | 出口指南 - 金霸汽车',
    },
    'ru': {
        'home': 'Экспорт подержанных автомобилей из Китая | Проверенный ассортимент для мировой доставки',
        'inventory': 'Подержанные автомобили на экспорт из Китая | Просмотр ассортимента',
        'about': 'О нас | Компания по экспорту авто из Китая',
        'contact': 'Связаться с нами | Запросить цену на экспорт авто из Китая',
        'market': '{market} | Автомобили из Китая в {market} - Экспортные услуги',
        'brand': '{brand} Автомобили на экспорт из Китая | Просмотр',
        'category': '{category} Автомобили для экспорта из Китая',
        'guide': 'Как купить подержанный автомобиль в Китае | Руководство по экспорту',
    },
    'ar': {
        'home': 'تصدير سيارات مستعملة من الصين | مخزون موثّق للشحن العالمي',
        'inventory': 'سيارات مستعملة للتصدير من الصين | تصفح المخزون الموثّق',
        'about': 'من نحن | شركة تصدير سيارات من الصين',
        'contact': 'اتصل بنا | اطلب عرض سعر لتصدير سيارات من الصين',
        'market': '{market} | سيارات من الصين إلى {market} - خدمات التصدير',
        'brand': '{brand} سيارات مستعملة للتصدير من الصين',
        'category': '{category} سيارات للتصدير من الصين',
        'guide': 'كيفية شراء سيارة مستعملة من الصين | دليل التصدير',
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
 return ''.join(f'<a class="{"active" if l==lang else ""}" href="/{l}{path}">{{l.upper() if l!="zh" else "中文"}}</a>' for l in langs)
def head(lang,title,desc,canonical,image='/images/og-image.jpg',page_type='website'):
 if len(title)>60:title=title[:57].rstrip()+'...'
 if len(desc)>160:desc=desc[:157].rstrip()+'...'
 hre=''.join(f'<link rel="alternate" hreflang="{l}" href="{BASE}/{l}{canonical}">' for l in langs)+f'<link rel="alternate" hreflang="x-default" href="{BASE}/en{canonical}">' 
 image_url=image if image.startswith('http') else BASE+image
 og_locale={'en':'en_US','zh':'zh_CN','ru':'ru_RU','ar':'ar_AR'}[lang]
 # Add WebSite schema with SearchAction for better SEO
 website_schema = json.dumps({
  '@context': 'https://schema.org',
  '@type': 'WebSite',
  'name': 'Jinba Auto Export',
  'url': BASE,
  'description': 'China used car export company - verified inventory for global shipping',
  'potentialAction': {
   '@type': 'SearchAction',
   'target': f'{BASE}/{{search_term_string}}',
   'query-input': 'required name=search_term_string'
  }
 }, ensure_ascii=False)
 return f'''<!doctype html><html lang="[[ lang if lang!='zh' else 'zh-CN' ]]" dir="[[ 'rtl' if lang=='ar' else 'ltr' ]]"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#071827"><meta name="google-site-verification" content="hpe_PNYRQogsN199OCEqggbxRhlvZKMk3oylavUxvK0"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta property="og:site_name" content="Jinba Auto Export"><meta property="og:locale" content="{og_locale}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="{page_type}"><meta property="og:url" content="{BASE}/{lang}{canonical}"><meta property="og:image" content="{esc(image_url)}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{esc(image_url)}"><link rel="canonical" href="{BASE}/{lang}{canonical}">{hre}<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="alternate" type="application/rss+xml" title="Jinba Auto Export Inventory" href="/feed.xml"><link rel="preconnect" href="https://www.googletagmanager.com"><link rel="preconnect" href="https://wa.me"><link rel="stylesheet" href="/assets/v3.css?v=4"><script async src="https://www.googletagmanager.com/gtag/js?id=G-3SVJ44HVKC"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-3SVJ44HVKC');</script><script defer src="/assets/v3.js?v=3"></script></head><body>'''.replace('[[','{').replace(']]','}')
