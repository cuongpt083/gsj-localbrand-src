<#
================================================================================
FORM STUDIO - SMART FASHION EXECUTIVE DASHBOARD
Script Tien Ich Quan Tri Khoi Dong / Dung Ung Dung Tren Windows (PowerShell)
================================================================================
#>

param (
    [ValidateSet("start", "stop", "restart", "status", "sdv", "menu")]
    [string]$Action = "menu",
    [int]$Port = 8501
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$AppName = "FORM Studio Smart Fashion Executive Dashboard"
$AppScript = "srcs/app.py"
$HealthUrl = "http://localhost:$Port/_stcore/health"

function Get-AppProcess {
    $pids = @()
    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        if ($connections) {
            foreach ($conn in $connections) {
                if ($conn.OwningProcess -and $conn.OwningProcess -ne 0) {
                    $pids += $conn.OwningProcess
                }
            }
        }
    } catch {}

    $stProcs = Get-Process -Name "streamlit" -ErrorAction SilentlyContinue
    if ($stProcs) {
        $pids += $stProcs.Id
    }

    return ($pids | Select-Object -Unique)
}

function Check-AppStatus {
    Write-Host ""
    Write-Host ">>> Dang kiem tra trang thai $AppName (Port: $Port)..." -ForegroundColor Cyan
    $pids = Get-AppProcess
    $isHealthy = $false

    try {
        $response = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 2 -ErrorAction Stop
        if ($response -eq "ok") {
            $isHealthy = $true
        }
    } catch {}

    if ($pids.Count -gt 0 -or $isHealthy) {
        $healthText = if ($isHealthy) { "200 OK (San sang)" } else { "Dang khoi dong..." }
        $pidText = $pids -join ", "
        Write-Host "[TRANG THAI] : DANG CHAY (RUNNING)" -ForegroundColor Green
        Write-Host "  - Dia chi   : http://localhost:$Port" -ForegroundColor Yellow
        Write-Host "  - PIDs      : $pidText" -ForegroundColor Gray
        Write-Host "  - Health    : $healthText" -ForegroundColor Gray
        return $true
    } else {
        Write-Host "[TRANG THAI] : DA DUNG (STOPPED)" -ForegroundColor Red
        Write-Host "  - Port $Port dang trong, ung dung chua chay." -ForegroundColor Gray
        return $false
    }
}

function Start-App {
    Write-Host ""
    Write-Host ">>> Dang khoi dong $AppName..." -ForegroundColor Cyan
    $isRunning = Check-AppStatus

    if ($isRunning) {
        Write-Host "INFO: Ung dung da dang chay tren Port $Port!" -ForegroundColor Yellow
        Write-Host "Opening browser: http://localhost:$Port" -ForegroundColor Green
        Start-Process "http://localhost:$Port"
        return
    }

    if (-not (Test-Path $AppScript)) {
        Write-Host "ERROR: Khong tim thay file ma nguon $AppScript!" -ForegroundColor Red
        return
    }

    Write-Host "Launching Streamlit server..." -ForegroundColor Gray
    Start-Process -FilePath "streamlit" -ArgumentList "run $AppScript --server.port $Port" -WindowStyle Normal

    Write-Host "Dang ket noi toi he thong" -NoNewline
    $attempts = 0
    while ($attempts -lt 15) {
        Start-Sleep -Seconds 1
        Write-Host "." -NoNewline
        try {
            $resp = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 1 -ErrorAction Stop
            if ($resp -eq "ok") {
                Write-Host " OK!" -ForegroundColor Green
                Write-Host "==================================================================" -ForegroundColor Green
                Write-Host "  KHOI DONG THANH CONG!                                           " -ForegroundColor Green
                Write-Host "  Dia chi truy cap Dashboard : http://localhost:$Port             " -ForegroundColor Yellow
                Write-Host "==================================================================" -ForegroundColor Green
                Start-Process "http://localhost:$Port"
                return
            }
        } catch {}
        $attempts++
    }

    Write-Host ""
    Write-Host "Luu y: Da phat lenh khoi dong, vui long kiem tra cua so Streamlit moi mo." -ForegroundColor Yellow
}

function Stop-App {
    Write-Host ""
    Write-Host ">>> Dang dung ung dung $AppName..." -ForegroundColor Cyan
    $pids = Get-AppProcess

    if ($pids.Count -eq 0) {
        Write-Host "INFO: Khong co tien trinh nao dang chay tren Port $Port." -ForegroundColor Yellow
        return
    }

    foreach ($procId in $pids) {
        try {
            $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "  -> Dang tat PID: $procId ($($proc.ProcessName))..." -ForegroundColor Gray
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            }
        } catch {
            Write-Host "  -> Khong the tat PID $procId" -ForegroundColor Red
        }
    }

    Start-Sleep -Seconds 1
    Write-Host "THANH CONG: Da dung ung dung va giai phong Port $Port." -ForegroundColor Green
}

function Restart-App {
    Write-Host ""
    Write-Host ">>> Dang thuc hien Restart..." -ForegroundColor Cyan
    Stop-App
    Start-Sleep -Seconds 2
    Start-App
}

function Run-SDV-Generator {
    Write-Host ""
    Write-Host ">>> Dang tai tao CSDL bang SDV Synthetic Data Vault..." -ForegroundColor Cyan
    if (Test-Path "srcs/generate_synthetic_data_sdv.py") {
        python srcs/generate_synthetic_data_sdv.py
        Write-Host "Hoan tat tai tao du lieu KiotViet vao data/fashion_brand.db!" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Khong tim thay script srcs/generate_synthetic_data_sdv.py" -ForegroundColor Red
    }
}

function Show-Menu {
    Clear-Host
    Write-Host "==================================================================" -ForegroundColor Cyan
    Write-Host "   FORM STUDIO - TIEN ICH QUAN TRI STREAMLIT DASHBOARD (WINDOWS)  " -ForegroundColor Yellow
    Write-Host "   Chuong Trinh Dao Tao BA & Vibe Coding - Smart Fashion System   " -ForegroundColor Gray
    Write-Host "==================================================================" -ForegroundColor Cyan
    Write-Host " [1] Khoi dong ung dung (Start Dashboard)" -ForegroundColor White
    Write-Host " [2] Dung ung dung (Stop Dashboard)" -ForegroundColor White
    Write-Host " [3] Khoi dong lai ung dung (Restart Dashboard)" -ForegroundColor White
    Write-Host " [4] Kiem tra trang thai may chu (Check Status)" -ForegroundColor White
    Write-Host " [5] Tai tao CSDL KiotViet bang SDV (Synthetic Data)" -ForegroundColor White
    Write-Host " [0] Thoat (Exit)" -ForegroundColor Gray
    Write-Host "==================================================================" -ForegroundColor Cyan

    $choice = Read-Host "Nhap lua chon cua ban (0-5)"
    switch ($choice) {
        "1" { Start-App }
        "2" { Stop-App }
        "3" { Restart-App }
        "4" { Check-AppStatus }
        "5" { Run-SDV-Generator }
        "0" { Write-Host "Tam biet!"; exit 0 }
        default { Write-Host "Lua chon khong hop le!" -ForegroundColor Red }
    }
}

switch ($Action.ToLower()) {
    "start"   { Start-App }
    "stop"    { Stop-App }
    "restart" { Restart-App }
    "status"  { Check-AppStatus }
    "sdv"     { Run-SDV-Generator }
    default   { Show-Menu }
}
