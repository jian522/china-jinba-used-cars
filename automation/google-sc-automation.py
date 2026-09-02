# Google Search Console 自动化脚本
# 使用 Playwright 自动提交 Sitemap

from playwright.sync_api import sync_playwright
import time

def automate_google_sc():
    print("=== Google Search Console 自动化 ===")
    
    with sync_playwright() as p:
        # 启动浏览器（使用您的现有登录会话）
        browser = p.chromium.launch(headless=False)
        
        # 使用已有的cookies文件（需要先导出）
        # context = browser.new_context(storage_state='google_cookies.json')
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # 步骤1: 打开 Search Console
            print("\n[步骤1] 打开 Google Search Console...")
            page.goto('https://search.google.com/search-console')
            time.sleep(3)
            
            # 检查是否已登录
            if 'accounts.google.com' in page.url:
                print("请先在打开的浏览器中登录Google账户")
                input("登录完成后按Enter继续...")
            
            # 步骤2: 选择网站属性
            print("\n[步骤2] 选择网站属性...")
            # 等待页面加载
            page.wait_for_selector('text=jinbacars.com', timeout=10000)
            
            # 点击网站属性
            page.click('text=jinbacars.com')
            time.sleep(2)
            
            # 步骤3: 提交 Sitemap
            print("\n[步骤3] 提交 Sitemap...")
            page.click('text=Sitemaps')
            time.sleep(2)
            
            # 在输入框中输入 sitemap
            page.fill('input[placeholder*="sitemap"]', 'sitemap.xml')
            time.sleep(1)
            
            # 点击提交按钮
            page.click('button:has-text("Submit")')
            time.sleep(3)
            
            # 检查提交结果
            if page.locator('text=Success').count() > 0:
                print("✅ Sitemap 提交成功！")
            else:
                print("⚠️ 请检查页面上的提交状态")
            
            # 步骤4: 请求索引新页面
            print("\n[步骤4] 请求索引新页面...")
            new_pages = [
                'https://jinbacars.com/en/guides/import-used-cars-to-uae/',
                'https://jinbacars.com/en/guides/import-used-cars-to-russia/',
                'https://jinbacars.com/en/guides/import-used-cars-to-africa/',
                'https://jinbacars.com/en/faq/',
                'https://jinbacars.com/en/blog/',
                'https://jinbacars.com/en/reviews/',
                'https://jinbacars.com/en/tools/shipping-calculator/',
            ]
            
            for url in new_pages:
                print(f"  正在索引: {url}")
                page.goto('https://search.google.com/search-console/url-inspection')
                time.sleep(1)
                page.fill('input[type="url"]', url)
                time.sleep(2)
                page.click('button:has-text("Test Live URL")')
                time.sleep(3)
                page.click('button:has-text("Request Indexing")')
                time.sleep(2)
            
            print("\n✅ 所有页面索引请求已发送！")
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            print("\n请确保:")
            print("1. 已登录Google账户")
            print("2. 已添加 jinbacars.com 作为属性")
            print("3. 已完成网站验证")
        
        finally:
            input("\n按Enter关闭浏览器...")
            browser.close()

if __name__ == '__main__':
    automate_google_sc()
