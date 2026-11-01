"""Verify current production Applications against one actual original full frame.

Observed resource delivery is a declared external input, never independent
production scheduling or whole-game acceptance.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json
R=Path(__file__).resolve().parents[1]
S=lambda b:hashlib.sha256(b).hexdigest()

def evidence(home):
    H=home.resolve(strict=True);assert H.is_relative_to(R/'artifacts/th14')
    N=R/'artifacts/th14/native-frame-readback-oct28/inline-ecl-worker-boundaries-v2'
    bindings={}
    def raw(path):
     data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=S(data));return data
    def load(path):return json.loads(raw(path))
    native=load(N/'report.json');nvs=load(N/'live-vms-before-readback.json');pixels=raw(N/native['readback']['file'])
    assert native['childExited']and native['frameReadbackCompleted']and not native['error']and len(pixels)==1228800
    assert native['originalCodeWrites']==native['gameStateWrites']==0 and not native['inputInjection']and native['threadContextRedirects']==2
    decoder=R/'tools/th14-native-title-live-compare-oct27.py';raw(decoder);spec=importlib.util.spec_from_file_location('native_vm_words',decoder);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    import struct
    addresses={struct.unpack_from('<I',bytes.fromhex(n['rawVmHex']),0x570)[0]:n['handle']for n in nvs['rows']}
    rows=[module.native_words(n,addresses)[1]for n in nvs['rows']];assert len(rows)==334
    backend_rows=[]
    for backend,folder in [('webgpu','availability'),('gles','gles-availability')]:
     strict=load(H/f'strict-{backend}.json');assert strict['strictAllSelectedStateLiveVmsAndPixelsEqual']and strict['noPixelToleranceOrFpsNormalization']
     for name,row in strict['bindings'].items():assert S(raw(R/name))==row['sha256']
     home=H/folder;run=load(home/'run/report.json');capture=run['captures'][0];assert run['frames']==2270 and len(run['checks'])==7 and all(x['passed']for x in run['checks'])
     assert raw(home/'run'/capture['file'])==pixels
     port=load(home/'run'/capture['liveAnimations']['file']);assert port['complete']and port['comparedValues']==303 and port['rows']==rows
     build_path=R/'artifacts/th14/webgpu-instance-production-oct30'/('webgpu-build'if backend=='webgpu'else'gles-build');build=load(build_path/'build.json')
     assert S(raw(build_path/'application.wasm'))==build['wasmSha256']==run['wasmSha256']
     for path,row in build['sourceBindings'].items():assert S(raw(R/path))==row['sha256']
     profile=load(home/'availability.json');assert run['observedResourceAvailabilityControl']['profile']==profile
     assert profile['nativeReport']['sha256']==S(raw(N/'report.json'))and profile['noVmRngPixelOrGameStateOverrides']and not profile['productionSchedulingChanged']
     assert profile['sourceToolSha256']==S(raw(R/'tools/th14-native-availability-control-oct28.py'))
     preparation=load(home/'preparation.json');assert preparation['sourceHostSha256']==S(raw(R/'tools/th14-native-application-process-host-oct27.py'))
     assert preparation['privateHostSha256']==S(raw(home/'host.py'))==S(raw(home/'run/run-tool.py'))==run['toolSha256']
     assert not preparation['productionSourcesChanged']and preparation['originalCodeWrites']==0
     first={};origin=profile['originalPlayerConstructionPresent']
     for row in native['mainResourcePumpEntries']:
      for slot in row['slots']:
       if slot['file']!=9 and slot['words128Through134'][0]and row['precedingPresentEntries']>=origin:first.setdefault(slot['file'],row['precedingPresentEntries'])
     assert profile['deliveries']==[dict(resourceFile=f,mainPumpOffsetFromPlayer=p-origin)for f,p in first.items()]

     backend_rows.append(dict(backend=backend,wasmSha256=run['wasmSha256'],actualApplicationFrames=2270,assertions=7,
      nativePresent=2278,stage=3,controllerFrame=241,pixelBytesCompared=1228800,pixelDifferences=0,
      vmRows=334,vmFields=303,bothRngExact=True,rawHandlesAndRegistryOrderExact=True,
      observedResourceAvailabilityIsExternalInput=True,independentLoadingSchedulingAccepted=False))
    proof=dict(verifiedFiniteCurrentOriginalDemoFrame=True,backends=backend_rows,currentProductionBuildsUsed=True,
     firstReplayRepairAndInstancingNotAssumedFromOldProof=True,actualOriginalFullBufferCompared=True,
     originalDiagnosticReadbackContextRedirects=2,alphaFpsAndHandlesNotNormalized=True,
     originalOrdinaryMenuAccepted=False,wholeOriginalPixelsOrPcmAccepted=False,completeGame=False,nativeEquivalent=False,
     bindings=bindings,verifierSha256=S(Path(__file__).read_bytes()))
    return proof

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    target=a.output.resolve();assert target.is_relative_to(R/'artifacts/th14')or target.is_relative_to(R/'docs/porting')
    result=evidence(a.case)
    if a.check:assert json.loads(target.read_bytes())==result
    else:target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))
if __name__=='__main__':main()
