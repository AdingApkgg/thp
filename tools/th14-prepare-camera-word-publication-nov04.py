"""Add mapped camera-word delivery and a Scene-only loader poll at an executing Stage."""
from pathlib import Path
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists()
 basepath=R/'artifacts/th14/stage-object-snapshot-readiness-nov04/build/ordinary/observer-build.json';basebytes=basepath.read_bytes();base=json.loads(basebytes);old=Path(base['sourceSnapshotRoot']);source=out/'source';changes=[]
 for name,digest in {**base['sourceHashes'],**base['headerHashes']}.items():
  raw=(old/name).read_bytes();assert SHA(raw)==digest;target=source/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
 def edit(name,before_text,after_text,count=1):
  path=source/'th12_web/cpp/game'/name;before=path.read_bytes();text=before.decode().replace('\r\n','\n');assert text.count(before_text)==count,(name,before_text,text.count(before_text));text=text.replace(before_text,after_text)
  ending='\r\n'if before.count(b'\r\n')==before.count(b'\n')and b'\r\n'in before else'\n';after=text.replace('\n',ending).encode();path.write_bytes(after)
  row=next((x for x in changes if x['path']=='th12_web/cpp/game/'+name),None)
  if row:row['afterSha256']=SHA(after)
  else:changes.append(dict(path='th12_web/cpp/game/'+name,beforeSha256=SHA(before),afterSha256=SHA(after)))
 edit('Stage.hpp','using StageObjectVmBoundaryTh14=', 'using StageCameraWordBoundaryTh14=std::function<bool(const Stage&,u32)>;\nusing StageObjectVmBoundaryTh14=')
 edit('Stage.hpp','''    bool update(
#if PORT_TITLE == 14
        const StageObjectVmBoundaryTh14& object_boundary={}
#endif''','''    bool update(
#if PORT_TITLE == 14
        const StageObjectVmBoundaryTh14& object_boundary={}
        ,const StageCameraWordBoundaryTh14& camera_word_boundary={}
#endif''')
 edit('Stage.hpp','    void publish_camera();','''    bool publish_camera(
#if PORT_TITLE == 14
        const StageCameraWordBoundaryTh14& camera_word_boundary={}
#endif
    );''')
 edit('Stage.cpp','#include <cmath>','#include <cmath>\n#include <type_traits>')
 edit('Stage.cpp','''bool Stage::update(
#if PORT_TITLE == 14
    const StageObjectVmBoundaryTh14& object_boundary
#endif''','''bool Stage::update(
#if PORT_TITLE == 14
    const StageObjectVmBoundaryTh14& object_boundary
    ,const StageCameraWordBoundaryTh14& camera_word_boundary
#endif''')
 edit('Stage.cpp','    state.frame_effect=0;publish_camera();','''    state.frame_effect=0;if(!publish_camera(
#if PORT_TITLE == 14
        camera_word_boundary
#endif
    ))return false;''')
 edit('Stage.cpp','''void Stage::publish_camera(){
    if(!active_camera)return;
    *active_camera=state.camera;''','''bool Stage::publish_camera(
#if PORT_TITLE == 14
    const StageCameraWordBoundaryTh14& camera_word_boundary
#endif
){
    if(!active_camera)return true;
#if PORT_TITLE == 14
    static_assert(std::is_trivially_copyable<SceneCamera>::value);
    static_assert(sizeof(SceneCamera)%sizeof(u32)==0);
    // Retail40dae7 publishes with REP MOVSD. Only the mapped camera words
    // are modeled here; two additional native copied words remain opaque.
    if(camera_word_boundary){
        if(!camera_word_boundary(*this,0)){error="loading before camera publication";return false;}
        for(u32 i=0;i<sizeof(SceneCamera)/sizeof(u32);++i){
            std::memcpy(reinterpret_cast<u8*>(active_camera)+i*sizeof(u32),
                reinterpret_cast<const u8*>(&state.camera)+i*sizeof(u32),sizeof(u32));
            if(!camera_word_boundary(*this,i+1)){error="loading during camera publication";return false;}
        }
    }else *active_camera=state.camera;
#else
    *active_camera=state.camera;
#endif''')
 edit('Stage.cpp','    manager.camera_delta=active_camera->animation_delta;\n}','    manager.camera_delta=active_camera->animation_delta;return true;\n}')
 edit('GameBattle.hpp','    bool poll_stage_initialization(u64 now);','    bool poll_stage_initialization(u64 now);\n    bool poll_stage_scene(u64 now);')
 edit('GameBattle.hpp','        ,const StageObjectVmBoundaryTh14& stage_object_boundary={}\n','        ,const StageObjectVmBoundaryTh14& stage_object_boundary={}\n        ,const StageCameraWordBoundaryTh14& camera_word_boundary={}\n')
 edit('GameBattle.cpp','bool GameBattle::retire_stage_owner(){','''bool GameBattle::poll_stage_scene(u64 now){
    if(!pending_stage)return true;
    BattleStageActions actions(*this);
    if(stage_loader.poll_scene(actions,now))return true;
    if(error.empty())error="TH14 stage scene copy stopped";
    return false;
}
bool GameBattle::retire_stage_owner(){''')
 edit('GameBattle.cpp','    ,const StageObjectVmBoundaryTh14& stage_object_boundary\n','    ,const StageObjectVmBoundaryTh14& stage_object_boundary\n    ,const StageCameraWordBoundaryTh14& camera_word_boundary\n')
 edit('GameBattle.cpp','        stage_object_boundary\n#endif','        stage_object_boundary,pending_stage?camera_word_boundary:StageCameraWordBoundaryTh14{}\n#endif',2)
 edit('GameSession.hpp','    StageObjectVmBoundaryTh14 stage_load_object_boundary;','    StageObjectVmBoundaryTh14 stage_load_object_boundary;\n    StageCameraWordBoundaryTh14 stage_load_camera_word_boundary;')
 edit('GameSession.cpp','''            return battle->poll_stage_initialization(stage_load_clock());
        }
#endif
        );''','''            return battle->poll_stage_initialization(stage_load_clock());
        }
        ,[this](const Stage& owner,u32 copied_words){
            if(!battle->pending_stage)return true;
            if(stage_load_camera_word_boundary&&!stage_load_camera_word_boundary(owner,copied_words))return false;
            // Only Scene may progress while the publisher is borrowed. Do not
            // run Timeline or the controller's later Stage retirement here.
            return battle->poll_stage_scene(stage_load_clock());
        }
#endif
        );''')
 edit('StagedLoaderPrototype.hpp','bool initial_stage=false,has_sample=false,initializing=false;','bool initial_stage=false,has_sample=false,initializing=false,preparing_scene=false;')
 marker=' bool pump(StageActions& actions,u64 now,i32 first_capture_index,u32 supervisor_flags){'
 helper=''' // Complete only an already-entered Scene phase while the Stage is borrowed.
 bool poll_scene(StageActions& actions,u64 now){
  if(phase==LoadPhase::Aborted||phase==LoadPhase::Failed)return false;
  if(preparing_scene||phase!=LoadPhase::Scene)return true;
  if(has_sample&&now<last_sample){phase=LoadPhase::Failed;return false;}
  has_sample=true;last_sample=now;
  struct Guard{bool& flag;Guard(bool& f):flag(f){flag=true;}~Guard(){flag=false;}}guard(preparing_scene);
  const auto result=actions.prepare_scene();
  if(result==Work::Waiting)return true;
  if(result==Work::Failed||!actions.publish_empty_owner()){phase=LoadPhase::Failed;return false;}
  phase=LoadPhase::Timeline;return true;
 }
'''
 edit('StagedLoaderPrototype.hpp',marker,helper+marker)
 edit('StagedLoaderPrototype.hpp',marker+'\n',marker+'\n  if(preparing_scene)return true;\n')
 edit('StagedLoaderPrototype.hpp','''    const auto result=actions.prepare_scene();
    if(result==Work::Waiting)return true;
    if(result==Work::Failed){phase=LoadPhase::Failed;return false;}
    if(!actions.publish_empty_owner()){phase=LoadPhase::Failed;return false;}
    phase=LoadPhase::Timeline;''','''    if(!poll_scene(actions,now))return false;
    if(phase==LoadPhase::Scene)return true;''')
 result=dict(prepared=True,baseBuild=basepath.relative_to(R).as_posix(),baseBuildSha256=SHA(basebytes),sourceRoot=str(source),changes=changes,sessionLayoutChanged=True,gameBattleLayoutChanged=True,mappedCameraDwords=73,nativePublicationDwords=75,additionalNativeCopiedWordsStillOpaque=2,sceneOnlyPollingWhileStageBorrowed=True,timelineNotAdvancedAtCameraWords=True,originalOldRecordingScheduleRecovered=False,rootProductionSourcesModified=False,productionIntegrated=False,oldFailureClosed=False,completeGame=False,nativeEquivalent=False,preparerSha256=SHA(Path(__file__).read_bytes()))
 (out/'prepared.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result),flush=True)
if __name__=='__main__':main()
