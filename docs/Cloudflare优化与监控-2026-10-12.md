# jinbacars.com Cloudflare 优化与监控

## 最终完成状态（北京时间 2026-10-12 15:39 复测）

Cloudflare 后台变更已经上线，下面逐条规则清单与 `cloudflare-rules-20261012.json` 的实际 ID、表达式和动作一致。

| 规则 / 操作 | 当前状态 |
|---|---|
| W1 扫描路径 Block | 已启用，排第一；保留原有防护并补环境文件、PHP、管理入口 |
| W2 扫描 IP Managed Challenge | 已启用；用户确认将原 SI 全国家挑战缩窄到 31.57.216.50，排除 verified bots |
| RL1 页面突发限速 | 已启用；每 IP 60 次/10 秒，Block 10 秒，图片和 CSS/JS 不计入；Free 限制下为 zone 级 |
| C1 公开静态资源 | 已启用；edge 1 天，browser 配置 2 小时，状态码 >=400 No store，保留全部查询参数 |
| C2 私有路径 / Authorization | 已启用；置于 C1 后，Bypass cache；不按所有 Cookie 绕过 |
| H1 成功公开静态响应头 | 已启用；Set static Cache-Control 为 public, max-age=7200, s-maxage=86400；排除授权、Set-Cookie、private/no-store 响应 |
| R1 四个旧库存入口 | 已启用；/cars、/cars/、/cars.html、/cars-detail.html → /en/cars/，301，保留 query |
| 三条旧 Page Rules | 均已禁用；保留快照便于复核，没有删除 |
| Zone Browser Cache TTL | Respect Existing Headers；开发模式和全站 Under Attack 未开启 |
| 定向 purge | 成功清理 19 个主域 URL；没有本次全 zone purge |
| 本地源文件 | _headers、_redirects、构建器、按变更 purge 已修正并检查；未部署 Pages，未发布本地新车 |

现场验证：CSS 和已发布实车图返回 200/HIT，Age 增长；实际静态响应头现在是一组 `public, max-age=7200, s-maxage=86400`。分析 Cookie 请求仍 HIT；带 Authorization 请求 DYNAMIC，不被 H1 改写。不存在的未来图片连续 404/no-store/BYPASS，没有旧 30 天负缓存。四语页面与询价入口 200，库存页保持源头 HTML 10 分钟/edge 1 小时策略和 Pages 原生缓存。扫描路径 403，旧入口 301 且 query 保留。没有进行生产高频压测来触发限速，以免影响共享 IP 上的客户；限速参数通过 Cloudflare 校验并在列表确认 Active。

7 天流量结论使用上午审计窗口：约 14.24k 请求、5xx 0，SI 扫描 IP 约 2.59k。它们不是运行配置后的改善百分比。没有足够数据计算真实买家占比，也没有证据声称原 504 已被永久修复。48–72 小时后按下文相同窗口和资源类别复核缓存、错误和询盘指标。

Cloudflare DNS 页面在本次浏览器中加载模块失败，现有 Token 也无 DNS/设置/完整分析读取权限；因此未声称完成 DNS 记录、全部日志的逐项核验。Pages API 已确认主域/www绑定、成功生产部署；实际 HTTPS 请求、四语页面及部署域对照正常，域名概览显示无连接 Worker，Rules Overview 无自定义 Origin Rules。历史 504 仍需原始 URL、时间、Ray ID 与 RequestSource 才能闭环定位。

日期：2026-10-12；时区：Asia/Shanghai。主站：jinbacars.com、www.jinbacars.com。当前套餐：Free。W1 的继承分支与 RL1 为 zone 级，可能影响 shop.jinbacars.com；不能把全部规则称为排除 shop。

这是可复用操作文档。旁边的 cloudflare-rules-20261012.json 记录逐条规则与状态，不是替换现有整个 ruleset 的 API payload。本次控制台已确认 W1、W2、RL1、C1、C2 启用，三条旧 Page Rules 停用，Browser Cache TTL 改为 Respect Existing Headers；C1针对限定静态资源单独覆盖为边缘1天、浏览器2小时。本地站点文件修正尚未部署，不能把控制台规则生效与源码部署混为一谈。

