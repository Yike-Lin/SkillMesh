param(
    [switch]$RunCodexAdd
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$PluginName = "skillmesh"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$HomeDir = [Environment]::GetFolderPath("UserProfile")
$PluginParent = Join-Path $HomeDir "plugins"
$PluginRoot = Join-Path $PluginParent $PluginName
$PluginCreatorScripts = Join-Path $HomeDir ".codex\skills\.system\plugin-creator\scripts"
$BundledPython = Join-Path $HomeDir ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

$CreatePluginScript = Join-Path $PluginCreatorScripts "create_basic_plugin.py"
$ValidatePluginScript = Join-Path $PluginCreatorScripts "validate_plugin.py"
$ReadMarketplaceScript = Join-Path $PluginCreatorScripts "read_marketplace_name.py"
$CachebusterScript = Join-Path $PluginCreatorScripts "update_plugin_cachebuster.py"

foreach ($required in @($CreatePluginScript, $ValidatePluginScript, $ReadMarketplaceScript, $CachebusterScript)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Missing required helper: $required"
    }
}

function Get-PythonCommandPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CommandName
    )

    $command = Get-Command $CommandName -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        return $null
    }

    return $command.Source
}

function Invoke-ProcessCapture {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [string[]]$Arguments = @(),
        [hashtable]$EnvironmentOverrides
    )

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $FilePath
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true

    $quotedArguments = foreach ($argument in $Arguments) {
        if ($argument -notmatch '[\s"]') {
            $argument
            continue
        }

        $escaped = $argument -replace '(\\*)"', '$1$1\"'
        $escaped = $escaped -replace '(\\+)$', '$1$1'
        '"' + $escaped + '"'
    }
    $startInfo.Arguments = ($quotedArguments -join " ")

    if ($null -ne $EnvironmentOverrides) {
        foreach ($entry in $EnvironmentOverrides.GetEnumerator()) {
            if ($startInfo.Environment.ContainsKey($entry.Key)) {
                $startInfo.Environment[$entry.Key] = $entry.Value
            }
            else {
                $startInfo.Environment.Add($entry.Key, $entry.Value)
            }
        }
    }

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    [void]$process.Start()
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()

    return [pscustomobject]@{
        ExitCode = $process.ExitCode
        StdOut   = $stdout
        StdErr   = $stderr
    }
}

function Test-PythonSnippet {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PythonExe,
        [Parameter(Mandatory = $true)]
        [string]$Code,
        [hashtable]$EnvironmentOverrides
    )

    if (-not (Test-Path -LiteralPath $PythonExe)) {
        return $false
    }

    $result = Invoke-ProcessCapture -FilePath $PythonExe -Arguments @("-c", $Code) -EnvironmentOverrides $EnvironmentOverrides
    return $result.ExitCode -eq 0
}

function Get-YamlSitePackages {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PythonExe
    )

    if (-not (Test-Path -LiteralPath $PythonExe)) {
        return $null
    }

    $result = Invoke-ProcessCapture -FilePath $PythonExe -Arguments @(
        "-c",
        "import inspect, os, yaml; print(os.path.dirname(os.path.dirname(inspect.getfile(yaml))))"
    )
    if ($result.ExitCode -ne 0) {
        return $null
    }

    return ($result.StdOut.Trim())
}

function Invoke-PythonScript {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PythonExe,
        [Parameter(Mandatory = $true)]
        [string]$ScriptPath,
        [string[]]$Arguments = @(),
        [hashtable]$EnvironmentOverrides
    )

    $processArguments = @($ScriptPath)
    $processArguments += $Arguments
    $result = Invoke-ProcessCapture -FilePath $PythonExe -Arguments $processArguments -EnvironmentOverrides $EnvironmentOverrides

    if (-not [string]::IsNullOrEmpty($result.StdOut)) {
        [Console]::Out.Write($result.StdOut)
    }

    if (-not [string]::IsNullOrEmpty($result.StdErr)) {
        [Console]::Error.Write($result.StdErr)
    }

    if ($result.ExitCode -ne 0) {
        throw "Python script failed: $ScriptPath"
    }
}

function Resolve-HelperPython {
    $systemPython = Get-PythonCommandPath -CommandName "python"
    if ($null -ne $systemPython) {
        return $systemPython
    }

    if (Test-Path -LiteralPath $BundledPython) {
        return $BundledPython
    }

    throw "No usable Python interpreter found. Install Python or Codex bundled runtime first."
}

