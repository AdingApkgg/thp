# Boot one title's artifact through the parameterised builder and the title-aware server.
#   pwsh -File tools/boot-title.ps1 13                       (one bare title)
#   pwsh -File tools/boot-title.ps1 -Titles 13,18           (several)
#   pwsh -File tools/boot-title.ps1 17 -Wait 180000 -Suffix=-long
# The window is the reach, and the reach is the wall of sections 387 and 388, so the window is a
# parameter: the default stays at the 60 s the per-round records use, and a longer run writes its
# own record (with the suffix) beside it.
# The URL carries a per-run query. Section 390 measured why: the same freshly built artifact booted
# at the plain URL behaved as the code before the round's edit (a four-name demo countdown), and the
# same artifact booted at "?run=<ticks>" played the new list and logged the record's own stage. The
# same URL means the same runtime as far as the page's loader is concerned, so a boot that is meant
# to test what was just built has to name a runtime that is just built.
# The titles are the first positional, as a plain array: with ValueFromRemainingArguments the
# second bare argument went to -Wait instead of the list (`13 18` measured titles=[13] wait=18, and
# an empty list boots nothing and still exits 0). Several titles are one comma list, and a suffix
# whose value starts with a dash needs the `-Suffix=-long` form.
param([string[]]$Titles, [int]$Wait = 60000, [string]$Suffix = "")
$node = "H:\code\thp\tools\emsdk\node\24.19.0_64bit\node.exe"
$web = "H:\code\thp\runtimes\th12\th12_web"
foreach ($t in $Titles) {
    Write-Host "=== boot th$t, window ${Wait} ms$Suffix ==="
    $env:TH_OUTPUT = "artifacts/sdl3-th$t"
    $env:TH_TITLE = "th$t"
    # the title's own runtime directory declares its archive and holds its converted music
    $env:TH_DATA_ROOT = "H:\code\thp\runtimes\th$t"
    $env:TH_ASSET_ROOT = "H:\code\thp\runtimes\th$t\th${t}_web\assets"
    $env:TH12_PORT = "8113"
    $log = "H:\code\thp\artifacts\th12\server-th$t.log"
    $srv = Start-Process -FilePath $node -ArgumentList 'scripts\serve-th12.mjs' -WorkingDirectory $web -PassThru -WindowStyle Hidden -RedirectStandardOutput $log
    Start-Sleep -Seconds 3
    $stamp = [DateTime]::Now.Ticks
    Push-Location H:\code\thp
    & $node tools\browser-proof.mjs --url "http://127.0.0.1:8113/?run=$stamp" --out "artifacts/th12/browser-th${t}${Suffix}" --shots 1 --wait $Wait --sample 500 --click '#start' --expect-start --expect-stage 1 --record "docs/porting/browser-run-th${t}${Suffix}.json" 2>&1 | Out-Null
    Pop-Location
    Stop-Process -Id $srv.Id -Force -ErrorAction SilentlyContinue
    py -3 "tools\read-boot.py" "docs/porting/browser-run-th${t}${Suffix}.json" "th$t$Suffix"
}
