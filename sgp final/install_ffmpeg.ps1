# Install FFmpeg for Audio Processing
# Run this script as Administrator in PowerShell

Write-Host "Installing FFmpeg for AI Case Documentation System..." -ForegroundColor Green

# Check if Chocolatey is installed
if (Get-Command choco -ErrorAction SilentlyContinue) {
    Write-Host "Chocolatey found. Installing FFmpeg..." -ForegroundColor Yellow
    choco install ffmpeg -y
} else {
    Write-Host "Chocolatey not found. Installing Chocolatey first..." -ForegroundColor Yellow
    
    # Install Chocolatey
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    
    # Install FFmpeg
    choco install ffmpeg -y
}

# Verify installation
Write-Host "Verifying FFmpeg installation..." -ForegroundColor Yellow
try {
    $ffmpegVersion = ffmpeg -version 2>&1 | Select-Object -First 1
    Write-Host "✅ FFmpeg installed successfully: $ffmpegVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ FFmpeg installation failed. Please install manually from https://ffmpeg.org/download.html" -ForegroundColor Red
    Write-Host "After manual installation, add FFmpeg to your system PATH." -ForegroundColor Red
}

Write-Host "`n🎉 Setup complete! Your AI Case Documentation System now supports audio transcription." -ForegroundColor Green
Write-Host "Restart your terminal and backend server to use audio features." -ForegroundColor Yellow
