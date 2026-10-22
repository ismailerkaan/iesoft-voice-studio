# Windows: starts IESOFT Voice Studio (if not already running) and opens the browser
# once the model is ready. Usage: scripts\launch.bat  (or: powershell -File scripts\launch.ps1)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Port = if ($env:PORT) { $env:PORT } else { "8765" }
$Url = "http://127.0.0.1:$Port"

# Keep the ~3.2 GB model cache on the project's drive unless the user chose another location.
if (-not $env:HF_HOME) { $env:HF_HOME = Join-Path (Split-Path -Parent $Root) ".cache\huggingface" }
# Pick up tools installed after this shell started (ffmpeg via winget).
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

function Get-ModelStatus {
    try { (Invoke-RestMethod -Uri "$Url/api/status" -TimeoutSec 2).model.status } catch { $null }
}

if (Get-ModelStatus) {
    Write-Host "IESOFT Voice Studio zaten çalışıyor -> $Url"
    Start-Process $Url
    exit 0
}
if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
    Write-Error "$Port portu başka bir uygulama tarafından kullanılıyor."
    exit 1
}
if (-not (Test-Path "frontend\dist")) { Push-Location frontend; npm run build; Pop-Location }

# Open the browser in the background once the model has finished loading.
Start-Job -ArgumentList $Url -ScriptBlock {
    param($Url)
    for ($i = 0; $i -lt 300; $i++) {
        try { $s = (Invoke-RestMethod -Uri "$Url/api/status" -TimeoutSec 2).model.status } catch { $s = $null }
        if ($s -in @("ready", "error")) { Start-Process $Url; return }
        Start-Sleep -Seconds 2
    }
} | Out-Null

Write-Host "IESOFT Voice Studio başlatılıyor... Model hazır olunca tarayıcı açılacak (CPU'da ~1 dk; ilk kez model iniyorsa daha uzun)."
Write-Host "Durdurmak için Ctrl + C"
& "$Root\.venv\Scripts\python.exe" -m uvicorn backend.app.main:app --host 127.0.0.1 --port $Port
