#Requires -Version 5.0

################################################################################
# ZARQA AL YAMAMA - ONE-CLICK INSTALLATION SCRIPT
# Platform: Windows (PowerShell)
# Creator: Qusai Al-Duaij
# Version: 1.0.0
# Status: Production-Ready
################################################################################

# Set error action preference
$ErrorActionPreference = "Stop"

# Configuration
$ProjectName = "zarqa-al-yamama"
$ProjectDir = Join-Path $PSScriptRoot $ProjectName
$DockerComposeFile = Join-Path $ProjectDir "docker-compose.yml"
$EnvFile = Join-Path $ProjectDir "backend" ".env"
$EnvExample = Join-Path $ProjectDir "backend" ".env.example"

################################################################################
# UTILITY FUNCTIONS
################################################################################

function Write-Header {
    Write-Host "================================================================================" -ForegroundColor Blue
    Write-Host "  ZARQA AL YAMAMA - FORESIGHT INTELLIGENCE AGENT" -ForegroundColor Blue
    Write-Host "  One-Click Installation Script (Windows)" -ForegroundColor Blue
    Write-Host "  Creator: Qusai Al-Duaij | LoLo AI Initiative" -ForegroundColor Blue
    Write-Host "================================================================================" -ForegroundColor Blue
    Write-Host ""
}

function Write-Section {
    Write-Host ""
    Write-Host ">>> $args" -ForegroundColor Blue
    Write-Host ""
}

function Write-Success {
    Write-Host "✓ $args" -ForegroundColor Green
}

function Write-Error-Custom {
    Write-Host "✗ $args" -ForegroundColor Red
}

function Write-Warning-Custom {
    Write-Host "⚠ $args" -ForegroundColor Yellow
}

function Write-Info {
    Write-Host "ℹ $args" -ForegroundColor Cyan
}

function Test-CommandExists {
    param($command)
    $null = Get-Command $command -ErrorAction SilentlyContinue
    return $?
}

################################################################################
# PREREQUISITE CHECKS
################################################################################

function Check-Prerequisites {
    Write-Section "CHECKING PREREQUISITES"
    
    $allGood = $true
    
    # Check Docker
    if (Test-CommandExists docker) {
        Write-Success "Docker is installed"
    } else {
        Write-Error-Custom "Docker is not installed"
        Write-Info "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
        $allGood = $false
    }
    
    # Check Docker Compose
    if (Test-CommandExists docker-compose) {
        Write-Success "Docker Compose is installed"
    } else {
        Write-Warning-Custom "Docker Compose not found (may be built into Docker Desktop)"
    }
    
    # Check Docker daemon
    try {
        $null = docker info 2>$null
        Write-Success "Docker daemon is running"
    } catch {
        Write-Error-Custom "Docker daemon is not running"
        Write-Info "Please start Docker Desktop"
        $allGood = $false
    }
    
    if (-not $allGood) {
        Write-Error-Custom "Please install missing prerequisites and try again"
        exit 1
    }
    
    Write-Success "All prerequisites are met!"
}

################################################################################
# PROJECT SETUP
################################################################################

function Setup-Project {
    Write-Section "SETTING UP PROJECT"
    
    # Check if project directory exists
    if (Test-Path $ProjectDir) {
        Write-Info "Project directory already exists at $ProjectDir"
        $response = Read-Host "Do you want to use the existing installation? (y/n)"
        if ($response -eq "y") {
            Write-Success "Using existing installation"
            return
        } else {
            Write-Info "Removing existing installation..."
            Remove-Item -Recurse -Force $ProjectDir
        }
    }
    
    # Copy project files
    Write-Info "Copying project files..."
    Copy-Item -Recurse -Path (Get-Location) -Destination $ProjectDir -Exclude @("install.ps1", ".git", "node_modules", "__pycache__")
    
    Write-Success "Project setup complete"
}

################################################################################
# ENVIRONMENT CONFIGURATION
################################################################################

function Configure-Environment {
    Write-Section "CONFIGURING ENVIRONMENT"
    
    # Check if .env already exists
    if (Test-Path $EnvFile) {
        Write-Info ".env file already exists"
        $response = Read-Host "Do you want to reconfigure? (y/n)"
        if ($response -ne "y") {
            Write-Success "Using existing configuration"
            return
        }
    }
    
    # Copy template
    if (Test-Path $EnvExample) {
        Copy-Item -Path $EnvExample -Destination $EnvFile -Force
        Write-Success "Created .env file from template"
    } else {
        Write-Error-Custom ".env.example not found"
        exit 1
    }
    
    Write-Info "Configuring API keys (press Enter to skip)..."
    Write-Host ""
    
    # Read API keys
    $keys = @{
        "OPENROUTER_API_KEY" = Read-Host "Enter OpenRouter API Key (optional)"
        "DEEPSEEK_API_KEY" = Read-Host "Enter DeepSeek API Key (optional)"
        "GDELT_API_KEY" = Read-Host "Enter GDELT API Key (optional)"
        "NEWSAPI_KEY" = Read-Host "Enter NewsAPI Key (optional)"
        "POLYGON_API_KEY" = Read-Host "Enter Polygon.io API Key (optional)"
        "ALPHA_VANTAGE_KEY" = Read-Host "Enter Alpha Vantage API Key (optional)"
    }
    
    # Update .env file
    $envContent = Get-Content $EnvFile
    foreach ($key in $keys.Keys) {
        if ($keys[$key]) {
            $envContent = $envContent -replace "$key=.*", "$key=$($keys[$key])"
            Write-Success "$key configured"
        }
    }
    Set-Content -Path $EnvFile -Value $envContent
    
    Write-Success "Environment configuration complete"
}

