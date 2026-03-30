# 📊 AI Case Documentation System - Status Check
# Quick status overview of the running system

Write-Host "🤖 AI Case Documentation System - Status Check" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

# Check Backend
try {
    $backendResponse = Invoke-WebRequest "http://localhost:8000/health/" -TimeoutSec 5
    $health = $backendResponse.Content | ConvertFrom-Json
    
    Write-Host "🐍 Backend Server:" -ForegroundColor Green
    Write-Host "   Status: RUNNING (Port 8000)" -ForegroundColor Green
    Write-Host "   Health: $($health.status.ToUpper())" -ForegroundColor $(if ($health.status -eq "healthy") { "Green" } elseif ($health.status -eq "degraded") { "Yellow" } else { "Red" })
    Write-Host "   Python: $($health.services.python.status)" -ForegroundColor Green
    Write-Host "   Database: $($health.services.database.status)" -ForegroundColor Green
    
    if ($health.warnings -and $health.warnings.Count -gt 0) {
        Write-Host "   ⚠️ Warnings:" -ForegroundColor Yellow
        foreach ($warning in $health.warnings) {
            Write-Host "     • $warning" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "🐍 Backend Server:" -ForegroundColor Red
    Write-Host "   Status: NOT RUNNING" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Check Frontend
try {
    $frontendResponse = Invoke-WebRequest "http://localhost:3000" -TimeoutSec 5
    Write-Host "⚛️ Frontend Server:" -ForegroundColor Green
    Write-Host "   Status: RUNNING (Port 3000)" -ForegroundColor Green
    Write-Host "   Response: $($frontendResponse.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "⚛️ Frontend Server:" -ForegroundColor Red
    Write-Host "   Status: NOT RUNNING" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Check Database
try {
    $statsResponse = Invoke-WebRequest "http://localhost:8000/stats/" -TimeoutSec 5
    $stats = $statsResponse.Content | ConvertFrom-Json
    
    Write-Host "💾 Database Status:" -ForegroundColor Green
    Write-Host "   Total Cases: $($stats.total_cases)" -ForegroundColor White
    Write-Host "   Total Documents: $($stats.total_documents)" -ForegroundColor White
    Write-Host "   Total Users: $($stats.total_users)" -ForegroundColor White
} catch {
    Write-Host "💾 Database Status:" -ForegroundColor Yellow
    Write-Host "   Unable to fetch statistics" -ForegroundColor Yellow
}

Write-Host ""

# Quick URLs
Write-Host "🔗 Application URLs:" -ForegroundColor Cyan
Write-Host "   Main App: http://localhost:3000" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   Health:   http://localhost:8000/health/" -ForegroundColor White

Write-Host ""
Write-Host "✅ Status check complete!" -ForegroundColor Green
