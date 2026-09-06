# 金霸二手车出口站 · 车源数据迁移与自动采集方案

> 版本：v1.0 · 2026-09-06 · 配套管线：`scripts/auto_pipeline.py`（一键入库→构建→验收→部署→索引提交）

---

## 一、各模块职责

| 模块 | 文件 | 职责 |
|---|---|---|
| 车源入库器 | `scripts/ingest_batch.py` | 读取批次 CSV + `imports/<批次>/<stock_id>/*.jpg`，校验后写入 `data/vehicles.json` 与 `uploads/cars/<id>/`（转 WebP ≤1600px q86）。**发布门槛内置**：图片 6–9 张、四语标题齐全，不达标自动置 `unpublished`；`primary` 字样文件或数字前缀 01 排首图 |
| 缩略图器 | `scripts/make_thumbs.py` | 为全部车辆图生成 `.th.webp` 缩略图（列表页 srcset 用） |
| 全站构建器 | `scripts/build_v2.py` | 从 vehicles.json 生成四语全站（约 1200 页）+ sitemap/feed/IndexNow key；**末尾自动补跑 rebuild_home_v7.py** 重建四语首页 |
| 首页生成器 | `scripts/rebuild_home_v7.py` | 2026-09 深蓝+橙改版首页；精选 4 卡自动重选（published + ≥6 图 + 文件在盘 + 首图不重复），在售台数 = published 数 |
| 验收器 | `scripts/verify_ui.py` | 62 项静态检查（v7 分区数、hreflang、RTL、图片路径、sitemap 一致性），退出码非 0 即阻断部署 |
| 部署器 | `scripts/push_api.py` | 唯一部署通道：GitHub REST API（远程基线树 diff → blob 上传 → 建树 → commit → 更新 main），finish 成功后自动跑 IndexNow。`push_batch.py` 已结构性报废，勿用 |
| 一键管线 | `scripts/auto_pipeline.py` | 调度上述全部模块，任一步失败立即中止 |

## 二、数据采集与存储方案

### 2.1 采集通道（合规边界）

**自动抓取"二手车之家"（che168）页面/图片不可行且不合规**（2026-09-03 已与用户确认）：
- 违反其 robots.txt 与用户协议；平台图片版权归平台与车商，商用侵权；
- 去除水印/logo 属移除版权管理信息（DMCA 1202），加重情节；
- 业务层面：二手车出口卖的是车况信任，图不符实 = 退定金 + 复购归零。

**可全自动执行的合规采集通道**：

1. **车商授权供稿（主通道，可全自动）**
   - 向合作车商下发《`imports/车商索图与拍摄规范.md`》：10 机位清单（首图=前脸正视或左前 45°，6 张必拍=5 外观+1 主驾内饰），横构图、长边 ≥1600px；
   - 车商按 `imports/<批次>/<stock_id>/01_正面.jpg … 10_机舱.jpg` 命名放入批次目录，或经网盘/微信收取后由本方归档；
   - CSV 每行一台车（模板 `data/import-template.csv`）：`stock_id,title,brand,model,year,mileage_km,price_usd,fuel,transmission,body_type,color,…`，可选 `title_en/ru/ar` 与 `action` 列。
2. **既有平台数据迁移（历史批次）**：`imports/2026-08-che168/`（56 台）已是此形态——CSV 行 + stock_id 图片目录，`ingest_batch.py` 直接消化；新批次照此办理即可无缝续接入库。
3. **人工/半自动补图**：`data/photo-completion-queue.csv` 按缺口降序+品牌聚合列出待补图车辆，用于向车商整批索图；收回后走同一管线。

> 后续如需自动下载车商网盘链接，可加一个取文件的前置脚本（把网盘文件落成 `imports/<批次>/<stock_id>/` 目录），管线其余环节零改动。

### 2.2 发布门槛（硬校验，管线内不可跳过）

| 项 | 规则 | 不达标处置 |
|---|---|---|
| 图片数量 | 6–9 张/台（≥6 发布） | 自动 `unpublished`，进入补图队列 |
| 首图 | 文件名含 `primary` 或 `01_` 前缀排第一；要求为前脸正视/左前 45° | 入库时提示人工确认角度 |
| 四语标题 | title + title_en/ru/ar 齐全 | 自动 `unpublished`（待翻译） |
| 图片质量 | 自动转 WebP ≤1600px q86；MD5 去重告警 | 重复图列出供人工核对 |
| 替换/下架 | CSV `action=update/unpublish` 或 `--unpublish` 清单 | 更新字段或下架，不删历史图 |

### 2.3 存储结构

```
data/vehicles.json                 # 单一数据真源（215+ 条；status=published 才上架）
uploads/cars/<id>/primary.webp     # 首图（_frontend 用 photos[0]）
uploads/cars/<id>/photo-02..09.webp
uploads/cars/<id>/*.th.webp        # 缩略图
imports/<批次>/<stock_id>/*.jpg     # 原始供稿（不部署到线上）
data/photo-audit.json              # 图片完整性/重复首图审计（rebuild_home_v7 读取）
```

## 三、部署上线方式

- **唯一通道**：`push_api.py`（GitHub REST API → GitHub Pages，jinbacars.com），禁止 `git push`。
- **全自动闭环**（`--mode all` 一次跑完）：

```
ingest 入库（6图/四语门槛，不达标自动 unpublished）
  → make_thumbs → build_v2（自动重建 v7 首页）→ verify_ui（62 项，失败即停）
  → git add -A + commit → push_api plan → upload（断点续传，400/批）→ finish
  → （finish 内部自动）IndexNow 提交全站 URL
```

- **推送后验证铁律**（9/3 事故教训）：`finish` 返回 OK 后必须核对远程 blob sha 与本地一致：
  `GET /contents/<path>?ref=main` 对比 `git ls-tree HEAD <path>`。
- **Pages 构建延迟 1–2 分钟**，推送后立即 curl 可能假 404，需等待重测。

## 四、操作速查

```bash
# 1) 新批次车源采集入库 + 构建 + 验收（预演）
python scripts/auto_pipeline.py --mode ingest --batch 2026-09-che168 --csv imports/2026-09-che168/vehicles.csv --dry-run
# 2) 正式全流程（入库→构建→验收→提交→部署→IndexNow）
python scripts/auto_pipeline.py --mode all --batch 2026-09-che168 --csv imports/2026-09-che168/vehicles.csv --commit-msg "feat: 9月车源批次上线"
# 3) 仅重建首页/全站并部署
python scripts/auto_pipeline.py --mode deploy --commit-msg "feat(home): v7 首页改版上线"
```

约束：一律用系统 Python 3.12.4（`C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe`）；`data/vehicles.json` 内嵌 GitHub token，严禁外传；破坏性操作（删文件/强推）需先获用户确认。
