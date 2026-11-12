"""Bind real-atlas observations without treating ignored raw state as identical."""
from pathlib import Path
import hashlib,json

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/ascii-atlas-geometry-nov12'
OUT=H/'qualified.json'
assert not OUT.exists()
bindings={}
def read(path):
    raw=path.read_bytes()
    bindings[path.relative_to(R).as_posix()]=hashlib.sha256(raw).hexdigest()
    return raw
load=lambda path:json.loads(read(path))
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
n=load(H/'native/report.json')
b=load(H/'component/build.json')
raw=load(H/'checked.json')
effective=load(H/'checked-effective.json')
runtime=load(H/'runtime-recheck.json')
assert n['error']=='' and n['cases']==648
assert sha(R/'tools/th14-ascii-atlas-geometry-native-nov12.py')==n['toolSha256']
assert sha(R/'tools/th14-ascii-atlas-geometry-component-nov12.cpp')==b['fixtureSha256']
assert sha(H/'component/probe.wasm')==b['wasmSha256']==effective['wasmSha256']
assert sha(R/'tools/th14-check-ascii-atlas-geometry-effective-nov12.mjs')==effective['checkerSha256']
for path,digest in {**b['sourceBindings'],**b['objectBindings']}.items():
    assert sha(R/path)==digest,path
assert len(b['sourceBindings'])==367 and len(b['objectBindings'])==141
assert raw['differentWords']==31392 and raw['failedCases']==574
assert effective['cases']==648 and effective['comparedWords']==941760
assert effective['differentWords']==effective['failedCases']==effective['drawCountDifferentCases']==0
assert effective['rawDifferentWords']==effective['nativeSubmittedVertices']==31392
assert effective['rawDifferencesByField']=={'22':31392}
assert effective['negativeControlsChecked'] and not effective['rawStateIdentityAccepted']
assert runtime['exact'] and runtime['actualBytes']==506
assert sha(R/'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp')=='a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
result=dict(schema='thp/th14-ascii-atlas-geometry/1',gameSourceCommit='6e8dcbb4ce667718d9af3971080728d7a7739498',
    cases=648,comparedWords=941760,submittedVertices=31392,effectiveDifferentWords=0,drawCountDifferentCases=0,
    rawDifferentWords=31392,rawFailedCases=574,rawDifference='D3DTSS_TEXTURETRANSFORMFLAGS: original 2, C++ 0; original observations retained',
    rawStateIdentityAccepted=False,screenVertexEffectiveTextureTransformOnly=True,
    negativeControls=['world-space transform flag remains active','one UV bit fails','one blend-factor word fails'],
    resolutions=[[640,480],[960,720],[1280,960]],fonts=6,passes=3,scalePairs=[[1,1],[0.7,0.3]],
    actualOriginalResourceLoaderVmBindingQueueTraversalGeometryAndBatchFlush=True,
    actualCppResourceParserAsciiTextAnmRendererAndCompositor=True,
    declaredServices=['texture creation/D3D boundary','opaque texture ordinal','initial device states','original screen-camera matrix helper'],
    nativeExecutableSha256=n['executableSha256'],asciiSha256=n['asciiSha256'],fixtureWasmSha256=b['wasmSha256'],
    currentSourceBindingsVerified=367,currentNormalGameObjectsVerified=141,
    semanticsSource=effective['semanticsSource'],noGpuPixels=True,newGameRuns=0,newGpuRuns=0,
    sourceChanged=False,runtimeRedeployed=False,browserUiAcceptance=False,wholeImageAccepted=False,completeGame=False,
    currentHtmlRecheck=dict(generation=runtime['generation'],bytes=runtime['actualBytes'],sha256=runtime['actualSha256'],manifestExact=True),
    bindings=bindings)
OUT.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='bindings'}))
