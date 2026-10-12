#include "../../cpp/game/Stage.hpp"
#include "../../cpp/game/ScreenFade.hpp"
#include "../../cpp/game/AnmRenderer.hpp"
#include <array>
namespace th11::test {
struct PassGraphics final:ZunGraphics {
    touhou::graphics::PipelineState state{};std::vector<u8> data;
    u32 calls=0,texture_id=0,layout=0;
    Matrix4 world{},uv{};u32 topology=0;
    struct TargetEvent {u32 kind,target,color,count;GraphicsViewport rectangle;};
    std::vector<TargetEvent> target_events;u32 target=0;GraphicsViewport viewport;
    struct Submission {u32 target,texture,start,size,topology,count,stride;};
    std::vector<Submission> submissions;
    struct Snapshot {u32 depth_write,depth_compare,fog,layout,factor;Matrix4 world,uv;};
    std::vector<Snapshot> snapshots;
    std::vector<std::array<u32,4>> extras;
    void snapshot(){u32 a,b;std::memcpy(&a,&state.fogNear,4);std::memcpy(&b,&state.fogFar,4);extras.push_back({u32(state.depthCompare)+1,state.fogColor,a,b});snapshots.push_back({state.depthWrite,u32(state.depthCompare),state.fog,layout,state.textureFactor,world,uv});}
    bool select_target(const AnmResource* file,u32 index)override{target=file?index+1:0;viewport={};target_events.push_back({0,target,0,0,{}});return true;}
    // The port gave the virtual a third, defaulted parameter (flags); an override that omits it stops
    // being an override. The parameter is unnamed here because the fixture records the call, and the
    // shape of its event record is read by the suites.
    bool clear_target(u32 color,const GraphicsViewport* rect,u32)override{target_events.push_back({1,target,color,rect?1u:0u,rect?*rect:viewport});return true;}
    void set_viewport(const GraphicsViewport& v)override{viewport=v;}
    touhou::graphics::PipelineState& pipeline()override{return state;}
    u32 texture(const AnmResource&,u32 index)override{return index+1;}
    void bind_texture(u32 handle)override{texture_id=handle;}
    void set_layout(touhou::graphics::VertexLayout v)override{layout=u32(v);}
    void set_matrix(touhou::graphics::MatrixKind kind,const Matrix4& m)override{if(kind==touhou::graphics::MatrixKind::World)world=m;if(kind==touhou::graphics::MatrixKind::Texture)uv=m;}
    void triangles(u32 n,const void* v,u32 stride)override{++calls;snapshot();submissions.push_back({target,texture_id,u32(data.size()),n*3*stride,3,n,stride});const auto* b=static_cast<const u8*>(v);data.insert(data.end(),b,b+n*3*stride);}
    void primitives(touhou::graphics::Topology t,u32 n,const void* v,u32 stride)override{++calls;snapshot();topology=u32(t);const u32 size=touhou::graphics::vertex_count(t,n)*stride;submissions.push_back({target,texture_id,u32(data.size()),size,u32(t),n,stride});const auto* b=static_cast<const u8*>(v);data.insert(data.end(),b,b+size);}
};
}

