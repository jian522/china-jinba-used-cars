@echo off
REM Jinba Auto Export - Traffic Growth Deployment Script for Windows
REM Run this script to deploy the new SEO content

echo ========================================
echo Jinba Auto Export - Traffic Growth
echo ========================================
echo.

REM Check if in correct directory
if not exist "sitemap.xml" (
    echo [ERROR] Please run this script from the china-jinba-used-cars directory
    pause
    exit /b 1
)

echo [Step 1] Checking git status...
git status --short
echo.

echo [Step 2] Adding all new files...
git add -A
echo.

echo [Step 3] Review changes above, then press Enter to commit...
pause

echo.
echo [Step 4] Committing changes...
git commit -m "Add SEO content: market guides, FAQ, and blog pages for traffic growth

New content:
- /en/guides/import-used-cars-to-uae/
- /en/guides/import-used-cars-to-russia/
- /en/guides/import-used-cars-to-africa/
- /en/guides/import-used-cars-to-southeast-asia/
- /en/faq/
- /en/blog/

SEO improvements:
- Schema markup (Article, FAQ, BlogPosting)
- Internal linking and breadcrumbs
- Optimized meta tags and Open Graph"
echo.

echo [Step 5] Pushing to GitHub...
git push origin main
echo.

echo [Step 6] Updating sitemap...
copy /Y sitemap-updated.xml sitemap.xml
git add sitemap.xml
git commit -m "Update sitemap with new SEO pages"
git push origin main
echo.

echo ========================================
echo Deployment Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Submit sitemap to Google Search Console
echo    https://search.google.com/search-console
echo.
echo 2. Submit sitemap to Bing Webmaster Tools
echo    https://www.bing.com/webmasters
echo.
echo 3. Share new pages on social media:
echo.
echo    LinkedIn:
echo    - https://jinbacars.com/en/guides/import-used-cars-to-uae/
echo    - https://jinbacars.com/en/guides/import-used-cars-to-russia/
echo    - https://jinbacars.com/en/guides/import-used-cars-to-africa/
echo.
echo    Facebook Groups (car export groups):
echo    - https://jinbacars.com/en/faq/
echo    - https://jinbacars.com/en/blog/
echo.
echo    Reddit:
echo    - r/cars
echo    - r/antoexport
echo    - r/china
echo.
echo 4. Monitor traffic in Google Analytics
echo    https://analytics.google.com/
echo.
pause
