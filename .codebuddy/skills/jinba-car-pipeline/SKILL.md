---
name: jinba-car-pipeline
description: 金霸二手车出口站（jinbacars.com）车源一条龙流水线：从二手车之家（che168.com）wap 站采集在售车源实拍图与参数，生成入库素材包，再批量入库、转 WebP、生成中英俄阿四语页面、校验并部署上线到 GitHub Pages。当用户说「抓二手车之家图片」「采集车源」「che168 采集」「扒图/抓车/下载实拍图」「批量上传车辆」「上架这批车」「把车传到 jinbacars.com」「发布车辆产品」「更新在售车型」「下架旧车」时使用。
description_en: End-to-end pipeline for the Jinba used-car export site (jinbacars.com) — scrape used-car listings and real photo sets from che168.com WAP, build an import batch, then batch-ingest, convert to WebP, generate zh/en/ru/ar pages, validate and deploy to GitHub Pages.
version: 1.0.0
author: jinba
level: project
---

# 金霸车源采集与上架流水线

从「二手车之家抓车」到「jinbacars.com 上线」的完整链路，一条龙跑完：

```
采集(che168) → 入库 → 缩略图 → 建四语页 → 校验 → 部署上线
```

两个阶段可单独调用，也可连起来跑。

## 前置（每次都要）

- 工作目录必须是项目根 `D:\二手车出口网站`。
- 解释器固定用 **Python 3.12**（含 requests / Pillow）。默认 `python` 是 WorkBuddy 内置 3.13，**缺依赖会报 ModuleNotFoundError**：

```bash
cd "D:/二手车出口网站"
PY="C:/Users/Administrator/AppData/Local/Programs/Python/Python312/python.exe"
```

- GitHub token：从 `GH_TOKEN` 环境变量或 `~/.git-credentials` 自动读取。

---

## 阶段一：从二手车之家采集车辆实拍图

按车型关键词从 `wap.che168.com` 抓在售车源，每台车下载 8–9 张实拍原图，
生成四语标题 + 规范化 CSV，落地成可直接入库的素材包。

```bash
# 单车型（推荐先小批量试跑）
"$PY" .workbuddy/scrape/scrape_wap.py \
  --kw "哈弗H6" --n 3 \
  --batch 2026-09-che168 \
  --stock-prefix JB-8100

# 全量（按脚本内置 TARGETS 逐车型跑）
"$PY" .workbuddy/scrape/scrape_wap.py --all --batch 2026-09-che168-full
```

### 采集参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--kw` | - | 车型关键词，与 `--all` 二选一 |
| `--all` | - | 按内置 TARGETS 全跑 |
| `--n` | 3 | 该车型抓几台 |
| `--pages` | 2 | 翻几页列表 |
| `--batch` | 必填 | 批次名，决定 `imports/<batch>/` |
| `--stock-prefix` | JB-8100 | 起始库存编号，逐台 +1 |
| `--fx` | 7.2 | 人民币→美元汇率 |
| `--out-rmb-min/max` | 1.5/30.0 | 车价（万元）区间过滤 |
| `--year-min` | 2018 | 上牌年份下限 |
| `--departure-port` / `--trade-term` | 上海港 / FOB | 写进 CSV |
| `--require-guo6` | 开 | 只要国六 |

### 产物

```
imports/<batch>/<stock_id>/<stock>_src_1..N.jpg   # 8–9 张原图，按 che168 顺序
imports/<batch>/<stock_id>/primary.jpg            # 首图（主图）
imports/<batch>/<stock_id>/spec.json              # 原始字段，供人工复核
imports/<batch>/vehicles.csv                      # 追加写入，直接进下一阶段
```

新增车型先补 `scrape_wap.py` 里的 `BRAND_EN` / `MODEL_I18N` / `MODEL_BRAND` 三张映射表，
否则标题翻译和品牌识别会缺失。

---

## 阶段二：批量上传产品到 jinbacars.com

### 1. 预演（默认，不写任何文件）——必须先跑

