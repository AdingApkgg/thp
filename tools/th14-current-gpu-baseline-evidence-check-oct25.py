"""Inspect actual current-source browser GPU captures; retain strict failures."""
from pathlib import Path
import argparse,hashlib,json
ROOT=Path(__file__).resolve().parents[1];H=ROOT/'artifacts/th14/current-gpu-baseline-oct25';SHA=lambda b:hashlib.sha256(b).hexdigest()
def inspect():
 bindings={}
 def raw(p):
  b=p.read_bytes();bindings[p.relative_to(ROOT).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
 def load(p):return json.loads(raw(p))
 for mode in ['color','uv-adapter','alpha','depth']:
  d=H/mode;b=load(d/'build.json');assert SHA(raw(d/'gpu.wasm'))==b['wasmSha256']and SHA(raw(d/'gpu.mjs'))==b['loaderSha256']
  for n,r in b['sources'].items():assert SHA(raw(d/n))==r['sha256']
  for n,r in b['sourceBindings'].items():assert SHA(raw(ROOT/n))==r['sha256']
  for n in ['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','Shaders.hpp','AlphaConversion.hpp','ResampleShader.hpp']:
   a=raw(d/n);p=raw(ROOT/'runtimes/th12/portable/sdl'/n)
   if mode=='uv-adapter'and n=='Shaders.hpp':
    old=b'outColor=c;';new=b'outColor=vec4(vUV,0.0,1.0);';assert p.count(old)==1 and a==p.replace(old,new)
   else:assert a==p,(mode,n)
 color=load(H/'color/capture/report.json');uv=load(H/'uv-adapter/capture/report.json');alpha=load(H/'alpha/browser-report.json');depth=load(H/'depth/browser-report.json')
 native=raw(H/'native/native.bgra');frozen=raw(ROOT/'artifacts/th14/stage-gpu-stream-replay/native.bgra');assert native==frozen
 n=load(H/'native/native.json');assert n['pixelsSha256']==SHA(native)
 total=0;first=[]
 for r in color['reports']:
  b=raw(H/'color/capture'/r['savedFile']);assert SHA(b)==r['portableSha256'];ref=next(x for x in n['frames']if x['stage']==r['stage']and x['frame']==r['frame']);e=native[ref['offset']:ref['offset']+ref['bytes']];assert len(b)==len(e)
  ds=[(i,a,v)for i,(a,v)in enumerate(zip(b,e))if a!=v];assert len(ds)==r['differentChannels'];total+=len(ds)
  first.extend(dict(stage=r['stage'],frame=r['frame'],x=(i//4)%640,y=i//2560,channel=i%4,portable=a,native=v)for i,a,v in ds)
 assert total==1 and color['exactFullBuffers']==20 and first==[dict(stage=3,frame=1199,x=144,y=373,channel=0,portable=119,native=120)]
 cases=load(H/'uv-cases.json');fullByKey={x['key']:x for x in cases['fullBindings']};fullNative=0
 assert uv['frames']==47 and uv['exactFullBuffers']==47 and uv['differentSampleWords']==0
 for r in uv['reports']:
  b=raw(H/'uv-adapter/capture'/r['savedFile']);assert SHA(b)==r['portableSha256']==r['nativeSha256']and r['strictFullBufferHashEqual']
  key='/'.join(str(r[k])for k in ['stage','frame','originalDrawIndex'])
  if key in fullByKey:
   ref=fullByKey[key];e=raw(ROOT/Path(ref['path']));start=ref.get('offset',0);e=e[start:start+ref['bytes']];assert SHA(e)==ref['sha256']and b==e;fullNative+=1
 assert fullNative==28
 assert alpha['cases']==alpha['exactCases']==2560 and alpha['strictPixelsEqual']and alpha['portablePixelsSha256']==alpha['nativePixelsSha256']
 assert SHA(raw(ROOT/'artifacts/th14/gpu-alpha-depth/native.bgra'))==alpha['nativePixelsSha256']
 oldDepthRaw=raw(ROOT/'artifacts/th14/stage-gpu-stream-replay/depth-threshold/native.json');assert SHA(oldDepthRaw)==depth['nativeReportSha256'];samples=next(r['samples']for r in json.loads(oldDepthRaw)['rows']if r['operation']=='copyD16')
 assert depth['cases']==915 and depth['strictDepthValuesEqual']and depth['differentDepthValues']==0 and len(samples)==len(depth['reports'])
 assert all(p['inputWord']==n['inputWord']and p['portable']==p['d3d9']==n['d16']for p,n in zip(depth['reports'],samples))
 rejected=load(H/'uv/capture/report.json');assert rejected['exactFullBuffers']==4 and rejected['differentSampleWords']==421
 return dict(verifiedScopedObservations=True,productionChanged=False,currentProductionRendererAndVertexSourcesVerified=True,fragmentOnlyUvAdapterExplicit=True,freshD3D9HalReferenceBytesEqualFrozen=True,colorFrames=21,colorExactFrames=20,colorDifferentChannels=1,colorFirstDifferences=first,strictColorPixelsEqual=False,uvFrames=47,uvExactFullHashes=47,uvNativeFullByteComparisons=28,uvNativeHistoricalHashOnly=19,alphaDepthCases=2560,alphaDepthHashEqual=True,alphaPortableWholeGroupRawBytesRetained=False,constantD16Values=915,constantD16DifferentValues=0,rejectedMissingUvAdapter=dict(exactFrames=4,frames=47,differentSampleWords=421,productionRegressionClaimed=False),bindings=bindings,scope='Current production Renderer and six related files, compiled and executed in actual browser WebGL. The UV control changes one fragment output statement only; its initial missing-adapter run is retained as a rejected harness configuration. Color compares all21 complete RGBA8 buffers to a fresh D3D9 HAL readback that equals the frozen reference. The sole blue-channel difference remains a strict failure. This UV47 rerun reads28 original full byte buffers and19 historical full hashes; it does not inherit the broader byte bindings of earlier reports. Alpha2560 compares one whole-group hash visible in the UI; portable whole-group bytes were not separately archived. Depth915 is authored constant screen depth, not arbitrary world interpolation. No whole-game frames, all hardware or PCM claim.',completeGame=False,nativeEquivalent=False)
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();r=inspect();out=ROOT/'docs/porting/th14-current-gpu-baseline-observed-oct25.json'
 if args.check:assert json.loads(out.read_text())==r
 else:out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in r.items()if k not in ['bindings','scope']}))
if __name__=='__main__':main()
