"""Bind actual browser shader observations without publishing source/telemetry.

Only new output is written. Original pixels, shader texts and API observations
remain private and hash-bound; no Native, browser, server or compiler is run.
"""
import hashlib
import json
from array import array
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = 'artifacts/th14/stage-angle-shader-diagnostic-oct14/'
DOC = ROOT / 'docs/porting/th14-stage-angle-shaders-observed-oct14.json'
SHA = lambda data: hashlib.sha256(data).hexdigest()
CANON = lambda data: SHA(json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())
PINS = {
    ART + 'diagnostic-manifest.json': '44aca92ff73265e938758d1f8e7c2725a18858e37d14e8517c2b7076c0e7961f',
    ART + 'workspace-descriptor.json': '26b31b5d2b7159bce273524e1c1e0dfe9ff2779d6444a787b55430fb5b6ce94d',
    ART + 'capture/color-report.json': 'ea6d8982efe64100b347b80cb873684ae1ab0b806ce66bdaea79bc2fccca97fd',
    ART + 'capture/uv-report.json': '55506bafbab213af9be33a8de662ce708631194977c4ae83ab633f69bb1df93c',
    'tools/th14-serve-workspace-diagnostics.mjs': '7f18a9cc7fc3be0516135a0cee23af70c64050394cfffd2ae35169fb06ae8a48',
    'tools/th14-stage-angle-shader-diagnostic-oct14.html': '876afbc8d746570dd6b7d9bf2857020962bb7cfa72c86ee2a7a5f3434cfed200',
    'tools/th14-stage-angle-shader-observer.mjs': '275e955a1066c94072d1544fb33a251c1cb3cf073ec0bab6cce671b94c8f8dac',
    'docs/porting/th14-workspace-diagnostics-gateway-prepared-oct14.json': 'c761fa30fe714eee6478ef7a36060ee65acf7b1d60d494503368deee09024379',
    'docs/porting/th14-stage-production-clip-current-source-verified-oct14.json': '39627e32290477fe3c6a5ca7e815847257325600e3ee6ad8b60f86e775303b2e',
}


