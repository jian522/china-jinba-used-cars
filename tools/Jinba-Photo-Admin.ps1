$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName Microsoft.VisualBasic

$repoName = 'jian522/china-jinba-used-cars'
$root = Join-Path $env:LOCALAPPDATA 'JinbaPhotoAdmin'
$repo = Join-Path $root 'repo'

function Fail([string]$message) {
  [System.Windows.Forms.MessageBox]::Show($message, 'Jinba 车辆补图', 'OK', 'Error') | Out-Null
  exit 1
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { Fail '未找到 GitHub CLI。请重新打开 PowerShell 后再运行。' }
gh auth status 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { Fail 'GitHub CLI 尚未登录，请先运行 gh auth login。' }
New-Item -ItemType Directory -Force -Path $root | Out-Null

if (-not (Test-Path (Join-Path $repo '.git'))) {
  gh repo clone $repoName $repo
} else {
  git -C $repo fetch origin main
  git -C $repo switch main
  git -C $repo pull --rebase origin main
}
if ($LASTEXITCODE -ne 0) { Fail '无法同步GitHub仓库，请检查网络后重试。' }

$dataPath = Join-Path $repo 'data\vehicles.json'
$vehicles = Get-Content -Raw -Encoding UTF8 $dataPath | ConvertFrom-Json
$rows = $vehicles | ForEach-Object {
  [pscustomobject]@{
    库存编号 = $_.stock_id
    车型 = if ($_.title_i18n.zh) { $_.title_i18n.zh } else { $_.title }
    年份 = $_.year
    里程 = $_.mileage
    照片数 = @($_.photos).Count
    状态 = $_.status
    id = $_.id
  }
}

$selected = $rows | Out-GridView -Title 'Jinba 车辆管理：搜索并选择一台需要补图的车辆' -PassThru
if (-not $selected) { exit 0 }
if (@($selected).Count -ne 1) { Fail '每次请选择一台车辆。' }
$vehicle = $vehicles | Where-Object { $_.id -eq $selected.id } | Select-Object -First 1

$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = '按封面优先顺序选择6–9张同一台车辆的原始照片'
$dialog.Filter = '车辆照片|*.jpg;*.jpeg;*.png'
$dialog.Multiselect = $true
if ($dialog.ShowDialog() -ne 'OK') { exit 0 }
$files = @($dialog.FileNames)
if ($files.Count -lt 6 -or $files.Count -gt 9) { Fail '每台车必须选择6–9张照片。请重新运行并选择正确数量。' }

foreach ($file in $files) {
  $info = Get-Item $file
  if ($info.Length -gt 15MB) { Fail "单张照片不能超过15MB：$($info.Name)" }
  try {
    $img = [System.Drawing.Image]::FromFile($file)
    $w = $img.Width; $h = $img.Height; $img.Dispose()
    if ($w -lt 800 -or $h -lt 600) { Fail "照片最低需要800×600：$($info.Name) ($w×$h)" }
  } catch { Fail "无法读取图片：$($info.Name)" }
}

$source = [Microsoft.VisualBasic.Interaction]::InputBox(
  '填写可追溯来源，例如：自有库存 / 供应商名称与库存编号。不要使用无授权平台图片。',
  '照片来源与授权',
  '自有库存'
)
if ([string]::IsNullOrWhiteSpace($source)) { Fail '必须填写照片来源。' }
$confirm = [System.Windows.Forms.MessageBox]::Show(
  "库存：$($vehicle.stock_id)\n车型：$($selected.车型)\n照片：$($files.Count)张\n来源：$source\n\n确认照片均属于同一台车并拥有商业展示权？",
  '最终确认',
  'YesNo',
  'Warning'
)
if ($confirm -ne 'Yes') { exit 0 }

$carDir = Join-Path $repo ("uploads\cars\{0}" -f $vehicle.id)
New-Item -ItemType Directory -Force -Path $carDir | Out-Null
$newPhotos = @()
for ($i=0; $i -lt $files.Count; $i++) {
  $ext = [IO.Path]::GetExtension($files[$i]).ToLowerInvariant()
  if ($ext -eq '.jpeg') { $ext = '.jpg' }
  $name = if ($i -eq 0) { "primary$ext" } else { 'photo-{0:d2}{1}' -f ($i + 1), $ext }
  Copy-Item -Force $files[$i] (Join-Path $carDir $name)
  $newPhotos += "/uploads/cars/$($vehicle.id)/$name"
}
$vehicle.photos = $newPhotos
$vehicle.photo_status = 'complete'
$vehicle | Add-Member -Force -NotePropertyName photo_source -NotePropertyValue $source

$json = $vehicles | ConvertTo-Json -Depth 20
[IO.File]::WriteAllText($dataPath, $json + [Environment]::NewLine, (New-Object Text.UTF8Encoding($false)))

git -C $repo add -- data/vehicles.json ("uploads/cars/{0}" -f $vehicle.id)
git -C $repo commit -m "Update photos for $($vehicle.stock_id)"
if ($LASTEXITCODE -ne 0) { Fail '没有检测到可提交的照片变更。' }
git -C $repo pull --rebase origin main
if ($LASTEXITCODE -ne 0) { Fail '远程库存刚刚发生变化。为避免覆盖，已停止发布；请联系管理员处理冲突。' }
git -C $repo push origin main
if ($LASTEXITCODE -ne 0) { Fail '上传失败，请检查网络并重试。' }

[System.Windows.Forms.MessageBox]::Show(
  "已上传 $($vehicle.stock_id) 的 $($files.Count) 张照片。网站将在约1–3分钟内自动更新。",
  '补图完成',
  'OK',
  'Information'
) | Out-Null
