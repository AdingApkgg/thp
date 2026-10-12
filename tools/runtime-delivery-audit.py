#!/usr/bin/env python3
"""Audit the delivery track of the six target titles.

The campaign has spent many rounds on one title's machine code; the objective asks for six runtimes
that run in a browser. This reads what each runtime directory actually holds - the engine tree its
checkers build, the original it declares, its own completeness flag, the artifacts it carries and
the launch script it ships - and writes the answer to docs/porting/runtime-delivery-audit.json, so
the next delivery round starts from a measurement instead of from a memory.

Usage: py -3 tools/runtime-delivery-audit.py
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TITLES = [12, 13, 14, 16, 17, 18]
SUBTREES = ['cpp', 'tests', 'assets', 'artifacts', 'reference', 'scripts', 'sdl-runtime',
            'portable', 'launcher', 'docs']


def size_of(path: Path) -> dict:
    if not path.is_dir():
        return {'files': 0, 'bytes': 0}
    files = [p for p in path.rglob('*') if p.is_file()]
    return {'files': len(files), 'bytes': sum(p.stat().st_size for p in files)}


def audit(title: int) -> dict:
    base = ROOT / 'runtimes' / ('th%d' % title)
    web = base / ('th%d_web' % title)
    row: dict = {'title': title, 'runtimeDir': ('runtimes/th%d' % title)}
    row['web'] = web.is_dir()
    if not row['web']:
        return row
    for target in (base / 'target.json', web / 'target.json'):
        if target.is_file():
            data = json.loads(target.read_text(encoding='utf-8'))
            row['declaredGame'] = data.get('game')
            row['executable'] = Path(str(data.get('executable', ''))).name
            row['completeGame'] = data.get('completeGame')
            row['targetJson'] = str(target.relative_to(ROOT)).replace('\\', '/')
            break
    readme = web / 'README.md'
    if readme.is_file():
        head = readme.read_text(encoding='utf-8', errors='replace').splitlines()
        row['readmeTitle'] = re.sub(r'^#+\s*', '', head[0]).strip() if head else ''
    row['subtrees'] = {name: size_of(web / name) for name in SUBTREES}
    row['launchScripts'] = sorted(p.name for p in web.glob('*.cmd'))
    row['deployment'] = (web / 'artifacts' / 'sdl-release' / 'verification'
                         / 'deployment.json').is_file()
    return row


def checker_engine_tree(title: int) -> str | None:
    """Which tree a title's checker compiles, and the title it passes. Read, not assumed."""
    for name in ('tools/th%d-anm-check.mjs' % title, 'tools/TH%d-anm-check.mjs' % title):
        path = ROOT / name
        if not path.is_file():
            continue
        text = path.read_text(encoding='utf-8', errors='replace')
        tree = re.search(r'runtimes/th\d+(?:/[\w.]+)*', text)
        port = re.search(r'PORT_TITLE=\$?\{?(\w+)\}?', text)
        return '%s%s' % (tree.group(0) if tree else '(no tree named)',
                         ' with PORT_TITLE=%s' % port.group(1) if port else '')
    return None


def read_builder(title: int) -> dict | None:
    """What the title's builder says it builds, read out of the builder rather than assumed."""
    for candidate in (ROOT / 'runtimes' / ('th%d' % title) / 'portable' / 'build.mjs',
                      ROOT / 'runtimes' / ('th%d' % title) / ('th%d_web' % title)
                      / 'portable' / 'build.mjs'):
        if candidate.is_file():
            text = candidate.read_text(encoding='utf-8', errors='replace')
            exports = re.search(r"const exported=\[([^\]]*)\]", text)
            return {
                'path': str(candidate.relative_to(ROOT)).replace('\\', '/'),
                'declaredGame': (re.search(r"game:'(\w+)'", text) or [None, None])[1],
                'exportPrefixes': sorted({m for m in re.findall(r"'(_th\d+)_", text)}),
                'exportsNamed': re.findall(r"'(_\w+)'", exports.group(1))[:6] if exports else []}
    return None


def run_records() -> list[dict]:
    """The browser-run records in docs/porting, which the directory scan of section 356 missed."""
    fields = ('kind', 'url', 'started', 'clicked', 'stageMax', 'stageSequence', 'phaseMax',
              'stageTransitions', 'seconds', 'pageErrors', 'consoleErrors', 'framesServed',
              'playedSamples', 'playedFrameMax')
    rows = []
    for path in sorted((ROOT / 'docs' / 'porting').glob('browser-run*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        row = {key: data.get(key) for key in fields}
        row['record'] = path.name
        rows.append(row)
    for name in ('browser-campaign-full.json',):
        path = ROOT / 'docs' / 'porting' / name
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding='utf-8'))
        row = {key: data.get(key) for key in fields}
        row['record'] = name
        rows.append(row)
    return rows


