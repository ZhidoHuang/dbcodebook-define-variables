param(
  [Parameter(Mandatory = $true)]
  [string]$WorkDir,

  [Parameter(Mandatory = $true)]
  [string]$Script,

  [Parameter(Mandatory = $true)]
  [string]$LogPrefix,

  [string]$Rscript = $env:DBCODEBOOK_RSCRIPT,

  [string]$Python = $env:DBCODEBOOK_PYTHON,

  [string]$ArchiveDir = "",

  [switch]$NoArchiveOldLogs
)

$ErrorActionPreference = "Stop"

function Resolve-RequiredPath {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$Kind
  )

  if (-not (Test-Path -LiteralPath $Path)) {
    throw "$Kind does not exist: $Path"
  }
  return (Resolve-Path -LiteralPath $Path).Path
}

$resolvedWorkDir = Resolve-RequiredPath -Path $WorkDir -Kind "WorkDir"
$scriptPath = if ([System.IO.Path]::IsPathRooted($Script)) {
  $Script
} else {
  Join-Path $resolvedWorkDir $Script
}
$resolvedScript = Resolve-RequiredPath -Path $scriptPath -Kind "R script"
if ([string]::IsNullOrWhiteSpace($Rscript)) {
  $rCommand = Get-Command Rscript -ErrorAction SilentlyContinue
  if ($rCommand) {
    $Rscript = $rCommand.Source
  }
}
if ([string]::IsNullOrWhiteSpace($Rscript)) {
  throw "Rscript is not configured. Pass -Rscript, set DBCODEBOOK_RSCRIPT, or add Rscript to PATH."
}
$resolvedRscript = Resolve-RequiredPath -Path $Rscript -Kind "Rscript"

$scriptText = [System.IO.File]::ReadAllText($resolvedScript, [System.Text.Encoding]::UTF8)
$publicBoundary = [regex]::Match($scriptText, '(?m)^# \u8F93\u51FA\s*$')
if (-not $publicBoundary.Success) {
  throw "Public R boundary is missing."
}
$publicSource = $scriptText.Substring(0, $publicBoundary.Index)
$publicIssues = [System.Collections.Generic.List[string]]::new()
$databaseRoot = Split-Path -Leaf (Split-Path -Parent $resolvedWorkDir)
$isCharls = $databaseRoot -eq "CHARLS"

if ($publicSource -match '(?m)^names\(dt\)\[1\]\s*<-\s*["'']ID["'']\s*$') {
  $publicIssues.Add('Remove redundant names(dt)[1] <- "ID".')
}
if ($publicSource -match '(?m)^names\(name_z\)\[1\]\s*<-\s*["'']Easy\.label["'']\s*$') {
  $publicIssues.Add('Remove redundant names(name_z)[1] <- "Easy.label".')
}
if ($publicSource -match '\[\[\s*["'']Easy label["'']\s*\]\]') {
  $publicIssues.Add('read.csv normalizes "Easy label" to "Easy.label". Use the normalized column name.')
}

$usesCheckNamesFalse = $publicSource -match '(?is)read\.csv\([^)]*check\.names\s*=\s*FALSE'
if ($usesCheckNamesFalse) {
  $publicIssues.Add('read.csv(check.names = FALSE) is forbidden. Assign unique aliases in dbCodeBook before download.')
}

