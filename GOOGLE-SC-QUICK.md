# Google Search Console - 快速操作指南

## 您已登录，请完成以下步骤：

### Step 1: 确认网站属性
1. 在左侧菜单查看是否已有 `https://jinbacars.com/`
2. 如果没有，点击 **"添加属性"** → 选择 **"URL 前缀"** → 输入 `https://jinbacars.com/` → 点击 **"继续"**

### Step 2: 验证所有权（如果还未验证）
您的网站已包含验证标签，应该已经验证成功。

### Step 3: 提交 Sitemap
1. 左侧菜单点击 **"Sitemaps"**
2. 在输入框中输入：`sitemap.xml`
3. 点击 **"提交"**
4. 等待显示 "Success!"

### Step 4: 请求索引新页面
对每个新页面执行：

1. 左侧菜单点击 **"网址检查"**
2. 输入完整 URL，例如：
   ```
   https://jinbacars.com/en/guides/import-used-cars-to-uae/
   ```
3. 点击 **"测试 live URL"**
4. 点击 **"请求编入索引"**
5. 选择 **"发送索引编造请求和爬取链接"**

需要索引的页面：
- https://jinbacars.com/en/guides/import-used-cars-to-uae/
- https://jinbacars.com/en/guides/import-used-cars-to-russia/
- https://jinbacars.com/en/guides/import-used-cars-to-africa/
- https://jinbacars.com/en/guides/import-used-cars-to-southeast-asia/
- https://jinbacars.com/en/faq/
- https://jinbacars.com/en/blog/
- https://jinbacars.com/en/blog/byd-ev-export-trends-2026/

---

## 或者使用 PING 方法（更快）

在浏览器地址栏输入以下链接并回车：

```
https://www.google.com/ping?sitemap=https://jinbacars.com/sitemap.xml
```

应该会显示 "Ping received. The sitemap was added to the queue."

---

## 完成后检查

1. 返回 Search Console 首页
2. 点击 **"报告"** → **"页面索引"**
3. 确认新页面已被收录