def main():
    assert not DOC.exists(), 'Completed observation receipt remains immutable'
    bindings = {}
    def bind(name, expected=None):
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT)
        raw = path.read_bytes()
        row = dict(bytes=len(raw), sha256=SHA(raw))
        if isinstance(expected, str):
            assert row['sha256'] == expected, name
        elif expected is not None:
            assert row == expected, name
        if name in bindings:
            assert bindings[name] == row
        bindings[name] = row
        return raw
    def load(name):
        return json.loads(bind(name, PINS.get(name)))
    for name, expected in PINS.items():
        bind(name, expected)
    manifest = load(ART + 'diagnostic-manifest.json')
    descriptor = load(ART + 'workspace-descriptor.json')
    prepared = load('docs/porting/th14-workspace-diagnostics-gateway-prepared-oct14.json')
    baseline = load('docs/porting/th14-stage-production-clip-current-source-verified-oct14.json')
    assert manifest['prepared'] and not manifest['observedShaders'] and not manifest['executed']
    assert prepared['prepared'] and not prepared['serverStarted'] and not prepared['graphicsExecuted']
    assert descriptor['slug'] == 'stage-angle-shaders' and prepared['mount'] == '/checks/stage-angle-shaders/'
    assert prepared['descriptor']['sha256'] == PINS[ART + 'workspace-descriptor.json']
    assert prepared['toolSha256'] == PINS['tools/th14-serve-workspace-diagnostics.mjs']
    assert prepared['getInventory'] == descriptor['get'] and prepared['postInventory'] == descriptor['post']
    assert len(descriptor['get']) == len(manifest['getRoutes']) == 54 and len(descriptor['post']) == 2
    gets = {row['name']: row for row in descriptor['get']}
    for name, row in gets.items():
        bind(row['path'], {key: row[key] for key in ('bytes', 'sha256')})
        if name:
            assert {key: row[key] for key in ('path', 'bytes', 'sha256')} == manifest['getRoutes']['/' + name]
    original_html = bind(ART + 'index.html', manifest['getRoutes']['/']['sha256'])
    adapted_html = bind(gets['']['path'], PINS[gets['']['path']])
    assert adapted_html == original_html.replace(b'Every portable buffer is archived.',
        b'Portable buffers are read for comparison; this shader diagnostic does not archive them.')
    assert not baseline['completeGame'] and not baseline['nativeEquivalent']

    source_names = ['Renderer.cpp', 'Renderer.hpp', 'GraphicsState.hpp', 'Shaders.hpp', 'AlphaConversion.hpp', 'ResampleShader.hpp']
    production = {}
    reports = {mode: load(ART + 'capture/' + mode + '-report.json') for mode in ('color', 'uv')}
    builds = {mode: json.loads(bind(ART + mode + '/build.json', manifest['getRoutes']['/' + mode + '/build.json']['sha256'])) for mode in reports}
    for name in source_names:
        path = 'runtimes/th12/portable/sdl/' + name
        actual = bind(path, baseline['sourceBindings'][path])
        production[path] = bindings[path]
        for mode, build in builds.items():
            compiled = bind(ART + mode + '/' + name, build['sources'][name])
            assert build['sourceBindings'][path] == bindings[path]
            expected = actual.replace(b'outColor=c;', b'outColor=vec4(vUV,0.0,1.0);') if mode == 'uv' and name == 'Shaders.hpp' else actual
            assert compiled == expected, (mode, name)
    for mode, report in reports.items():
        build = builds[mode]
        assert report['mode'] == mode and report['frames'] == len(report['reports']) == (21 if mode == 'color' else 23)
        assert report['diagnosticOnly'] and not report['completeGame'] and not report['nativeEquivalent']
        assert not report['fullPixelsArchived'] and not report['vertexSourceChanged']
        assert report['fragmentUVOverride'] == (mode == 'uv')
        assert report['wasmSha256'] == build['wasmSha256'] == gets[mode + '/gpu.wasm']['sha256']
        assert build['loaderSha256'] == gets[mode + '/gpu.mjs']['sha256']
        assert report['sourceBindings'] == build['sourceBindings']
        assert report['shaderObserverSha256'] == gets['observer.mjs']['sha256'] == PINS['tools/th14-stage-angle-shader-observer.mjs']
        assert '-O2' in build['flags'] and '-ffp-contract=off' in build['flags'] and '-DPORT_TITLE=14' in build['flags']
        for name, row in build['sources'].items():
            bind(ART + mode + '/' + name, row)
    color, uv = reports['color'], reports['uv']
    assert sum(row['differentChannels'] for row in color['reports']) == color['differentChannels']
    assert max(row['maxDelta'] for row in color['reports']) == color['maxDelta']
    for report in reports.values():
        assert sum(row['portableSha256'] == row['nativeSha256'] for row in report['reports']) == report['exactFullBuffers']
        assert report['strictPixelsEqual'] == (report['exactFullBuffers'] == report['frames'])
    assert sum(sample['differentWords'] for row in uv['reports'] for sample in row['samples']) == uv['differentSampleWords']
    native_cases = json.loads(bind(gets['uv-cases.json']['path'], gets['uv-cases.json']['sha256']))['cases']
    native_color = json.loads(bind(gets['native-color.json']['path'], gets['native-color.json']['sha256']))['frames']
    summary_rows, hash_comparison = {}, {}
    for mode, report in reports.items():
        rows = report['reports']; old_rows = baseline[mode]['rows']; refs = native_color if mode == 'color' else native_cases
        assert len(rows) == len(old_rows) == len(refs)
        summaries, changed = [], []
        for index, (row, old, reference) in enumerate(zip(rows, old_rows, refs)):
            assert row['index'] == old['index'] == index
            assert (row['stage'], row['frame']) == (old['stage'], old['frame']) == (reference['stage'], reference['frame'])
            assert row['nativeSha256'] == old['nativeSha256'] == reference['sha256' if mode == 'color' else 'nativeSha256']
            assert row['strictFullBufferHashEqual'] == (row['portableSha256'] == row['nativeSha256'])
            if row['portableSha256'] != old['portableSha256']:
                changed.append(index)
            keep = ['index', 'stage', 'frame', 'originalDrawIndex', 'role', 'portableSha256', 'nativeSha256', 'bytes', 'strictFullBufferHashEqual']
            keep += ['differentChannels', 'maxDelta'] if mode == 'color' else ['portableCovered', 'nativeFullBytesAvailable', 'nativeCovered', 'coverageDifferences', 'differentUVOnCommonCoverage', 'maxUVDelta']
            summaries.append({key: row[key] for key in keep if key in row})
            if mode == 'uv':
                assert row['originalDrawIndex'] == old['draw'] == reference['originalDrawIndex']
                summaries[-1]['selectedSampleWordsDifferent'] = sum(s['differentWords'] for s in row['samples'])
                summaries[-1]['sampleArraySha256'] = CANON(row['samples'])
        summary_rows[mode] = summaries
        hash_comparison[mode] = dict(comparedRows=len(rows), changedPortableHashIndices=changed, allPortableHashesMatchHistoricalPhysicalCapture=not changed, nativeReferenceHashesUnchanged=True)

    full_controls = [row for row in uv['reports'] if row['nativeFullBytesAvailable']]
    assert len(full_controls) == 7
    full_recompute = []
    for row in full_controls:
        native_get = gets[f'native-full/{row["index"]:03d}']
        assert native_get['sha256'] == row['nativeSha256']
        native_raw = bind(native_get['path'], {key: native_get[key] for key in ('bytes', 'sha256')})
        old_path = f'artifacts/th14/stage-production-clip-no-finite-guard-oct14/uv/capture/frame-{row["index"]:03d}.rgba32f'
        # This browser run archives hashes, not buffers. A historical byte buffer
        # can reproduce its output only if its pinned hash equals the new hash.
        pinned = baseline['evidence'][old_path]
        if pinned['sha256'] != row['portableSha256']:
            full_recompute.append(dict(index=row['index'], historicalByteRecomputeAvailable=False, newPortableBufferArchived=False))
            continue
        portable_raw = bind(old_path, pinned)
        assert len(native_raw) == len(portable_raw) == row['bytes'] == 640 * 480 * 16
        nw, pw = array('I'), array('I'); nw.frombytes(native_raw); pw.frombytes(portable_raw)
        difference = sum(a != b for a, b in zip(nw, pw))
        coverage = sum(bool(nw[j + 3] & 0x7fffffff) != bool(pw[j + 3] & 0x7fffffff) for j in range(0, len(nw), 4))
        common_uv = sum((nw[j] != pw[j]) + (nw[j + 1] != pw[j + 1]) for j in range(0, len(nw), 4) if nw[j + 3] & 0x7fffffff and pw[j + 3] & 0x7fffffff)
        assert coverage == row['coverageDifferences'] and common_uv == row['differentUVOnCommonCoverage']
        full_recompute.append(dict(index=row['index'], historicalByteRecomputeAvailable=True, newPortableBufferArchived=False,
            newPortableHashMatchesPinnedHistoricalBytes=True, allRGBA32FWordDifferences=difference, coverageDifferences=coverage, differentUVOnCommonCoverage=common_uv,
            nativeFullBytes=len(native_raw), nativeSha256=row['nativeSha256'], portableSha256=row['portableSha256']))

    shader_summary = {}
    for mode, report in reports.items():
        backend = report['shaderBackend']; contexts = backend['contexts']; reduced_contexts = []
        assert backend['readsActualAttachedShaders'] and backend['extensionUnavailableIsNegative']
        for context in contexts:
            programs, shader_rows, statuses = context['programs'], [], Counter()
            assert len(programs) == context['linkCalls']
            assert len(context['programEvents']) == context['useCalls'] + context['drawCalls']
            assert len({p['programId'] for p in programs}) == len(programs)
            for program in programs:
                for shader in program['shaders']:
                    item = dict(programId=program['programId'], linkOrdinal=program['linkOrdinal'], programLinked=program['linked'], type=shader['typeName'], compiled=shader['compiled'], translatedStatus=shader['translatedStatus'])
                    statuses[shader['translatedStatus']] += 1
                    for field in ['submittedSource', 'actualApiSource', 'translatedSource']:
                        text = shader[field]; assert text is None or isinstance(text, str)
                        raw = None if text is None else text.encode()
                        hashed = None if raw is None else SHA(raw)
                        assert hashed == shader[field + 'Sha256']
                        item[field + 'Sha256'] = hashed; item[field + 'Utf8Bytes'] = None if raw is None else len(raw)
                    status = shader['translatedStatus']
                    if status == 'returned':
                        assert context['gpu']['debugShadersExtensionAvailable'] and shader['translatedSource']
                    elif status == 'extension_unavailable':
                        assert not context['gpu']['debugShadersExtensionAvailable'] and shader['translatedSource'] is None
                    elif status == 'empty_translation':
                        assert shader['translatedSource'] == ''
                    else:
                        assert status == 'query_failed' and shader['translatedSource'] is None
                    log = shader['infoLog'] or ''
                    item.update(infoLogUtf8Bytes=len(log.encode()), infoLogSha256=SHA(log.encode()), infoLogNonempty=bool(log),
                                dynamicIndexingPerformanceWarning='dynamic indexing' in log.lower())
                    item['submittedSourceMatchesActualApiSource'] = shader['submittedSource'] == shader['actualApiSource']
                    shader_rows.append(item)
            gpu = context['gpu']; raw_gpu_hashes = {key: dict(utf8Bytes=len(value.encode()), sha256=SHA(value.encode())) for key, value in gpu.items() if isinstance(value, str)}
            renderer = gpu.get('unmaskedRenderer') or gpu.get('renderer') or ''
            family = 'ANGLE/D3D11' if 'ANGLE' in renderer and ('D3D11' in renderer or 'Direct3D11' in renderer) else 'Unclassified API-returned backend'
            errors = context['observerErrors']
            reduced_contexts.append(dict(id=context['id'], apiObservedBackendFamily=family, rawApiStringHashes=raw_gpu_hashes,
                debugShadersExtensionAvailable=gpu['debugShadersExtensionAvailable'], actualShaderSourcesObserved=context['actualShaderSourcesObserved'], translatedShadersObserved=context['translatedShadersObserved'],
                programs=len(programs), shaderRecords=len(shader_rows), linkCalls=context['linkCalls'], useCalls=context['useCalls'], drawCalls=context['drawCalls'],
                linkedProgramFailures=sum(not p['linked'] for p in programs), shaderCompileFailures=sum(not s['compiled'] for s in shader_rows),
                shaderInfoLogNonemptyCount=sum(s['infoLogNonempty'] for s in shader_rows), dynamicIndexingPerformanceWarnings=sum(s['dynamicIndexingPerformanceWarning'] for s in shader_rows),
                translationStatusCounts=dict(statuses), observerErrorCount=len(errors), observerErrorArraySha256=CANON(errors),
                programEventsCount=len(context['programEvents']), programEventsArraySha256=CANON(context['programEvents']),
                shaderRecordsHashOnly=shader_rows))
        shader_summary[mode] = dict(actualContexts=len(contexts), contexts=reduced_contexts, observerErrorsRetainedInPrivateReports=True,
            observerInstrumentedVisibleFixtureOnly=True, actualProductionGameplayShaderObservation=False)

    browser_files = ['color-browser.jpg', 'color-browser-ax.txt', 'uv-browser.jpg', 'uv-browser-ax.txt', 'browser-console.json']
    for name in browser_files:
        raw = bind(ART + name)
        if name.endswith('.jpg'):
            assert raw[:3] == bytes.fromhex('ffd8ff')
        if name.endswith('-ax.txt'):
            text = raw.decode()
            assert 'localhost:8208/checks/stage-angle-shaders/' in text
            expected = '3/21' if name.startswith('color') else '20/23'
            assert 'Completed · ' + expected + ' exact full buffers' in text
    console = json.loads(bind(ART + 'browser-console.json'))
    errors = [row for row in console if row.get('level') == 'error']
    warnings = [row for row in console if row.get('level') in ['warn', 'warning']]
    output = dict(diagnosticObservationEvidenceVerified=True, completeGame=False, nativeEquivalent=False, productionChanged=False,
        currentSixProductionSourcesVerified=True, sourceBindings=production, compiledColorFilesEqualCurrent=True, compiledUVOnlyFragmentOutputOverride=True,
        actualShaderApiObservations=shader_summary, rawShaderTextsPublished=False, rawGpuTelemetryPublished=False,
        privateCaptureReportsRetained=True, newPortableFullBuffersArchived=False, newPortableBuffersReadAndHashedByBrowserFixture=True,
        color=dict(frames=color['frames'], exactFullBuffers=color['exactFullBuffers'], differentChannels=color['differentChannels'], maxDelta=color['maxDelta'], strictPixelsEqual=color['strictPixelsEqual'], rendererStatistics=color['rendererStatistics'], rows=summary_rows['color']),
        uv=dict(cases=uv['frames'], exactFullBufferHashes=uv['exactFullBuffers'], selectedSampleWordsDifferent=uv['differentSampleWords'], nativeFullPixelCases=7, nativeHashAndSelectedSampleOnlyCases=16,
            reportedCommonCoverageUVWordDifferences=sum(r['differentUVOnCommonCoverage'] for r in full_controls), reportedFullControlCoverageDifferences=sum(r['coverageDifferences'] for r in full_controls),
            nativeFullBytes=7 * 640 * 480 * 16, strictAllHashesEqual=uv['strictPixelsEqual'], rendererStatistics=uv['rendererStatistics'], rows=summary_rows['uv'],
            historicalCompleteByteRecomputationsTiedByIdenticalNewHashes=full_recompute),
        historicalPhysicalHashComparison=hash_comparison,
        historicalBaselineMetrics=dict(colorDifferentChannels=baseline['color']['differentChannels'], nativeFullRGBA32FWordDifferences=baseline['uv']['allNativeFullCaseWordDifferences'], nativeFullCases=baseline['uv']['nativeFullBufferCases']),
        browser=dict(origin='http://localhost:8208', mount=prepared['mount'], rootReportedGatewaySession=55555, rootReportedVisibleLinkAndRuns=True,
            consoleRows=len(console), consoleErrors=len(errors), consoleWarnings=len(warnings), consoleArraySha256=CANON(console),
            generatedTitleInheritedTouhou10=True, titleOrFrozenSourceChanged=False, completeInputLedgerCaptured=False),
        bindings=bindings, bindingCount=len(bindings), toolSha256=SHA(Path(__file__).read_bytes()),
        scope='Actual ROOT-visible Color21 and UV23 runs through the pinned fixed8208 gateway. Attached shader API and nonempty debug-extension translations are reported as actual observed strings, hash/length/status only; vendor/model/device IDs/UA and full source text remain private. Compile info logs, observer failures and unavailable/empty/query-failed translations are retained as negative statistics rather than guessed backend programs. Diagnostic color consumes the exact six current production files; UV changes only fragment output. All44 portable buffers were read/hashed in this run but not newly archived. Seven Native UV full inputs are physically hash-bound; sixteen other UV cases have Native hashes and selected samples only. Where new hashes equal archived historical portable bytes, the producer separately recomputes those seven complete byte comparisons and labels their historical custody. Reported Color880/UV5292/coverage0 may remain failed; no new corpus or production arithmetic change is introduced. ROOT screenshots/AX and the fetched console snapshot are bound; inherited Touhou10 browser title remains unchanged. This is a diagnostic frontend observation, not a long gameplay, full-screen Native FFP, audio/loading/all-mode or whole-game1:1 claim.')
    DOC.write_bytes((json.dumps(output, indent=2) + '\n').encode())
    print(json.dumps(dict(report=str(DOC), sha256=SHA(DOC.read_bytes()), bindings=len(bindings), colorChannels=color['differentChannels'],
        uvCommonWords=output['uv']['reportedCommonCoverageUVWordDifferences'], fullCoverageDifferences=output['uv']['reportedFullControlCoverageDifferences'],
        colorShaderRecords=sum(c['shaderRecords'] for c in shader_summary['color']['contexts']), uvShaderRecords=sum(c['shaderRecords'] for c in shader_summary['uv']['contexts']))))


if __name__ == '__main__':
    main()