if ($isCharls) {
  foreach ($rawName in @('raw_data.csv', 'raw_codebook.csv')) {
    $rawPath = Join-Path $resolvedWorkDir $rawName
    if (Test-Path -LiteralPath $rawPath) {
      $rawBytes = [System.IO.File]::ReadAllBytes($rawPath)
      $hasUtf8Bom = (
        $rawBytes.Length -ge 3 -and
        $rawBytes[0] -eq 0xEF -and
        $rawBytes[1] -eq 0xBB -and
        $rawBytes[2] -eq 0xBF
      )
      if ($hasUtf8Bom) {
        $publicIssues.Add("$rawName contains a UTF-8 BOM. Fix the export instead of adding read.csv options.")
      }
    }
  }
  $rawDataPath = Join-Path $resolvedWorkDir 'raw_data.csv'
  if (Test-Path -LiteralPath $rawDataPath) {
    $rawHeader = [System.IO.File]::ReadLines($rawDataPath, [System.Text.Encoding]::UTF8) |
      Select-Object -First 1
    $rawHeaderCounts = [System.Collections.Generic.Dictionary[string, int]]::new(
      [System.StringComparer]::Ordinal
    )
    foreach ($columnName in $rawHeader.Split(',')) {
      if ($rawHeaderCounts.ContainsKey($columnName)) {
        $rawHeaderCounts[$columnName]++
      } else {
        $rawHeaderCounts[$columnName] = 1
      }
    }
    $duplicateRawHeader = @(
      $rawHeaderCounts.GetEnumerator() |
        Where-Object { $_.Value -gt 1 } |
        ForEach-Object { $_.Key }
    )
    if ($duplicateRawHeader) {
      $publicIssues.Add(
        "raw_data.csv contains duplicate columns. Assign unique aliases in dbCodeBook before download: $($duplicateRawHeader -join ', ')"
      )
    }
  }
  if (-not $publicSource.Contains('name_z <- read.csv("raw_codebook.csv")')) {
    $publicIssues.Add(
      'CHARLS public R must use the simple read: name_z <- read.csv("raw_codebook.csv")'
    )
  }
  $hasSimpleDataRead = $publicSource.Contains('dt <- read.csv("raw_data.csv")')
  if (-not $hasSimpleDataRead) {
    $publicIssues.Add(
      'CHARLS public R must use dt <- read.csv("raw_data.csv").'
    )
  }
  if ($publicSource -match '(?m)^names\((?:data|dt)\)\s*\[[^\]]+\]\s*<-') {
    $publicIssues.Add(
      'CHARLS public R must not rename raw columns by position. Assign unique aliases in dbCodeBook before download.'
    )
  }
  if ($publicSource -match 'read\.csv\(\s*["'']raw_(?:data|codebook)\.csv["''][^)]*(?:fileEncoding|encoding|col\.names)\s*=') {
    $publicIssues.Add('CHARLS public raw reads must not add encoding or column-name options.')
  }
}

if ($publicSource -match '(?m)^raw_row_count\s*<-\s*nrow\(data\)\s*$') {
  $publicIssues.Add('Background raw_row_count leaked into public R.')
}
if ($publicSource -match '(?m)^raw_vars\s*<-\s*name_z\$newname\s*$') {
  $publicIssues.Add('raw_vars detours through raw_codebook in public R.')
}
if ($publicSource -match '(?m)^if\s*\(\s*!"id"\s*%in%\s*names\((?:data|dt)\)\s*\)\s*\{') {
  $publicIssues.Add('Defensive id fallback leaked into public R.')
}
if ($publicSource -match '(?ms)^data\s*<-\s*data\s*%>%\s*\n?\s*filter\(year\s*%in%') {
  $publicIssues.Add('Global target-wave filter belongs at the formal output boundary, not the read block.')
}

$requiredPublicHeader = @(
  'library("devtools")',
  'library("openxlsx")',
  'library("dplyr")',
  'install_github("ZhidoHuang/dbCodeBookr")',
  'library("dbCodeBookr")'
)
foreach ($token in $requiredPublicHeader) {
  if (-not $publicSource.Contains($token)) {
    $publicIssues.Add("Missing fixed public R header token: $token")
  }
}
if ($publicSource -match '(?is)for\s*\(\s*pkg\s+in\s+c\([^)]*["'']dbCodeBookr["'']') {
  $publicIssues.Add('Do not place dbCodeBookr in the generic package loop.')
}

if ($publicSource -match '(?mi)^#\s*raw_data\.csv.*dbcodebook\.cn.*Go to.*$') {
  $publicIssues.Add('Remove the reader-facing raw_data.csv guide from formal definition R.')
}

