#requires -Version 5
# Bootstrap the Emscripten (emsdk) toolchain used by every Web Runtime in this workspace.
$ErrorActionPreference = 'Stop'

$ws       = 'H:\code\thp'
$emsdkDir = Join-Path $ws 'tools\emsdk'
$py       = 'C:\Users\APKGG\AppData\Local\Programs\Python\Python313\python.exe'

if (-not (Test-Path $py)) { $py = 'python' }
$env:EMSDK_PYTHON = $py
# emsdk.bat resolves `python` from PATH, so the >=3.10 interpreter must win there too.
$pyDir = Split-Path $py -Parent
$env:PATH = "$pyDir;$env:PATH"
Write-Host "python in use: $((Get-Command python).Source)"

if (-not (Test-Path (Join-Path $emsdkDir 'emsdk.bat'))) {
    Write-Host "== cloning emsdk =="
    git clone --depth 1 https://github.com/emscripten-core/emsdk.git $emsdkDir
    if ($LASTEXITCODE -ne 0) { throw "emsdk clone failed" }
}

Push-Location $emsdkDir
try {
    Write-Host "== emsdk install latest =="
    & cmd /c "emsdk.bat install latest" 2>&1 | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0) { throw "emsdk install failed ($LASTEXITCODE)" }

    Write-Host "== emsdk activate latest =="
    & cmd /c "emsdk.bat activate latest" 2>&1 | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0) { throw "emsdk activate failed ($LASTEXITCODE)" }
}
finally {
    Pop-Location
}

Write-Host "== done =="