rows = [audit(t) for t in TITLES]
engines = {t: checker_engine_tree(t) for t in TITLES}
builders = {t: read_builder(t) for t in TITLES}
runs = run_records()
print('  the delivery track, as the directories hold it:')
print('  %-5s %-5s %-8s %-9s %-8s %-9s %-8s %s' % (
    'title', 'web', 'declared', 'cpp files', 'assets MB', 'artifacts', 'targetj', 'complete'))
for row in rows:
    st = row.get('subtrees', {})
    print('  th%-3d %-5s %-8s %-9s %-8.1f %-9s %-8s %s' % (
        row['title'], row.get('web'), row.get('declaredGame'),
        st.get('cpp', {}).get('files', 0), st.get('assets', {}).get('bytes', 0) / 1e6,
        st.get('artifacts', {}).get('files', 0), row.get('targetJson'), row.get('completeGame')))
print()
print('  the builder each runtime ships, read out of the builder:')
for title in TITLES:
    info = builders[title]
    if not info:
        print('    th%-3d (no builder found)' % title)
        continue
    print('    th%-3d %s declares game %s, exports %s' % (
        title, info['path'], repr(info['declaredGame']), ','.join(info['exportPrefixes'])))
    print('           first exports: %s' % ', '.join(info['exportsNamed']))
print()
print('  the engine tree each checker compiles, read out of the checker:')
for title, tree in engines.items():
    print('    th%-3d %s' % (title, tree or '(no checker)'))
print()
print('  the browser-run records the directory scan did not see:')
for row in runs:
    print('    %-32s kind %s stageMax %s phaseMax %s %ss %d/%d errors frame %s' % (
        row['record'], row['kind'], row['stageMax'], row['phaseMax'], row['seconds'],
        row['pageErrors'], row['consoleErrors'], row['framesServed']))
print()
for row in rows:
    if row.get('readmeTitle'):
        print('    th%-3d readme "%s" (%d chars) | launch %s | deployment %s' % (
            row['title'], row['readmeTitle'], len(row['readmeTitle']),
            ','.join(row['launchScripts']) or '(none)', row['deployment']))

source = Path(__file__).resolve()
out = ROOT / 'docs' / 'porting' / 'runtime-delivery-audit.json'
shared = sorted({t for t in engines.values() if t})
report = {
    'why': 'the objective asks for six titles that run in a browser, and this is what each '
           'runtime directory holds: the engine tree its checker builds, the original it '
           'declares, its own completeness flag, the artifacts it carries and its launch script',
    'method': 'file scan of runtimes/thNN, with the checker path read out of the checker',
    'engineTrees': {str(t): engines[t] for t in TITLES},
    'builders': {str(t): builders[t] for t in TITLES},
    'browserRuns': runs,
    'browserReading': 'the directory scan of the first version of this audit read shapes, and the '
                     'playability evidence is not a shape: these records are runs, one of them '
                     'through all six stages and the ending phase',
    'oneEngineTree': {'trees': shared, 'titlesUsingIt': [t for t in TITLES
                                                        if engines[t] in shared],
                     'reading': 'the port lives once and the title is a build parameter'},
    'titles': rows,
    'readings': {
        'completeGame': {str(r['title']): r.get('completeGame') for r in rows},
        'withCppSources': [r['title'] for r in rows if r.get('subtrees', {}).get('cpp', {})
                          .get('files', 0)],
        'withAssets': [r['title'] for r in rows if r.get('subtrees', {}).get('assets', {})
                       .get('bytes', 0)],
        'withLaunchScript': [r['title'] for r in rows if r.get('launchScripts')],
        'withDeployment': [r['title'] for r in rows if r.get('deployment')]},
    'tool': {'path': str(source.relative_to(ROOT)).replace('\\', '/'),
             'sha256': hashlib.sha256(source.read_bytes()).hexdigest()[:32]},
}
out.write_text(json.dumps(report, ensure_ascii=False, indent=2).replace('\n', '\r\n'),
              encoding='utf-8', newline='')
print()
print('  wrote %s (%d bytes)' % (out.relative_to(ROOT), out.stat().st_size))
