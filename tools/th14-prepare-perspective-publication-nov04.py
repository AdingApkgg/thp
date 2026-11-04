"""Prepare isolated TH14 perspective publication boundaries from the published core."""
from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[1];O=R/'artifacts/th14/perspective-publication-nov04';B=R/'artifacts/th14/camera-native-order-nov04/build/ordinary/observer-build.json';SHA=lambda b:hashlib.sha256(b).hexdigest()
assert not O.exists();O.mkdir();base=json.loads(B.read_bytes());source=O/'source';shutil.copytree(base['sourceSnapshotRoot'],source);changes=[]
def change(name,fn):
 p=source/name;old=p.read_bytes();text=old.decode();ending='\r\n'if b'\r\n'in old and old.count(b'\r\n')==old.count(b'\n')else'\n';new=fn(text.replace('\r\n','\n')).replace('\n',ending).encode();assert new!=old;p.write_bytes(new);changes.append(dict(path=name,beforeSha256=SHA(old),afterSha256=SHA(new)))
def header(s):
 marker='static_assert(sizeof(SceneCamera)==0x118+(kPortTitle==13||kPortTitle==14?12:0));';assert s.count(marker)==1
 return s.replace(marker,marker+"""
#if PORT_TITLE == 14
// Original446400 publication phases. This scope observes one camera without
// changing SceneCamera's native-mapped layout or intercepting other cameras.
struct SceneCameraPerspectiveScopeTh14 {
 using Callback=bool(*)(void*,const SceneCamera&,u32);
 SceneCamera* camera;void* owner;Callback callback;SceneCameraPerspectiveScopeTh14* previous;
 bool running=false,failed=false;
 static inline SceneCameraPerspectiveScopeTh14* active=nullptr;
 SceneCameraPerspectiveScopeTh14(SceneCamera& c,void* o,Callback f):camera(&c),owner(o),callback(f),previous(active){active=this;}
 ~SceneCameraPerspectiveScopeTh14(){active=previous;}
 SceneCameraPerspectiveScopeTh14(const SceneCameraPerspectiveScopeTh14&)=delete;
 SceneCameraPerspectiveScopeTh14& operator=(const SceneCameraPerspectiveScopeTh14&)=delete;
 static bool checkpoint(const SceneCamera& c,u32 point){
  for(auto* scope=active;scope;scope=scope->previous){
   if(scope->camera!=&c)continue;
   if(scope->failed)return false;
   if(scope->running)return true;
   scope->running=true;scope->failed=!scope->callback(scope->owner,c,point);scope->running=false;
   return !scope->failed;
  }
  return true;
 }
};
#endif
""")
change('th12_web/cpp/game/SceneCamera.hpp',header)
def camera(s):
 s=s.replace('void SceneCamera::perspective(){','''void SceneCamera::perspective(){
#if PORT_TITLE == 14
    if(!SceneCameraPerspectiveScopeTh14::checkpoint(*this,0))return;
#endif''')
 marker='    projection=GraphicsMath::perspective(';i=s.index(marker);s=s[:i]+'''#if PORT_TITLE == 14
    if(!SceneCameraPerspectiveScopeTh14::checkpoint(*this,1))return;
#endif
'''+s[i:]
 marker='    // Retail446539..44659d rounds each SSE product before subtraction.';assert s.count(marker)==1;s=s.replace(marker,'    if(!SceneCameraPerspectiveScopeTh14::checkpoint(*this,2))return;\n'+marker)
 marker='    right=GraphicsMath::normalize(axis);';assert s.count(marker)==1
 s=s.replace(marker,'''    // Native446590 stores XY,44659d stores Z, then D3DX normalizes in place.
    right.x=axis.x;right.y=axis.y;
    if(!SceneCameraPerspectiveScopeTh14::checkpoint(*this,3))return;
    right.z=axis.z;
    if(!SceneCameraPerspectiveScopeTh14::checkpoint(*this,4))return;
    right=GraphicsMath::normalize(right);
    if(!SceneCameraPerspectiveScopeTh14::checkpoint(*this,5))return;''')
 return s
change('th12_web/cpp/game/SceneCamera.cpp',camera)
def session_header(s):
 marker='    StageCameraWordBoundaryTh14 stage_load_camera_word_boundary;';assert s.count(marker)==1;return s.replace(marker,marker+'\n    std::function<bool(const SceneCamera&,u32)> stage_load_perspective_boundary;')
change('th12_web/cpp/game/GameSession.hpp',session_header)
def session(s):
 marker='    const std::function<bool()> camera_published=[this](){';assert s.count(marker)==1
 s=s.replace(marker,'''    SceneCameraPerspectiveScopeTh14 perspective_scope(compositor.world_camera,this,
        [](void* owner,const SceneCamera& camera,u32 point){
            auto& session=*static_cast<GameSession*>(owner);
            if(!session.battle||!session.battle->pending_stage)return true;
            if(session.stage_load_perspective_boundary&&!session.stage_load_perspective_boundary(camera,point))return false;
            // A draw borrows its Stage owner. Complete only an already-entered
            // Scene copy; Timeline/retirement remain outside this scope.
            return session.battle->poll_stage_scene(session.stage_load_clock());
        });
'''+marker)
 marker='        if(overlay&&pass.kind==SceneDrawKind::AsciiOuter';assert s.count(marker)==1
 s=s.replace(marker,'''#if PORT_TITLE == 14
        if(perspective_scope.failed)return fail("TH14 worker failed during perspective publication");
#endif
'''+marker)
 return s
change('th12_web/cpp/game/GameSession.cpp',session)
prep=dict(prepared=True,baseBuild=B.relative_to(R).as_posix(),baseBuildSha256=SHA(B.read_bytes()),sourceRoot=str(source),changes=changes,sessionLayoutChanged=True,preparerSha256=SHA(Path(__file__).read_bytes()),nativePerspectiveBoundaries=6,matrixInternalStoresNotModeled=True,rootProductionSourcesModified=False,productionIntegrated=False,oldFailureClosed=False,completeGame=False)
(O/'prepared.json').write_bytes((json.dumps(prep,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in prep.items()if k!='changes'}),flush=True)