| 已确认配置 | 规则 ID / 范围 | 现场状态 |
|---|---|---|
| W1：Block common exploit scanning paths | b5c60f930e164c2eb3a971427bc800af；原8项全zone分支保留，新增分支限apex/www | Active；自定义规则第1条；Block |
| W2：Challenge confirmed scanner 31.57.216.50 | f433847f080b49e9ab8752b0dc70b791；apex/www，排除verified bot | Active；自定义规则第5条；Managed Challenge；已按用户追加批准从整个SI缩窄至该IP |
| RL1：HTML burst protection 60 per 10s | b83d25ed6dd54c6981604d1e0b03313a；根路径与四语路径，zone级 | Active；每IP 60次/10秒，Block 10秒；已控制台核对 |
| 旧 Page Rules | CSS 30天、WebP 30天、全站1天覆盖 | 三条均 Disabled；Token PATCH 返回403，实际通过控制台保存成功；不是API修改成功 |
| Browser Cache TTL | zone设置 | 已在控制台改为 Respect Existing Headers |
| C1：JINBA public static assets 1d edge 2h browser | a47447fc55944498af417686fbf9ee23；主站限定静态目录与扩展名 | Active；边缘86400秒、浏览器7200秒；状态>=400 No store；保存后编辑页再次核对 |
| C2：JINBA private paths and authorization bypass | 33e7fc3719414779814413aa2d7cd10f；主站敏感路径或Authorization | Active；Bypass cache；Cache Rules最后一条 |
| 精确缓存清理 | 19个apex URL | Purge API成功；没有Purge Everything，没有清整个zone |

## 现场结论与证据边界

| 项目 | 已知事实 | 判断 |
|---|---|---|
| 当前近 7 天请求 | Cloudflare UI 约 14.24k | 与用户最初 14,315 的截图可能窗口或取整不同；比较前先统一起止时间、host 和筛选 |
| 当前 5xx | 同一 UI 近 7 天显示 0 | 用户最初“504 9.8%”尚未在当前同口径数据复现；不能声称已经修好 504 |
| 斯洛文尼亚 | 约 2.59k 请求全部来自 31.57.216.50；约 3 个 2xx、1.11k 个 3xx、1.47k 个 4xx；约 2 visits | 单 IP、高失败率、敏感路径探测构成扫描证据；visits 不是两个真实客户 |
| 热门扫描路径 | /.env.workers、/.env.razorpay 等 | 这是泄露配置扫描，不是看车路径；Top 路径页面为 50% 采样，不能据此还原全部请求 |
| 生产架构 | Cloudflare Pages Direct Upload；生产部署 769832b0.jinba-cars.pages.dev（10-11） | 没有本项目 VPS、Nginx、PHP 或数据库可调；优先排 Pages、zone 路由、规则和具体异常 |
| 页面业务 | 四语静态 HTML；库存筛选在浏览器；询价表单生成 wa.me / mailto 链接；GA4 有 whatsapp_click | 可以缓存公开内容；真实转化应看询价与业务结果 |
| 缓存改动 | 旧全站1天与CSS / WebP 30天 Page Rules 均已在控制台停用；Browser TTL已尊重现有头部 | 停用了曾将不存在WebP的404长期缓存的覆盖；既有缓存与源头头部仍须复核 |
| 新缓存规则 | C1限定静态目录及扩展名，1天edge / 2小时browser / >=400 No store；C2敏感路径或授权请求Bypass | 不缓存全站HTML、不忽略v、不因任何cookie就跳过；后续复核静态资源重复命中 |
| 现网页面复核 | 精确purge后四语HTML均200；max-age=600、s-maxage=3600，cf-cache-status=DYNAMIC | HTML继续Pages原生服务；DYNAMIC不等于直接打自管源站 |
| 源头头部 | 预览域 CSS 响应确认合并三组 Cache-Control，包含冲突 max-age / s-maxage | _headers 重叠是真问题；修正头部后要在上线后的主域再次验证 |
| 清缓存 | 10-10 部署日志显示 purged 930/930 URLs | 大范围 purge 会制造冷缓存；应避免把它保留为每日默认 |
| 新车边界 | 生产 HTML 最高 ID 470；本地今天新增 471–474 尚未发布 | 473 / 474 的未来图片 URL 404，不是已发布车辆的坏链证据 |
| 本地检查 | 995 份公开 HTML、54,315 个本站引用、992 个 sitemap URL 未发现可部署清单缺失路径 | 属于本地引用检查，不代表已逐一验收所有现网 URL |

本地 _headers、构建器的无效 _redirects 生成以及部署 purge 范围已修正，但尚未公开部署。这一事实必须与已经在 Cloudflare 后台配置的规则分开记录。不得为了发布缓存修改，顺带发布今天尚未完成流程的新车；下一次站点部署仍须遵循 AGENTS.md 与车辆流水线 SOP，图片目检、photo_check.py、validate_inventory.py 均通过后才能部署。

## ① 判断流量与处理斯洛文尼亚异常

美国 40%、斯洛文尼亚 15.9% 只是来源分布。美国既可能是真实买家，也可能是搜索引擎、机房和代理；欧洲、美国、中东的普通访客都不能仅凭国家或 ASN 被拦。

建议以会话行为分类：

