"""Recalculate finite TH14 near-clip pixel evidence from retained full buffers.

Public output contains counters, paths and hashes, never images, game assets,
save/replay files, memory observations or compiled binaries.
"""
from pathlib import Path
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/gles-clip-portable-nov04';SHA=lambda b:hashlib.sha256(b).hexdigest()

def evidence():
    bindings={}
    def read(path):
        path=Path(path).resolve(strict=True);assert path.is_relative_to(R);raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    build=load(H/'production-build-nov05/build.json');assert build['originalRendererSourcesUnmodified'] and build['backend']=='gles'
    assert SHA(read(H/'production-build-nov05/probe.wasm'))==build['wasmSha256']
    for name,row in build['sourceBindings'].items():assert SHA(read(R/name))==row['sha256']
    for name,digest in build['sourceFiles'].items():assert SHA(read(H/'production-build-nov05/src'/name))==digest
    plan=load(H/'production-integration-nov05/plan.json')
    for row in plan['sourceFiles']:assert SHA(read(R/row['path']))==row['afterSha256'] and SHA(read(H/'production-integration-nov05'/(Path(row['path']).name+'.before')))==row['beforeSha256']
    def buffers(home,reference_home):
        report=load(home/'comparison.json');native=load(reference_home/'native.json');expected=read(reference_home/'native.bgra');prepared=read(reference_home/'prepared.json')
        assert SHA(expected)==report['nativePixelsSha256']==native['pixelsSha256'] and SHA(prepared)==report['preparedSha256']==native['preparedSha256']
        actual_hash=hashlib.sha256();wrong=0;rows=[]
        assert len(report['rows'])==len(native['frames'])==report['frames']
        for row,original in zip(report['rows'],native['frames']):
            assert (row['stage'],row['frame'])==(original['stage'],original['frame'])
            raw=read(home/f"stage{row['stage']}-frame{row['frame']}.bgra");before=expected[original['offset']:original['offset']+original['bytes']]
            assert len(raw)==len(before)==640*480*4 and SHA(raw)==row['actualSha256'] and SHA(before)==row['originalSha256']==original['sha256']
            different=sum(a!=b for a,b in zip(raw,before));assert different==row['differentChannels'];wrong+=different;actual_hash.update(raw)
            rows.append(dict(stage=row['stage'],frame=row['frame'],differentChannelBytes=different,actualSha256=SHA(raw),referenceSha256=SHA(before)))
        assert wrong==report['differentChannels'] and actual_hash.hexdigest()==report['actualPixelsSha256']
        assert sum(not x['differentChannelBytes']for x in rows)==report['exactFrames']
        return dict(frames=len(rows),exactFrames=report['exactFrames'],differentChannelBytes=wrong,comparedBytes=len(expected),rows=rows,wasmSha256=report['wasmSha256'],originalRendererSourcesUnmodified=report['originalRendererSourcesUnmodified'],browserAcceptance=report['browserAcceptance'])
    production=[]
    for name,ref in [('production-retained21-nov05',R/'artifacts/th14/stage-gpu-stream-replay'),('production-near48-nov05',H/'generated-near-clip-matrix-nov05'),('production-order16-nov05',H/'generated-order-geometry-nov05')]:
        row=buffers(H/name,ref);assert row['wasmSha256']==build['wasmSha256'] and row['differentChannelBytes']==0 and row['originalRendererSourcesUnmodified'] and not row['browserAcceptance'];production.append(dict(name=name,**row))
    baseline=buffers(H/'baseline',R/'artifacts/th14/stage-gpu-stream-replay');assert baseline['frames']==21 and baseline['differentChannelBytes']==1 and baseline['exactFrames']==20
    rejected=buffers(H/'generated-order-candidate-v8',H/'generated-order-geometry-nov05');assert rejected['frames']==16 and rejected['differentChannelBytes']==17 and rejected['exactFrames']==10
    synthetic_baseline=buffers(H/'generated-order-baseline',H/'generated-order-geometry-nov05');assert synthetic_baseline['exactFrames']==16 and synthetic_baseline['differentChannelBytes']==0
    syntax=load(H/'production-shared-syntax-nov05/report.json');assert syntax['rows']==[dict(title=t,webgpu=w,returncode=0)for t,w in [(12,False),(13,False),(14,False),(16,False),(14,True)]]
    assert syntax['sourceBindings']==build['sourceBindings'] and syntax['buildSha256']==SHA(read(H/'production-build-nov05/build.json'))
    profiles=load(H/'homogeneous-viewport-nov05/report.json');assert len(profiles['rows'])==6
    assert all(row['exactFrames']==(16 if row['profile'].startswith('original-')else 10)for row in profiles['rows'])
    padding=load(H/'generated-order-padded-target-control/comparison.json');assert padding['exactFrames']==10 and padding['differentChannels']==17 and padding['paddedPhysicalTargetIntervention']
    viewport=load(H/'generated-order-native-postclip-v10/comparison.json');assert viewport['exactFrames']==16 and viewport['nativeD3D11ViewportIntervention'] and not viewport['portableCandidate']
    return dict(schema='th14/portable-near-clip/1',productionFixVerifiedFiniteBuffers=True,productionRendererFiles=plan['sourceFiles'],gameplayCoreChanged=False,
        frames=sum(x['frames']for x in production),comparedBytes=sum(x['comparedBytes']for x in production),differentChannelBytes=0,production=production,
        previousRetainedBaseline=baseline,rejectedPowerOfTwoViewport=rejected,syntheticUnmodifiedBaseline=synthetic_baseline,
        homogeneousArithmeticControls=profiles['rows'],paddedTargetHypothesisSupported=False,nativeFractionalViewportDiagnosticPassed=True,nativeFractionalViewportPromoted=False,
        sharedSyntax=syntax['rows'],references=['runtimes/th143/web/ClipTrianglesToHardwareV4.mjs','runtimes/th143/web/FloatMultiplyNearestV2.mjs'],
        productionUsesOriginalIntegerViewport=True,productionRequiresNativeIntervention=False,productionUsesPerPixelCorrections=False,
        ownProceduralTextureForSyntheticMatrices=True,referenceIsIndependentD3d9Component=True,originalWholeFramebufferCompared=False,
        otherGpusAccepted=False,browserAcceptance=False,independentSchedulingAccepted=False,wholeAudioAccepted=False,allModesAccepted=False,completeGame=False,nativeEquivalent=False,
        publicEvidenceContainsOnlyCountersPathsHashes=True,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');args=p.parse_args();out=args.output.resolve();assert out.is_relative_to(R)
    value=evidence()
    if args.check:assert json.loads(out.read_bytes())==value
    else:assert not out.exists();out.write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({k:value[k]for k in ['productionFixVerifiedFiniteBuffers','frames','comparedBytes','differentChannelBytes','browserAcceptance','completeGame']}))

if __name__=='__main__':main()
