"""Freeze overlay dispatch and place BeforeCall before the VM pre-update callback."""
from pathlib import Path
import argparse, hashlib, json
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists()
    base_path=R/'artifacts/th14/normal-vm-boundaries-v2-nov04/build/ordinary/observer-build.json';base_raw=base_path.read_bytes();base=json.loads(base_raw)
    assert base['wasmSha256']=='59f98d528450a7f960a8c471d99b300b084cb5a2aea9232116cc2897d48b21f6'
    old=Path(base['sourceSnapshotRoot']);source=out/'source'
    for name,digest in {**base['sourceHashes'],**base['headerHashes']}.items():
        raw=(old/name).read_bytes();assert sha(raw)==digest
        target=source/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    path=source/'th12_web/cpp/game/GameBattle.cpp';before=path.read_bytes();text=before.decode().replace('\r\n','\n')
    block='''#if PORT_TITLE == 14
    // Resume at priority9 continues this frame; overlay8 has already run.
    if(!overlay_already_updated)
#endif
    if(!animations.update(true)){last_error=-1005;if(error.empty())error="overlay animation update: "+animations.last_error_text();return false;}
'''
    replacement='''#if PORT_TITLE == 14
    // The worker may finish during overlay ANM8 as well as normal ANM29.
    // Keep the legacy normal-only callback out of the overlay traversal.
    bool overlay_loading_failed=false;
    AnmManager::VmBoundaryCallbackTh14 overlay_boundary;
    if(pending_stage&&normal_vm_boundary)overlay_boundary=[&](const AnmVm& vm,AnmManager::VmBoundaryTh14 point){
        if(normal_vm_boundary(vm,point))return true;
        overlay_loading_failed=true;return false;
    };
    // Resume at priority9 continues this frame; overlay8 has already run.
    if(!overlay_already_updated&&!animations.update(true,overlay_boundary)){
        last_error=overlay_loading_failed?-1009:-1005;
        if(error.empty())error=overlay_loading_failed?"loading at overlay VM boundary":"overlay animation update: "+animations.last_error_text();
        return false;
    }
#else
    if(!animations.update(true)){last_error=-1005;if(error.empty())error="overlay animation update: "+animations.last_error_text();return false;}
#endif
'''
    assert text.count(block)==1;text=text.replace(block,replacement)
    ending='\r\n'if before.count(b'\r\n')==before.count(b'\n')and b'\r\n'in before else'\n'
    after=text.replace('\n',ending).encode();path.write_bytes(after)
    manager=source/'th12_web/cpp/game/AnmManager.cpp';manager_before=manager.read_bytes();manager_text=manager_before.decode().replace('\r\n','\n')
    old_order='''        if(vm.before_update)vm.before_update(vm);
#if PORT_TITLE == 14
        // Original47e65b calls the VM only after its pre-update callback.
        if(boundary&&!boundary(vm,VmBoundaryTh14::BeforeCall))return false;
#endif
        const int status=vm.update(*this);'''
    new_order='''#if PORT_TITLE == 14
        // Original47e65b/47e73b precede the callback inside46fe50 at46ff1f.
        if(boundary&&!boundary(vm,VmBoundaryTh14::BeforeCall))return false;
#endif
        if(vm.before_update)vm.before_update(vm);
        const int status=vm.update(*this);'''
    assert manager_text.count(old_order)==1;manager_text=manager_text.replace(old_order,new_order)
    manager_ending='\r\n'if manager_before.count(b'\r\n')==manager_before.count(b'\n')and b'\r\n'in manager_before else'\n'
    manager_after=manager_text.replace('\n',manager_ending).encode();manager.write_bytes(manager_after)
    result=dict(prepared=True,baseBuild=base_path.relative_to(R).as_posix(),baseBuildSha256=sha(base_raw),sourceRoot=str(source),
        changes=[dict(path='th12_web/cpp/game/GameBattle.cpp',beforeSha256=sha(before),afterSha256=sha(after)),dict(path='th12_web/cpp/game/AnmManager.cpp',beforeSha256=sha(manager_before),afterSha256=sha(manager_after))],
        overlayAndNormalTypedVmBoundaries=True,beforeCallPrecedesPreUpdateCallback=True,legacyNormalOnlyCallbackUnchanged=True,
        sessionLayoutChanged=False,rootProductionSourcesModified=False,productionIntegrated=False,
        nativeRngOrStateValuesProvidedToEngine=False,completeGame=False,nativeEquivalent=False,preparerSha256=sha(Path(__file__).read_bytes()))
    (out/'prepared.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result),flush=True)


if __name__=='__main__':main()
