# PowerShell script to build Docker image for Bot Slack Service
# Usage: .\build-docker.ps1 [tag] [environment]

param(
    [string]$Tag = "latest",
    [string]$Environment = "production",
    [switch]$NoBuildCache = $false,
    [switch]$Verbose = $false
)

# Colors for output
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"
$WarningColor = "Yellow"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Test-DockerAvailable {
    try {
        $dockerVersion = docker --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✓ Docker is available: $dockerVersion" $SuccessColor
            return $true
        }
    } catch {
        Write-ColorOutput "✗ Docker command failed" $ErrorColor
    }
    return $false
}

function Build-DockerImage {
    param([string]$ImageTag, [bool]$NoCache)
    
    $buildArgs = @(
        "build",
        "-t", "bot-slack:$ImageTag",
        "-f", "deployment\Dockerfile"
    )
    
    if ($NoCache) {
        $buildArgs += "--no-cache"
    }
    
    # Add build arguments for environment
    $buildArgs += @(
        "--build-arg", "ENVIRONMENT=$Environment",
        "--build-arg", "BUILD_DATE=$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')",
        "--build-arg", "VERSION=$ImageTag"
    )
    
    $buildArgs += "."
    
    Write-ColorOutput "Building Docker image with command:" $InfoColor
    Write-ColorOutput "docker $($buildArgs -join ' ')" $InfoColor
    Write-ColorOutput "" 
    
    $startTime = Get-Date
    
    if ($Verbose) {
        & docker @buildArgs
    } else {
        & docker @buildArgs 2>&1 | Tee-Object -Variable buildOutput
    }
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "" 
        Write-ColorOutput "✓ SUCCESS: Docker image built successfully!" $SuccessColor
        Write-ColorOutput "  Image: bot-slack:$ImageTag" $SuccessColor
        Write-ColorOutput "  Build time: $($duration.ToString('mm\:ss'))" $InfoColor
        return $true
    } else {
        Write-ColorOutput "" 
        Write-ColorOutput "✗ ERROR: Failed to build Docker image!" $ErrorColor
        if (!$Verbose -and $buildOutput) {
            Write-ColorOutput "Build output:" $WarningColor
            $buildOutput | ForEach-Object { Write-ColorOutput "  $_" }
        }
        return $false
    }
}

function Show-ImageInfo {
    param([string]$ImageTag)
    
    Write-ColorOutput "" 
    Write-ColorOutput "Docker Images:" $InfoColor
    
    try {
        $images = docker images --filter "reference=bot-slack" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
        $images | ForEach-Object { Write-ColorOutput "  $_" }
    } catch {
        Write-ColorOutput "  Could not list images" $WarningColor
    }
}

function Show-Usage {
    Write-ColorOutput "" 
    Write-ColorOutput "Usage Examples:" $InfoColor
    Write-ColorOutput "  # Run the container:" 
    Write-ColorOutput "  docker run -d -p 5000:5000 --name bot-slack-container bot-slack:$Tag" $InfoColor
    Write-ColorOutput "" 
    Write-ColorOutput "  # Run with environment file:" 
    Write-ColorOutput "  docker run -d -p 5000:5000 --env-file .env --name bot-slack-container bot-slack:$Tag" $InfoColor
    Write-ColorOutput "" 
    Write-ColorOutput "  # Use docker-compose:" 
    Write-ColorOutput "  docker-compose -f deployment\docker-compose.yml up -d" $InfoColor
    Write-ColorOutput "" 
    Write-ColorOutput "  # Use development override:" 
    Write-ColorOutput "  docker-compose -f deployment\docker-compose.yml -f deployment\docker-compose.override.yml up -d" $InfoColor
}

# Main execution
Write-ColorOutput "=== Bot Slack Docker Build Script ===" $InfoColor
Write-ColorOutput "Tag: $Tag" $InfoColor
Write-ColorOutput "Environment: $Environment" $InfoColor
Write-ColorOutput "No Cache: $NoBuildCache" $InfoColor
Write-ColorOutput "" 

# Check if Docker is available
if (-not (Test-DockerAvailable)) {
    Write-ColorOutput "✗ Docker is not available!" $ErrorColor
    Write-ColorOutput "Please make sure Docker Desktop is installed and running." $WarningColor
    exit 1
}

# Check if Dockerfile exists
if (-not (Test-Path "deployment\Dockerfile")) {
    Write-ColorOutput "✗ Dockerfile not found at deployment\Dockerfile" $ErrorColor
    exit 1
}

# Check if requirements.txt exists
if (-not (Test-Path "requirements.txt")) {
    Write-ColorOutput "✗ requirements.txt not found" $ErrorColor
    exit 1
}

Write-ColorOutput "✓ All required files found" $SuccessColor
Write-ColorOutput "" 

# Build the image
if (Build-DockerImage -ImageTag $Tag -NoCache $NoBuildCache) {
    Show-ImageInfo -ImageTag $Tag
    Show-Usage
    Write-ColorOutput "" 
    Write-ColorOutput "✓ Build completed successfully!" $SuccessColor
} else {
    Write-ColorOutput "" 
    Write-ColorOutput "✗ Build failed!" $ErrorColor
    exit 1
}