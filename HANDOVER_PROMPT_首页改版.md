# 金霸二手车出口网站 · 首页改版开发部署提示词

> 生成时间：2026-09-06 · 配套设计稿：Ardot https://ardot.tencent.com/file/722844951625143
> 用法：在**新对话窗口**，将下方分割线以内的全部内容作为**第一条消息**发送。

---

你负责「金霸汽车出口」二手车出口网站（d:\二手车出口网站）的**首页改版落地与部署**。项目已在生产运行（jinbacars.com，GitHub Pages 托管，纯静态 HTML/CSS/JS，无框架，页面由 Python 脚本生成）。完整项目背景与约束见项目根目录 `HANDOVER_PROMPT.md`，开始前先通读。

## 一、本次任务（P3 首页改版）

按已定稿的设计稿，重做四语首页（en/zh/ru/ar）并部署上线。

**设计稿（以此为准）**：Ardot https://ardot.tencent.com/file/722844951625143
- 2026-09-06 定稿，方向=**深蓝+橙品牌延续**（弃用 9/3 暗底青柠稿 721801039769668）
- 设计稿内所有图片均为占位灰框，落地时替换真实图（uploads/cars/{id}/primary.jpg）

**设计规格速览**：
- 画布 #F9F9F9；深蓝 #0A1628（深色区/CTA 卡，可用 #0A1628→#0D2944 渐变）；强调橙 #FF6B2C；WhatsApp 绿 #25D366；正文色 #0A1628 / #6B7280；白卡 + 1px #EAEAEA 边框
- 圆角：主卡 50px、内嵌卡 32px、小芯片 24px、按钮全圆
- 字体：Mona Sans（标题 Bold/ExtraBold）、Inter（正文）、JetBrains Mono（kicker/库存号/数据标签，全大写+字距加宽）
- 桌面 1440px，需 1440/768/375 三档响应式

**页面分区（11 区，按序）**：
1. **Top Bar**：深蓝细条 36px，左"Licensed used-car exporter · Shenzhen, China · Since 2016"，右 sales@jinbacars.com + +86 755 8899 2100
2. **导航** 76px 白底：橙圆角方块卡车 logo + JINBA CARS/EXPORT + Inventory/Markets/Process/About + 绿色 WhatsApp 按钮
3. **Hero** 左文右图（左 640px 文案列，右图 50px 大圆角）：徽章"209 vehicles in stock · ready to ship"（橙点+橙底浅色芯片）→ H1"Drive China's best value cars to your market"（58px 三行）→ 副文案 → 双 CTA（橙实心 Browse inventory / 白描边 How buying works）→ 图下深蓝数据带（圆角 50）：209 vehicles in stock / 1,900+ cars exported / 14 destination countries / **25** days to Mombasa avg.（25 用橙色）
4. **精选车源**：kicker"FEATURED STOCK"（JetBrains Mono 橙）+ 标题"Fresh arrivals, export-ready" + 右侧"View all 209 vehicles →"；4 卡网格（白卡 50px 圆角 + 1px 边框，图高 216px；卡内：年份/动力灰芯片 + 库存号橙浅底芯片 + 车名 16px + 规格 13px + 价格 22px + FOB Shenzhen + 深蓝全圆"Request quote"按钮）：
   - JB-0001 BYD Seal 650 Smart Driving · 2025 · EV · 17,000 km · $19,833
   - JB-0002 BYD Han DM-i Flagship · 2025 · PHEV · 2,300 km · $19,417
   - JB-0006 Haval H6 PHEV 2026 · 2026 · SUV · 100 km · $18,028
   - JB-0008 Jetour X70 Plus · 2024 · SUV · 10,000 km · $10,389
   （以上为设计稿示例，落地时从 data/vehicles.json 按"published+6 图齐全"重选最新车源）
