param(
  [Parameter(Mandatory = $true)]
  [ValidateSet("CHARLS", "ELSA")]
  [string]$Database,

  [Parameter(Mandatory = $true)]
  [ValidatePattern("^\d{3}_.+")]
  [string]$TopicDirectoryName,

  [string]$DbCodeBookHome = $env:DBCODEBOOK_HOME,

  [switch]$CreateExecutionDirectory
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($DbCodeBookHome)) {
  throw "DBCODEBOOK_HOME is not configured. Pass -DbCodeBookHome or set the user environment variable."
}

$demoDirectoryName = -join @([char]0x6F14, [char]0x793A)
$definitionDirectoryName = -join @([char]0x5B9A, [char]0x4E49)
$executionDirectoryName = "_" + (-join @([char]0x6267, [char]0x884C, [char]0x7EBF, [char]0x7A0B))
$definitionRoot = Join-Path (Join-Path ([System.IO.Path]::GetFullPath($DbCodeBookHome)) $demoDirectoryName) $definitionDirectoryName
if (-not (Test-Path -LiteralPath $definitionRoot -PathType Container)) {
  throw "Definition root does not exist: $definitionRoot"
}

$formalDirectory = Join-Path (Join-Path $definitionRoot $Database) $TopicDirectoryName
if (Test-Path -LiteralPath $formalDirectory) {
  throw "Formal topic directory already exists: $formalDirectory"
}

New-Item -ItemType Directory -Path $formalDirectory | Out-Null

$executionDirectory = $null
if ($CreateExecutionDirectory) {
  $executionDirectory = Join-Path (Join-Path (Join-Path $definitionRoot $executionDirectoryName) $Database) $TopicDirectoryName
  if (-not (Test-Path -LiteralPath $executionDirectory)) {
    New-Item -ItemType Directory -Path $executionDirectory -Force | Out-Null
  }
}

[ordered]@{
  ok = $true
  database = $Database
  topic = $TopicDirectoryName
  formal_directory = $formalDirectory
  execution_directory = $executionDirectory
} | ConvertTo-Json -Depth 3
