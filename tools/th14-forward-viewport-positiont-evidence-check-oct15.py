"""Read only the already executed POSITIONT experiment; retain its failure.

No fixture import, emulator, compiler, WASI, Native process, browser or GPU run.
Full word differences remain private; public output is bounded metadata.
"""
import hashlib
import json
import math
from pathlib import Path
import struct
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'artifacts/th14/stage-forward-viewport-positiont-prepared-oct15/native'
PRIVATE = ROOT/'artifacts/th14/stage-forward-viewport-positiont-observed-oct15'
OUT = ROOT/'docs/porting/th14-forward-viewport-positiont-observed-oct15.json'
BINDINGS = {}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path, digest=None, size=None):
    path = Path(path).resolve()
    raw = path.read_bytes()
    if digest:
        assert sha(raw) == digest, path
    if size is not None:
        assert len(raw) == size, path
    try:
        name = path.relative_to(ROOT).as_posix()
    except ValueError:
        name = path.as_posix()
    BINDINGS[name] = dict(path=name, bytes=len(raw), sha256=sha(raw))
    return raw


def pinned(row):
    return read(row['path'], row['sha256'], row['bytes'])


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as file:
        json.dump(value, file, indent=2)
        file.write('\n')
    data = path.read_bytes()
    return dict(path=path.relative_to(ROOT).as_posix(), bytes=len(data), sha256=sha(data))


