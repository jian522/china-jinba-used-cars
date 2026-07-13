"""Localized, people-first content used by the SEO landing page generator."""

MARKETS = [
    {"slug": "uae", "names": {"en": "United Arab Emirates", "zh": "阿联酋", "ru": "ОАЭ", "ar": "الإمارات العربية المتحدة"}},
    {"slug": "saudi-arabia", "names": {"en": "Saudi Arabia", "zh": "沙特阿拉伯", "ru": "Саудовская Аравия", "ar": "المملكة العربية السعودية"}},
    {"slug": "kazakhstan", "names": {"en": "Kazakhstan", "zh": "哈萨克斯坦", "ru": "Казахстан", "ar": "كازاخستان"}},
    {"slug": "uzbekistan", "names": {"en": "Uzbekistan", "zh": "乌兹别克斯坦", "ru": "Узбекистан", "ar": "أوزبكستان"}},
    {"slug": "nigeria", "names": {"en": "Nigeria", "zh": "尼日利亚", "ru": "Нигерия", "ar": "نيجيريا"}},
]

UI = {
    "en": {"markets":"Export markets","brands":"Browse by brand","categories":"Vehicle categories","guides":"Buying guides","available":"Available vehicles","check":"What to confirm before ordering","quote":"Request a destination quotation","related":"Related resources","updated":"Information updated","all":"View inventory"},
    "zh": {"markets":"出口市场","brands":"按品牌选车","categories":"车辆分类","guides":"出口指南","available":"可选车辆","check":"订车前需要确认","quote":"获取目的国报价","related":"相关内容","updated":"资料更新时间","all":"查看库存"},
    "ru": {"markets":"Рынки экспорта","brands":"Автомобили по маркам","categories":"Категории автомобилей","guides":"Руководства покупателя","available":"Автомобили в наличии","check":"Что проверить до заказа","quote":"Запросить расчет доставки","related":"Полезные материалы","updated":"Обновлено","all":"Все автомобили"},
    "ar": {"markets":"أسواق التصدير","brands":"تصفح حسب العلامة","categories":"فئات السيارات","guides":"دليل الشراء","available":"السيارات المتاحة","check":"ما يجب تأكيده قبل الطلب","quote":"اطلب عرضاً للوجهة","related":"موارد ذات صلة","updated":"آخر تحديث","all":"عرض المخزون"},
}

MARKET_COPY = {
    "en": {
        "intro":"Browse used vehicles available in China and request an export quotation for {market}. Jinba Auto Export coordinates vehicle information, condition confirmation, export documents and shipping arrangements with the buyer and appointed logistics partners.",
        "body":"Import and registration requirements can change. Before payment, confirm model-year eligibility, emissions and conformity requirements, steering position, customs valuation, taxes and local registration rules with the destination authority or a licensed customs broker in {market}.",
        "items":["Vehicle stock number, year, mileage and condition report","Current availability and final written quotation","Departure port, destination port and shipping method","Import eligibility, customs duties and local registration","Payment beneficiary, trade term and document list"],
    },
    "zh": {
        "intro":"浏览中国现有二手车，并获取发往{market}的出口报价。金霸汽车出口协助买方确认车辆资料、车况、出口文件，并与指定物流合作方协调运输。",
        "body":"进口和注册要求可能发生变化。付款前，请向{market}主管部门或持牌清关代理确认车型年份、排放与认证、方向盘位置、海关估值、税费和当地上牌要求。",
        "items":["库存编号、年份、里程和车况报告","当前库存和最终书面报价","起运港、目的港和运输方式","进口资格、关税和当地注册要求","收款主体、贸易条款和文件清单"],
    },
    "ru": {
        "intro":"Выберите подержанный автомобиль в Китае и запросите экспортный расчет для доставки в {market}. Jinba Auto Export помогает подтвердить данные и состояние автомобиля, подготовить экспортные документы и согласовать перевозку с покупателем и логистическим партнером.",
        "body":"Правила импорта и регистрации могут меняться. До оплаты уточните допустимый год выпуска, экологические и сертификационные требования, расположение руля, таможенную стоимость, налоги и регистрацию у органов или лицензированного брокера в стране {market}.",
        "items":["Номер автомобиля, год, пробег и отчет о состоянии","Фактическое наличие и письменное предложение","Порт отправления, порт назначения и способ перевозки","Правила импорта, пошлины и местная регистрация","Получатель платежа, условия поставки и список документов"],
    },
    "ar": {
        "intro":"تصفح السيارات المستعملة المتاحة في الصين واطلب عرض تصدير إلى {market}. تساعد Jinba Auto Export في تأكيد بيانات السيارة وحالتها ووثائق التصدير وترتيبات الشحن مع المشتري وشريك الخدمات اللوجستية.",
        "body":"قد تتغير متطلبات الاستيراد والتسجيل. قبل الدفع، تحقق من أهلية سنة الصنع والانبعاثات والمطابقة وموقع المقود والتقييم الجمركي والضرائب والتسجيل المحلي مع الجهة المختصة أو مخلص جمركي مرخص في {market}.",
        "items":["رقم المخزون والسنة والمسافة وتقرير الحالة","التوفر الحالي والعرض المكتوب النهائي","ميناء المغادرة والوصول وطريقة الشحن","أهلية الاستيراد والرسوم والتسجيل المحلي","جهة استلام الدفع وشرط التجارة وقائمة الوثائق"],
    },
}