```bash
"$PY" scripts/ingest_batch.py --batch 2026-09-che168 --csv imports/2026-09-che168/vehicles.csv
```

### 2. 正式入库（加 `--commit` 才写 `data/vehicles.json` + `uploads/cars/<id>/`）

```bash
"$PY" scripts/ingest_batch.py --batch 2026-09-che168 --csv imports/2026-09-che168/vehicles.csv --commit
```

### 3. 缩略图 + 重建四语页面 + 库存校验

```bash
"$PY" scripts/make_thumbs.py
"$PY" scripts/build_v2.py
"$PY" scripts/validate_inventory.py
```

### 4. 部署上线

```bash
"$PY" scripts/push_api.py plan            # 看差异（新增/修改/删除 + API 配额）
"$PY" scripts/push_api.py upload 150      # 分批传 blob，重复跑直到传完
"$PY" scripts/push_api.py finish "新增 12 台哈弗/比亚迪"   # 建树 → commit → 更新 main
```

`finish` 成功后自动提交 IndexNow，GitHub Pages 约 1–3 分钟生效。

### 入库参数

| 参数 | 说明 |
|---|---|
| `--batch` | 批次目录名（默认在 `imports/` 下） |
| `--batch-root` | 批次根目录（沙箱测试时指向别处） |
| `--csv` | 车辆 CSV 路径 |
| `--data` | 目标 `vehicles.json`，默认 `data/vehicles.json` |
| `--uploads-root` | 图片落盘根目录，默认 `uploads/` |
| `--min-photos` | 最少图片数，默认 6，不足自动未发布 |
| `--commit` | 真正写入；缺省预演 |
| `--unpublish` | 一个文件，每行一个要下架的 stock_id（配合替换老车型） |

### 数据约定

CSV 列（与 `data/import-template.csv` 一致）：

```
stock_id,title,brand,model,year,mileage_km,price_usd,fuel,transmission,
body_type,color,drive,engine,seats,emission,departure_port,trade_term,
vin_last6,registration_date,production_date,status,source
```

可选：`title_en` / `title_ru` / `title_ar` / `action(add|update|unpublish|replace)`

图片：`imports/<批次>/<stock_id>/*.jpg|png|webp`，6–9 张；文件名排序即展示顺序
（可加 `01_/02_` 前缀，文件名含 `primary` 优先排第一）。主图应为前脸或左前 45°。

发布条件：图片 ≥6 张 **且** 四语标题齐全，否则自动置 `unpublished`（待补待译）。

---

## 一键跑完（可选）

项目内已有编排脚本，可替代上面的分步执行：

```bash
"$PY" scripts/auto_pipeline.py --mode all --batch 2026-09-che168 \
  --csv imports/2026-09-che168/vehicles.csv --commit-msg "新增车辆"
```

## 沙箱测试（不碰真实数据）

```bash
"$PY" scripts/ingest_batch.py --batch 2026-09-che168 \
  --csv imports/2026-09-che168/vehicles.csv \
  --data .workbuddy/tmp/vehicles.json --uploads-root .workbuddy/tmp/uploads
```

## 注意事项

- **永远先跑不带 `--commit` 的预演**，确认新增/更新/下架数量与图片张数无误再写。
- 部署前 `validate_inventory.py` 必须无 ERROR，否则先修数据再推。
- 已存在的 `stock_id` 视为更新，会替换该车照片与字段；替换老车型请在 CSV 里对旧 stock 标 `action=unpublish`。
- `data/` 与 `admin/` 是运营目录，`push_api.py` 已配置 `DEPLOY_DROP` 不推送到公开站点，别改这个规则。
- `m.che168.com` 被 EdgeOne 拦截，只能走 `wap.che168.com`；列表页结构变了先跑 `.workbuddy/scrape/probe_list.py` 探结构。
- 采集只抓公开页面可见内容，脚本已带请求间隔，不要并发放大；图片上架前人工复核 `spec.json`，收到盗图/水印诉求立即下架。
