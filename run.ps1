#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Launcher script for Stream Futebol Dashboard
.DESCRIPTION
    Run this PowerShell script from the root directory to start the application.
    This script sets up the Python environment and launches the goal_score application.
.PARAMETER PythonPath
    Optional path to Python executable. If not specified, uses 'python' from PATH.
.EXAMPLE
    .\run.ps1
    Runs the application using the default Python installation.
.EXAMPLE
    .\run.ps1 -PythonPath "C:\Python39\python.exe"
    Runs the application using a specific Python installation.
#>

param(
    [string]$PythonPath = "python"
)

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Change to the script directory
Set-Location $ScriptDir

Write-Host "Starting Stream Futebol Dashboard..." -ForegroundColor Green
Write-Host "Working directory: $ScriptDir" -ForegroundColor Yellow

try {
    # Check if Python is available
    $pythonVersion = & $PythonPath --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Python not found. Please ensure Python is installed and in your PATH, or specify the path using -PythonPath parameter."
        exit 1
    }
    
    Write-Host "Using Python: $pythonVersion" -ForegroundColor Cyan
    
    # Run the application using the module syntax
    Write-Host "Launching application..." -ForegroundColor Green
    & $PythonPath -m src.goal_score
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Application failed to start. Exit code: $LASTEXITCODE"
        exit $LASTEXITCODE
    }
}
catch {
    Write-Error "An error occurred while running the application: $_"
    exit 1
}
finally {
    Write-Host "Application closed." -ForegroundColor Yellow
}
