$ErrorActionPreference = "Stop"
$TOKEN = "YOUR_GITHUB_TOKEN"
$REPO = "jian522/usedchinesecars"
$WORK_DIR = "C:\Users\25394\Documents\金霸二手车网站"
$API_BASE = "https://api.github.com/repos/$REPO"

function Invoke-GitHubAPI {
    param([string]$Method, [string]$UrlPath, [object]$Body)
    $url = "$API_BASE$UrlPath"
    $headers = @{
        "Authorization" = "Bearer $TOKEN"
        "Accept" = "application/vnd.github+json"
        "User-Agent" = "jinba-deploy"
    }
    Write-Host "  [API] $Method $UrlPath" -ForegroundColor DarkGray
    if ($Body) {
        $jsonBody = $Body | ConvertTo-Json -Depth 100 -Compress
        $response = Invoke-RestMethod -Uri $url -Method $Method -Headers $headers -Body $jsonBody -ContentType "application/json"
    } else {
        $response = Invoke-RestMethod -Uri $url -Method $Method -Headers $headers
    }
    return $response
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  金霸二手车 - GitHub 部署脚本" -ForegroundColor Cyan
Write-Host "  仓库: jian522/usedchinesecars" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "[1/5] 收集文件列表..." -ForegroundColor Yellow
$essentialFiles = @(
    "index.html", "cars.html", "cars-detail.html",
    "about.html", "services.html", "contact.html", "404.html",
    "js/cars-data.js", "js/i18n.js", "js/slug-map.js",
    "css/style.css",
    "sitemap.xml", "robots.txt", "CNAME", ".nojekyll",
    "favicon.svg", "sw.js"
)

$carPages = @()
if (Test-Path "$WORK_DIR\cars") {
    $carPages = Get-ChildItem -Path "$WORK_DIR\cars" -Filter "*.html" | ForEach-Object {
        "cars/$($_.Name)"
    }
}

$imageFiles = @()
if (Test-Path "$WORK_DIR\uploads") {
    $imageFiles = Get-ChildItem -Path "$WORK_DIR\uploads" -Recurse -File | ForEach-Object {
        $relative = $_.FullName.Substring($WORK_DIR.Length + 1)
        $relative -replace '\\', '/'
    }
}

$allFiles = $essentialFiles + $carPages + $imageFiles
Write-Host "  共 $($allFiles.Count) 个文件" -ForegroundColor Green

Write-Host "[2/5] 获取仓库状态..." -ForegroundColor Yellow
try {
    $ref = Invoke-GitHubAPI -Method "GET" -UrlPath "/git/refs/heads/main"
    $parentSha = $ref.object.sha
    Write-Host "  当前 HEAD: $($parentSha.Substring(0,7))" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: 无法获取仓库状态 - $_" -ForegroundColor Red
    exit 1
}

Write-Host "[3/5] 上传文件到 GitHub..." -ForegroundColor Yellow
$entries = @()
$successCount = 0
$failCount = 0
$total = $allFiles.Count
$i = 0

foreach ($fileName in $allFiles) {
    $i++
    $fullPath = Join-Path $WORK_DIR $fileName
    if (-not (Test-Path $fullPath)) {
        $failCount++
        continue
    }
    $ext = [System.IO.Path]::GetExtension($fileName).ToLower()
    $isBinary = @('.jpg', '.jpeg', '.png', '.gif', '.webp', '.ico', '.svg') -contains $ext
    try {
        if ($isBinary) {
            $bytes = [System.IO.File]::ReadAllBytes($fullPath)
            $content = [Convert]::ToBase64String($bytes)
            $blob = Invoke-GitHubAPI -Method "POST" -UrlPath "/git/blobs" -Body @{ content = $content; encoding = "base64" }
        } else {
            $content = [System.IO.File]::ReadAllText($fullPath, [System.Text.Encoding]::UTF8)
            $blob = Invoke-GitHubAPI -Method "POST" -UrlPath "/git/blobs" -Body @{ content = $content; encoding = "utf-8" }
        }
        $entries += @{ path = $fileName -replace '\\', '/'; mode = "100644"; type = "blob"; sha = $blob.sha }
        $successCount++
    } catch {
        $failCount++
    }
    if ($i % 50 -eq 0 -or $i -eq $total) {
        Write-Host "  进度: $i/$total (成功:$successCount 失败:$failCount)" -ForegroundColor Gray
    }
}
Write-Host "  上传完成: $successCount 个文件" -ForegroundColor Green

if ($entries.Count -eq 0) { Write-Host "错误: 没有文件成功上传" -ForegroundColor Red; exit 1 }

Write-Host "[4/5] 创建 Git tree..." -ForegroundColor Yellow
$treeSha = $null
$batchSize = 100
$batchNum = 0
for ($start = 0; $start -lt $entries.Count; $start += $batchSize) {
    $batchNum++
    $batchEntries = $entries[$start..[Math]::Min($start + $batchSize - 1, $entries.Count - 1)]
    $treeBody = @{ tree = $batchEntries }
    if ($treeSha) { $treeBody.base_tree = $treeSha }
    $treeResult = Invoke-GitHubAPI -Method "POST" -UrlPath "/git/trees" -Body $treeBody
    $treeSha = $treeResult.sha
    Write-Host "  Tree batch $batchNum : $($treeSha.Substring(0,7))" -ForegroundColor Green
}

Write-Host "[5/5] 创建提交并更新分支..." -ForegroundColor Yellow
$commitMsg = "SEO优化 + 数据修复: 160个独立车型页面, WhatsApp, GA4, 编码修复"
$newCommit = Invoke-GitHubAPI -Method "POST" -UrlPath "/git/commits" -Body @{
    message = $commitMsg
    tree = $treeSha
    parents = @($parentSha)
}
Write-Host "  提交: $($newCommit.sha.Substring(0,7))" -ForegroundColor Green

Invoke-GitHubAPI -Method "PATCH" -UrlPath "/git/refs/heads/main" -Body @{ sha = $newCommit.sha; force = $true }
Write-Host "  分支更新成功!" -ForegroundColor Green

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  部署完成!" -ForegroundColor Cyan
Write-Host "  提交: $($newCommit.sha.Substring(0,7))" -ForegroundColor Cyan
Write-Host "  网站: https://jinbacars.com" -ForegroundColor Cyan
Write-Host "  刷新时间: 1-5 分钟" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步:"
Write-Host "1. 在 https://analytics.google.com 创建 GA4 属性"
Write-Host "2. 获取测量ID (G-XXXXXXXX) 替换所有HTML文件中的 G-XXXXXXXXXX"
Write-Host "3. 在 https://search.google.com/search-console 提交新的 sitemap.xml"
Write-Host "4. 检查 WhatsApp 号码是否正确（当前: +86-180-7908-9999）"
