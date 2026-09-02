# Bing Webmaster Tools 自动化脚本
# 使用 Playwright 自动添加站点和提交 Sitemap

from playwright.sync_api import sync_playwright
import time

def automate_bing():
    print("=== Bing Webmaster Tools 自动化 ===")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # 步骤1: 打开 Bing Webmaster
            print("\n[步骤1] 打开 Bing Webmaster Tools...")
            page.goto('https://www.bing.com/webmasters')
            time.sleep(3)
            
            # 检查是否已登录
            if 'login.microsoftonline.com' in page.url:
                print("请先在打开的浏览器中登录Microsoft账户")
                input("登录完成后按Enter继续...")
            
            # 步骤2: 添加站点
            print("\n[步骤2] 添加站点...")
            page.click('text=Add Sites')
            time.sleep(2)
            
            # 输入网站URL
            page.fill('input[placeholder*="https://"]', 'https://jinbacars.com/')
            time.sleep(1)
            
            # 点击继续
            page.click('button:has-text("Continue")')
            time.sleep(3)
            
            # 步骤3: 验证所有权 (使用HTML标签方法)
            print("\n[步骤3] 验证网站所有权...")
            
            # 选择HTML标签验证方法
            page.click('text=HTML tag')
            time.sleep(2)
            
            # 获取验证meta标签
            meta_tag = page.text_content('meta[name="msvalidate.01"]')
            
            if meta_tag:
                print(f"已找到验证标签: {meta_tag}")
                print("\n请将以下代码添加到您的网站 head 部分:")
                print(meta_tag)
                print("\n然后返回此窗口按Enter继续验证...")
                input()
            
            # 点击验证按钮
            page.click('button:has-text("Verify")')
            time.sleep(3)
            
            # 检查验证结果
            if page.locator('text=verified').count() > 0 or page.locator('text=Verified').count() > 0:
                print("✅ 网站验证成功！")
            else:
                print("⚠️ 验证可能失败，请检查是否正确添加了meta标签")
            
            # 步骤4: 提交 Sitemap
            print("\n[步骤4] 提交 Sitemap...")
            page.click('text=Sitemaps')
            time.sleep(2)
            
            page.fill('input[placeholder*="sitemap"]', 'sitemap.xml')
            time.sleep(1)
            
            page.click('button:has-text("Submit")')
            time.sleep(3)
            
            if page.locator('text=successfully').count() > 0:
                print("✅ Sitemap 提交成功！")
            else:
                print("⚠️ 请检查提交状态")
            
            print("\n=== Bing Webmaster 自动化完成 ===")
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
        
        finally:
            input("\n按Enter关闭浏览器...")
            browser.close()

if __name__ == '__main__':
    automate_bing()
