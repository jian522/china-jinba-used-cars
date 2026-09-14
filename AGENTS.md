# AGENTS.md — 金霸二手车出口站（jinbacars.com）

本文件是给 AI 编码助手（Codex CLI / Claude Code / WorkBuddy 等）的项目指令。

## 动手之前：先读完整 SOP

```
C:\Users\Administrator\.workbuddy\skills\jinba-car-pipeline\SKILL.md
```

凡是涉及「采集车源 / 上架车辆 / 抓图 / 修图 / 重建页面 / 部署上线」的操作，
**必须先读上面那份 SKILL.md 并按它的流程执行**，不要自创流程或跳过校验步骤。

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

它跑到 `cover_auto.py --export` 那步就停下来等目检，你必须接着做：

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
