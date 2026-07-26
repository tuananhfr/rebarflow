# Build 1 lệnh: pytest -> PyInstaller -> Inno Setup -> dist\rebarflow-setup-x.y.z.exe
# Chạy từ thư mục gốc repo:  powershell -File packaging\build.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

# version đọc từ single source
$version = (Select-String -Path "rebarflow\__version__.py" -Pattern '"([^"]+)"').Matches[0].Groups[1].Value
Write-Host "== rebarFlow v$version ==" -ForegroundColor Cyan

Write-Host "[1/3] pytest..." -ForegroundColor Cyan
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest -q
if ($LASTEXITCODE -ne 0) { Write-Error "Tests FAILED - khong build." }
Remove-Item Env:QT_QPA_PLATFORM

Write-Host "[2/3] PyInstaller..." -ForegroundColor Cyan
python -m PyInstaller --noconfirm packaging\rebarflow.spec
if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller FAILED." }

Write-Host "[3/3] Inno Setup..." -ForegroundColor Cyan
$iscc = Get-Command iscc.exe -ErrorAction SilentlyContinue
if ($null -eq $iscc) {
    $default = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if (Test-Path $default) { $iscc = $default }
    else {
        Write-Warning "Khong tim thay Inno Setup (iscc.exe). Cai tu https://jrsoftware.org/isdl.php"
        Write-Warning "Da build xong dist\rebarflow\ - chi thieu buoc dong goi setup.exe."
        exit 1
    }
} else { $iscc = $iscc.Source }

& $iscc "/DMyAppVersion=$version" "packaging\installer.iss"
if ($LASTEXITCODE -ne 0) { Write-Error "Inno Setup FAILED." }

Write-Host "XONG: dist\rebarflow-setup-$version.exe" -ForegroundColor Green
Write-Host "Phat hanh: tao GitHub release tag v$version, dinh kem file setup.exe nay."
