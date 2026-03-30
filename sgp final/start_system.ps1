# 🚀 AI Case Documentation System - Startup Script
# Run this script to start both backend and frontend servers

Write-Host "🤖 Starting AI Case Documentation and Compliance Automation System..." -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray

# Check if required dependencies are installed
Write-Host "📋 Checking system requirements..." -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = python --version 2>$null
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>$null
    Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Check if ports are available
Write-Host "🔍 Checking port availability..." -ForegroundColor Yellow

$backendRunning = $false
$frontendRunning = $false

try {
    $client = New-Object System.Net.Sockets.TcpClient
    $client.Connect("localhost", 8000)
    $client.Close()
    Write-Host "✅ Backend already running on port 8000" -ForegroundColor Green
    $backendRunning = $true
} catch {
    Write-Host "🔄 Port 8000 available for backend" -ForegroundColor Yellow
}

try {
    $client = New-Object System.Net.Sockets.TcpClient
    $client.Connect("localhost", 3000)
    $client.Close()
    Write-Host "✅ Frontend already running on port 3000" -ForegroundColor Green
    $frontendRunning = $true
} catch {
    Write-Host "🔄 Port 3000 available for frontend" -ForegroundColor Yellow
}

# Start Backend Server
if (-not $backendRunning) {
    Write-Host "🐍 Starting Backend Server (FastAPI + Uvicorn)..." -ForegroundColor Cyan
    
    # Check if virtual environment exists
    if (Test-Path "backend\venv") {
        Write-Host "📦 Activating virtual environment..." -ForegroundColor Yellow
        & "backend\venv\Scripts\Activate.ps1"
    }
    
    # Install backend dependencies
    if (-not (Test-Path "backend\.dependencies_installed")) {
        Write-Host "📦 Installing backend dependencies..." -ForegroundColor Yellow
        Set-Location "backend"
        pip install -r requirements.txt
        New-Item -Name ".dependencies_installed" -ItemType File -Force | Out-Null
        Set-Location ".."
    }
    
    # Start backend in background
    Start-Process powershell -ArgumentList "-Command", "cd 'd:\sgp final'; python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload" -WindowStyle Minimized
    
    Write-Host "⏳ Waiting for backend to start..." -ForegroundColor Yellow
    do {
        Start-Sleep 2
        try {
            $response = Invoke-WebRequest "http://localhost:8000/health/" -TimeoutSec 2 -ErrorAction Stop
            $backendRunning = $true
            Write-Host "✅ Backend started successfully!" -ForegroundColor Green
        } catch {
            Write-Host "." -NoNewline -ForegroundColor Yellow
        }
    } while (-not $backendRunning)
}

# Start Frontend Server
if (-not $frontendRunning) {
    Write-Host "⚛️ Starting Frontend Server (React)..." -ForegroundColor Cyan
    
    # Install frontend dependencies
    if (-not (Test-Path "frontend\node_modules")) {
        Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
        Set-Location "frontend"
        npm install
        Set-Location ".."
    }
    
    # Start frontend in background
    Start-Process powershell -ArgumentList "-Command", "cd 'd:\sgp final\frontend'; npm start" -WindowStyle Minimized
    
    Write-Host "⏳ Waiting for frontend to start..." -ForegroundColor Yellow
    do {
        Start-Sleep 3
        try {
            $response = Invoke-WebRequest "http://localhost:3000" -TimeoutSec 2 -ErrorAction Stop
            $frontendRunning = $true
            Write-Host "✅ Frontend started successfully!" -ForegroundColor Green
        } catch {
            Write-Host "." -NoNewline -ForegroundColor Yellow
        }
    } while (-not $frontendRunning)
}

# System Status
Write-Host ""
Write-Host "🎉 AI Case Documentation System is now running!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Gray

Write-Host "🌐 Application URLs:" -ForegroundColor Cyan
Write-Host "   Frontend (Main App): http://localhost:3000" -ForegroundColor White
Write-Host "   Backend API:         http://localhost:8000" -ForegroundColor White
Write-Host "   API Documentation:   http://localhost:8000/docs" -ForegroundColor White
Write-Host "   System Health:       http://localhost:8000/health/" -ForegroundColor White

Write-Host ""
Write-Host "📋 Quick Health Check:" -ForegroundColor Cyan
try {
    $health = Invoke-WebRequest "http://localhost:8000/health/" | ConvertFrom-Json
    Write-Host "   System Status: $($health.status.ToUpper())" -ForegroundColor $(if ($health.status -eq "healthy") { "Green" } elseif ($health.status -eq "degraded") { "Yellow" } else { "Red" })
    Write-Host "   Database: $($health.services.database.status.ToUpper())" -ForegroundColor Green
    Write-Host "   Dependencies: $($health.dependencies.Count) checked" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️ Unable to fetch health status" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🛠️ Available Features:" -ForegroundColor Cyan
Write-Host "   ✅ Document Upload & Processing" -ForegroundColor Green
Write-Host "   ✅ OCR Text Extraction" -ForegroundColor Green
Write-Host "   ✅ Case Management" -ForegroundColor Green
Write-Host "   ✅ Compliance Checking" -ForegroundColor Green
Write-Host "   ✅ Health Monitoring" -ForegroundColor Green
Write-Host "   ✅ User Authentication" -ForegroundColor Green
Write-Host "   ⚠️ Audio Transcription (requires FFmpeg)" -ForegroundColor Yellow

Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Open http://localhost:3000 in your browser" -ForegroundColor White
Write-Host "   2. Create a new user account or login" -ForegroundColor White
Write-Host "   3. Create a new case for document processing" -ForegroundColor White
Write-Host "   4. Upload documents for AI analysis" -ForegroundColor White

Write-Host ""
Write-Host "🔧 To stop the servers, close the PowerShell windows or press Ctrl+C" -ForegroundColor Gray
Write-Host "💡 For production deployment, see IMPLEMENTATION_ROADMAP.md" -ForegroundColor Gray

# Open browser automatically
Write-Host ""
$openBrowser = Read-Host "🌐 Open the application in your default browser? (Y/n)"
if ($openBrowser -ne "n" -and $openBrowser -ne "N") {
    Start-Process "http://localhost:3000"
    Write-Host "🎉 Application opened in browser!" -ForegroundColor Green
}

Write-Host ""
Write-Host "🚀 System startup complete! Happy document processing!" -ForegroundColor Green