def main():
    assert not OUT.exists() and not PRIVATE.exists(), 'New immutable receipts only'
    read(__file__)
    report = json.loads(read(BASE/'run-oct15/report.json',
        'a6c607a6892f20897a9f4a9c78b4790faae068aa3c181253c760ac80961a258b', 6637))
    inputs = json.loads(read(BASE/'inputs.json',
        '9e813010b2a04ba4dcf0921b8d5594151be81dc857e4aa0b1d3f39ad5f6b89b8', 93770))
    plan = json.loads(read(BASE/'plan.json',
        '170fcae3ebcfbd9353f56e849885f4e5d5ab4f1804ae344ccec8240edc8f47da', 5575))
    source = read(BASE/'fixture.py',
        '0d19e305e528c330fd54f30a3c16009dc14fdebd16a294ea08c5c26149757bef', 21862)
    assert source == pinned(plan['source']) == pinned(inputs['source'])
    assert report['sourceSha256'] == plan['source']['sha256']
    assert report['inputsSha256'] == plan['inputs']['sha256']
    assert pinned(plan['inputs']) == read(BASE/'inputs.json')
    assert len(inputs['bindings']) == 22
    for row in inputs['bindings']:
        pinned(row)
    bound = json.loads(read(BASE/'run-oct15/inputs-bound.json'))
    assert bound['inputs'] == inputs and bound['inputsSha256'] == report['inputsSha256']
    libraries = json.loads(read(BASE/'run-oct15/loaded-system-libraries.json'))
    assert libraries['paths'] == inputs['plannedLoadedSystemDlls']
    assert not libraries['visibleWindow'] and not libraries['audio']
    assert not libraries['compilerDllLoaded'] and not libraries['retailProcess']
    assert report['executed'] and report['executionCompleted']
    assert report['drawAttempts'] == report['successfulDrawCalls'] == report['drawCalls'] == 2
    assert report['nativeControlFullGate'] and report['aControlGate'] and report['positiontArmExecuted']
    assert report['finiteOutputGate'] and report['formatGate'] and report['comparisonEligible']
    assert not report['positiontFullMatchesFrozenNative'] and not report['declaredModelCompatibilitySupported']
    assert report['cleanupErrors'] == []
    assert [(x['method'], x['hresult']) for x in report['cleanupApiCalls']] == [
        ('EndScene', 0), ('UnlockRect', 0), ('EndScene', 0), ('UnlockRect', 0)]
    assert not any(x['deadlineReached'] for x in report['cleanupApiCalls'])
    for key in ['visibleWindow', 'audioPlayed', 'originalFfpClipCaptured', 'completeGame', 'nativeEquivalent', 'productionChanged']:
        assert report[key] is False
    for key in ['presentCalls', 'audioDevicesOpened', 'retailProcessesStarted', 'originalGameFilesWritten', 'newShaderAssemblies']:
        assert report[key] == 0
    assert len(report['rows']) == 2
    reference = pinned(inputs['nativeReference'])
    assert len(reference) == 4915200
    observed = []
    for row, label, filename in zip(report['rows'], ['a-control', 'b-positiont-model'], ['a-full.rgba32f', 'b-full.rgba32f']):
        assert row['label'] == label and row['path'] == filename
        assert row['bytes'] == row['fullBytes'] == 4915200 and row['sha256'] == row['fullSha256']
        assert (row['primitiveCount'], row['vertexCount'], row['stride']) == (78, 234, 24)
        observed.append(read(BASE/'run-oct15'/filename, row['sha256'], 4915200))
    assert observed[0] == reference and report['rows'][0]['differentWordsFromFrozenNative'] == 0
    b = observed[1]
    differences, pixel_differences, coverage = [], [], []
    channel_counts = [0]*4
    native_covered = model_covered = nonfinite = format_invalid = 0
    common_channel_counts, common_ulp_histograms = [0]*4, [Counter() for _ in range(4)]
    row_histogram = Counter()
    for pixel, (n, m) in enumerate(zip(struct.iter_unpack('<4I', reference), struct.iter_unpack('<4I', b))):
        x, y = pixel % 640, pixel//640
        nf, mf = struct.unpack('<4f', struct.pack('<4I', *n)), struct.unpack('<4f', struct.pack('<4I', *m))
        nc, mc = nf[3] != 0.0, mf[3] != 0.0
        native_covered += nc
        model_covered += mc
        nonfinite += not all(math.isfinite(value) for value in mf)
        format_invalid += (m[2:] != (0, 0x3f800000)) if mc else (m != (0, 0, 0, 0))
        if nc != mc:
            coverage.append(dict(pixel=pixel, x=x, y=y, nativeCovered=nc, modelCovered=mc,
                                 nativeWords=list(n), modelWords=list(m)))
        if n != m:
            pixel_differences.append(dict(pixel=pixel, x=x, y=y, nativeWords=list(n), modelWords=list(m), commonCovered=nc and mc))
            row_histogram[y] += 1
        for channel, (nv, mv) in enumerate(zip(n, m)):
            if nv != mv:
                channel_counts[channel] += 1
                differences.append(dict(wordIndex=pixel*4+channel, pixel=pixel, x=x, y=y, channel=channel,
                                        nativeWord=nv, modelWord=mv, commonCovered=nc and mc))
                if nc and mc:
                    common_channel_counts[channel] += 1
                    # Inputs/results in this selected geometry are nonnegative U/V.
                    if nf[channel] >= 0 and mf[channel] >= 0:
                        common_ulp_histograms[channel][abs(nv-mv)] += 1
    row = report['rows'][1]
    assert len(differences) == row['differentWordsFromFrozenNative'] == 1315
    assert channel_counts == row['differentWordsByChannel'] == [702, 612, 0, 1]
    assert model_covered == row['coveredPixels'] == 2439 and native_covered == 2438
    assert nonfinite == row['nonfinitePixelCount'] == 0 and format_invalid == row['formatInvalidPixelCount'] == 0
    assert 307200-model_covered == row['uncoveredPixels']
    assert len(coverage) == 1 and coverage[0]['modelCovered'] and not coverage[0]['nativeCovered']
    assert [dict(pixel=x['pixel'], channel=x['channel'], observedWord=x['modelWord'], frozenNativeWord=x['nativeWord'])
            for x in differences[:16]] == row['firstDifferencesFromFrozenNative']
    bbox = dict(xMin=min(x['x'] for x in pixel_differences), xMax=max(x['x'] for x in pixel_differences),
                yMin=min(x['y'] for x in pixel_differences), yMax=max(x['y'] for x in pixel_differences))
    PRIVATE.mkdir()
    private = save(PRIVATE/'analysis.json', dict(
        originalReportSha256=sha(read(BASE/'run-oct15/report.json')),
        modelInputScope='Declared RN32 CPU forward viewport/z/rhw, not captured Native viewport/rhw.',
        completeDifferentWords=differences, completeDifferentPixels=pixel_differences,
        completeCoverageDifferences=coverage, differentPixelBoundingBox=bbox,
        differentPixelsByY=[dict(y=k, pixels=v) for k, v in sorted(row_histogram.items())],
        commonCoveredDifferentWordsByChannel=common_channel_counts,
        commonCoveredPositiveFloatUlpDistanceHistograms=[dict(sorted(c.items())) for c in common_ulp_histograms],
        uniqueCauseEstablished=False, scope='Readonly complete physical comparison only. Pixel region and ULP counts do not isolate viewport, reciprocal/rhw, pretransformed setup or interpolation. No fit, clamp, normalization, epsilon or rerun.'))
    result = dict(schema='th14-forward-viewport-positiont-observation-v1', evidenceVerified=True,
        result='FAILED_DECLARED_MODEL_COMPATIBILITY', aControlFullMatchesFrozenNative=True,
        aFullBytes=4915200, aFullSha256=sha(observed[0]), bFullBytes=4915200, bFullSha256=sha(b),
        comparedWords=1228800, bDifferentWords=1315, bDifferentWordsByChannel=channel_counts,
        bDifferentPixels=len(pixel_differences), differentPixelBoundingBox=bbox,
        nativeCoveredPixels=native_covered, modelCoveredPixels=model_covered, coverageDifferences=len(coverage),
        coverageDifferencePositions=[dict(x=x['x'], y=x['y'], nativeCovered=x['nativeCovered'], modelCovered=x['modelCovered']) for x in coverage],
        commonCoveredDifferentWordsByChannel=common_channel_counts,
        finiteOutputGate=True, formatGate=True, comparisonEligible=True,
        declaredModelCompatibilitySupported=False, uniqueViewportCauseEstablished=False,
        validatesPrebiasSnapGlCandidate=False, measuredNativeViewportOrRhw=False,
        modelOperations=plan['genericFormula'], declarationA='POSITION0/FLOAT4 +TEXCOORD0/FLOAT2/MOVVS2',
        declarationB='POSITIONT9/FLOAT4 +TEXCOORD0/FLOAT2/VSNULL',
        reusedPixelShaderContainsUnusedTexld=True, noTextureCreatedOrBound=True,
        privateCompleteAnalysis=private, bindings=sorted(BINDINGS.values(), key=lambda x:x['path']),
        producerObservedCounts=dict(drawAttempts=2, successfulDrawCalls=2, presentCalls=0, audioDevicesOpened=0,
            audioPlayed=False, retailProcessesStarted=0, shaderAssemblies=0, cleanupApiCalls=4, cleanupErrors=0),
        reviewerExecutionCounts=dict(native=0, gpu=0, compiler=0, browser=0, audio=0),
        originalFfpClipCaptured=False, nativeEquivalent=False, completeGame=False, productionChanged=False,
        scope='Independent readonly source/input/report pins and full4915200-byte A/B comparisons. NewA reproduced immutable694d. NewB is a declared generic CPU RN32 forward viewport/z/rhw model submitted as POSITIONT, not an actual Native viewport/rhw capture. Its1315-word and1-coverage differences remain failure; finite/format/comparisonEligible are not a compatibility pass. Source73 or viewport alone is not isolated by this transfer: geometry setup, reciprocal/rhw rounding and interpolation may differ as a combined boundary. This negative cannot validate a prebias-snap GL candidate or infer a unique hardware/ISA cause. No additional Native/GPU/fixture/compiler/browser/audio execution or frozen/production changes occurred. Complete raw buffers and difference indices remain private; this public receipt contains only pins and bounded statistics.')
    public = save(OUT, result)
    print(json.dumps(dict(public=public, private=private, differentWords=1315,
                          differentPixels=len(pixel_differences), coverageDifferences=coverage,
                          commonCoveredDifferentWordsByChannel=common_channel_counts)))


if __name__ == '__main__':
    main()