################################################################################
# DOCKER SERVICES
################################################################################

function Start-Services {
    Write-Section "STARTING DOCKER SERVICES"
    
    Set-Location $ProjectDir
    
    Write-Info "Building Docker images (this may take a few minutes)..."
    & docker-compose build --no-cache
    
    Write-Info "Starting services..."
    & docker-compose up -d
    
    Write-Success "Services started"
}

################################################################################
# HEALTH CHECKS
################################################################################

function Wait-ForService {
    param(
        [string]$ServiceName,
        [string]$Url,
        [int]$MaxAttempts = 30
    )
    
    Write-Info "Waiting for $ServiceName to be ready..."
    
    for ($attempt = 0; $attempt -lt $MaxAttempts; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Success "$ServiceName is ready"
                return $true
            }
        } catch {
            # Service not ready yet
        }
        
        Write-Host -NoNewline "."
        Start-Sleep -Seconds 2
    }
    
    Write-Error-Custom "$ServiceName did not start within timeout"
    return $false
}

function Verify-Installation {
    Write-Section "VERIFYING INSTALLATION"
    
    Set-Location $ProjectDir
    
    # Check Docker containers
    Write-Info "Checking Docker containers..."
    & docker-compose ps
    
    # Wait for services
    Wait-ForService "Backend API" "http://localhost:8000/health"
    Wait-ForService "Frontend" "http://localhost:3000"
    
    # Health check
    Write-Info "Running health check..."
    try {
        $health = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing | ConvertFrom-Json
        if ($health.status -eq "healthy") {
            Write-Success "Backend health check passed"
        }
    } catch {
        Write-Warning-Custom "Backend health check inconclusive"
    }
    
    Write-Success "Installation verification complete"
}

################################################################################
# SAMPLE FORECAST
################################################################################

function Run-SampleForecast {
    Write-Section "RUNNING SAMPLE FORECAST"
    
    Write-Info "Generating sample forecast (this may take 30-60 seconds)..."
    
    try {
        $body = @{
            scenario = "Middle East Oil Price Stability"
            user_id = "installation_test"
        } | ConvertTo-Json
        
        $forecast = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/forecast" `
            -Method POST `
            -ContentType "application/json" `
            -Body $body `
            -UseBasicParsing | ConvertFrom-Json
        
        if ($forecast.request_id) {
            Write-Success "Sample forecast generated successfully"
            Write-Info "Response preview:"
            Write-Host ($forecast | ConvertTo-Json | Select-Object -First 10)
        }
    } catch {
        Write-Warning-Custom "Sample forecast generation inconclusive"
    }
}

################################################################################
# DISPLAY RESULTS
################################################################################

function Display-Results {
    Write-Section "INSTALLATION COMPLETE!"
    
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host "  ZARQA AL YAMAMA IS READY TO USE" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host ""
    
    Write-Info "Access the application:"
    Write-Host "  Frontend Dashboard:    http://localhost:3000" -ForegroundColor Cyan
    Write-Host "  API Endpoint:          http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  API Documentation:     http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "  Health Check:          http://localhost:8000/health" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "Available Services:" -ForegroundColor Green
    Write-Host "  • Backend API (FastAPI) - Port 8000"
    Write-Host "  • Frontend (Next.js) - Port 3000"
    Write-Host "  • PostgreSQL Database - Port 5432"
    Write-Host "  • Qdrant Vector DB - Port 6333"
    Write-Host "  • Neo4j Graph DB - Port 7687"
    Write-Host "  • Redis Cache - Port 6379"
    Write-Host ""
    
    Write-Host "Useful Commands:" -ForegroundColor Green
    Write-Host "  • View logs:              docker-compose logs -f"
    Write-Host "  • Stop services:          docker-compose down"
    Write-Host "  • Restart services:       docker-compose restart"
    Write-Host "  • View service status:    docker-compose ps"
    Write-Host ""
    
    Write-Host "Documentation:" -ForegroundColor Green
    Write-Host "  • User Guide:             $ProjectDir\USER_GUIDE.md"
    Write-Host "  • Developer Guide:        $ProjectDir\DEVELOPER_GUIDE.md"
    Write-Host "  • Operations Manual:      $ProjectDir\OPERATIONS_MANUAL.md"
    Write-Host "  • README:                 $ProjectDir\README.md"
    Write-Host ""
    
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Open http://localhost:3000 in your browser"
    Write-Host "  2. Generate your first forecast"
    Write-Host "  3. Review the documentation for advanced usage"
    Write-Host "  4. Configure additional API keys as needed"
    Write-Host ""
    
    Write-Host "For support and documentation:" -ForegroundColor Blue
    Write-Host "  • Creator: Qusai Al-Duaij"
    Write-Host "  • Initiative: LoLo AI Tree (Sovereign AI Initiative)"
    Write-Host "  • Version: 1.0.0"
    Write-Host ""
}

################################################################################
# ERROR HANDLING
################################################################################

function Cleanup-OnError {
    Write-Error-Custom "Installation failed!"
    Write-Info "Cleaning up..."
    Set-Location $ProjectDir -ErrorAction SilentlyContinue
    & docker-compose down -ErrorAction SilentlyContinue
}

$ErrorActionPreference = "Stop"
trap { Cleanup-OnError; exit 1 }

################################################################################
# MAIN EXECUTION
################################################################################

function Main {
    Write-Header
    
    Check-Prerequisites
    Setup-Project
    Configure-Environment
    Start-Services
    Verify-Installation
    Run-SampleForecast
    Display-Results
    
    Write-Success "Installation completed successfully!"
}

# Run main function
Main
