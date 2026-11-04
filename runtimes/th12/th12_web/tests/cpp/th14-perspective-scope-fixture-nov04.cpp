#include "th14-perspective-publication-fixture-nov04.cpp"
namespace {
struct ScopeTestContext {SceneCamera* target;u32 calls=0;u32 fail=~0u;bool reenter=false,reentered=false;};
bool scope_test_callback(void* owner,const SceneCamera&,u32 point){
 auto& c=*static_cast<ScopeTestContext*>(owner);++c.calls;
 if(c.reenter&&!c.reentered){c.reentered=true;c.target->perspective();}
 return point!=c.fail;
}
}
API(perspective_scope_case) u32 perspective_scope_case(u32 mode){
 if(mode<1||mode>6||!perspective_case(0,0,0))return 0;
 SceneCamera a=perspective_camera,b=perspective_camera;ScopeTestContext outer{&a},inner{&b};bool ok=true;
 {
  SceneCameraPerspectiveScopeTh14 first(a,&outer,scope_test_callback);
  if(mode==1){b.perspective();ok=outer.calls==0;a.perspective();ok=ok&&outer.calls==6;}
  if(mode==2){
   {SceneCameraPerspectiveScopeTh14 second(a,&inner,scope_test_callback);a.perspective();ok=inner.calls==6&&outer.calls==0;}
   a.perspective();ok=ok&&outer.calls==6;
  }
  if(mode==3){
   SceneCameraPerspectiveScopeTh14 second(b,&inner,scope_test_callback);a.perspective();ok=outer.calls==6&&inner.calls==0;b.perspective();ok=ok&&inner.calls==6;
  }
  if(mode==4){outer.reenter=true;a.perspective();ok=outer.calls==6&&outer.reentered&&!first.failed;}
  if(mode==5){outer.fail=2;a.perspective();ok=first.failed&&outer.calls==3;a.perspective();ok=ok&&outer.calls==3;}
  if(mode==6){
   inner.fail=4;
   {SceneCameraPerspectiveScopeTh14 second(a,&inner,scope_test_callback);a.perspective();ok=second.failed&&inner.calls==5&&outer.calls==0;}
   a.perspective();ok=ok&&outer.calls==6&&!first.failed;
  }
 }
 if(SceneCameraPerspectiveScopeTh14::active)return 0;
 {ScopeTestContext recovered{&a};SceneCameraPerspectiveScopeTh14 last(a,&recovered,scope_test_callback);a.perspective();ok=ok&&recovered.calls==6&&!last.failed;}
 return ok&&!SceneCameraPerspectiveScopeTh14::active;
}