GUIDES = [
    {
        "slug":"buy-used-cars-from-china",
        "titles":{"en":"How to buy a used car from China","zh":"如何从中国采购二手车","ru":"Как купить подержанный автомобиль из Китая","ar":"كيفية شراء سيارة مستعملة من الصين"},
        "copy":{
            "en":["Start with the destination country's import rules, not only the vehicle price. Confirm eligibility before choosing a stock unit.","Request a written quotation that identifies the vehicle by stock number and separates vehicle price, inland transport, freight, insurance and destination charges.","Review original photos and a condition report before payment. Confirm the commercial terms, beneficiary and required export documents in writing."],
            "zh":["采购应从目的国进口要求开始，而不是只看车辆价格。选车前先确认车型是否符合进口条件。","要求书面报价明确库存编号，并分别列明车价、国内运输、海运、保险和目的地费用。","付款前查看原始照片和车况报告，并书面确认贸易条款、收款主体和出口文件。"],
            "ru":["Начинайте с правил импорта страны назначения, а не только с цены автомобиля. До выбора машины подтвердите ее допустимость.","Запросите письменное предложение с номером автомобиля и отдельными суммами за автомобиль, внутреннюю перевозку, фрахт, страхование и расходы назначения.","До оплаты изучите оригинальные фото и отчет о состоянии. Письменно подтвердите условия сделки, получателя платежа и экспортные документы."],
            "ar":["ابدأ بمتطلبات الاستيراد في بلد الوجهة وليس بسعر السيارة فقط، وتأكد من الأهلية قبل اختيار المركبة.","اطلب عرضاً مكتوباً يحدد رقم المخزون ويفصل سعر السيارة والنقل الداخلي والشحن والتأمين ورسوم الوجهة.","راجع الصور الأصلية وتقرير الحالة قبل الدفع، وأكد شروط التجارة والمستفيد ووثائق التصدير كتابةً."],
        },
    },
    {
        "slug":"vehicle-inspection-checklist",
        "titles":{"en":"Used vehicle inspection checklist","zh":"出口二手车验车清单","ru":"Проверка подержанного автомобиля","ar":"قائمة فحص السيارة المستعملة"},
        "copy":{
            "en":["Match the VIN and stock number across the vehicle, quotation and documents.","Check exterior panels, paint, glass, tires, lights, underbody and signs of collision, fire or flooding.","Confirm dashboard warnings, mileage, battery or engine condition, transmission operation, air conditioning and available keys.","Keep dated photos and the written condition report with the transaction record."],
            "zh":["核对车辆、报价和文件中的VIN及库存编号是否一致。","检查外观覆盖件、漆面、玻璃、轮胎、灯光、底盘，以及事故、火烧和泡水痕迹。","确认仪表故障灯、里程、电池或发动机状态、变速箱、空调和钥匙数量。","保存带日期的照片和书面车况报告。"],
            "ru":["Сверьте VIN и номер автомобиля на машине, в предложении и документах.","Проверьте кузов, окраску, стекла, шины, свет, днище и признаки ДТП, пожара или затопления.","Проверьте предупреждения панели, пробег, батарею или двигатель, коробку передач, кондиционер и ключи.","Сохраните датированные фотографии и письменный отчет о состоянии."],
            "ar":["طابق رقم VIN ورقم المخزون على السيارة والعرض والوثائق.","افحص الهيكل والطلاء والزجاج والإطارات والأضواء والأسفل وآثار الحوادث أو الحريق أو الغمر.","تحقق من تحذيرات لوحة العدادات والمسافة والبطارية أو المحرك وناقل الحركة والتكييف والمفاتيح.","احتفظ بالصور المؤرخة وتقرير الحالة المكتوب ضمن سجل المعاملة."],
        },
    },
    {
        "slug":"export-documents-and-shipping",
        "titles":{"en":"Export documents and vehicle shipping","zh":"二手车出口文件与运输","ru":"Экспортные документы и доставка автомобиля","ar":"وثائق التصدير وشحن السيارات"},
        "copy":{
            "en":["The required document set depends on the vehicle, trade term, shipping route and destination country.","A typical transaction may involve a commercial invoice, contract, vehicle registration or title records, export declaration and transport documents. Confirm the final list before payment.","Choose container, RoRo or another permitted method according to route availability, vehicle type, cost and destination handling."],
            "zh":["所需文件取决于车辆、贸易条款、运输路线和目的国。","常见文件可能包括商业发票、合同、车辆登记资料、出口申报和运输单据，付款前应确认最终清单。","根据航线、车型、成本和目的港条件选择集装箱、滚装或其他允许的运输方式。"],
            "ru":["Комплект документов зависит от автомобиля, условий поставки, маршрута и страны назначения.","Обычно могут потребоваться инвойс, договор, регистрационные документы, экспортная декларация и транспортные документы. Итоговый список подтвердите до оплаты.","Контейнер, RoRo или другой разрешенный способ выбирают по маршруту, типу автомобиля, стоимости и условиям порта назначения."],
            "ar":["تعتمد الوثائق المطلوبة على السيارة وشرط التجارة ومسار الشحن وبلد الوجهة.","قد تشمل المعاملة فاتورة تجارية وعقداً ووثائق تسجيل وإقرار تصدير ووثائق نقل. أكد القائمة النهائية قبل الدفع.","اختر الحاوية أو سفن RoRo أو وسيلة مسموحة أخرى وفق المسار ونوع السيارة والتكلفة وظروف ميناء الوصول."],
        },
    },
    {
        "slug":"safe-payment-and-quotation",
        "titles":{"en":"Safe quotation and payment checks","zh":"出口报价与付款安全检查","ru":"Безопасная проверка предложения и оплаты","ar":"التحقق الآمن من العرض والدفع"},
        "copy":{
            "en":["A quotation should show the seller, buyer, stock number, vehicle details, currency, validity period, trade term and included costs.","Verify that payment instructions match the contracted seller. Treat any last-minute beneficiary change as a reason to stop and reconfirm through a known contact channel.","Keep the signed terms, payment record, vehicle evidence and shipping documents together."],
            "zh":["报价应列明买卖双方、库存编号、车辆资料、币种、有效期、贸易条款和包含费用。","核实收款信息与合同卖方一致。遇到临时更换收款账户，应暂停付款并通过已知联系方式重新确认。","统一保存签署条款、付款记录、车辆证据和运输文件。"],
            "ru":["В предложении должны быть продавец, покупатель, номер автомобиля, характеристики, валюта, срок действия, условия поставки и включенные расходы.","Платежные реквизиты должны совпадать с продавцом по договору. При внезапной смене получателя остановите платеж и перепроверьте данные через известный канал связи.","Храните подписанные условия, платежные документы, данные автомобиля и перевозочные документы вместе."],
            "ar":["يجب أن يوضح العرض البائع والمشتري ورقم المخزون وبيانات السيارة والعملة ومدة الصلاحية وشرط التجارة والتكاليف المشمولة.","تحقق من تطابق تعليمات الدفع مع البائع المتعاقد. عند تغيير المستفيد في اللحظة الأخيرة أوقف الدفع وأعد التأكيد عبر قناة اتصال معروفة.","احتفظ بالشروط الموقعة وسجل الدفع وأدلة السيارة ووثائق الشحن معاً."],
        },
    },
]

CATEGORY_NAMES = {
    "ev":{"en":"Electric vehicles","zh":"纯电动车","ru":"Электромобили","ar":"السيارات الكهربائية"},
    "phev":{"en":"Plug-in hybrid vehicles","zh":"插电混动车","ru":"Гибриды PHEV","ar":"سيارات PHEV الهجينة"},
    "petrol":{"en":"Petrol vehicles","zh":"汽油车","ru":"Бензиновые автомобили","ar":"سيارات البنزين"},
    "diesel":{"en":"Diesel vehicles","zh":"柴油车","ru":"Дизельные автомобили","ar":"سيارات الديزل"},
}

