# AGENTS.md — 金霸二手车出口站（jinbacars.com）

本文件是给 AI 编码助手（Codex CLI / Claude Code / WorkBuddy 等）的项目指令。

## 动手之前：先读完整 SOP

```
C:\Users\Administrator\.workbuddy\skills\jinba-car-pipeline\SKILL.md
```

凡是涉及「采集车源 / 上架车辆 / 抓图 / 修图 / 重建页面 / 部署上线」的操作，
**必须先读上面那份 SKILL.md 并按它的流程执行**，不要自创流程或跳过校验步骤。

```
D:\二手车出口网站\.codebuddy\skills\jinba-wa-quote\SKILL.md
```

凡是涉及「WhatsApp 客户询价 / 报价 / 回客户消息 / 发实车图」的操作，
**必须先读 jinba-wa-quote 并按它的流程执行**。
加价规则只有那一个口径，**已在 `scripts/quote_calc.py` 里固化，禁止心算、禁止自创档位**。

## WhatsApp 询价报价（日常高频，一次两条命令）

```bash
cd "D:/二手车出口网站"
PY="C:/Users/Administrator/AppData/Local/Programs/Python/Python312/python.exe"
S=".codebuddy/skills/jinba-wa-quote/scripts"

# 1) 匹配库存 → 只认 status=published
"$PY" .workbuddy/wa_stock_lookup.py --search "哈弗H6" --limit 10

# 2) 算 FOB 报价（加价规则固化在脚本里）
"$PY" "$S/quote_calc.py" --price-usd <price_usd> --id <vehicle_id>

# 3) 桌面端dry-run 看文案，加 --send 才真发（--expect 必填）
"$PY" .workbuddy/wa_desktop_send.py --vehicle-id <id> --price-usd <加价后报价>
"$PY" .workbuddy/wa_desktop_send.py --vehicle-id <id> --price-usd <加价后报价> \
    --expect <客户号码> --send
```

### 加价规则（方案 C · 保底封顶比例制，2026-08 简哥确认）

**护栏**：`MIN 15%` ／ `MAX 35%` ／ `DEFAULT 22%`

| 档 | 车价（人民币） | 加价率区间 |
|---|---|---|
| A | `< 10 万` | 20% ~ 30% |
| B | `10 万 ≤ 车价 < 20 万` | 18% ~ 28% |
| C | `≥ 20 万` | 15% ~ 25% |

- 报价**向上取整到 100 美元**，汇率 `USD/CNY = 7.10`
- **旧口径保留**：`--mode abs` 走人民币绝对额分档（默认 `band`）
- ⚠️ **成本基数 = `price_usd`（零售挂牌价），非采购成本**。`vehicles.json` 无任何成本字段，
  所以 `markup_ratio` 是零售价口径。**补齐采购成本表后必须重算。**

### 三条硬约束（违反即返工，与本文件规则同级）

4. **报价必须走 `quote_calc.py`**，禁止心算或直接报 `price_usd`（那是成本价，没加价）。
5. **只用 WhatsApp 桌面端**（UWP/Store 版，`WhatsApp.Root.exe`，在 `WindowsApps` 目录），
   **不新开窗口/标签页**。网页版已停用。发送一律走 `.workbuddy/wa_desktop_send.py`。
6. **3 分钟内有店主真人在对话 → 让位，禁止插话**（会出现自相矛盾的两个报价）。

> ⚠️ **UWP 收件人核对局限**：桌面端读不到 DOM，无法程序化校验会话身份。
> 实操必须：`--probe` 看截图 → 人工确认会话 → 再 `--send`。

## 环境（每次都要）

```bash
cd "D:/二手车出口网站"
PY="C:/Users/Administrator/AppData/Local/Programs/Python/Python312/python.exe"
```

- Python **必须用 3.12**（含 requests / Pillow）。默认 `python` 是 3.13，缺依赖会 ModuleNotFoundError。
- GitHub token 从 `GH_TOKEN` 环境变量或 `~/.git-credentials` 读。
- `m.che168.com` 被 EdgeOne 拦截，只能走 `wap.che168.com`。

## 三条硬规则（违反即返工）

1. **首图（primary / 封面）必须是车辆正前脸或左前 45° 外观照。**
   内饰、车尾、正侧面、局部特写（车灯 / 轮胎 / 中控 / 座椅 / 钥匙）、带车商横幅的图
   一律不能当封面。纯图像算法判不准，**必须由你亲自 Read 拼图目检后裁决**。
2. **每张图不得含水印 / logo / 角标叠印。**
3. **`photo_check.py` 或 `validate_inventory.py` 不过，绝不部署。**

## 日常主入口

每天上架 3~5 台走这一个命令，内部已串好全链路（含封面合规与 CF Pages 现网部署）：

```bash
"$PY" scripts/daily_upload.py --dry-run    # 先看计划：今天轮到哪些车型、起始库存号
"$PY" scripts/daily_upload.py              # 正式跑，默认 4 台
"$PY" scripts/daily_upload.py --count 3    # 指定台数（自动夹到 3~5）
```

⚠ **注意（2026-09-25 实测校正）**：`daily_upload.py` **不会**在 `cover_auto --export` 处停下等目检 ——
找不到 `picks.json` 时它只打印一条告警就继续构建并**直接部署**。所以要么**先分步跑**
（采集 → ingest → photo_fix → cover_auto --export → 目检裁决 → picks --commit → 构建 → 校验 → 部署），
要么先把 `picks.json` 准备好再整体跑。**别裸跑整体流程，否则等于违反规则 1。**

分步复刻时必须接着做：

1. `Read` `.workbuddy/cover_auto/candidates.png`
   （拼图看不清就按车读 `.workbuddy/cover_auto/<vid>/img_NN.jpg`）
2. 写 `.workbuddy/cover_auto/picks.json`，格式 `{"<vehicle_id>": <图片序号>}`，序号从 1 开始
3. `"$PY" scripts/cover_auto.py --picks .workbuddy/cover_auto/picks.json --commit`

**没有 picks.json，封面就不会被校正 —— 等于违反规则 1。**
全部候选都不合规时，该车置 `unpublished` 等人工处理，**绝不硬塞**。

## 部署（两步都要，缺一不可）

```bash
"$PY" scripts/push_api.py plan              # 看差异
"$PY" scripts/push_api.py upload 150        # 分批传，重复跑到「待传 0」
"$PY" scripts/push_api.py finish "说明"     # 建树 → commit → 更新 main
"$PY" scripts/deploy_pages.py               # ★ 现网 jinbacars.com 由 CF Pages 服务
```

`push_api.py` 只同步 GitHub 备份仓库；**漏掉 `deploy_pages.py`，新车不会出现在现网。**
成功标志：输出含 `Deployment complete`。

## 其他约定

- 写盘类操作（`--commit`）之前一律先跑预演。`cover_auto.py` / `photo_fix.py` / `ingest_batch.py`
  都是「不传 `--commit` 即预演」，**没有 `--dry-run` 这个参数**（只有 `daily_upload.py` 有）。
- `data/`、`admin/` 是运营目录，`push_api.py` 的 `DEPLOY_DROP` 已配置不推公开站点，别改这个规则。
- 采集只抓公开页面可见内容，脚本自带请求间隔，不要并发放大。
- 新增车型要先在 `.workbuddy/scrape/scrape_wap.py` 补
  `BRAND_EN` / `MODEL_I18N` / `MODEL_BRAND` 三张映射表，否则标题翻译与品牌识别会缺失。
- 选型参考：`scripts/build_v2.py` 生成中英俄阿四语页面；缩略图用 `make_thumbs.py`。
