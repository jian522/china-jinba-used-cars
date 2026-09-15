# WhatsApp Business 自动回复文案（优化版）

> 用途：直接粘贴到手机 WhatsApp Business → 商业工具 → 离开消息 / 问候消息
> 事实来源：`docs/K-客户问答库-出口客服.md`
> 更新：2026-09-15

---

## 一、离开消息 Away message（你离线时自动发送）

### 方案 A｜英文单条（推荐·通用）

```
Thanks for messaging Jinba Used Cars 🇨🇳
We're offline — we'll reply as soon as we're back.
We speak English · Русский · العربية
Stock & prices: jinbacars.com
For a quote, send: model + destination port
WhatsApp/WeChat: +86 180 7908 9999
```

**为什么这样写**
- 第 1 行先出现品牌名（手机预览只显示前 1～2 行，品牌必须最前）
- 第 2 行给出明确预期，避免客户以为没人管
- 第 3 行声明语言能力（俄语/阿语客户占比高，这句能显著降低流失）
- 第 4 行给自助入口（官网看库存价）
- 第 5 行**只要一个动作**：报车型 + 目的港 → 客户回消息的门槛降到最低
- 第 6 行留即时联系方式作兜底

### 方案 B｜英俄双语（覆盖俄罗斯 / 中亚客群）

```
Thanks for your message! / Спасибо за сообщение!
We're offline — we'll reply soon. / Мы офлайн — ответим скоро.
Stock & prices / Склад и цены: jinbacars.com
Send model + port for a quote / Модель и порт — для расчёта
WhatsApp/WeChat: +86 180 7908 9999
```

> 二选一。WhatsApp Business 的离开消息**只能存一条**，无法按语言分流。
> 主力客群若是俄语区（俄罗斯/哈萨克/吉尔吉斯），用方案 B；全球通吃用方案 A。

---

## 二、问候消息 Greeting message（客户首次联系时自动发送）

```
Welcome to Jinba Used Cars 🇨🇳
MOFCOM-licensed China used-car exporter since 2016.
BYD · Li Auto · Haval · Chery · Geely · AITO · Changan
Export to Africa, Middle East, Central Asia & Russia — FOB Shanghai/Shenzhen.
Which model do you need, and which port should we quote to?
Full stock: jinbacars.com | WhatsApp/WeChat: +86 180 7908 9999
```

> 离开消息只在**你离线时**触发；客户在你在线时第一次来，只会收到问候消息。
> 两条都要开，否则在线时段进来的新客户会「无人应答」。

---

## 三、设置路径（手机 App）

1. 打开 **WhatsApp Business** → 右上角 **⋮**（iOS 为「设置」）
2. 进入 **商业工具 / Business Tools**
3. 点 **离开消息 Away message** → 打开开关 → 铅笔图标编辑 → 粘贴方案 A 或 B → 保存
4. 排期选：
   - **始终发送**（常在外跑、无法随时回消息 → 选这个）
   - **营业时间外**（有固定客服时段 → 选这个）
5. 同样路径进 **问候消息 Greeting message** → 打开开关 → 粘贴第二节文案 → 保存
6. 收件人建议选 **所有人**（All contacts）

---

## 四、自动回复红线（写在文案里的边界，别越过）

| 禁止 | 原因 |
|---|---|
| 承诺具体到港日期 | 船期不可控；只说 18–35 天区间 |
| 报具体关税金额 | 各国税则不同，报错要担责 |
| 说「无任何问题 / 完美车况」 | 二手车必有使用痕迹，只说「无重大事故」 |
| 议价超过 5% | 超出授权 → 转人工 |
| 变更付款方式（货到付款等） | 超出授权 → 转人工 |
| 提供非公司账户收款 | 诈骗风险 |

**转人工触发词**：`refund` `scam` `cheated` `lawyer` `lawsuit` `complaint` `dispute` `退款` `投诉` `骗子` `法院` `возврат` `обман` `суд` `мошенник`

---

## 五、快速回复 Quick Replies（已建好 / 待修 1 条）

聊天框输入 `/` 即可从列表选择，秒发。**当前账号状态（2026-09-15 AI 代建后）：**

| 快捷方式 | 状态 | 内容要点 |
|---|---|---|
| `/price` | ✅ 原本就有 | 报价条款（含 FOB/CIF 占位符） |
| `/inspect` | ✅ 原本就有 | 检测报告包含项 |
| `/ship` | ✅ 原本就有 | 物流方式与时效 |
| `/how` | ✅ 原本就有 | 购买流程 4 步 |
| **`/pay`** | 🆕 **AI 新建** | 付款：T/T 或 L/C，30% 定金 + 70% 见提单副本，只走对公账户 |
| **`/doc`** | 🆕 **AI 新建** | 六种单证清单 |
| **`/cond`** | 🆕 **AI 新建** | 168 点检测、事故/泡水/火烧车不出口、EV 电池 SOH |
| `/stock` | ⚠️ **待修** | 里面还有中文占位符，见下方 |
| `谢谢` | ✅ 原本就有 | 中文致谢 |

### ⚠️ `/stock` 需要你手动修（约 30 秒）

这条里还留着没填的占位符：`[每次手动更新这里，或链接到网站]` 和 `[你的网站/阿里国际站链接]`。
**万一有客户收到，会看到方括号里的中文**，建议立刻替换。

手机路径：**WhatsApp Business → ⋮ → 商业工具 → 快速回复 → 点 `/stock` → 编辑 → 粘贴↓ → 保存**

```
Our current available stock 🚗
Browse all vehicles with real photos & prices: https://jinbacars.com
Looking for something specific? Tell me:
• Brand preference
• Budget range (USD)
• Destination port
I'll find the best match for you 💪
```

> 备注：手机上快捷方式可以带 `/`，网页版表单不允许（会自动补），所以 AI 新建的 3 条存的是 `pay/doc/cond`，在聊天框输入 `/` 一样能选到。

