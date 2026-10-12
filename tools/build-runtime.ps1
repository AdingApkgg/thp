# Build one Runtime's SDL3 / WebGL2 WASM with this workspace's toolchain.
#
# Usage:
#   pwsh -NoProfile -File tools/build-runtime.ps1 -Runtime th12
#   pwsh -NoProfile -File tools/build-runtime.ps1 -Runtime th12 -Release
#
# Why this wrapper exists (both conditions are required, each is a documented quirk):
#   1. `python` on PATH must be >= 3.10; this machine's default is 3.7.
#   2. clang fails with "unable to make temporary file: permission denied" when it
#      writes intermediates under the default %TEMP%; a workspace temp dir works.
param(
  [Parameter(Mandatory = $true)][string]$Runtime,
  [switch]$Release,
  [switch]$Viewer
)

$ErrorActionPreference = 'Stop'
$ws = Split-Path $PSScriptRoot -Parent
$rt = Join-Path $ws "runtimes\$Runtime"
if (-not (Test-Path $rt)) { throw "Unknown runtime: $Runtime" }

$python = 'C:\Users\APKGG\AppData\Local\Programs\Python\Python313\python.exe'
if (-not (Test-Path $python)) { throw "Python >= 3.10 not found at $python" }

$tmp = Join-Path $ws 'tools\tmp'
New-Item -ItemType Directory -Force -Path $tmp | Out-Null

$env:TEMP = $tmp
$env:TMP = $tmp
$env:TMPDIR = $tmp
$env:PATH = "$(Split-Path $python -Parent);$ws\tools\emsdk\node\24.19.0_64bit;$env:PATH"

$node = Join-Path $ws 'tools\emsdk\node\24.19.0_64bit\node.exe'
$web  = Join-Path $rt "${Runtime}_web"
$args = @((Join-Path $web 'scripts\build-sdl.mjs'))
if ($Release) { $args += '--release' }

Push-Location $rt
try {
  & $node @args
  if ($LASTEXITCODE -ne 0) { throw "Runtime build failed with exit code $LASTEXITCODE" }
}
finally {
  Pop-Location
}
