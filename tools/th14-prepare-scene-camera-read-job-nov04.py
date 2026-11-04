"""Prepare a private resumable incoming Scene camera read in the staged loader."""
from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/scene-camera-read-job-nov04';J=R/'artifacts/th14/camera-normalize-store-order-nov04';SHA=lambda b:hashlib.sha256(b).hexdigest()
assert not(H/'source').exists()and not(H/'prepared.json').exists();shutil.copytree(J/'source',H/'source');source=H/'source';changes=[]
def change(name,transform):
 path=source/name;before=path.read_bytes();text=before.decode().replace('\r\n','\n');assert b'R"'not in before
 text=transform(text);after=text.replace('\n','\r\n').encode()if b'\r\n'in before else text.encode();assert before!=after;path.write_bytes(after);changes.append(dict(path=name,beforeSha256=SHA(before),afterSha256=SHA(after)))
def header(text):
 old='#include "StagedLoaderPrototype.hpp"';assert text.count(old)==1;text=text.replace(old,old+'\n#include "SceneCameraReadJobTh14.hpp"')
 old='    bool stage_initialization_started=false,stage_initialization_finished=false;';assert text.count(old)==1
 return text.replace(old,old+'\n    SceneCameraReadJobTh14 stage_camera_read_job;\n    std::unique_ptr<Stage> incoming_scene_owner;\n    std::function<prototype::Work(u32)> stage_camera_read_boundary;')
def cpp(text):
 old='    pending_stage=number;next_stage_source=&source;next_stage_initializer=std::move(initialize);';assert text.count(old)==1
 text=text.replace(old,'    if(!stage_camera_read_job.reset()){error="TH14 scene camera read still active";return false;}\n    incoming_scene_owner.reset();\n'+old)
 old='''    stage=std::make_unique<Stage>(animations,incoming->background,resources.core.text,compositor.clear_color,u16((pending_stage&1)+3));
    stage->active_camera=&compositor.world_camera;
    if(!stage->initialize(incoming->scene,pending_stage,compositor.world_camera,false)){error=stage->error;return prototype::Work::Failed;}''';assert text.count(old)==1
 new='''    // Native40d445 reads75 words while the main publisher may be active.
    // Keep the incoming owner private until all reads and initialization finish.
    if(!incoming_scene_owner){
        incoming_scene_owner=std::make_unique<Stage>(animations,incoming->background,resources.core.text,compositor.clear_color,u16((pending_stage&1)+3));
        incoming_scene_owner->active_camera=&compositor.world_camera;
    }
    const auto copied=stage_camera_read_job.advance(compositor.world_camera,[this](u32 word){
        return stage_camera_read_boundary?stage_camera_read_boundary(word):prototype::Work::Ready;
    });
    if(copied!=prototype::Work::Ready){
        if(copied==prototype::Work::Failed)error="TH14 scene camera read failed";
        return copied;
    }
    if(!incoming_scene_owner->initialize(incoming->scene,pending_stage,stage_camera_read_job.snapshot(),false)){error=incoming_scene_owner->error;return prototype::Work::Failed;}
    stage=std::move(incoming_scene_owner);'''
 return text.replace(old,new)
change('th12_web/cpp/game/GameBattle.hpp',header);change('th12_web/cpp/game/GameBattle.cpp',cpp)
name='th12_web/cpp/game/SceneCameraReadJobTh14.hpp';data=(H/'SceneCameraReadJobTh14.hpp').read_bytes();(source/name).write_bytes(data);changes.append(dict(path=name,beforeSha256=None,afterSha256=SHA(data)))
base=J/'build/observer-build.json';report=dict(prepared=True,baseBuild=base.relative_to(R).as_posix(),baseBuildSha256=SHA(base.read_bytes()),sourceRoot=str(source),changes=changes,
 sourcePreparationToolSha256=SHA(Path(__file__).read_bytes()),sessionLayoutChanged=True,gameBattleLayoutChanged=True,newHeader=name,
 nativeRepComponentSha256=SHA((H/'native.json').read_bytes()),candidateComponentSha256=SHA((H/'component-verified.json').read_bytes()),rootProductionSourcesModified=False,productionIntegrated=False,completeGame=False,nativeEquivalent=False)
(H/'prepared.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(json.dumps(report))
