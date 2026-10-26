"""Verify declared Application inputs, actual GLES quad repair and scope.

Requires retained private observations. This checks finite controls, keeps old
failures and the Stage blue-byte failure, and never accepts the complete game.
"""
from pathlib import Path
import argparse
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home',type=Path,default=ROOT/'artifacts/th14/application-process-input-oct27')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/porting/th14-process-input-quad-verified-oct27.json')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args();home=args.home.resolve();old=ROOT/'artifacts/th14/application-render-trace-oct27';bindings={}
    assert home.is_relative_to(ROOT/'artifacts/th14')
    def bind(path):
        path=path.resolve(strict=True);assert path.is_relative_to(ROOT)or path in [Path('H:/Games/th/14/th14.dat'),Path('H:/Games/th/14/th14.exe')]
        with path.open('rb')as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        key=path.relative_to(ROOT).as_posix()if path.is_relative_to(ROOT)else path.as_posix()
        bindings[key]=dict(bytes=path.stat().st_size,sha256=digest);return digest
    def read(path):
        bind(path);return path.read_bytes()
    def load(path):return json.loads(read(path))
    def diff(a,b):
        assert len(a)==len(b);indices=[i for i,(x,y)in enumerate(zip(a,b))if x!=y]
        return dict(bytes=len(indices),pixels=len({i//4 for i in indices}))
    def entropy(folder,cookie):
        e=load(folder/'declared-process-entropy.json')
        assert e['events']==[dict(bytes=4,value=cookie,beforeGameCallbacks=True)]
        assert e['externalEnvironmentInputDeclared']and not e['productionProcessCookieForced']and not e['gameRngStateSupplied']
    def run(folder,cookie,frames,checks):
        d=load(folder/'report.json');assert d['completed']and not d['error']and d['frames']==frames and len(d['checks'])==checks
        assert d['physicalAudioDevicesOpened']==0 and not d['browserAcceptance']and not d['completeGame'];entropy(folder,cookie);return d
    for name in ['tools/th14-prepare-application-cookie-controls-oct27.py','tools/th14-application-gles-trace-oct27.py',
        'tools/th14-application-render-pair-check.py','tools/th14-build-native-gles-component.py','tools/th14-build-native-application.py',
        'runtimes/th12/th12_web/tests/cpp/th14-application-semantic-trace-fixture.cpp','runtimes/th12/portable/sdl/Renderer.cpp',
        'runtimes/th12/portable/sdl/Shaders.hpp','runtimes/th12/portable/sdl/Th14WebGpu.wgsl']:
        bind(ROOT/name)
    plan=load(home/'attract-common/plan.json');assert plan['scenarioScope']=='attract'and plan['maximumOutputBytesPerCase']==128*1024**2
    assert plan['minimumFreeBytes']==100*1024**3 and plan['runnerSha256']==bind(home/'attract-common/runner.py')
    assert plan['preparerSha256']==bind(ROOT/'tools/th14-prepare-application-cookie-controls-oct27.py')
    for name,row in plan['sourceBindings'].items():assert bind(ROOT/name)==row['sha256']
    controls=old/'cookie-controls';a=run(controls/'gles-fallback',0xbb40e64f,11220,16);b=run(controls/'gles-positive',0x4b000000,11220,16)
    assert a['wasmSha256']==b['wasmSha256']and a['scenarioSha256']==b['scenarioSha256']and a['toolSha256']==b['toolSha256']
    assert a['metadataEpochAtFrameZero']==b['metadataEpochAtFrameZero']and a['pcmFrames']==b['pcmFrames']==8057856
    assert len(a['rows'])==2714 and len(b['rows'])==2715 and a['pcmSha256']!=b['pcmSha256']
    assert [v['actions'][-1]['state'][9]for v in [a,b]]==[653433,653434]
    first=next(i for i,(x,y)in enumerate(zip(a['rows'],b['rows']))if x!=y);assert first==2707
    failed=load(old/'cookie-common-v2/webgpu/report.json');prefix=run(old/'cookie-common-v2/gles',0xbb40e64f,11220,16)
    limit=load(old/'cookie-common-v2/webgpu/storage-limit.json');assert not failed['completed']and failed['error']and failed['frames']==11220
    assert failed['rows']==prefix['rows']and failed['pcmSha256']==prefix['pcmSha256'];assert limit
    before=load(home/'attract-common/pair.json');assert not before['allPairedCapturedBuffersEqual']and before['journalComparison']['allRowsEqual']
    assert before['silentPcmSinkComparison']['reportedHashEqual']and before['pairedJournalRows']==4239
    assert before['pairs'][1]['differentBytes']==10 and before['pairs'][1]['differentPixels']==8
    for backend in ['webgpu','gles']:run(home/'attract-common'/backend,0xbb40e64f,17545,30)
    raw_native=read(home/'hal-draw149/control/frame.bgra');assert len(raw_native)==1228800
    legacy_native_before=read(home/'hal-draw149/control/draw-148-native.bgra')
    assert legacy_native_before==read(home/'gles-semantic-third/first-target-9-before-gles.bgra')
    legacy_native=read(home/'hal-draw149/control/draw-149-native.bgra');legacy_gl=read(home/'gles-semantic-third/first-target-9-gles.bgra')
    assert diff(legacy_native,legacy_gl)==dict(bytes=15,pixels=10)
    legacy_report=load(home/'gles-semantic-third/report.json');assert legacy_report['completed']and legacy_report['actualApplicationBaselineExact']
    assert legacy_report['steps'][next(i for i,r in enumerate(legacy_report['steps'])if not r['nativeHashEqual'])]['completedDraws']==149
    semantic=load(home/'gles-quad-production/report.json');assert semantic['completed']and semantic['completeBufferBaselineExact']
    assert semantic['baselineKind']=='independent-hal'and not semantic['rendererCppChanged']and len(semantic['steps'])==199
    assert semantic['actualSemanticBatches']==192 and semantic['representedNativeDraws']==416 and semantic['actualClears']==7
    assert all(r['nativeHashEqual']for r in semantic['steps'])and read(home/'gles-quad-production/frame.bgra')==raw_native
    current={name:run(home/('attract-quad-'+name),0xbb40e64f,17545,30)for name in ['gles','webgpu']}
    for name,d in current.items():
        build_home=home/('current-quad-build-'+name);build=load(build_home/'build.json')
        assert d['wasmSha256']==build['wasmSha256']==bind(build_home/'application.wasm')
        for path,row in build['sourceBindings'].items():assert bind(ROOT/path)==row['sha256']
        assert read(home/('attract-quad-'+name)/'demo-1-ready.bgra')==raw_native
    pair=load(home/'attract-quad-pair.json');assert pair['allPairedCapturedBuffersEqual']and pair['allSharedActionStatesEqual']
    assert pair['journalComparison']['allRowsEqual']and pair['silentPcmSinkComparison']['reportedHashEqual']and pair['pairedJournalRows']==4239
    assert pair['silentPcmSinkComparison']['framesPerBackend']==12681216 and pair['pairedImages']==7 and pair['comparedImageBytes']==8601600
    assert current['gles']['rows']==current['webgpu']['rows']and current['gles']['actions']==current['webgpu']['actions']
    assert current['gles']['pcmSha256']==current['webgpu']['pcmSha256']=='cd197e69142d40cc42e64da3ce7914578b02a0c0b1579409e64f2ec831b7cd36'
    for left,right in zip(current['gles']['captures'],current['webgpu']['captures']):
        assert left==right;assert read(home/'attract-quad-gles'/left['file'])==read(home/'attract-quad-webgpu'/right['file'])
    stage=load(home/'stage-quad-final/comparison.json');assert stage['frames']==21 and stage['exactFrames']==20 and stage['differentChannels']==1
    assert next(r for r in stage['rows']if r['differentChannels'])['first']==[dict(x=144,y=373,channel=0,actual=119,original=120)]
    archive_rows=[]
    for suffix in ['', '/batch-03','/batch-04','/batch-06']:
        folder=ROOT/('artifacts/th14/input-archives-oct27'+suffix);v=load(folder/'verified.json');retired=load(folder/'retired.json')
        assert v['archiveSha256']==retired['archiveSha256']==bind(folder/'inputs.tar.zst')
        assert v['manifestSha256']==retired['manifestSha256']==bind(folder/'manifest.json')
        assert v['restoreToolSha256']==bind(folder/'restore.py')and retired['restoreProbeVerified']and retired['allObservationReportsUnchanged']
        assert retired['workingInputsRecoverableFromArchive']and retired['observationsRetainedInPlace']and not retired['originalGameFilesChanged']
        archive_rows.append(dict(directory=folder.relative_to(ROOT).as_posix(),objects=v['objects'],aliases=v['aliases'],sourceBytes=v['sourceBytes'],archiveBytes=v['archiveBytes'],restoreProbeVerified=True))
    assert sum(r['objects']for r in archive_rows)==62 and sum(r['aliases']for r in archive_rows)==192
    assert sum(r['sourceBytes']for r in archive_rows)==5630984651
    compression=[]
    for name in ['lzx-pilot','lzx-frozen','lzx-extra']:
        d=load(old/name/'verified.json');rows=d.get('files',[d])
        for row in rows:
            p=Path(row['path']);p=p if p.is_absolute()else ROOT/p
            assert bind(p)==row['sha256']and p.stat().st_size==row['bytes']and p.stat().st_mtime_ns==row['mtimeNs']
            compression.append(dict(path=p.relative_to(ROOT).as_posix(),bytes=row['bytes']))
        print(json.dumps(dict(verifiedCompressionGroup=name)),flush=True)
    assert len(compression)==14 and sum(r['bytes']for r in compression)==9648939195
    assert bind(Path('H:/Games/th/14/th14.exe'))=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert bind(Path('H:/Games/th/14/th14.dat'))=='57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233'
    result=dict(schema='th14/process-input-quad-repair/1',verifiedFiniteControls=True,fullAttractFramesPerBackend=17545,assertionsPerBackend=30,
        declaredProcessCookie=0xbb40e64f,differentCookieChangesPortableStateAndPcm=True,oldUnrecordedCookieFailureCauseUniquelyProven=False,
        sameInputBeforeQuadAllJournalRowsEqual=True,sameInputBeforeQuadPcmHashesEqual=True,beforeQuadDifferentBytes=10,beforeQuadDifferentPixels=8,
        sameInputPrefixStorageFailureRetained=True,currentAll4239JournalRowsEqual=True,currentPcmFramesPerBackend=12681216,currentPcmHashesEqual=True,
        currentPcmSha256=current['gles']['pcmSha256'],currentPairedImages=7,currentComparedImageBytes=8601600,currentPairedImagesEqual=True,
        firstGlesDifferentDraw=149,firstGlesDrawBeforeBuffersExact=True,firstGlesDrawDifferentBytes=15,firstGlesDrawDifferentPixels=10,
        actualSemanticBatches=192,independentNativeDraws=416,independentNativeClears=7,all199SemanticAndClearNativeHashesEqual=True,
        currentActualApplicationFrameNativeBytesEqual=1228800,glesStageExactFrames=20,glesStageFrames=21,glesStageBlueDifferenceRetained=True,
        productionGraphicsChanged=True,productionGameplayChanged=False,productionProcessCookieForced=False,gameRngStateSupplied=False,
        archivedDerivedInputs=archive_rows,archivedSourceBytes=5630984651,archiveBytes=sum(r['archiveBytes']for r in archive_rows),
        additionalLzxFiles=14,additionalLzxLogicalBytes=9648939195,additionalLzxAllocatedBefore=2987847680,additionalLzxAllocatedAfter=768684032,
        observationsAndOriginalGameFilesPreserved=True,minimumFreeBytes=100*1024**3,maximumNewCaseOutputBytes=128*1024**2,
        completeGame=False,nativeEquivalent=False,browserAcceptance=False,old8216CandidateNotUpdated=True,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
    if args.check:assert json.loads(args.output.read_bytes())==result
    else:args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k not in ['bindings','archivedDerivedInputs']}),flush=True)


if __name__=='__main__':main()