$publicLines = $publicSource -split "`r?`n"
for ($lineIndex = 0; $lineIndex -lt $publicLines.Count; $lineIndex++) {
  $recodeMatch = [regex]::Match(
    $publicLines[$lineIndex],
    '^\s*#\s*recode\.(chr|num)\(([^)]+)\)\s*$'
  )
  if (-not $recodeMatch.Success) {
    continue
  }
  $recodeKind = $recodeMatch.Groups[1].Value
  $recodeTarget = $recodeMatch.Groups[2].Value.Trim()
  $nextIndex = $lineIndex + 1
  while ($nextIndex -lt $publicLines.Count -and [string]::IsNullOrWhiteSpace($publicLines[$nextIndex])) {
    $nextIndex++
  }
  if ($nextIndex -ge $publicLines.Count) {
    $publicIssues.Add("Orphan recode.$recodeKind marker for $recodeTarget.")
    continue
  }
  $assignmentPattern = '^\s*' + [regex]::Escape($recodeTarget) + '\s*<-'
  if ($publicLines[$nextIndex] -notmatch $assignmentPattern) {
    $publicIssues.Add("recode.$recodeKind marker target differs from assignment: $recodeTarget")
    continue
  }
  $blockLines = [System.Collections.Generic.List[string]]::new()
  for ($blockIndex = $nextIndex; $blockIndex -lt $publicLines.Count; $blockIndex++) {
    $blockLines.Add($publicLines[$blockIndex])
    if ($blockIndex -gt $nextIndex -and $publicLines[$blockIndex] -match '^\s*\)\)?\s*$') {
      break
    }
  }
  $blockText = $blockLines -join "`n"
  $targetCount = [regex]::Matches($blockText, [regex]::Escape($recodeTarget)).Count
  if ($targetCount -lt 2) {
    $publicIssues.Add("recode.$recodeKind marker does not recode its own target: $recodeTarget")
  }
}

