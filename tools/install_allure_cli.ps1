param(
    [string]$Version = "2.25.0",
    [string]$InstallDir = "${PSScriptRoot}\..\tools\allure"
)

$ErrorActionPreference = "Stop"

function Write-Step($message) {
    Write-Host "[Allure Installer] $message"
}

function Get-AllureDownloadUrl([string]$version) {
    return "https://github.com/allure-framework/allure2/releases/download/$version/allure-$version.zip"
}

Write-Step "Preparing installation directory at $InstallDir"
if (Test-Path $InstallDir) {
    Remove-Item -Recurse -Force $InstallDir
}
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

$tempZip = Join-Path $env:TEMP "allure-$([Guid]::NewGuid()).zip"
$url = Get-AllureDownloadUrl -version $Version
Write-Step "Downloading Allure $Version from $url"
Invoke-WebRequest -Uri $url -OutFile $tempZip

Write-Step "Extracting archive"
Expand-Archive -LiteralPath $tempZip -DestinationPath $InstallDir
Remove-Item $tempZip

# Allure archives contain a versioned folder at the root; flatten to InstallDir
$extractedRoot = Get-ChildItem -Path $InstallDir | Where-Object { $_.PSIsContainer } | Select-Object -First 1
if ($null -ne $extractedRoot) {
    Write-Step "Flattening directory structure"
    Get-ChildItem -Path $extractedRoot.FullName | ForEach-Object {
        Move-Item -Path $_.FullName -Destination $InstallDir
    }
    Remove-Item -Recurse -Force $extractedRoot.FullName
}

Write-Step "Installation complete. Add the following to your PATH:"
Write-Host "  $InstallDir\bin"
Write-Step "Example (current session): $env:PATH = \"$InstallDir\bin;$env:PATH\""
Write-Step "Once PATH is updated run 'allure --version' to verify."
