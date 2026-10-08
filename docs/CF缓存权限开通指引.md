# 给 Cloudflare Token 加「Cache Purge」权限

> ✅ **2026-10-08 16:45 已开通并实测通过。**
> zone_id = `c9b48e5c76c121593eff18f6d9164795`，
> 部署日志已能输出 `purged 12 URLs`，部署完立刻可见，不再等边缘缓存过期。
> 本文档保留作为**权限被回退时的重操作指引**。

## 为什么需要

每天上新后，主域 `jinbacars.com` 命中旧 CF 边缘缓存，最长 **4 小时**才刷新，
表现为「部署成功了但列表页还是老车排在前面」，很容易被误判成部署失败。

根因：`_headers` 里写的是 `max-age=600`（10 分钟），但 Cloudflare 后台的
Cache Rule 把它覆盖成了 `max-age=14400`（4 小时）—— 配置文件改不动，
只能主动调 purge API 清。

`scripts/deploy_pages.py` 已经内置了这个能力（部署成功后自动清），
**唯一卡点就是 token 缺 `Zone → Cache Purge` 权限**。权限给到后无需再改代码。

---

## 操作步骤（浏览器里点，约 2 分钟）

1. 打开 <https://dash.cloudflare.com>
2. 右上角头像 → **My Profile** → 左侧 **API Tokens**
3. 找到当前用的那个 token（项目 `jinba-cars` / Pages Write 那个），点右边的 **Edit**
4. ��� **Permissions** 区域，在已有的 `Account → Cloudflare Pages → Edit` 下面，
   再加两行：
   - `Zone → Zone → Read`
   - `Zone → Cache Purge → Purge`
5. **Zone Resources** 选择：
   - `Include → Specific zone → jinbacars.com`
   （如果只勾 Specific zone 而不选对，代码里自动探测 zone 会拿到空列表，清缓存会静默跳过）
6. 拉到底部点 **Update Token**（或 Save）

改完后 token 字符串通常不变，`.workbuddy/cf_token.txt` 不用动。

---

## 怎么确认成功了（已实测通过）

部署日志里应该出现这两行：

```
zone_id cached: c9b48e5c76c121593eff18f6d9164795
purged 12 URLs
```

- 出现 `purged 12 URLs` → 权限正常（首次会自动打印 `zone_id cached`，之后走缓存不再重复探测）
- 仍是 `SKIP cache purge (...)` → 权限或 zone 范围没选对，把括号里的原因发我

验证线上效果（裸路径 = 真实用户视角，应直接看到新内容）：

```bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"
curl -s -A "$UA" "https://jinbacars.com/en/cars/" | grep -o 'JB-[0-9]\{4\}' | awk '!seen[$0]++' | head -3
```

---

## 临时方案（权限万一又被回退）

不改权限的话，边缘缓存 `s-maxage=3600` 会自然过期，误差最多 1 小时。
每天上新后如果想让访客立刻看到，手动清一下这几个链接即可（浏览器打开即触发刷新）：

- <https://jinbacars.com/en/cars/>
- <https://jinbacars.com/zh/cars/>
- <https://jinbacars.com/ru/cars/>
- <https://jinbacars.com/ar/cars/>

带 `?` 随机参数的请求不会命中旧缓存，可用来验证源站内容是否已经是新的。

## 排查提示

CF API 偶发 `curl: (56)` 之类报错 = **代理抖动，不是权限问题** ——
重试或加 `--noproxy '*'` 直连即可恢复，别误判成 token 出问题。