| 类型 | 实用证据 | 处理 |
|---|---|---|
| 高意向买家 | 多个车辆详情页、车型 / 港口相关页面、WhatsApp 点击、有效业务询价 | 保留访问；用 GA4 与真实询价对照 |
| 普通访客 | 首页或内容页正常浏览，无扫描行为 | 保留；不能因为停留短、无 referer 或单页访问就定为恶意 |
| 已验证搜索爬虫 | Cloudflare cf.client.bot；正常抓 sitemap / robots / 页面 | 不用地理封锁；W2 和限速排除此类 bot |
| 恶意扫描 | 同 IP 连续探测 .env、.git、PHP / WordPress；大量 4xx / 重定向；无看车行为 | 敏感路径 Block；已证实 IP 暂时 Managed Challenge |
| 尚未确认的采集器 | 高频正常目录抓取，证据不足 | 先观察 HTML 请求速率、访问路径、转化；必要时短限速，不封国家 |

已对 31.57.216.50 启用 W2 临时挑战，并按用户追加批准将原SI整体挑战缩窄到该IP。24 小时后看命中、挑战通过、路径和业务反馈再决定是否继续。规则不会自动过期，需人工复核、禁用或删除。不能扩大成整个斯洛文尼亚、整个 ASN 或所有美国机房的永久封禁。

安全事件与分析应同时记录 host、path、country、IP、ASN、action、status、UA 和时间。Referer、UA 都可伪造，不能作为单一白名单；cf.client.bot 是 Cloudflare 的验证结果，不能靠伪造 Googlebot UA 获得。

## ② 504 排查树与对应优化

第一步先证明错误存在：选定具体时间窗口和 host，检查 HTTP 状态码细分是否真的有 504。保存异常 URL、时间和时区、响应状态、完整 cf-ray、colo、响应头、错误页截图。区分访问失败、部署 API 超时、Cloudflare 页面中单独的统计指标。

本地 10-10 Wrangler 日志中的 Cloudflare API 超时发生在部署期间，重试后部署成功；这不能解释访客 504。

还需区分内部缓存子请求：Early Hints 的 cache MISS、Workers Cache API 的 cache.match MISS可以在日志或分析中出现504，而访客最终响应仍成功。若有日志权限，按 RequestSource 的 earlyHintsCache / edgeWorkerCacheAPI 与真正访客请求拆分，并检查最终响应与 Ray ID。当前请求分析UI显示近7天5xx为0；没有证据证明用户原“504 9.8%”一定来自这些内部请求，不能将这一可能性直接定为根因。[官方关于内部缓存MISS与504的说明](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-502-504/)

~~~text
当前同口径是否出现真实 504？
├─ 没有：保留原截图和筛选；比较窗口 / host / 采样 / 指标；
│        继续短期监控，不改超时参数，也不声称彻底修复。
└─ 有：对同一个已发布、实际存在的 URL做少量对照
   ├─ 主域异常，生产 canonical Pages URL 正常：
   │   检查主域 DNS / Pages 自定义域名状态、Worker routes、
   │   Origin Rules、Redirect Rules、缓存规则、旧 Page Rules；
   │   用 Trace 查看匹配，临时撤销最近相关规则后复核。
   ├─ 主域和生产 canonical Pages URL 都异常：
   │   查 Pages 部署状态、部署资产、Cloudflare 服务状态；
   │   若有 Function / Worker，查其日志、子请求和外部依赖超时；
   │   当前仓库没有 Functions，不能假设 PHP / SQL慢。
   └─ 仅少数 colo / 时间段：
       保存 Ray ID / colo / 时间 / 路径，检查平台事件；
       重复发生时将证据提交平台支持，不用全球延长超时掩盖。
~~~

Cloudflare / Pages 侧优先保留静态架构与原生资产缓存，修冲突响应头，减少日常全站 purge，限制已确认扫描。不要自行更改 DNS、切换源站、新增 Worker 或套用服务器超时脚本。

若以后接入传统源站，才需要进一步查源站 access / error 日志、CPU / 内存 / 磁盘、连接数、反向代理 upstream 时间、慢 SQL、外部接口、SSL / DNS、压缩和完整 Content-Length。动态操作不能为了提高命中率被缓存；缓慢任务应用异步处理与明确超时 / 重试预算。该分支是以后适用的方案，不是当前站点已发现的根因。

[Cloudflare 502 / 504 排查说明](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-502-504/)

## ③ 404 扫描与历史路径分别处理

敏感路径在 WAF 边缘 Block，避免继续打到 Pages 服务。保留顶层 404.html 和真正的 404 状态；不要把所有不存在路径统一 301 到首页或返回 200，这会隐藏故障、造成软 404，也不能阻止扫描。

历史客户 / 搜索路径保留有意义的 301，例如 /cars.html、/cars-detail.html、旧 /car/8xxx/ 与旧品牌查询入口。已售、已下架车辆应按实际业务选择相关列表或真实 404 / 410；不得盲目创建空详情页。GSC 旧清单在 .workbuddy/gsc_404.json，其年份 / 抓取时间不能当成本周扫描统计。