if ($publicIssues.Count -gt 0) {
  throw "Public R preflight failed:`n- $($publicIssues -join "`n- ")"
}

$topicLeaf = Split-Path -Leaf $resolvedWorkDir
if ($topicLeaf -match '^(\d{3})_' -and [int]$Matches[1] -ge 23) {
  $topicId = $Matches[1]
  $formalRoot = Split-Path -Parent $resolvedWorkDir
  $definitionRoot = Split-Path -Parent $formalRoot
  $executionThreadsName = "_" + (
    [string][char]0x6267 +
    [string][char]0x884C +
    [string][char]0x7EBF +
    [string][char]0x7A0B
  )
  $sourceRecord = Join-Path (
    Join-Path (Join-Path $definitionRoot $executionThreadsName) "CHARLS\$topicLeaf"
  ) "definition_search_record.json"
  $sourceChecker = Join-Path $PSScriptRoot "check_definition_source_record.py"
  $rawCodebook = Join-Path $resolvedWorkDir "raw_codebook.csv"

  $resolvedSourceRecord = Resolve-RequiredPath -Path $sourceRecord -Kind "Definition source-search record"
  $resolvedSourceChecker = Resolve-RequiredPath -Path $sourceChecker -Kind "Definition source-record checker"
  $resolvedRawCodebook = Resolve-RequiredPath -Path $rawCodebook -Kind "raw_codebook.csv"
  if ([string]::IsNullOrWhiteSpace($Python)) {
    $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
      $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    }
    if (-not $pythonCommand) {
      throw "Python launcher was not found. Set DBCODEBOOK_PYTHON or add py/python to PATH."
    }
    $pythonLauncher = $pythonCommand.Source
  } elseif (Test-Path -LiteralPath $Python -PathType Leaf) {
    $pythonLauncher = (Resolve-Path -LiteralPath $Python).Path
  } else {
    $pythonCommand = Get-Command $Python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
      throw "Python launcher does not exist: $Python"
    }
    $pythonLauncher = $pythonCommand.Source
  }
  $pythonPrefixArguments = if (
    [System.IO.Path]::GetFileNameWithoutExtension($pythonLauncher) -ieq "py"
  ) {
    @("-3")
  } else {
    @()
  }

  & $pythonLauncher @pythonPrefixArguments $resolvedSourceChecker `
    --record $resolvedSourceRecord `
    --r-script $resolvedScript `
    --raw-codebook $resolvedRawCodebook `
    --topic-id $topicId
  if ($LASTEXITCODE -ne 0) {
    throw "Definition source-search gate failed. Resolve and report source or logic issues before formal R execution."
  }
}

$scriptBytes = [System.IO.File]::ReadAllBytes($resolvedScript)
if ($scriptBytes.Length -ge 3 -and $scriptBytes[0] -eq 0xEF -and $scriptBytes[1] -eq 0xBB -and $scriptBytes[2] -eq 0xBF) {
  throw "R script has a UTF-8 BOM. Rewrite it as UTF-8 without BOM before running: $resolvedScript"
}

if ([string]::IsNullOrWhiteSpace($ArchiveDir)) {
  $ArchiveDir = Join-Path $resolvedWorkDir "archived_logs"
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logName = "${LogPrefix}_run_${timestamp}.log"
$logPath = Join-Path $resolvedWorkDir $logName

if (-not $NoArchiveOldLogs) {
  $resolvedArchiveDir = $ArchiveDir
  if (-not [System.IO.Path]::IsPathRooted($resolvedArchiveDir)) {
    $resolvedArchiveDir = Join-Path $resolvedWorkDir $resolvedArchiveDir
  }
  New-Item -ItemType Directory -Force -Path $resolvedArchiveDir | Out-Null

  Get-ChildItem -LiteralPath $resolvedWorkDir -Filter "${LogPrefix}_run_*.log" -File |
    Where-Object { $_.FullName -ne $logPath } |
    ForEach-Object {
      $target = Join-Path $resolvedArchiveDir $_.Name
      if (Test-Path -LiteralPath $target) {
        $target = Join-Path $resolvedArchiveDir ("{0}.archived_{1}.log" -f $_.BaseName, (Get-Date -Format "yyyyMMdd_HHmmssfff"))
      }
      Move-Item -LiteralPath $_.FullName -Destination $target
    }
}

$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = $resolvedRscript
$psi.WorkingDirectory = $resolvedWorkDir
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.StandardOutputEncoding = [System.Text.UTF8Encoding]::new($false)
$psi.StandardErrorEncoding = [System.Text.UTF8Encoding]::new($false)
$scriptParent = Split-Path -Parent $resolvedScript
$relativeScript = if ($scriptParent -eq $resolvedWorkDir) {
  Split-Path -Leaf $resolvedScript
} else {
  $resolvedScript.Replace('\', '/')
}
$rExpression = "eval(parse(file=`"$relativeScript`", encoding=`"UTF-8`"), envir=.GlobalEnv)"
if ($null -ne $psi.ArgumentList) {
  $psi.ArgumentList.Add("--encoding=UTF-8")
  $psi.ArgumentList.Add("-e")
  $psi.ArgumentList.Add($rExpression)
} else {
  $escapedExpression = $rExpression.Replace('"', '\"')
  $psi.Arguments = "--encoding=UTF-8 -e `"$escapedExpression`""
}

$process = [System.Diagnostics.Process]::new()
$process.StartInfo = $psi

$started = $process.Start()
if (-not $started) {
  throw "Failed to start Rscript."
}

$stdoutTask = $process.StandardOutput.ReadToEndAsync()
$stderrTask = $process.StandardError.ReadToEndAsync()
$process.WaitForExit()
$stdout = $stdoutTask.Result
$stderr = $stderrTask.Result
$exitCode = $process.ExitCode

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add("===== Rscript invocation =====")
$lines.Add("Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$lines.Add("WorkDir: $resolvedWorkDir")
$lines.Add("Script: $resolvedScript")
$lines.Add("Rscript: $resolvedRscript")
$lines.Add("")
$lines.Add("===== stdout =====")
$lines.Add($stdout.TrimEnd())
$lines.Add("")
$lines.Add("===== stderr =====")
$lines.Add($stderr.TrimEnd())
$lines.Add("")
$lines.Add("===== Rscript status =====")
$lines.Add("Rscript exit code: $exitCode")

[System.IO.File]::WriteAllText($logPath, ($lines -join [Environment]::NewLine), [System.Text.UTF8Encoding]::new($false))

if ($exitCode -ne 0) {
  Write-Error "Rscript failed with exit code $exitCode. Log: $logPath"
  exit $exitCode
}

Write-Output "Rscript completed successfully."
Write-Output "Log: $logPath"
exit 0
