"""Qualify actual Application no-BGM startup/Continue and required-media errors."""
from pathlib import Path
import hashlib
import json

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/no-music-startup-nov13'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_bytes())


def main():
    changed = 'runtimes/th12/th12_web/cpp/sdl/AudioDevice.cpp'
    before = load(H / 'component-before/build.json')
    after = load(H / 'component-after/build.json')
    assert sha(H / 'AudioDevice.before.cpp') == before['sourceBindingsByMode']['candidate'][changed]
    for n, v in {**after['sourceBindingsByMode']['candidate'], **after['objectBindings']}.items():
        assert sha(R / n) == v, n
    reports = {}
    names = ['before-off-empty', 'after-off-empty', 'after-on-real', 'after-on-empty', 'after-on-corrupt']
    for name in names:
        folder = H / name
        j = load(folder / 'report.json')
        assert j['terminal'] and j['closed'] and j['retired'] and not j['errors']
        assert j['driverSha256'] == sha(folder / 'executed-driver.mjs')
        assert j['sourceWasmSha256'] == sha(H / ('component-before' if name.startswith('before') else 'component-after') / 'candidate.wasm')
        assert all(w['closed'] and w['exitCode'] == 0 for w in j['physicalWorkers'])
        p = load(folder / 'platform.json')
        assert not p['audibleOutput'] and not p['pendingTimers'] and not any(p['liveObjects'].values())
        reports[name] = j
    failed = reports['before-off-empty']
    assert not failed['passed'] and 'Unable to decode /music/th14_01.ogg' in failed['exception']
    fixed = reports['after-off-empty']
    assert fixed['passed'] and fixed['exception'] is None and fixed['phase'] == 'continued-without-music-files'
    assert not list((H / 'after-off-empty/music').iterdir())
    assert [x['name'] for x in fixed['checkpoints']] == ['title-ready', 'ordinary-gameplay', 'game-over', 'continued']
    assert [x['audio'] for x in fixed['checkpoints']] == [[0, 0], [0, 1], [0, 17], [0, 1]]
    assert fixed['checkpoints'][-1]['state'][19] == 2 and fixed['checkpoints'][-1]['state'][9] == 3
    assert reports['after-on-real']['passed'] and reports['after-on-real']['exception'] is None
    for name in ['after-on-empty', 'after-on-corrupt']:
        assert reports[name]['passed'] and reports[name]['expectedFailureVerified']
        assert 'Unable to decode /music/th14_01.ogg' in reports[name]['exception']
    browser = load(H / 'browser/build.json')
    assert browser['unitsRecompiled'] == 1 and browser['objectsVerifiedReused'] == 145
    for n, v in browser['objects'].items():
        assert sha(H / 'browser' / n) == v
    for n, v in browser['runtimeFiles'].items():
        p = H / 'browser' / n
        assert p.stat().st_size == v['bytes'] and sha(p) == v['sha256']
    assert sha(R / 'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp') == 'a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
    result = dict(passed=True, beforeNoBgmMissingFileFailureReproduced=True,
                  noBgmTitleOrdinaryDeathAndContinueVerified=True, noMusicFilesSupplied=True,
                  logicalCues=[0, 1, 17, 1], continuedLives=2, continuedBombs=3,
                  enabledValidVorbisTitlePassed=True, enabledMissingAndCorruptMusicStillRejected=True,
                  allMeasuredResourcesRetired=True, silent=True, productionUnitsRecompiled=1,
                  browserProductionObjectsReused=145, browserWasmSha256=browser['sha256'],
                  sourceBeforeSha256=sha(H / 'AudioDevice.before.cpp'), sourceAfterSha256=sha(R / changed),
                  reportHashes={n: sha(H / n / 'report.json') for n in names},
                  browserThisCaseAccepted=False, observedColdStartErrorUniquelyExplained=False,
                  otherTitlesOrWholeGameAccepted=False, completeGame=False)
    (H / 'qualified.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