5. **Why 区**（深蓝 #0A1628 全宽 + 右上橙色径向光晕 18% 透明）：kicker"WHY JINBA CARS"+ 标题"Trade with a partner, not a listing site"；网格=左 780px 宽卡（168-point inspection，内含 bento 三小格：168 Check points / 6+ Photos per listing / 24h Video walkaround + 240px 高港口堆场图窗 + FOB/CIF/RoRo/Container 芯片）+ 右 400px 列三窄卡（Export paperwork, done right / Secure T/T & L/C payment / Shipping to 14 countries——第三张为橙卡反白）；玻璃卡=白 6% 填充+白 10% 描边
6. **流程区**：HOW IT WORKS + "From selection to shipping, end to end" + 右侧深蓝"Start your order"按钮；4 步白卡（01 Tell us your needs / 02 Inspect & reserve / 03 Documents & customs / 04 Ship & track，编号橙色 JetBrains Mono）
7. **市场区**：WHERE WE SHIP + "Established lanes, local know-how"；3 卡等宽：AFRICA Kenya·Nigeria·Tanzania·Ghana（深蓝反白主卡，kicker 橙）/ MIDDLE EAST UAE·Jordan·Iraq（白卡）/ EURASIA Russia·Kazakhstan·Kyrgyzstan（白卡）
8. **评价区**：CLIENT STORIES；左 800px 白卡（五星 SVG 橙 + "Third batch this year..." + Daniel Otieno · Fleet importer · Nairobi, Kenya）+ 右 #FFEDE2 浅橙卡（"Documents cleared Russian customs..." + Alexey Voronov · Dealer · Vladivostok, Russia）
9. **FAQ**：左侧标题列（"Questions buyers ask first"+ WhatsApp 引导语）+ 右侧 4 问列表（How is payment arranged? 为**展开态**含答案 / How long is shipping? / Can I inspect before paying? / Which documents do I receive?），答案文案沿用现站
10. **底部 CTA**：深蓝 50px 大圆角卡含光晕，"Reserve your first shipment this month"（40px）+ 副文案 + 绿 WhatsApp 按钮"Chat on WhatsApp"+ 白描边 sales@jinbacars.com + 注脚"Quotes valid for 7 days · FOB / CIF · English, Russian & Arabic support"
11. **页脚**（深蓝）：品牌列（logo+简介）+ INVENTORY/COMPANY/SUPPORT/LANGUAGES 四列（LANGUAGES 列含 English/简体中文/Русский/العربية，English 高亮）+ 底栏"Copyright 2026 Jinba Cars Export Co., Ltd. · jinbacars.com"与"MOFCOM licensed · COI verified · B/L on every shipment"

**多语言**：en 为主版；zh/ru/ar 内容对应翻译；ar 必须 dir="rtl" 且布局镜像；hreflang 5 向、OG、Vehicle JSON-LD 沿用现站做法。

## 二、实现要求

1. 新建 `scripts/rebuild_home_v7.py` 生成四语首页；样式新增 `assets/jinba-home-v7.css`（勿动 v3/v4/v5 历史），脚本参考现有 rebuild_home_v6.py 的生成方式
2. 数据从 `data/vehicles.json` 读取；首页"在售台数"口径=**209**（与现站一致，勿用 215/210）
3. 图片：车辆卡/Hero 用 uploads 真实图（注意 photo-audit 的 duplicate_primary_groups，重复首图不选两张）；堆场/头像可用 images/ 现有资源，不得引用外链
4. WhatsApp 链接与号码沿用现站 wa.me 设置
5. SEO：每语独立 title/description（含 used car export / China 关键词）、hreflang 5 向、OG 标签、JSON-LD 保持
6. 旧首页先备份到 `.workbuddy/backup_home/` 再覆盖

## 三、硬性约束（违反即生产事故）

1. Python 一律用 `C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe`（托管 3.13 已损坏，禁用）
2. 部署**只走** `python scripts/push_batch.py`（GitHub REST API），禁止 `git push`
3. `data/vehicles.json` 内嵌 GitHub token——严禁外传、严禁写入日志/截图/公开仓库
4. 图片压缩/替换前确认原图已备份 `.workbuddy/backup_images/`
5. 破坏性操作（删文件/强推/重置）先说明并获我确认
6. 本地与远程 git 不同步属常态（部署走 API），不要 rebase/force-push

## 四、执行步骤（SOP）

1. 读取 `.workbuddy/memory/` 下 2026-09-03 至 09-06 日志与 `MEMORY.md`；`git status` 确认工作区（若 48 张删除态图片问题仍未处置，先停下问我）
2. 打开设计稿核对分区、文案与真实车源数据
3. 实现 rebuild_home_v7.py，生成四语首页，本地校验（分区数、车卡数、ar 为 RTL、hreflang 数量）
4. 我确认预览后：`git status` 核实变更 → commit → `python scripts/push_batch.py`
5. 线上验收：curl 校验四语首页 title、新分区标记、hreflang 数量、抽样车辆详情页 HTTP 200
6. `python scripts/submit_indexnow.py` 提交索引
7. 变更与验收结果追加到 `.workbuddy/memory/` 当日日志

## 五、首轮指令（从这条开始干）

1. 读日志与 HANDOVER_PROMPT.md，用 3 句话汇报你对项目现状的理解
2. 检查 P1（图片压缩、48 张删除态图）与 P2（数据口径 209/215）是否已解决；未解决的列出但**不阻塞**首页改版，除非确实影响
3. 开始实现 rebuild_home_v7.py，先给我 **en 版本地预览**，我确认后再铺四语并部署

---

*文档版本：v1 | 生成：2026-09-06*