function Resolve-ValidatorPython {
    $systemPython = Get-PythonCommandPath -CommandName "python"
    $candidates = @()
    if (Test-Path -LiteralPath $BundledPython) {
        $candidates += $BundledPython
    }
    if ($null -ne $systemPython) {
        $candidates += $systemPython
    }

    $versionCheck = "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)"
    $yamlCheck = "import yaml"

    foreach ($candidate in $candidates) {
        if ((Test-PythonSnippet -PythonExe $candidate -Code $versionCheck) -and
            (Test-PythonSnippet -PythonExe $candidate -Code $yamlCheck)) {
            return @{
                PythonExe = $candidate
                EnvironmentOverrides = $null
            }
        }
    }

    foreach ($candidate in $candidates) {
        if (-not (Test-PythonSnippet -PythonExe $candidate -Code $versionCheck)) {
            continue
        }

        if ($null -ne $systemPython) {
            $yamlSitePackages = Get-YamlSitePackages -PythonExe $systemPython
            if (-not [string]::IsNullOrWhiteSpace($yamlSitePackages)) {
                $envOverrides = @{
                    PYTHONPATH = $yamlSitePackages
                }
                if (Test-PythonSnippet -PythonExe $candidate -Code $yamlCheck -EnvironmentOverrides $envOverrides) {
                    return @{
                        PythonExe = $candidate
                        EnvironmentOverrides = $envOverrides
                    }
                }
            }
        }
    }

    throw "No Python interpreter can run the plugin validator. Need Python >= 3.9 with PyYAML, or Codex bundled Python plus an importable PyYAML site-packages path."
}

function Copy-PluginItem {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $source = Join-Path $RepoRoot $Name
    if (-not (Test-Path -LiteralPath $source)) {
        return
    }

    $target = Join-Path $PluginRoot $Name
    if (Test-Path -LiteralPath $target) {
        $targetItem = Get-Item -LiteralPath $target -Force
        if ($targetItem.PSIsContainer) {
            Get-ChildItem -LiteralPath $target -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        }
        else {
            Remove-Item -LiteralPath $target -Force -ErrorAction SilentlyContinue
        }
    }

    Copy-Item -LiteralPath $source -Destination $PluginRoot -Recurse -Force
}

$HelperPython = Resolve-HelperPython
$ValidatorPython = Resolve-ValidatorPython

Write-Host "Scaffolding personal marketplace entry for $PluginName ..."
Invoke-PythonScript -PythonExe $HelperPython -ScriptPath $CreatePluginScript -Arguments @(
    $PluginName,
    "--path", $PluginParent,
    "--with-marketplace",
    "--with-skills",
    "--with-assets",
    "--with-scripts",
    "--force"
)

foreach ($item in @(".codex-plugin", "skills", "assets", "scripts", "README.md", "docs")) {
    Copy-PluginItem -Name $item
}

Write-Host "Updating staged plugin cachebuster ..."
Invoke-PythonScript -PythonExe $HelperPython -ScriptPath $CachebusterScript -Arguments @($PluginRoot)

Write-Host "Validating staged plugin ..."
Invoke-PythonScript -PythonExe $ValidatorPython.PythonExe -ScriptPath $ValidatePluginScript -Arguments @($PluginRoot) -EnvironmentOverrides $ValidatorPython.EnvironmentOverrides

$MarketplaceName = (& $HelperPython $ReadMarketplaceScript).Trim()
$MarketplacePath = Join-Path $HomeDir ".agents\plugins\marketplace.json"
$EncodedMarketplacePath = [System.Uri]::EscapeDataString($MarketplacePath)
$ViewUrl = "codex://plugins/${PluginName}?marketplacePath=$EncodedMarketplacePath"
$ShareUrl = "$ViewUrl&mode=share"
$InstallCommand = "codex plugin add $PluginName@$MarketplaceName"

Write-Host ""
Write-Host "Plugin staged at: $PluginRoot"
Write-Host "Marketplace: $MarketplaceName"
Write-Host "Next command:"
Write-Host "  $InstallCommand"
Write-Host "Codex app:"
Write-Host "  View:  $ViewUrl"
Write-Host "  Share: $ShareUrl"

if ($RunCodexAdd) {
    if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
        throw "The 'codex' command is not available in PATH."
    }

    $pluginHelp = Invoke-ProcessCapture -FilePath "cmd.exe" -Arguments @("/c", "codex", "help", "plugin")

    if ($pluginHelp.ExitCode -ne 0) {
        Write-Host ""
        Write-Host "This Codex CLI build does not expose 'codex plugin add'."
        Write-Host "Open the plugin in the Codex app via the View link above, then install or enable it there."
        return
    }

    Write-Host ""
    Write-Host "Reinstalling plugin into Codex ..."
    $installResult = Invoke-ProcessCapture -FilePath "cmd.exe" -Arguments @("/c", "codex", "plugin", "add", "$PluginName@$MarketplaceName")
    if (-not [string]::IsNullOrEmpty($installResult.StdOut)) {
        [Console]::Out.Write($installResult.StdOut)
    }
    if (-not [string]::IsNullOrEmpty($installResult.StdErr)) {
        [Console]::Error.Write($installResult.StdErr)
    }
    if ($installResult.ExitCode -ne 0) {
        throw "codex plugin add failed."
    }

    Write-Host ""
    Write-Host "Done. Start a new Codex thread to pick up updated skills and tools."
}
