# Bing Webmaster Tools - 验证指南

## 方法 1: HTML 文件验证（推荐）

1. 在 Bing Webmaster Tools 中选择 "HTML 文件" 验证方法
2. 下载生成的验证文件（通常是 xxxxx.txt）
3. 将文件上传到网站根目录：`https://jinbacars.com/xxxxx.txt`
4. 点击 "验证"

## 方法 2: HTML 标签验证

1. 在 Bing Webmaster Tools 中选择 "HTML 标签" 验证方法
2. 复制生成的 `<meta>` 标签
3. 添加到以下文件的 `<head>` 部分：
   - `D:\deepseek harness\china-jinba-used-cars\en\index.html`
4. 保存并提交更改到 GitHub
5. 点击 "验证"

## 方法 3: DNS TXT 记录验证

1. 在 Bing Webmaster Tools 中选择 "DNS TXT 记录" 验证方法
2. 复制生成的 TXT 记录值
3. 到您的域名注册商（如 GoDaddy、Namecheap）添加 TXT 记录
4. 等待 DNS 传播（通常几分钟到几小时）
5. 点击 "验证"

---

## 验证成功后

1. 左侧菜单点击 **"Sitemaps"**
2. 输入：`sitemap.xml`
3. 点击 **"提交"**

---

## 验证代码（如果需要）

根据您的需求，可以添加以下 meta 标签到 en/index.html：

```html
<meta name="msvalidate.01" content="您的Bing验证代码" />
```
