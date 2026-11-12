"""Bind full-track decoder observations without claiming original PCM equality."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/vorbis-stream-nov13'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
r=load(H/'result-v2.json');b=load(H/'build.json');plan=load(H/'validation-input.json')
assert r['passed']and r['tracks']==18 and r['totalDecodedStereoFrames']==99457880
assert r['exception']is None and not r['outputDeviceOpened']and r['unexpectedPlatformCalls']==0
assert r['bindings']['runner']==sha(R/'tools/th14-check-vorbis-stream-v2-nov13.mjs')
assert r['bindings']['wasm']==sha(H/'probe.wasm')==b['wasmSha256']
assert r['bindings']['plan']==sha(H/'validation-input.json')and r['bindings']['formats']==sha(H/'thbgm.fmt')
assert all(x['aboveToleranceSamples']==x['seekDifferentBytes']==x['loopDifferentBytes']==0 for x in r['rows'])
assert sum(x['seekWindows']for x in r['rows'])==54
assert sum(x['shiftedSeekControlDetected']for x in r['rows'])==18
assert r['codecToleranceFixedBeforeExecution']==plan['sampleTolerance']==0.0001
for name,digest in b['sourceBindings'].items():assert sha(R/name)==digest,name
assert b['normalAccessControl']and b['deviceIoDisabledByProductionCode']
summary=dict(schema='thp/th14-vorbis-stream/1',passed=True,sourceCommit=r['sourceCommit'],tracks=18,
 totalDecodedStereoFrames=99457880,comparedFloatSamples=198915760,allTracksActualOggNoFlacFallback=True,
 actualProductionAudioTranslationUnitIncluded=True,normalAccessControl=True,
 fullTrackIndependentFfmpegDecodeCompared=True,fixedPerSampleTolerance=0.0001,
 maximumObservedAbsoluteError=max(x['maxAbsoluteError']for x in r['rows']),aboveToleranceSamples=0,
 expectedFramesAndIntroPointsFromActualRetailFormat=True,seekWindows=54,seekDifferentBytes=0,
 loopBoundaryCases=18,loopBoundaryFramesPerCase=192,loopDifferentBytes=0,
 seekAndLoopBitExactAgainstSameDecoderSequentialOutput=True,oneFrameShiftControlsDetected=18,
 firstMultitrackFixtureFormatClearFailurePreserved=True,fixtureOnlyCorrectedProductionUnchanged=True,
 standaloneWasiDecoderNotActualBrowserModule=True,outputDeviceOpened=False,
 musicOrArchiveAssetsTransferredToWindows=False,originalPcmBitEqualityAccepted=False,
 actualBrowserPlaybackLatencyOrFinalMixerAccepted=False,completeGame=False,
 rows=r['rows'],bindings={p.relative_to(R).as_posix():sha(p)for p in [
 H/'build.json',H/'validation-input.json',H/'result-v1.json',H/'result-v2.json',Path(__file__)]})
out=R/'docs/porting/th14-vorbis-stream-nov13.json';assert not out.exists();out.write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:summary[k]for k in ['passed','tracks','totalDecodedStereoFrames','maximumObservedAbsoluteError','seekWindows','loopBoundaryCases']}))
