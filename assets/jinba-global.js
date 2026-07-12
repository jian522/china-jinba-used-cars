(function(){
  var langs=['en','zh','ru','ar'];
  var names={en:'EN',zh:'中文',ru:'RU',ar:'عربي'};
  var home={
    'Direct sourcing and export support from China':{zh:'中国二手车采购与出口一站式服务',ru:'Подбор и экспорт автомобилей из Китая',ar:'خدمة توريد وتصدير السيارات من الصين'},
    'Inventory':{zh:'车辆库存',ru:'Автомобили',ar:'المخزون'},'How It Works':{zh:'采购流程',ru:'Как это работает',ar:'آلية العمل'},'Services':{zh:'出口服务',ru:'Услуги',ar:'الخدمات'},'Company':{zh:'公司介绍',ru:'Компания',ar:'الشركة'},'Contact':{zh:'联系我们',ru:'Контакты',ar:'اتصل بنا'},'Get a Quote':{zh:'获取报价',ru:'Получить цену',ar:'احصل على عرض'},
    'China’s used cars, ready for the world.':{zh:'中国优质二手车，驶向全球。',ru:'Китайские автомобили — для всего мира.',ar:'سيارات الصين المستعملة جاهزة للعالم.'},
    "China's used cars, ready for the world.":{zh:'中国优质二手车，驶向全球。',ru:'Китайские автомобили — для всего мира.',ar:'سيارات الصين المستعملة جاهزة للعالم.'},
    'Choose from inspected vehicles, get clear export documentation, and ship to your port with one dedicated team.':{zh:'精选车源、清晰出口文件、专业物流运输，由专属团队全程跟进。',ru:'Проверенные автомобили, прозрачные экспортные документы и доставка в ваш порт одной командой.',ar:'سيارات مفحوصة ووثائق تصدير واضحة وشحن إلى مينائك عبر فريق واحد.'},
    'Browse 160+ Vehicles':{zh:'浏览160+台车辆',ru:'Смотреть 160+ авто',ar:'تصفح أكثر من 160 سيارة'},'Talk to an Export Advisor':{zh:'咨询出口顾问',ru:'Связаться с консультантом',ar:'تحدث مع مستشار التصدير'},
    'Vehicles buyers ask for.':{zh:'海外买家热门车型。',ru:'Автомобили, которые выбирают покупатели.',ar:'السيارات الأكثر طلباً.'},
    'From shortlist to shipment.':{zh:'从选车到发运，全程服务。',ru:'От выбора до отправки.',ar:'من الاختيار إلى الشحن.'},
    'Share your requirement':{zh:'告诉我们需求',ru:'Сообщите требования',ar:'شارك متطلباتك'},'Receive a shortlist':{zh:'获取推荐清单',ru:'Получите подборку',ar:'استلم قائمة مختارة'},'Inspect the vehicle':{zh:'确认车辆检测',ru:'Проверка автомобиля',ar:'فحص السيارة'},'Confirm quotation':{zh:'确认报价',ru:'Подтвердите цену',ar:'تأكيد العرض'},'Documents & customs':{zh:'出口文件与报关',ru:'Документы и таможня',ar:'الوثائق والجمارك'},'Ship to your port':{zh:'发运至目的港',ru:'Доставка в ваш порт',ar:'الشحن إلى مينائك'},
    'Your sourcing partner in China':{zh:'你在中国的车辆采购伙伴',ru:'Ваш партнер по закупкам в Китае',ar:'شريكك للتوريد من الصين'},'Built for overseas dealers and individual buyers.':{zh:'服务海外车商与个人买家。',ru:'Для зарубежных дилеров и частных покупателей.',ar:'للتجار والمشترين الأفراد حول العالم.'},
    'Tell us which car you need.':{zh:'告诉我们你需要什么车。',ru:'Скажите, какой автомобиль вам нужен.',ar:'أخبرنا بالسيارة التي تحتاجها.'},'Start on WhatsApp →':{zh:'通过WhatsApp开始咨询 →',ru:'Написать в WhatsApp →',ar:'ابدأ عبر واتساب ←'},'WhatsApp Quote':{zh:'WhatsApp询价',ru:'Цена в WhatsApp',ar:'عرض عبر واتساب'}
  };
  function translatePlain(lang){
    var walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);var nodes=[],n;
    while(n=walker.nextNode()) if(n.parentElement&&!/^(SCRIPT|STYLE)$/.test(n.parentElement.tagName)&&n.nodeValue.trim()) nodes.push(n);
    nodes.forEach(function(t){var raw=t.nodeValue.trim();if(!t.parentElement.dataset.jbEn)t.parentElement.dataset.jbEn=raw;var en=t.parentElement.dataset.jbEn;var v=lang==='en'?en:(home[en]&&home[en][lang]);if(v)t.nodeValue=t.nodeValue.replace(raw,v);});
  }
  function setLang(lang){if(langs.indexOf(lang)<0)lang='en';localStorage.setItem('jinba-lang',lang);document.documentElement.lang=lang==='zh'?'zh-CN':lang;document.documentElement.dir=lang==='ar'?'rtl':'ltr';document.querySelectorAll('[data-lang]').forEach(function(el){el.style.display=el.getAttribute('data-lang')===lang?'':'none'});translatePlain(lang);document.querySelectorAll('.jb-langbar button').forEach(function(b){b.classList.toggle('active',b.dataset.jbLang===lang)});}
  function init(){if(!document.querySelector('.jb-langbar')){var b=document.createElement('div');b.className='jb-langbar';b.setAttribute('aria-label','Language');langs.forEach(function(l){var x=document.createElement('button');x.type='button';x.dataset.jbLang=l;x.textContent=names[l];x.onclick=function(){setLang(l)};b.appendChild(x)});document.body.appendChild(b)}var saved=localStorage.getItem('jinba-lang');var browser=(navigator.language||'en').toLowerCase();setLang(saved||(browser.startsWith('zh')?'zh':browser.startsWith('ru')?'ru':browser.startsWith('ar')?'ar':'en'));}
  window.jbSetLang=setLang;if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
