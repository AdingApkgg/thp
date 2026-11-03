"""Freeze explicit loader checkpoints around outgoing/background object VMs."""
from pathlib import Path
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(R/'artifacts/th14')and not out.exists()
    base_path=R/'artifacts/th14/overlay-vm-boundaries-v2-nov04/build/ordinary/observer-build.json';base_raw=base_path.read_bytes();base=json.loads(base_raw)
    assert base['wasmSha256']=='a2f732df6464dc0b698716d836543a86c7eda9416d419138f7c2c7e4ac08c94f'
    source=out/'source';old=Path(base['sourceSnapshotRoot']);changes=[]
    for name,digest in {**base['sourceHashes'],**base['headerHashes']}.items():
        raw=(old/name).read_bytes();assert sha(raw)==digest;target=source/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    def replace(text,old,new):assert text.count(old)==1,(old,text.count(old));return text.replace(old,new)
    def edit(name,transform):
        path=source/'th12_web/cpp/game'/name;before=path.read_bytes();text=transform(before.decode().replace('\r\n','\n'))
        ending='\r\n'if before.count(b'\r\n')==before.count(b'\n')and b'\r\n'in before else'\n';after=text.replace('\n',ending).encode();path.write_bytes(after)
        changes.append(dict(path='th12_web/cpp/game/'+name,beforeSha256=sha(before),afterSha256=sha(after)))
    def stage_header(text):
        text=replace(text,'class Stage final:public StageScriptWorld {','''#if PORT_TITLE == 14
class Stage;
using StageObjectVmBoundaryTh14=std::function<bool(const Stage&,const AnmVm&,u32,u32,u32,AnmManager::VmBoundaryTh14)>;
#endif
class Stage final:public StageScriptWorld {''')
        for name in('update','update_objects'):
            text=replace(text,'    bool '+name+'();','    bool '+name+'(\n#if PORT_TITLE == 14\n        const StageObjectVmBoundaryTh14& object_boundary={}\n#endif\n    );')
        return text
    edit('Stage.hpp',stage_header)
    def stage(text):
        first=text.index('bool Stage::update_objects(){');last=text.index('bool Stage::update(){',first)
        text=text[:first]+'''bool Stage::update_objects(
#if PORT_TITLE == 14
    const StageObjectVmBoundaryTh14& object_boundary
#endif
){
    for(u32 object_index=0;object_index<resource.objects.size();++object_index){
        auto& object=resource.objects[object_index];if(!(object.flags&1))continue;u32 active=0;
        for(u32 primitive_index=0;primitive_index<object.primitives.size();++primitive_index){
            const auto& primitive=object.primitives[primitive_index];auto& vm=object_animations[primitive.animation];
#if PORT_TITLE == 14
            // Retail40f2a2 calls this detached background VM;40f2a7 resumes.
            if(object_boundary&&!object_boundary(*this,vm,object_index,primitive_index,primitive.animation,AnmManager::VmBoundaryTh14::BeforeCall)){
                error="loading before stage object VM call";return false;
            }
#endif
            if(vm.update(manager)<0){error="stage object animation failed";return false;}
#if PORT_TITLE == 14
            if(object_boundary&&!object_boundary(*this,vm,object_index,primitive_index,primitive.animation,AnmManager::VmBoundaryTh14::AfterReturn)){
                error="loading after stage object VM return";return false;
            }
#endif
            if(vm.instruction)++active;
        }
        if(!active)object.flags&=~1u;
    }
    return true;
}
'''+text[last:]
        text=replace(text,'bool Stage::update(){','bool Stage::update(\n#if PORT_TITLE == 14\n    const StageObjectVmBoundaryTh14& object_boundary\n#endif\n){')
        return replace(text,'if(!update_objects()||!update_script())return false;','''if(!update_objects(
#if PORT_TITLE == 14
            object_boundary
#endif
        )||!update_script())return false;''')
    edit('Stage.cpp',stage)
    edit('GameBattle.hpp',lambda text:replace(text,'        ,const AnmManager::VmBoundaryCallbackTh14& normal_vm_boundary={}',
        '        ,const AnmManager::VmBoundaryCallbackTh14& normal_vm_boundary={}\n        ,const StageObjectVmBoundaryTh14& stage_object_boundary={}'))
    def battle(text):
        text=replace(text,'    ,const AnmManager::VmBoundaryCallbackTh14& normal_vm_boundary\n',
            '    ,const AnmManager::VmBoundaryCallbackTh14& normal_vm_boundary\n    ,const StageObjectVmBoundaryTh14& stage_object_boundary\n')
        for name in('stage','outgoing_stage'):
            text=replace(text,'!'+name+'->update()','!'+name+'->update(\n#if PORT_TITLE == 14\n        stage_object_boundary\n#endif\n    )')
        return text
    edit('GameBattle.cpp',battle)
    edit('GameSession.hpp',lambda text:replace(text,'    AnmManager::VmBoundaryCallbackTh14 stage_load_vm_boundary;',
        '    AnmManager::VmBoundaryCallbackTh14 stage_load_vm_boundary;\n    StageObjectVmBoundaryTh14 stage_load_object_boundary;'))
    def session(text):
        marker='''            return battle->pump_stage_loading(stage_load_clock(),
                animations.first_deferred_capture_file_index(),stage_load_host_flags);
        }
#endif
        );'''
        return replace(text,marker,'''            return battle->pump_stage_loading(stage_load_clock(),
                animations.first_deferred_capture_file_index(),stage_load_host_flags);
        }
        ,[this](const Stage& owner,const AnmVm& vm,u32 object,u32 primitive,u32 animation,AnmManager::VmBoundaryTh14 point){
            if(!battle->pending_stage)return true;
            if(stage_load_object_boundary&&!stage_load_object_boundary(owner,vm,object,primitive,animation,point))return false;
            // The owner is executing: finish only Initialize, without replacing
            // or retiring the current scene/resources inside this borrowed call.
            return battle->poll_stage_initialization(stage_load_clock());
        }
#endif
        );''')
    edit('GameSession.cpp',session)
    result=dict(prepared=True,baseBuild=base_path.relative_to(R).as_posix(),baseBuildSha256=sha(base_raw),sourceRoot=str(source),changes=changes,
        sessionLayoutChanged=True,stageStateLayoutChanged=False,stageObjectCallPc=0x40f2a2,stageObjectReturnPc=0x40f2a7,
        objectAndPrimitiveAndAnimationIndicesProvided=True,currentSceneReplacementInsideCallback=False,
        originalFailingRecordVmIdentityRecovered=False,nativeRngOrStateValuesProvidedToEngine=False,
        rootProductionSourcesModified=False,productionIntegrated=False,completeGame=False,nativeEquivalent=False,preparerSha256=sha(Path(__file__).read_bytes()))
    (out/'prepared.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result),flush=True)


if __name__=='__main__':main()