Pages 的 _redirects 不支持用 404 / 410 状态码重写来挡扫描；无效的 /uploads/cars/* 404 和 /cdn-cgi/l/email-protection 410 应从生成器和文件同时移除。真实实车图就在 /uploads/cars/，不得封整个目录。若确实需要 410，需平台支持的方式或明确代码实现；不是给 _redirects 填 410。

对 4xx 监控至少分为“敏感扫描”、“旧客户 / GSC路径”、“当前已发布 HTML / JS / 图片实际故障”。已发布图片返回 404应立即处理；尚未发布的 471–474 URL不计为现网坏链。

[Pages 重定向支持范围](https://developers.cloudflare.com/pages/configuration/redirects/)

## ④ 缓存方案：先恢复 Pages 原生，再考虑限定 Cache Rules

Pages 已自带资产缓存和 Tiered Cache。低 cf-cache-status HIT 不能直接等同于每次都打到了自管源站；本项目也没有这样的源站。官方建议通常不要在 Pages 自定义域名叠加全站自定义缓存，这样会干扰部署更新、重定向或 Functions。先恢复正确缓存行为，再按合格资源计算命中率。[Pages 缓存行为与建议](https://developers.cloudflare.com/pages/configuration/serving-pages/)

执行顺序：

1. 三条旧 Page Rules 已通过控制台停用并确认 Disabled；保留旧配置快照，继续检查zone范围与shop影响。Token PATCH 403不代表UI变更失败，也不能报告API已修改成功。
2. Browser Cache TTL 已通过控制台改为 Respect Existing Headers；当前现网HTML源头为600/3600秒，本地待部署的新头部为300/3600秒。
3. 在下一次合规部署中发布修好的 _headers；同一资源只返回一组明确 Cache-Control。
4. 清理已经缓存的错误与旧内容。优先单 URL；需要一次 Purge Everything 时，先确认这是 zone 级，会影响 shop。不要每天 Purge Everything。
5. 连续请求同一个真实 URL、同一个 v 参数，比较 status / Cache-Control / Age / ETag / cf-cache-status；不要加随机 ?cb= 或 ?fresh= 测命中。
6. 保留 CSS / JS 的 ?v= 版本参数为缓存键的一部分；不启用 Ignore Query String。同名 hero / 车辆图片会被替换，不能随意给浏览器一年 immutable；使用较短浏览器 TTL或升级文件名版本。
7. 不建立“任何 Cookie存在就 Bypass”的规则。GA4、Cloudflare 挑战 cookie 不代表页面个性化；仅明确登录、会话、授权请求才单独避开缓存。
8. C1已将状态>=400设为No store；源头错误页的浏览器头部仍应核对，不能用扩展名 .webp / .css 就认定响应成功。状态TTL的-1是规则中的No store，不应改成0，也不能把edge设置误写成一定重写了浏览器响应头。

已完成一次19个apex精确URL的Purge API清理，未全zone清理。清理后四语HTML均200，现网源头max-age=600、s-maxage=3600，cf-cache-status=DYNAMIC；这与保留HTML的Pages原生服务相符，不证明每次都直连自管源站。静态CSS与实车图的重复请求结果应另按实际cf-cache-status / Age记录。

本地已准备的 _headers 目标如下，尚未部署；不是目前所有现网资源的响应头。各资源URL可复用，因此没有immutable：

| 内容 | 浏览器 | 边缘 |
|---|---|---|
| 公开 HTML | max-age=300：5分钟；当前现网源头仍600：10分钟 | s-maxage=3600：1小时；尊重源头 / Pages原生 |
| CSS / JS（保留v参数） | max-age=3600：1小时 | s-maxage=86400：1天；尊重源头 / Pages原生 |
| 同 URL 可替换的车辆图、hero | max-age=3600：1小时；不标immutable | s-maxage=86400：1天；换图清准确 URL |
| robots / sitemap / feed | max-age=300：5分钟 | s-maxage=3600：1小时；每日上新可见 |
| 404、其他 4xx、5xx | no-store | 不长期负缓存，尤其不能被30天WebP规则覆盖 |
| 运营 / 登录 / API | no-store | 不做公开缓存 |

C1已经启用：JINBA public static assets 1d edge 2h browser，ID a47447fc55944498af417686fbf9ee23。匹配主站静态目录及指定扩展名；Eligible for cache，Edge TTL覆盖源头为86400秒（1天），Browser TTL覆盖为7200秒（2小时），状态>=400为No store。保存后再次进入编辑页，以上三项均已核实。Free控制台此次TTL预设最低2小时，因此实际C1浏览器是2小时；不能将本地待部署源头的1小时写成已经在C1生效。保留默认cache key和全部查询参数，没有自定义cacheKey；HTML不匹配C1。

C1 表达式：

~~~text
(http.host in {"jinbacars.com" "www.jinbacars.com"} and
 (starts_with(http.request.uri.path, "/assets/") or
  starts_with(http.request.uri.path, "/js/") or
  starts_with(http.request.uri.path, "/images/") or
  starts_with(http.request.uri.path, "/uploads/cars/")) and
 http.request.uri.path.extension in {"css" "js" "mjs" "webp" "jpg" "jpeg" "png" "svg" "ico" "gif" "avif" "woff" "woff2" "ttf" "otf"})
~~~

对应action_parameters示例如下，记录实际配置含义，不是替换整个ruleset的payload，也不表示曾用Token调用成功：

~~~json
{
  "cache": true,
  "edge_ttl": {
    "mode": "override_origin",
    "default": 86400,
    "status_code_ttl": [
      {"status_code_range": {"from": 400}, "value": -1}
    ]
  },
  "browser_ttl": {"mode": "override_origin", "default": 7200}
}
~~~

状态>=400覆盖4xx / 5xx，防止再次把缺失图片或服务错误缓存1天。C1只作用于指定静态目录与扩展名，JSON与HTML保持原生策略。Cache Rules后匹配的同类设置会覆盖前项，因此C2置最后；需用Trace和真实响应验证匹配。

C2已经启用：JINBA private paths and authorization bypass，ID 33e7fc3719414779814413aa2d7cd10f，Cache Rules最后一条，动作Bypass cache（cache:false）。覆盖精确敏感入口、其主要子路径和任何携带Authorization的请求；不是所有cookie都绕缓存，也不代表这些接口现在都存在：

~~~text
(http.host in {"jinbacars.com" "www.jinbacars.com"} and
 (http.request.uri.path in {"/admin" "/data" "/api" "/auth" "/login" "/logout"} or
  starts_with(http.request.uri.path, "/admin/") or
  starts_with(http.request.uri.path, "/data/") or
  starts_with(http.request.uri.path, "/api/") or
  starts_with(http.request.uri.path, "/auth/") or
  len(http.request.headers["authorization"]) gt 0))
~~~

单 URL purge 和状态规则仍需复核查询参数、host 和实际错误状态。不要靠一次命中结果推断所有地区均已缓存。

[Cache Rules 设置](https://developers.cloudflare.com/cache/how-to/cache-rules/settings/) · [规则顺序](https://developers.cloudflare.com/cache/how-to/cache-rules/order/) · [Pages 头部合并行为](https://developers.cloudflare.com/pages/configuration/headers/)

## ⑤ Free WAF 与限速：可粘贴表达式

不使用收费 Bot Management score，也不使用 Free 不支持的正则 matches。对客户正常看车路径不按国家挑战。不开全站 Under Attack，也不假设某个 UA / 语言 / 国家是可信客户。

W1：Block common exploit scanning paths；ID b5c60f930e164c2eb3a971427bc800af；已启用，Block，自定义规则第1条。实际保存表达式保留原8项全zone匹配，再OR新增主站限定分支：

~~~text
(http.request.uri.path contains "/wp-json/" or
 http.request.uri.path contains "/wp-admin/" or
 http.request.uri.path contains "/.git/" or
 http.request.uri.path contains "/xmlrpc.php" or
 http.request.uri.path contains "/phpinfo" or
 http.request.uri.path contains "/vendor/" or
 http.request.uri.path contains "/.aws/" or
 http.request.uri.path contains "/.ssh/") or
(http.host in {"jinbacars.com" "www.jinbacars.com"} and
 (starts_with(lower(http.request.uri.path), "/.env") or
  starts_with(lower(http.request.uri.path), "/.git") or
  starts_with(lower(http.request.uri.path), "/wp-") or
  starts_with(lower(http.request.uri.path), "/phpmyadmin") or
  ends_with(lower(http.request.uri.path), ".php") or
  lower(http.request.uri.path) contains "/.aws/" or
  lower(http.request.uri.path) contains "/.ssh/"))
~~~

新增主站分支针对纯静态站不存在的敏感 / PHP 路径，没有国家条件；原8项全zone分支继续保留既有防护，也可能匹配shop。不能说整条W1排除了shop。未来若有主机使用WordPress / PHP、vendor等正常资源，须先核对相应分支。

W2：Challenge confirmed scanner 31.57.216.50；ID f433847f080b49e9ab8752b0dc70b791；已启用，Managed Challenge，自定义规则第5条。

~~~text
(http.host in {"jinbacars.com" "www.jinbacars.com"} and
 ip.src eq 31.57.216.50 and
 not cf.client.bot)
~~~

W2只针对现场已确认 IP，保留验证 bot 排除，复核窗口 24 小时。挑战通过是需要检查的信号，不是永久认定客户 / 永久认定恶意的证据。

RL1：HTML burst protection 60 per 10s；ID b83d25ed6dd54c6981604d1e0b03313a；已启用，控制台确认每客户端 IP 60 次 / 10 秒、Block 10 秒。Free可用字段受限，实际表达式只用 URI path 与 cf.client.bot，不含 http.host / method，并包含根路径：

~~~text
(not cf.client.bot and
 (http.request.uri.path in {"/" "/en" "/zh" "/ru" "/ar"} or
  starts_with(http.request.uri.path, "/en/") or
  starts_with(http.request.uri.path, "/zh/") or
  starts_with(http.request.uri.path, "/ru/") or
  starts_with(http.request.uri.path, "/ar/")))
~~~

这个限速计根路径与四语路由，避开 /assets/、/images/、/uploads/cars/ 图片瀑布和 verified bot。它是 zone 级，shop.jinbacars.com 的 / 与相同 /en/ 等路由也会匹配；若出现子站误限或真实多用户共享出口受影响，先禁用RL1再评估，不能为了限定host添加Free不支持的字段。它不是响应404计数器，也不能写“只对出现20次404的IP封禁”。

美国、中东、欧洲共享 NAT、代理、移动网络都可能聚合多名买家。发生真实客户误拦时先禁用该限速 / 收窄条件，不能将整个国家设为 Skip 全部安全检查。验证真实 crawler用 cf.client.bot，不能使用 UA 包含 Google 的宽泛跳过规则。

[WAF 自定义规则](https://developers.cloudflare.com/waf/custom-rules/) · [限速套餐能力](https://developers.cloudflare.com/waf/rate-limiting-rules/) · [cf.client.bot 字段](https://developers.cloudflare.com/ruleset-engine/rules-language/fields/reference/cf.client.bot/)

## ⑥ 验收、监控与回滚

规则发布当天先做少量正常路径检查：四语首页、库存列表、一辆已发布470或更早的详情、一张实际存在的实车图、CSS、contact 和 robots。验证 WhatsApp 链接可点击、列表筛选与车型图片可用。不要用未来车辆474做验收对象。W1的 .env 检查只需少量一条；不通过高频请求强行触发限速。

| 指标与口径 | 建议监控 | 初始目标 / 处理阈值 |
|---|---|---|
| 主站已发布路径 5xx / 504 | 15 分钟、1 小时、每日；统一host与状态码窗口 | 0；重复真实504或多地区异常立即取Ray证据 |
| 当前已发布 HTML / 图片 / JS 的 404 | 每日，按path对照部署清单 | 0；有实际页面引用即排查部署与缓存 |
| 敏感路径到达服务的次数 | WAF W1 action、对应4xx趋势 | 尽量在WAF Block；不要只用全站404比例 |
| SI / 31.57.216.50行为 | 24小时复核路径、请求、challenge通过率 | 扫描下降；IP复用或正常业务迹象出现时撤销W2 |
| 合格静态资源缓存命中 | apex/www、200、GET/HEAD、已发布静态资源；分HIT/MISS/BYPASS | 有重复请求的资源预热后争取 >80%；低流量长尾不保证达到 |
| 全站缓存比例 | 作为辅助，分开看WAF/redirect/error/长尾 | 不以全球HIT 10%一项验收；Pages原生缓存可能不等于zone HIT标签 |
| BYPASS原因 | 相同真实URL响应头、cookie/Authorization、匹配规则 | 公开静态资产不应因冲突Cache-Control或所有cookie被跳过 |
| 业务误杀 | 正常美国/中东/欧洲会话、contact、WhatsApp点击与反馈 | 已确认真实客户误拦0；出现即先撤规则 |
| 买家转化 | GA4 whatsapp_click按国家/语言/车型 + 实际有效询价 | 与同流量口径基线比较；点击不等于消息送达或成交 |
| 内容新鲜度 | 上新后生产HTML库存号、图片、etag对照最新部署 | 成功部署和必要purge后立即正确；不能长期读旧列表 |

命中率公式必须写清分母。推荐单独报告“有资格缓存且成功的已发布静态资源”中的 HIT 请求 / (HIT + MISS + EXPIRED + REVALIDATED 等相关缓存请求)，同时列出 BYPASS 与 DYNAMIC，不能删去异常行后只给漂亮百分比。总请求数还包括扫描、重定向、挑战、错误和冷门路径，不等同于独立买家数。

命中率目标是运营目标而非保证；大量长尾页面 / 图片只有一次访问时，即使配置正确也可能MISS。先看重复请求的少数热门真实资产是否复用，再看全站。查缓存时不用随机查询参数，也不以代理出口colo代表所有客户地区。

回滚步骤：

1. 保存规则 ID、顺序、表达式、动作、发布时间和截图。一次只改一个规则 / 策略，正常客户问题先禁用最近相关W2或RL1。
2. 发生缓存内容异常，先撤新增 Cache Rule、恢复 Pages 原生；清具体错误URL。如果必须全清，说明zone内shop也会冷缓存，不把全清做日常措施。
3. 不默认恢复“全站HTML一天 / WebP错误30天”旧规则。只有紧急需要恢复旧配置时才用保存的快照，并记录它的已知风险。
4. 源文件回滚仅限本次缓存 / redirects / purge修改，不覆盖库存、图片与他人工作。不要运行构建器顺带发布待审核车辆。
5. 回滚后验证四语页面、已发布图、CSS、WhatsApp入口、错误路径状态和新鲜度，再观察15分钟；保持504原证据，不把暂时正常写成永久治愈。

正式上线必须区分：Cloudflare后台安全 / zone缓存规则变更、仓库源文件修正、Pages实际部署三个状态。前两项完成不代表第三项完成。当前本地新车471–474未发布，缓存源文件修正应安排在下一次完整、校验通过的站点发布中。


## H1：真正缩短当前静态资源的浏览器 TTL

Cache Rule 的 Browser TTL 较低时不会缩短源头更大的 max-age，所以 C1 单独不能把原 30 天改成 2 小时。H1 在缓存判断之后覆盖成功公开响应的 Cache-Control；它不会改变 C1 的 edge 86400。实测已从 2592000 改为 7200，并删除旧 immutable/重复项。

产品：Response Header Transform Rule；ID：`d8afc7306fcf47a68d11988e08d9ea89`；动作：Set static（不能用 Add）。

```text
((http.host in {"jinbacars.com" "www.jinbacars.com"} and (starts_with(http.request.uri.path, "/assets/") or starts_with(http.request.uri.path, "/js/") or starts_with(http.request.uri.path, "/images/") or starts_with(http.request.uri.path, "/uploads/cars/")) and http.request.uri.path.extension in {"css" "js" "mjs" "webp" "jpg" "jpeg" "png" "svg" "ico" "gif" "avif" "woff" "woff2" "ttf" "otf"}) and http.response.code ge 200 and http.response.code lt 300 and not has_key(http.request.headers, "authorization") and not has_key(http.response.headers, "set-cookie") and any(lower(http.response.headers["cache-control"][*])[*] contains "public") and (not has_key(http.response.headers, "cache-control") or (not any(lower(http.response.headers["cache-control"][*])[*] contains "private") and not any(lower(http.response.headers["cache-control"][*])[*] contains "no-store"))) and (not has_key(http.response.headers, "cdn-cache-control") or (not any(lower(http.response.headers["cdn-cache-control"][*])[*] contains "private") and not any(lower(http.response.headers["cdn-cache-control"][*])[*] contains "no-store"))) and (not has_key(http.response.headers, "cloudflare-cdn-cache-control") or (not any(lower(http.response.headers["cloudflare-cdn-cache-control"][*])[*] contains "private") and not any(lower(http.response.headers["cloudflare-cdn-cache-control"][*])[*] contains "no-store"))))
```

设置：

```text
Cache-Control: public, max-age=7200, s-maxage=86400
```

H1 仅匹配 2xx、指定主站静态目录与扩展名，且响应已有 public 缓存头；排除 Authorization、Set-Cookie、private/no-store（含 CDN 专用缓存头）。这避免把私有响应强制公开。不存在的头应使用 has_key 检查；对数组 lower 后仍须 [*] 展开。CF 清缓存无法清除已经驻留客户浏览器的旧 30 天缓存；新响应修正不等于旧客户端立即刷新。[Browser TTL 规则](https://developers.cloudflare.com/cache/how-to/edge-browser-cache-ttl/set-browser-ttl/)、[响应头转换](https://developers.cloudflare.com/rules/transform/response-header-modification/)

下一次合规部署发布 _headers 后，如希望采用源头静态 browser 1 小时，应将 C1 Browser 改为 Respect origin 并停用 H1；若保留当前规则，生产浏览器 TTL 仍为 2 小时。不要仅改源文件后声称现网 TTL 已改变。

## R1：恢复四个真实历史入口

产品：Single Redirect；ID：`a40ec1a072004862a6f9452244ec86a7`；Active。

```text
(http.host in {"jinbacars.com" "www.jinbacars.com"} and http.request.uri.path in {"/cars" "/cars/" "/cars.html" "/cars-detail.html"})
```

静态目标 `https://jinbacars.com/en/cars/`；301；保留查询字符串。四条路径均已实测 301，最终库存列表 200，不存在循环。旧 id 参数保留供追踪，但没有虚构它与当前车辆 ID 的映射；其他旧详情路径应按真实迁移关系处理。这不是把全站 404 统一跳首页。[Single Redirect 设置](https://developers.cloudflare.com/rules/url-forwarding/single-redirects/settings/)

## 证据文件与复核范围

- `.workbuddy/cf_ops/config_before.json`：初始 API 可读配置和权限边界。
- `.workbuddy/cf_ops/live_rules.json`：7 条实际启用规则，来自 UI 保存与复核；不是完整 ruleset 导出。
- `.workbuddy/cf_ops/live_verify_after.json`：19 URL purge 与正常访问/扫描/缓存例外验证。
- `.workbuddy/cf_ops/final_check.json`：北京时间 15:39 的 H1、R1 最终实际 HTTP 验证。
- `.workbuddy/cf_ops/screenshots/`：WAF、旧规则停用、Cache Rules、历史跳转的控制台截图。
- `photo_check.py`：203 台 published，违规 0；`validate_inventory.py`：419 台，ERROR/WARNING 均 0。源文件语法与 CRLF diff 检查通过。它们不是待上线新车的封面目检替代，本次没有部署车辆。

回滚时先区分是哪条规则影响实际客户：H1 只改浏览器响应头，C1 改边缘 TTL，C2 避免私有缓存，R1 只改四个历史入口，W2 只针对确认扫描 IP，RL1 控制页面突发速率。不能为了回滚某一条而整体关闭 WAF 或恢复全站一天缓存。


## 第二轮深化：发布可靠性与可重复监测

本轮已修改本地发布工具，尚未执行生产部署；此前 7 条在线 Cloudflare 规则保持原状。

- 每次发布新建唯一 `snapshot_*` 目录，旧目录保留但不混入上传；拒绝运营目录、链接文件以及上传快照与 hash 清单不一致。`push_api.py` 的 `DEPLOY_DROP` 未修改。
- 无缓存基线或 `_headers` / `_redirects` 改变时，按当前/历史已知公开文件刷新主站和 www URL，不再使用全 zone `purge_everything`，避免连带刷新其他子域。
- 正常增量发布刷新修改、新增、删除文件及已记录的查询版本；覆盖 index.html、目录和无扩展名 HTML 路由。任意未记录的外部查询参数版本不能靠这个清单穷尽，应保留合理 TTL。
- 清缓存失败返回非零退出码并保留上一次成功基线；上传成功与刷新完成分别报告。明确指定 `--no-purge` 则跳过刷新，不更新基线。
- `--skip-stage` 必须指定 `_pages_deploy` 下的实际快照目录，防止无意重传历史混合目录。增加 `--dry-run`，仅生成本地快照和刷新数量，无上传、清缓存和基线更新。
- 增加 `scripts/cf_health_check.py`：每秒最多发起一个只读请求，检查四语联系页、库存列表、主站/www 静态缓存、历史入口保留参数以及错误图片不缓存；异常记录状态、时间和 Ray ID。不会自动修改 WAF，也没有创建定时任务。

首次健康检查 10 请求，无告警：四语联系页及库存页 200；主站 CSS 两次 HIT；www 首次 MISS；旧 cars.html 301；不存在图片 404/BYPASS。耗时来自单个代理位置，包含网络开销，不等于源站处理耗时；HTML DYNAMIC 不作为故障。后续版增加 www 重复探测。

执行命令（项目根目录，Python 3.12）：

```powershell
& 'C:/Users/Administrator/AppData/Local/Programs/Python/Python312/python.exe' scripts/test_deploy_pages.py
& 'C:/Users/Administrator/AppData/Local/Programs/Python/Python312/python.exe' scripts/deploy_pages.py --dry-run
& 'C:/Users/Administrator/AppData/Local/Programs/Python/Python312/python.exe' scripts/cf_health_check.py --proxy http://127.0.0.1:7890
```

健康报告默认 `.workbuddy/cf_ops/health_latest.json`，告警退出码为 1；每次覆盖最近报告，需保留历史时用 `--output` 指定不同路径。发布预演产生快照占用磁盘，历史目录本轮未删除。真正发布前仍须完成项目要求的图片检查、库存检查及待发布车辆封面目检；当前本地 471–474 尚未在现网发布，不在本轮优化中顺带上线。

Cloudflare 官方建议优先按 URL 清理，以减少全清后的 MISS 和回源峰值：[Purge everything](https://developers.cloudflare.com/cache/how-to/purge-cache/purge-everything/)。本工具 URL 批次为 30，批次间隔至少 250ms；失败不写成功基线。

本轮最终验证：11 个现网请求，无告警；www CSS 连续两次为 MISS → HIT。完整发布预演通过：7,249 文件、271.0 MB、首次已知 URL 刷新计划 18,576 条；没有执行刷新或部署。首次数量较大是缺少成功发布 hash 基线导致，后续无文件变化时固定主站/www 首页、列表和元文件 24 URL。5 项离线可靠性测试通过，包含删除文件隔离、快照变动检测、双域名查询版本刷新、API 失败保留基线和上传成功/刷新失败时非零返回。
