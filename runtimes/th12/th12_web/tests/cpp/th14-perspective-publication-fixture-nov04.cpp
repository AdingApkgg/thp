// Synthetic camera inputs shared with the original-instruction component.
#include "SceneCamera.hpp"
#include <cstring>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
namespace {SceneCamera perspective_camera;u32 snapshots[6][73],seen[6],final_words[73];u32 callback_count=0,failed=0,cut_point=0;}
API(perspective_case) u32 perspective_case(u32 profile,u32 cut,u32 fail){
 if(profile>3||cut>5||fail>1)return 0;
 std::memset(&perspective_camera,0,sizeof perspective_camera);
 auto& c=perspective_camera;c.position={12.5f,-3.25f,-600};c.direction={0,300,600};
 const Vec3 directions[]={{0,0,1},{2,3,4},{.25f,-.75f,1.5f},{0,0,0}};
 c.up=profile==2?Vec3{.1f,1,.2f}:Vec3{0,1,0};c.reserved24=directions[profile];
 c.right={9,8,7};c.eye_offset={1,2,3};c.target_offset={.5f,-.5f,.25f};
 c.fov=.5235987901687622f;c.viewport={32,16,384,448,0,1};c.mode=3;c.offset={.25f,-.5f};c.animation_delta={.125f,.25f,.5f};
 c.fog.near_distance=1000;c.fog.far_distance=5000;c.fog.channels[0]=160;c.fog.channels[1]=170;c.fog.channels[2]=180;c.fog.channels[3]=255;c.fog.color=0xffb4aaa0;
 std::memset(snapshots,0,sizeof snapshots);std::memset(seen,0,sizeof seen);callback_count=failed=0;cut_point=fail?cut:~0u;
 {
  SceneCameraPerspectiveScopeTh14 scope(c,nullptr,[](void*,const SceneCamera& camera,u32 point){
   if(point>5)return false;++callback_count;++seen[point];std::memcpy(snapshots[point],&camera,sizeof camera);
   return point!=cut_point;
  });
  c.perspective();failed=scope.failed;
 }
 std::memcpy(final_words,&c,sizeof c);return SceneCameraPerspectiveScopeTh14::active==nullptr;
}
API(perspective_word) u32 perspective_word(u32 point,u32 word){return point<6&&word<73?snapshots[point][word]:~0u;}
API(perspective_final_word) u32 perspective_final_word(u32 word){return word<73?final_words[word]:~0u;}
API(perspective_seen) u32 perspective_seen(u32 point){return point<6?seen[point]:~0u;}
API(perspective_meta) u32 perspective_meta(u32 field){const u32 words[]={callback_count,failed,sizeof(SceneCamera),SceneCameraPerspectiveScopeTh14::active!=nullptr};return field<4?words[field]:~0u;}
