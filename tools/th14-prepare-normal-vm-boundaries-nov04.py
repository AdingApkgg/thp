"""Freeze typed before-call/after-return worker boundaries in an isolated core."""
from pathlib import Path
import argparse, hashlib, json
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists()
    base_path=R/'artifacts/th14/replay-rng-restore-nov04/step-candidate/core/observer-build.json';base_bytes=base_path.read_bytes();base=json.loads(base_bytes)
    assert base['wasmSha256']=='1e15bb751d12dac304d3d48ec5f70c4a222221c6f4ce444ebb3507773e0e239d'
    old=Path(base['sourceSnapshotRoot']);source=out/'source';changes=[]
    for name,digest in {**base['sourceHashes'],**base['headerHashes']}.items():
        raw=(old/name).read_bytes();assert sha(raw)==digest
        target=source/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    def replace(text,old,new):
        assert text.count(old)==1,(old,text.count(old));return text.replace(old,new)
    def edit(name,transform):
        path=source/'th12_web/cpp/game'/name;before=path.read_bytes();text=transform(before.decode().replace('\r\n','\n'))
        ending='\r\n'if before.count(b'\r\n')==before.count(b'\n')and b'\r\n'in before else'\n'
        after=text.replace('\n',ending).encode();path.write_bytes(after);changes.append(dict(path='th12_web/cpp/game/'+name,beforeSha256=sha(before),afterSha256=sha(after)))
    def manager_header(text):
        return replace(text,'    bool update(bool overlay,const std::function<bool()>& after_vm);',
            '    enum class VmBoundaryTh14:u32 {BeforeCall,AfterReturn};\n'+
            '    using VmBoundaryCallbackTh14=std::function<bool(const AnmVm&,VmBoundaryTh14)>;\n'+
            '    bool update(bool overlay,const std::function<bool()>& after_vm);\n'+
            '    bool update(bool overlay,const VmBoundaryCallbackTh14& boundary);')
    edit('AnmManager.hpp',manager_header)
    def manager(text):
        text=replace(text,'    return update(overlay,{});\n}\nbool AnmManager::update(bool overlay,const std::function<bool()>& after_vm){',
            '    return update(overlay,VmBoundaryCallbackTh14{});\n}\n'+
            'bool AnmManager::update(bool overlay,const std::function<bool()>& after_vm){\n'+
            '    VmBoundaryCallbackTh14 boundary;\n'+
            '    if(after_vm)boundary=[&](const AnmVm&,VmBoundaryTh14 point){return point==VmBoundaryTh14::BeforeCall||after_vm();};\n'+
            '    return update(overlay,boundary);\n}\n'+
            'bool AnmManager::update(bool overlay,const VmBoundaryCallbackTh14& boundary){')
        text=replace(text,'        if(vm.before_update)vm.before_update(vm);const int status=vm.update(*this);',
            '        if(vm.before_update)vm.before_update(vm);\n#if PORT_TITLE == 14\n'+
            '        // Original47e65b calls the VM only after its pre-update callback.\n'+
            '        if(boundary&&!boundary(vm,VmBoundaryTh14::BeforeCall))return false;\n#endif\n'+
            '        const int status=vm.update(*this);')
        return replace(text,'        if(after_vm&&!after_vm())return false;',
            '        if(boundary&&!boundary(vm,VmBoundaryTh14::AfterReturn))return false;')
    edit('AnmManager.cpp',manager)
    edit('GameBattle.hpp',lambda text:replace(text,'        ,const std::function<bool()>& before_normal_animation_update={}',
        '        ,const std::function<bool()>& before_normal_animation_update={}\n'+
        '        ,const AnmManager::VmBoundaryCallbackTh14& normal_vm_boundary={}'))
    def battle(text):
        text=replace(text,'    ,const std::function<bool()>& before_normal_animation_update\n',
            '    ,const std::function<bool()>& before_normal_animation_update\n'+
            '    ,const AnmManager::VmBoundaryCallbackTh14& normal_vm_boundary\n')
        text=replace(text,
            '    std::function<bool()> after_normal_vm;\n'+
            '    if(pending_stage&&before_normal_animation_update)after_normal_vm=[&]{\n'+
            '        if(before_normal_animation_update())return true;\n'+
            '        loading_failed=true;return false;\n'+
            '    };\n'+
            '    if(!animations.update(false,after_normal_vm)){',
            '    AnmManager::VmBoundaryCallbackTh14 vm_boundary;\n'+
            '    if(pending_stage&&(normal_vm_boundary||before_normal_animation_update))vm_boundary=[&](const AnmVm& vm,AnmManager::VmBoundaryTh14 point){\n'+
            '        if(normal_vm_boundary){if(normal_vm_boundary(vm,point))return true;}\n'+
            '        else if(point==AnmManager::VmBoundaryTh14::BeforeCall||before_normal_animation_update())return true;\n'+
            '        loading_failed=true;return false;\n'+
            '    };\n'+
            '    if(!animations.update(false,vm_boundary)){')
        return replace(text,'loading at normal VM return','loading at normal VM boundary')
    edit('GameBattle.cpp',battle)
    edit('GameSession.hpp',lambda text:replace(text,'    u32 stage_load_host_flags=0;',
        '    // An external scheduler can supply readiness at the real VM call/return.\n'+
        '    AnmManager::VmBoundaryCallbackTh14 stage_load_vm_boundary;\n'+
        '    u32 stage_load_host_flags=0;'))
    def session(text):
        marker='''        ,[this](){
            return !battle->pending_stage||battle->pump_stage_loading(stage_load_clock(),
                animations.first_deferred_capture_file_index(),stage_load_host_flags);
        }
#endif
        );'''
        return replace(text,marker,'''        ,[this](){
            return !battle->pending_stage||battle->pump_stage_loading(stage_load_clock(),
                animations.first_deferred_capture_file_index(),stage_load_host_flags);
        }
        ,[this](const AnmVm& vm,AnmManager::VmBoundaryTh14 point){
            if(!battle->pending_stage)return true;
            if(stage_load_vm_boundary&&!stage_load_vm_boundary(vm,point))return false;
            if(point==AnmManager::VmBoundaryTh14::BeforeCall)return battle->poll_stage_initialization(stage_load_clock());
            return battle->pump_stage_loading(stage_load_clock(),
                animations.first_deferred_capture_file_index(),stage_load_host_flags);
        }
#endif
        );''')
    edit('GameSession.cpp',session)
    result=dict(prepared=True,baseBuild=str(base_path.relative_to(R)),baseBuildSha256=sha(base_bytes),sourceRoot=str(source),
        changes=changes,typedOriginalVmCallReturnBoundaries=True,originalBeforeCallPc=0x47e65b,originalAfterReturnPc=0x47e660,
        normalVmCallbackPointersWrapped=False,legacyAfterVmOverloadRetained=True,fullRecompileRequiredForSessionLayout=True,
        nativeRngOrStateValuesProvidedToEngine=False,rootProductionSourcesModified=False,productionIntegrated=False,
        completeGame=False,nativeEquivalent=False,preparerSha256=sha(Path(__file__).read_bytes()))
    (out/'prepared.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({key:value for key,value in result.items()if key!='changes'}))


if __name__=='__main__':main()
