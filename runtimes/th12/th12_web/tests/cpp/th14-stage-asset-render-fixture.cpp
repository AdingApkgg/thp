#include "../../cpp/game/Stage.hpp"
#include "../../cpp/game/ScreenFade.hpp"
#include "render-fixture.hpp"
#include <cstdlib>
using namespace th11;using namespace th11::test;
static AnmManager manager;static AnmResource animations,text;static u32 background=0;
static Stage stage(manager,animations,text,background,3);static RecordingGraphics graphics;static AnmRenderer renderer(graphics);static SceneCamera camera;static AnmSprite sprite;static std::vector<float> result;static StageResource asset;static float camera_input[16];
static std::vector<u32> draw_states;
static AnmTh14Ribbon ribbon;static std::vector<u32> submissions;
extern "C" int __real__ZN4th1111AnmRenderer4drawERNS_5AnmVmE(AnmRenderer*,AnmVm&);
extern "C" int __wrap__ZN4th1111AnmRenderer4drawERNS_5AnmVmE(AnmRenderer* renderer,AnmVm& vm){
 auto& p=graphics.state;draw_states.insert(draw_states.end(),{u32(&vm-stage.object_animations.data()),u32(p.depthWrite),u32(p.fog)});
 return __real__ZN4th1111AnmRenderer4drawERNS_5AnmVmE(renderer,vm);
}
#define API(name) extern "C" __attribute__((export_name(#name)))
API(run) i32 run(u32 layer,u32 mode,u32 initial_depth,u32 initial_fog,u32 mask,u32 callbacks,u32 visibility){
 draw_states.clear();stage.resource=asset;stage.state.drawn_objects=stage.state.culled_objects=stage.state.drawn_primitives=0;stage.state.draw_distance_squared=9610000;
 stage.object_animations.clear();stage.object_animations.resize(asset.animation_count);camera={};std::memcpy(&camera.position,camera_input,12);std::memcpy(&camera.direction,camera_input+3,12);std::memcpy(&camera.up,camera_input+6,12);std::memcpy(&camera.eye_offset,camera_input+9,12);std::memcpy(&camera.reserved24,camera_input+12,12);camera.fov=camera_input[15];camera.viewport={116,4,408,472,0,1};sprite.width=32;sprite.height=48;
 renderer.invalidate();graphics.data.clear();graphics.submissions.clear();graphics.snapshots.clear();submissions.clear();graphics.state={};graphics.state.depthWrite=initial_depth;graphics.state.fog=initial_fog;
 for(u32 n=0;n<80;++n)ribbon.vertices[n]={{float(n*.37),float(double(-int(n))*.71),float(n*1.3)},0x80123456,{float(double(n)/80),.25f}};
 for(u32 i=0;i<asset.animation_count;++i){
  auto& vm=stage.object_animations[i];vm.flags=((mask&(1<<(i%2)))?0x800:0)|((visibility&(1<<(i%2)))?3:0);vm.set_drawing_mode(mode);vm.sprite=&sprite;vm.resource=&animations;vm.scale=vm.extra_scale=vm.texture_scale={1,1};vm.position={180.f+i*24,100.f+i*20,.375f};vm.sprite_size={32,48};vm.integers[0]=40;vm.uv[0]={0,0};vm.uv[1]={1,0};vm.uv[2]={0,1};vm.uv[3]={1,1};vm.inherited_color=0xff123456;vm.secondary_color=0xffabcdef;vm.th13_effect=callbacks&(1<<(i%2))?8:0;vm.geometry=&ribbon;vm.uv_matrix.identity();vm.color=0xff123456;
 }
 const bool ok=stage.draw_layer(renderer,camera,layer);
 renderer.flush();for(u32 i=0;i<graphics.submissions.size();++i){const auto& draw=graphics.submissions[i];const auto& p=graphics.snapshots[i];const auto* words=reinterpret_cast<const u32*>(graphics.data.data()+draw.start);
  if(draw.stride==28){for(u32 q=0;q<draw.count/2;++q){submissions.insert(submissions.end(),{0,p.depth_write,p.fog});for(u32 index:{0u,1u,2u,5u})submissions.insert(submissions.end(),words+(q*6+index)*7,words+(q*6+index)*7+7);}}
  else{if(draw.stride==24)submissions.insert(submissions.end(),{1,draw.topology+1,draw.count,draw.stride,p.depth_write,p.fog});else if(draw.stride==20)submissions.insert(submissions.end(),{2,draw.topology+1,draw.count,p.depth_write,p.fog,p.factor});else return 0;const auto* w=reinterpret_cast<const u32*>(p.world.m);const auto* uv=reinterpret_cast<const u32*>(p.uv.m);submissions.insert(submissions.end(),w,w+16);submissions.insert(submissions.end(),uv,uv+16);submissions.insert(submissions.end(),words,words+draw.size/4);}
 }
 result.resize(asset.animation_count*6);for(u32 i=0;i<asset.animation_count;++i){const auto& vm=stage.object_animations[i];result[i*6]=vm.position.x;result[i*6+1]=vm.position.y;result[i*6+2]=vm.position.z;result[i*6+3]=vm.scale.x;result[i*6+4]=vm.scale.y;result[i*6+5]=(vm.flags&8)!=0;}
 return ok;
}
API(vms) const float* vms(){return result.data();}
API(draw_states_data) const u32* draw_states_data(){return draw_states.data();}
API(draw_states_words) u32 draw_states_words(){return draw_states.size();}
API(submissions_data) const u32* submissions_data(){return submissions.data();}API(submissions_words) u32 submissions_words(){return submissions.size();}
API(field) u32 field(u32 index){if(index==0)return stage.state.drawn_objects;if(index==1)return stage.state.culled_objects;if(index==2)return stage.state.drawn_primitives;if(index==3)return graphics.state.depthWrite;return graphics.state.fog;}
API(object_flag) u32 object_flag(u32 index){return stage.resource.objects[index].flags;}API(instance_flag) u32 instance_flag(u32 index){return stage.resource.instances[index].flags;}
API(allocate) void* allocate(u32 n){return std::malloc(n);}API(release) void release(void* p){std::free(p);}
API(open_asset) u32 open_asset(const u8* p,u32 n){return asset.open(p,n);}API(camera_data) float* camera_data(){return camera_input;}
API(vm_words) u32 vm_words(){return result.size();}
