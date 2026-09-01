# Google Search Console - 完整操作指南

## 当前状态
- 您已登录 Google Search Console ✓
- 需要添加网站属性: jinbacars.com

---

## 步骤 1: 添加网站属性

### 方法 A: URL 前缀方法（推荐，最简单）

1. 在 Google Search Console 首页点击 **"开始现在"** 或 **"添加属性"**
2. 选择 **"URL 前缀"** 选项卡
3. 输入: `https://jinbacars.com/`
4. 点击 **"继续"**

### 方法 B: 域名方法（更完整，但需要 DNS 验证）

1. 选择 **"域名"** 选项卡
2. 输入: `jinbacars.com`
3. 点击 **"继续"**
4. 需要添加 TXT 记录到 DNS（较复杂，不推荐初次使用）

---

## 步骤 2: 验证网站所有权

### 推荐方法: HTML 标签验证（最快）

1. 在下载 HTML 标签文件中，复制 `<meta>` 标签内容
2. 打开您的网站代码编辑器
3. 在 `D:\deepseek harness\china-jinba-used-cars\en\index.html` 的 `<head>` 部分添加标签
4. 保存并推送更改到 GitHub
5. 回到 Google Search Console 点击 **"验证"**

### 备选方法: HTML 文件上传

1. 下载 Google 提供的 HTML 验证文件
2. 上传到网站根目录
3. 点击 **"验证"**

---

## 步骤 3: 提交 Sitemap

验证成功后：

1. 左侧菜单点击 **"Sitemaps"**
2. 输入: `sitemap.xml`
3. 点击 **"提交"**

---

## 步骤 4: 请求索引新页面

对于每个新页面：

1. 左侧菜单点击 **"网址检查"**
2. 输入完整 URL，例如: `https://jinbacars.com/en/guides/import-used-cars-to-uae/`
3. 点击 **"请求编入索引"**
4. 选择 **"发送索引编造请求和爬取链接"**

---

## 需要添加的验证标签

在 `en/index.html` 的 `<head>` 中添加：

```html
<meta name="google-site-verification" content="您从Google获取的验证码" />
```

---

## 新页面列表（需要索引）

1. https://jinbacars.com/en/guides/import-used-cars-to-uae/
2. https://jinbacars.com/en/guides/import-used-cars-to-russia/
3. https://jinbacars.com/en/guides/import-used-cars-to-africa/
4. https://jinbacars.com/en/guides/import-used-cars-to-southeast-asia/
5. https://jinbacars.com/en/faq/
6. https://jinbacars.com/en/blog/
7. https://jinbacars.com/en/blog/byd-ev-export-trends-2026/
