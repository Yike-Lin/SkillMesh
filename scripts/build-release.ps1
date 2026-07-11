param(
    [string]$OutputDir = "dist"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ManifestPath = Join-Path $RepoRoot ".codex-plugin\plugin.json"
$Manifest = Get-Content -Raw -Encoding UTF8 $ManifestPath | ConvertFrom-Json
$Version = $Manifest.version
$PluginName = $Manifest.name
$ReleaseRoot = Join-Path $RepoRoot $OutputDir
$StageRoot = Join-Path $ReleaseRoot "$PluginName-$Version"
$ZipPath = Join-Path $ReleaseRoot "$PluginName-$Version.zip"
$HashPath = Join-Path $ReleaseRoot "$PluginName-$Version.sha256.txt"
$Validator = Join-Path $PSScriptRoot "validate-release.py"
$PluginValidator = Join-Path $env:USERPROFILE ".codex\skills\.system\plugin-creator\scripts\validate_plugin.py"
$BundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

function Get-ValidatorEnvironment {
    $yamlSitePackages = python -c "import inspect, os, yaml; print(os.path.dirname(os.path.dirname(inspect.getfile(yaml))))"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to locate PyYAML site-packages from system python."
    }

    return @{
        PythonExe = $BundledPython
        PYTHONPATH = $yamlSitePackages.Trim()
    }
}

function Assert-ReleaseStage {
    param(
        [Parameter(Mandatory = $true)]
        [string]$StagePath
    )

    foreach ($required in @(".codex-plugin\\plugin.json", "README.md", "scripts\\skillmesh.py", "config\\recommendation-rules.json")) {
        $path = Join-Path $StagePath $required
        if (-not (Test-Path -LiteralPath $path)) {
            throw "Missing staged file: $required"
        }
    }
}

function Copy-StageItem {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SourcePath,
        [Parameter(Mandatory = $true)]
        [string]$StagePath
    )

    $sourceItem = Get-Item -LiteralPath $SourcePath -Force
    if ($sourceItem.PSIsContainer) {
        $targetDir = Join-Path $StagePath $sourceItem.Name
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        Get-ChildItem -LiteralPath $SourcePath -Force | ForEach-Object {
            Copy-Item -LiteralPath $_.FullName -Destination $targetDir -Recurse -Force
        }
        return
    }

    Copy-Item -LiteralPath $SourcePath -Destination (Join-Path $StagePath $sourceItem.Name) -Force
}

if (Test-Path -LiteralPath $ReleaseRoot) {
    Remove-Item -LiteralPath $ReleaseRoot -Recurse -Force
}

New-Item -ItemType Directory -Path $StageRoot | Out-Null

foreach ($item in @(".codex-plugin", "skills", "assets", "scripts", "config", "docs", "README.md")) {
    $source = Join-Path $RepoRoot $item
    if (Test-Path -LiteralPath $source) {
        Copy-StageItem -SourcePath $source -StagePath $StageRoot
    }
}

Get-ChildItem -LiteralPath $StageRoot -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -LiteralPath $StageRoot -Recurse -File | Where-Object { $_.Extension -eq ".pyc" } | Remove-Item -Force

Assert-ReleaseStage -StagePath $StageRoot

$ValidatorEnv = Get-ValidatorEnvironment
$originalPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = $ValidatorEnv.PYTHONPATH
& $ValidatorEnv.PythonExe $PluginValidator $StageRoot
$env:PYTHONPATH = $originalPythonPath
if ($LASTEXITCODE -ne 0) {
    throw "Official plugin validation failed."
}

& python $Validator $StageRoot
if ($LASTEXITCODE -ne 0) {
    throw "Release directory validation failed."
}

Compress-Archive -LiteralPath $StageRoot -DestinationPath $ZipPath -Force
& python $Validator $ZipPath
if ($LASTEXITCODE -ne 0) {
    throw "Release zip validation failed."
}

$Hash = (Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant()
Set-Content -LiteralPath $HashPath -Value "$Hash  $(Split-Path -Leaf $ZipPath)" -Encoding UTF8

Write-Host "Release ready:"
Write-Host "  Stage: $StageRoot"
Write-Host "  Zip:   $ZipPath"
Write-Host "  SHA:   $HashPath"
