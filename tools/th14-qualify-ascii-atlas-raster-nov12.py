"""Compare the corrected D3D9 reference with the one retained, unchanged C++ GPU run."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/ascii-atlas-raster-nov12';OUT=H/'qualified.json';assert not OUT.exists()
bindings={}
def read(p):
    raw=p.read_bytes();bindings[p.relative_to(R).as_posix()]=hashlib.sha256(raw).hexdigest();return raw
load=lambda p:json.loads(read(p));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
declared=load(H/'declared-inputs.json');build=load(H/'component/build.json');old=load(H/'d3d9-before-initial-camera/report.json');new=load(H/'d3d9/report.json');cpp=load(H/'gles/report.json')
assert build['normalAccess'] and build['normalGameObjects']==141 and build['normalHostObjects']==4
for p,d in {**build['sourceBindings'],**build['objectBindings']}.items():assert sha(Path(p) if Path(p).is_absolute() else R/p)==d,p
assert sha(H/'component/probe.wasm')==build['wasmSha256']==cpp['wasmSha256']
assert sha(R/'tools/th14-ascii-atlas-raster-component-nov12.cpp')==build['fixtureSha256']
assert sha(R/'tools/th14-check-ascii-atlas-raster-nov12.mjs')==cpp['checkerSha256']
assert sha(R/'tools/th14-ascii-atlas-raster-native-nov12.py')==new['toolSha256']==old['toolSha256']
assert cpp['exception'] is None and cpp['closed'] and cpp['gpuContextClosed'] and cpp['cases']==18
assert cpp['differentPixels']==314 and cpp['differentChannels']==1240
assert all(v==0 for v in cpp['gpu']['liveObjects'].values()) and cpp['platform']['audioBytes']==0
assert new['allDeviceObjectsReleased'] and new['hiddenWindowDestroyed']
assert declared['cases']==len(new['cases'])==18
base=read(R/'tools/th14-ascii-atlas-geometry-native-nov12.py');assert hashlib.sha256(base).hexdigest()==declared['geometryOracleParentSha256']
preparer=read(R/'tools/th14-prepare-ascii-atlas-raster-nov12.py').decode()
tree=ast.parse(preparer);changes=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='changes' for t in n.targets))
derived=base.decode()
for before,after in changes.items():assert derived.count(before)==1;derived=derived.replace(before,after)
expected_ast=ast.parse(derived);actual_ast=ast.parse((H/'native-geometry-tool.py').read_text())
# Windows text-mode rewriting added blank lines to the descriptive docstring.
assert ast.dump(ast.Module(body=expected_ast.body[1:],type_ignores=[]))==ast.dump(ast.Module(body=actual_ast.body[1:],type_ignores=[]))
before=load(H/'geometry-before-initial-camera/report.json');after=load(H/'geometry/report.json')
assert sha(H/'native-geometry-tool.py')==after['toolSha256']
assert sha(H/'geometry/report.json')==new['originalGeometryReportSha256']
changed=[]
for i,(a,b) in enumerate(zip(before['rows'],after['rows'])):
    aa=json.loads(json.dumps(a));bb=json.loads(json.dumps(b))
    for x,y in zip(aa['draws'],bb['draws']):
        if x['viewport']!=y['viewport']:changed.append(i)
        del x['viewport'];del y['viewport']
    assert aa==bb,i
assert sorted(set(changed))==[0,6,12]
rawold=read(H/'d3d9-before-initial-camera/native.bgra');rawnew=read(H/'d3d9/native.bgra')
assert hashlib.sha256(rawold).hexdigest()==old['rawSha256'] and hashlib.sha256(rawnew).hexdigest()==new['rawSha256']
words=0;pixels=0;non_background=0;reused=0;recompared=0;changed_pixels=0
for a,b,c in zip(old['cases'],new['cases'],cpp['rows']):
    assert a['index']==b['index']==c['index'] and a['offset']==b['offset']==c['offset']
    assert a['bytes']==b['bytes']==c['bytes']
    view=rawnew[b['offset']:b['offset']+b['bytes']]
    assert hashlib.sha256(view).hexdigest()==b['sha256']==c['cppSha256']
    if c['differentPixels']:
        actual=read(H/f"gles/failed-{c['index']}-cpp.bgra")
        assert actual==view;recompared+=1
        original=rawold[a['offset']:a['offset']+a['bytes']]
        changed_pixels+=sum(original[i:i+4]!=view[i:i+4] for i in range(0,len(view),4))
    else:
        assert a['sha256']==b['sha256'] and c['differentChannels']==0;reused+=1
    non_background+=sum(view[i:i+4]!=bytes.fromhex('8b67427f') for i in range(0,len(view),4))
    words+=len(view);pixels+=len(view)//4
assert reused==16 and recompared==2 and changed_pixels==314 and non_background>1000
result=dict(schema='thp/th14-ascii-atlas-raster/1',gameSourceCommit='6e8dcbb4ce667718d9af3971080728d7a7739498',cases=18,resolutions=[[640,480],[960,720],[1280,960]],fonts=[0,4],passes=[0,1,2],scale=[.7,.3],shadow=True,alignment=[1,1],differentPixels=0,comparedPixels=pixels,comparedChannels=words,nonBackgroundPixels=non_background,
    actualCurrentCppResourceParserAsciiTextGraphicsDeviceAndRenderer=True,originalGeometryAndActualSeparateD3d9Hal=True,rawOriginalArgb4444TextureBytes=True,declaredFogAndDepthDisabled=True,
    declaredInitialCameraEstablishedByActualOriginalEmptyTraversal=True,originalRawGeometryExceptViewportUnchanged=True,
    rejectedInitialViewportFixture=dict(differentPixels=314,differentChannels=1240,retained=True),
    cppGpuRuns=1,cppRunAssertionExitCode=1,cppRunAssertionExitWasAgainstRejectedViewportReference=True,cppGpuErrors=False,cppGpuResourcesRetired=True,
    unchangedReferenceExactCasesReused=16,correctedReferenceCasesByteComparedFromRetainedCppImages=2,newOriginalGameRuns=0,newCppGpuRunsAfterReferenceCorrection=0,
    allOriginalFixtureComObjectsReleased=True,hiddenOriginalFixtureWindowDestroyed=True,audibleOutput=False,
    wholeGameFrame=False,loadingRngScheduleAccepted=False,browserUiAcceptance=False,allModesOrWholeGameAccepted=False,sourceChanged=False,runtimeRedeployed=False,completeGame=False,
    nativeD3d9Sha256=new['d3d9Sha256'],glesContext=cpp['gpu']['contextInfo']['renderer'],fixtureWasmSha256=build['wasmSha256'],bindings=bindings)
OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='bindings'}))
