param(
  [string]$DbCodeBookHome = $env:DBCODEBOOK_HOME,
  [string]$BookAppRoot = $env:DBCODEBOOK_BOOKAPP_ROOT,
  [string]$RPackageRoot = $env:DBCODEBOOK_R_PACKAGE_ROOT,
  [string]$Rscript = $env:DBCODEBOOK_RSCRIPT,
  [string]$Python = $env:DBCODEBOOK_PYTHON
)

$ErrorActionPreference = "Stop"
$checks = [System.Collections.Generic.List[object]]::new()

function Add-Check {
  param(
    [string]$Name,
    [bool]$Ok,
    [string]$Value,
    [bool]$Required = $true
  )

  $checks.Add([pscustomobject]@{
    name = $Name
    ok = $Ok
    required = $Required
    value = $Value
  })
}

if ([string]::IsNullOrWhiteSpace($DbCodeBookHome)) {
  Add-Check -Name "DBCODEBOOK_HOME" -Ok $false -Value ""
} else {
  $DbCodeBookHome = [System.IO.Path]::GetFullPath($DbCodeBookHome)
  Add-Check -Name "DBCODEBOOK_HOME" -Ok (Test-Path -LiteralPath $DbCodeBookHome -PathType Container) -Value $DbCodeBookHome
}

$demoDirectoryName = -join @([char]0x6F14, [char]0x793A)
$definitionDirectoryName = -join @([char]0x5B9A, [char]0x4E49)
$definitionRoot = if ($DbCodeBookHome) {
  Join-Path (Join-Path $DbCodeBookHome $demoDirectoryName) $definitionDirectoryName
} else {
  ""
}
Add-Check -Name "definition_root" -Ok ($definitionRoot -and (Test-Path -LiteralPath $definitionRoot -PathType Container)) -Value $definitionRoot

if ([string]::IsNullOrWhiteSpace($RPackageRoot) -and $DbCodeBookHome) {
  $RPackageRoot = Join-Path $DbCodeBookHome "R package\dbCodeBookr"
}
Add-Check -Name "dbCodeBookr_source" -Ok ($RPackageRoot -and (Test-Path -LiteralPath $RPackageRoot -PathType Container)) -Value $RPackageRoot

Add-Check -Name "bookapp_root" -Ok ($BookAppRoot -and (Test-Path -LiteralPath $BookAppRoot -PathType Container)) -Value $BookAppRoot -Required $false

if ([string]::IsNullOrWhiteSpace($Rscript)) {
  $rCommand = Get-Command Rscript -ErrorAction SilentlyContinue
  if ($rCommand) {
    $Rscript = $rCommand.Source
  }
}
Add-Check -Name "Rscript" -Ok ($Rscript -and (Test-Path -LiteralPath $Rscript -PathType Leaf)) -Value $Rscript

if ([string]::IsNullOrWhiteSpace($Python)) {
  $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
  if (-not $pythonCommand) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
  }
} elseif (Test-Path -LiteralPath $Python -PathType Leaf) {
  $pythonCommand = Get-Item -LiteralPath $Python
} else {
  $pythonCommand = Get-Command $Python -ErrorAction SilentlyContinue
}
$pythonPath = if ($pythonCommand -and $pythonCommand.PSObject.Properties["Source"]) {
  $pythonCommand.Source
} elseif ($pythonCommand -and $pythonCommand.PSObject.Properties["FullName"]) {
  $pythonCommand.FullName
} else {
  ""
}
Add-Check -Name "Python launcher" -Ok ([bool]$pythonCommand) -Value $pythonPath

$requiredFailures = @($checks | Where-Object { $_.required -and -not $_.ok })
$report = [ordered]@{
  ok = ($requiredFailures.Count -eq 0)
  definition_root = $definitionRoot
  checks = $checks
}

$report | ConvertTo-Json -Depth 5
if ($requiredFailures.Count -gt 0) {
  exit 1
}
