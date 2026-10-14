"""Verify the narrow private dirty-mark candidate against independent Native."""
import hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/th14/deferred-capture-pixels-oct14';OUT=ROOT/'artifacts/th14/deferred-capture-success-dirty-oct14';REPORT=ROOT/'docs/porting/th14-deferred-capture-success-dirty-verified-oct14.json';SHA=lambda b:hashlib.sha256(b).hexdigest()
def bind(p):return dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=SHA(p.read_bytes()))
def main():
    assert not REPORT.exists(),'Completed candidate evidence immutable'
    previous=ROOT/'docs/porting/th14-deferred-capture-pixels-observed-oct14.json';baseline=json.loads(previous.read_bytes());build=json.loads((OUT/'webgl-build.json').read_bytes());web=json.loads((OUT/'webgl-capture/report.json').read_bytes());native=json.loads((BASE/'native.json').read_bytes());beforeweb=json.loads((BASE/'webgl-capture/report.json').read_bytes());oldbuild=json.loads((BASE/'webgl-build.json').read_bytes())
    assert baseline['deferredPixelEvidenceVerified'] and baseline['exactFullBuffers']==8 and baseline['differentBytes']==0 and not baseline['nativeEquivalent']
    assert SHA(previous.read_bytes())==build['baselinePixelReportSha256'] and SHA((BASE/'webgl-build.json').read_bytes())==build['baselineBuildSha256']
    custody={row['path']:row for row in baseline['bindings']}
    for path in [BASE/'native.json',BASE/'native-output.bin',BASE/'native-source.bgra',BASE/'source.bgra',BASE/'inputs.json',BASE/'webgl-build.json',BASE/'webgl-capture/report.json']:
        row=custody[path.relative_to(ROOT).as_posix()];assert path.stat().st_size==row['bytes'] and SHA(path.read_bytes())==row['sha256'],'Frozen baseline reference custody'
    assert len(native['cases'])==len(beforeweb['reports'])==beforeweb['frames']==8
    assert build['toolSha256']==SHA((ROOT/'tools/th14-deferred-capture-success-dirty-build.py').read_bytes())
    assert build['wasmSha256']==web['wasmSha256']==SHA((OUT/'capture.wasm').read_bytes()) and build['loaderSha256']==SHA((OUT/'capture.mjs').read_bytes())
    assert build['captureConsumerSha256']==web['captureConsumerSha256']==SHA((OUT/'ApplicationCaptureTh14.candidate.hpp').read_bytes())==SHA((OUT/'private/cpp/sdl/ApplicationCaptureTh14.hpp').read_bytes())
    assert build['beforeConsumerSha256']==oldbuild['captureConsumerSha256']==SHA((OUT/'ApplicationCaptureTh14.before.hpp').read_bytes())
    assert SHA((OUT/'success-dirty.patch').read_bytes())==build['patchSha256']
    assert build['fixtureSha256']==oldbuild['fixtureSha256']==SHA((OUT/'private/fixture.cpp').read_bytes())
    assert [f for f in build['flags'] if not f.startswith('-I')]==[f for f in oldbuild['flags'] if not f.startswith('-I')]
    changed=[]
    for row in build['bindings']:
        assert SHA((OUT/row['snapshot']).read_bytes())==row['sha256']
        if row['sha256']!=row['beforeSha256']:changed.append(row['snapshot'])
    assert changed==['private/cpp/sdl/ApplicationCaptureTh14.hpp'] and web['sourceBindings']==build['bindings']
    for row in build['stateBindings']:assert SHA((OUT/row['snapshot']).read_bytes())==row['sha256']
    before=(OUT/'ApplicationCaptureTh14.before.hpp').read_bytes();after=(OUT/'ApplicationCaptureTh14.candidate.hpp').read_bytes();nl=b'\r\n' if b'\r\n' in before else b'\n'
    needle=b'  graphics.backend.resample(Graphics::screen,from,target,to,nullptr,0,0);\n  graphics.changed(target);renderer.invalidate();'.replace(b'\n',nl)
    replacement=b'  if(graphics.backend.resample(Graphics::screen,from,target,to,nullptr,0,0))graphics.changed(target);\n  // Material-cache invalidation is separate from the successful target write.\n  renderer.invalidate();'.replace(b'\n',nl)
    assert before.count(needle)==1 and before.replace(needle,replacement)==after
    helper=ROOT/'tools/th14-deferred-capture-pixels-evidence-check.py';spec=importlib.util.spec_from_file_location('copy_compare',helper);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);comparisons=[];exact=0;total=0
    assert len(web['reports'])==web['frames']==8
    for n,w,bw in zip(native['cases'],web['reports'],beforeweb['reports']):
        assert n['index']==w['index']==bw['index'] and n['request']==w['request'] and n['sourceRect']==w['sourceRect'] and n['destinationRect']==w['destinationRect']
        actual=(OUT/'webgl-capture'/f"portable-{n['index']:03d}.pixels").read_bytes();original=(BASE/n['pixelFile']).read_bytes();old=(BASE/'webgl-capture'/f"portable-{n['index']:03d}.pixels").read_bytes()
        assert len(actual)==len(original)==len(old)==n['bytes'] and SHA(actual)==w['portableSha256'] and SHA(original)==n['pixelSha256'] and SHA(old)==bw['portableSha256']
        diff=m.difference(actual,original,n['bpp']);before_diff=m.difference(actual,old,n['bpp'])
        for key,value in diff.items():assert w[key]==value
        assert w['strictFullBufferEqual']==(actual==original) and w['words']==[-1,1,1,1,1,1,0,1,2,1]
        comparisons.append(dict(name=n['name'],bytes=n['bytes'],nativeSha256=SHA(original),candidateSha256=SHA(actual),beforeSha256=SHA(old),strictNativeEqual=actual==original,strictBeforeEqual=actual==old,**diff,beforeDifferentBytes=before_diff['differentBytes']));exact+=actual==original;total+=len(actual)
    assert web['exactFullBuffers']==exact and web['differentBytes']==sum(c['differentBytes'] for c in comparisons)
    controls=web['controls'];assert [r['mode'] for r in controls]==[0,1,2]
    assert controls[0]['words']==controls[1]['words']==[-1,0,0,0,0,0,0,1,2,0]
    assert controls[2]['words']==[-1,0,1,1,1,0,0,1,2,0] and beforeweb['controls'][2]['words']==[-1,1,1,1,1,0,0,1,2,0]
    renderer=(OUT/'private/portable/sdl/Renderer.cpp').read_text();anm=(OUT/'state-source/AnmRenderer.cpp').read_text();gfx=(OUT/'state-source/GraphicsDevice.hpp').read_text()
    assert 'if(src==dst)return false;' in renderer and 'if(!im[0]||!om[0])return false;' in renderer
    assert renderer.index('if(src==dst)return false;')<renderer.index('flush();auto& input=surface(src)') and renderer.index('if(!im[0]||!om[0])return false;')<renderer.index('flush();auto& input=surface(src)')
    assert 'void AnmRenderer::invalidate(){flush();texture_handle=blend_mode=filter=~0u;uv_sprite=nullptr;}' in anm
    assert 'void changed(u32 handle){auto it=textures.find(handle);if(it!=textures.end()){backend.flush();++it->second.revision;}}' in gfx
    report=dict(privateSuccessDirtyCandidateVerified=True,productionChanged=False,completeGame=False,nativeEquivalent=False,cases=8,comparedRawBytes=total,exactNativeFullBuffers=exact,strictPixelsEqual=exact==8,exactBeforeFullBuffers=sum(c['strictBeforeEqual'] for c in comparisons),differentBytes=sum(c['differentBytes'] for c in comparisons),comparisons=comparisons,controls=controls,beforeFalseReturnControl=beforeweb['controls'][2],candidateFalseReturnControl=controls[2],queueRetirementPreserved=True,nullTargetNoFlushPreserved=True,unconditionalMaterialInvalidationPreserved=True,stateAudit=dict(backendFalseReturnBeforeGLStateMutation=True,successUtilityRenderingRestoresDrawStateCache=True,targetChangedIncrementsTextureRevision=True,anmInvalidateFlushesAndClearsOnlyMaterialCache=True,reason='Only graphics.changed represents a successful target write. ANM invalidate is a separate conservative cache repair, kept after attempted non-null-target copy regardless of bool return. The controlledfalse adapter is not an observed actualGLerror or NativeHRESULT conversion.'),originalHresultControls=baseline['originalDirtyAndRetirementControls'],gpu=web['gpu'],beforeHelperSha256=SHA(before),candidateHelperSha256=SHA(after),candidateHelperPath=str(OUT/'ApplicationCaptureTh14.candidate.hpp'),patchSha256=build['patchSha256'],patchPath=str(OUT/'success-dirty.patch'),wasmSha256=build['wasmSha256'],retainedBuildGuardFailure=bind(OUT/'attempt01-crlf-guard/failure.json'),bindings=[bind(p) for p in [previous,BASE/'native.json',BASE/'webgl-capture/report.json',OUT/'webgl-build.json',OUT/'webgl-capture/report.json',OUT/'capture.wasm',OUT/'capture.mjs',OUT/'ApplicationCaptureTh14.before.hpp',OUT/'ApplicationCaptureTh14.candidate.hpp',OUT/'success-dirty.patch',helper,ROOT/'tools/th14-deferred-capture-success-dirty-build.py',ROOT/'tools/th14-deferred-capture-success-dirty-serve.mjs']],stateBindings=build['stateBindings'],toolSha256=SHA(Path(__file__).read_bytes()),scope='One private helper change only: bool successful backend copy controls target revision/dirty notification. Same8 complete independent original32 D3DX bytes and3 explicitly labelled null/controlledfalse retirement controls. All shader/renderer/fixture code and compilation flags retained,8 before-pixel buffers independently compared. No production edit, actualGLfailure observation, full Native game frame equivalence, or universal APIerror mapping.')
    REPORT.write_bytes((json.dumps(report,indent=2)+'\n').encode());(OUT/'candidate-complete.json').write_bytes((json.dumps(dict(reportSha256=SHA(REPORT.read_bytes()),patchSha256=build['patchSha256'],helperSha256=SHA(after),toolSha256=report['toolSha256']),indent=2)+'\n').encode());print(json.dumps({k:report[k] for k in ['privateSuccessDirtyCandidateVerified','cases','comparedRawBytes','exactNativeFullBuffers','exactBeforeFullBuffers','differentBytes','candidateHelperSha256','patchSha256']}))
if __name__=='__main__':main()