#include <cstdlib>
using namespace th11;using namespace th11::test;
static AnmManager manager;static AnmResource animations,text;static u32 background=0;
static Stage stage(manager,animations,text,background,3);static PassGraphics graphics;static AnmRenderer renderer(graphics);static SceneCamera camera;static AnmSprite sprite;static std::vector<float> result;static StageResource asset;static float camera_input[16];
static std::vector<u32> draw_states,pass_values,clears;static ScreenFades fades;static u32 fog_color;static float fog_near,fog_far;
static u32 word(float v){u32 r;std::memcpy(&r,&v,4);return r;}
static void observe(){const auto& s=stage.state;const auto& p=graphics.state;pass_values.insert(pass_values.end(),{s.tint,s.draw_flags,u32(s.fade_timer.previous),u32(s.fade_timer.current),word(s.fade_timer.fractional),s.effects_enabled,s.drawn_objects,s.culled_objects,s.drawn_primitives,u32(renderer.tint_enabled),renderer.tint,u32(p.depthWrite),u32(p.depthCompare)+1,u32(p.fog),p.fogColor,word(p.fogNear),word(p.fogFar)});}
static AnmTh14Ribbon ribbon;static std::vector<u32> submissions;
extern "C" int __real__ZN4th1111AnmRenderer4drawERNS_5AnmVmE(AnmRenderer*,AnmVm&);
extern "C" int __wrap__ZN4th1111AnmRenderer4drawERNS_5AnmVmE(AnmRenderer* renderer,AnmVm& vm){
 auto& p=graphics.state;draw_states.insert(draw_states.end(),{u32(&vm-stage.object_animations.data()),u32(p.depthWrite),u32(p.fog)});
 return __real__ZN4th1111AnmRenderer4drawERNS_5AnmVmE(renderer,vm);
}
#define API(name) extern "C" __attribute__((export_name(#name)))
API(run) i32 run(u32 mode,u32 flags,u32 timer,u32 frame,u32 tint,u32 effect,u32 initial_depth,u32 initial_fog,u32 callbacks){
 const u32 mask=0,visibility=3;stage.state={};pass_values.clear();clears.clear();fades.effects.clear();
 draw_states.clear();stage.resource=asset;stage.state.drawn_objects=stage.state.culled_objects=stage.state.drawn_primitives=0;stage.state.draw_distance_squared=9610000;
 stage.object_animations.clear();stage.object_animations.resize(asset.animation_count);camera={};std::memcpy(&camera.position,camera_input,12);std::memcpy(&camera.direction,camera_input+3,12);std::memcpy(&camera.up,camera_input+6,12);std::memcpy(&camera.eye_offset,camera_input+9,12);std::memcpy(&camera.reserved24,camera_input+12,12);camera.fov=camera_input[15];camera.viewport={116,4,408,472,0,1};camera.fog.set(fog_color,fog_near,fog_far);stage.state.camera=camera;stage.state.effects_enabled=3;stage.state.tint=tint;stage.state.frame_effect=effect;stage.state.draw_flags=flags;stage.state.fade_timer.set(timer,&manager.rate);stage.state.frame_count=frame;stage.state.drawn_objects=17;stage.state.culled_objects=19;stage.state.drawn_primitives=23;sprite.width=32;sprite.height=48;
 renderer.invalidate();graphics.data.clear();graphics.submissions.clear();graphics.snapshots.clear();graphics.extras.clear();graphics.target_events.clear();submissions.clear();graphics.state={};graphics.state.depthWrite=initial_depth;graphics.state.fog=initial_fog;graphics.state.depthCompare=touhou::graphics::Compare::Always;renderer.tint_enabled=false;renderer.tint=0x80808080;
 for(u32 n=0;n<80;++n)ribbon.vertices[n]={{float(n*.37),float(double(-int(n))*.71),float(n*1.3)},0x80123456,{float(double(n)/80),.25f}};
 for(u32 i=0;i<asset.animation_count;++i){
  auto& vm=stage.object_animations[i];vm.flags=((mask&(1<<(i%2)))?0x800:0)|((visibility&(1<<(i%2)))?3:0);vm.set_drawing_mode(mode);vm.sprite=&sprite;vm.resource=&animations;vm.scale=vm.extra_scale=vm.texture_scale={1,1};vm.position={180.f+i*24,100.f+i*20,.375f};vm.sprite_size={32,48};vm.integers[0]=40;vm.uv[0]={0,0};vm.uv[1]={1,0};vm.uv[2]={0,1};vm.uv[3]={1,1};vm.inherited_color=0xff123456;vm.secondary_color=0xffabcdef;vm.th13_effect=callbacks&(1<<(i%2))?8:0;vm.geometry=&ribbon;vm.uv_matrix.identity();vm.color=0xff123456;
 }
 bool ok=true;for(u32 repeat=0;repeat<2;++repeat){ok&=stage.draw_background(renderer,camera,fades);observe();ok&=stage.draw_foreground(renderer,camera);observe();}
 renderer.flush();for(u32 i=0;i<graphics.submissions.size();++i){const auto& draw=graphics.submissions[i];const auto& p=graphics.snapshots[i];const auto* words=reinterpret_cast<const u32*>(graphics.data.data()+draw.start);
  if(draw.stride==28){for(u32 q=0;q<draw.count/2;++q){submissions.insert(submissions.end(),{0,p.depth_write,p.fog});for(u32 index:{0u,1u,2u,5u})submissions.insert(submissions.end(),words+(q*6+index)*7,words+(q*6+index)*7+7);}}
  else{if(draw.stride==24)submissions.insert(submissions.end(),{1,draw.topology+1,draw.count,draw.stride,p.depth_write,p.fog});else if(draw.stride==20)submissions.insert(submissions.end(),{2,draw.topology+1,draw.count,p.depth_write,p.fog,p.factor});else return 0;submissions.insert(submissions.end(),graphics.extras[i].begin(),graphics.extras[i].end());const auto* w=reinterpret_cast<const u32*>(p.world.m);const auto* uv=reinterpret_cast<const u32*>(p.uv.m);submissions.insert(submissions.end(),w,w+16);submissions.insert(submissions.end(),uv,uv+16);submissions.insert(submissions.end(),words,words+draw.size/4);}
 }
 result.resize(asset.animation_count*6);for(u32 i=0;i<asset.animation_count;++i){const auto& vm=stage.object_animations[i];result[i*6]=vm.position.x;result[i*6+1]=vm.position.y;result[i*6+2]=vm.position.z;result[i*6+3]=vm.scale.x;result[i*6+4]=vm.scale.y;result[i*6+5]=(vm.flags&8)!=0;}
 for(const auto& e:graphics.target_events)if(e.kind==1){const auto& r=e.rectangle;clears.insert(clears.end(),{3,e.color,u32(r.x),u32(r.y),u32(r.x+r.width),u32(r.y+r.height)});}return ok;
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

API(pass_field) u32 pass_field(u32 i){return pass_values[i];}API(clear_words) u32 clear_words(){return clears.size();}API(clear_data) const u32* clear_data(){return clears.data();}API(fade_count) u32 fade_count(){return fades.effects.size();}
API(camera_fog) void camera_fog(u32 color,float near,float far){fog_color=color;fog_near=near;fog_far=far;}
