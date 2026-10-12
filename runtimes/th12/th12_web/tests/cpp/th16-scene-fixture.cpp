#include "render-fixture.hpp"
#include "../../cpp/game/SceneCompositor.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;using namespace th11::test;
#define API(name) extern "C" __attribute__((export_name(#name)))
static RecordingGraphics graphics;static AnmRenderer renderer{graphics};
static AnmManager manager;static SceneCompositor scene{manager};static AnmResource resource;
static u32 observed=~0u,calls=0;
static AnmSprite sprite;
static void observe(AnmVm&){observed=renderer.viewport.x; ++calls;}
static SceneCamera& camera(u32 i){return i==0?scene.full_camera:i==1?scene.play_camera:i==2?scene.scaled_play_camera:scene.world_camera;}
API(pass_count) u32 pass_count(){return sizeof(scene_draw_passes)/sizeof(scene_draw_passes[0]);}
API(pass_value) u32 pass_value(u32 n,u32 field){const auto& p=scene_draw_passes[n];return field==0?p.priority:field==1?u32(p.kind):p.layer;}
API(reset_cameras) void reset_cameras(u32 width,u32 height){scene.reset_cameras(true,width,height);}
API(camera_value) u32 camera_value(u32 i,u32 field){const auto& c=camera(i);return field==0?c.viewport.x:field==1?c.viewport.y:field==2?c.viewport.width:field==3?c.viewport.height:c.mode;}
API(run_wrapper) i32 run_wrapper(u32 layer,u32 dirty){
 manager.clear();resource={};resource.scripts.resize(1);resource.scripts[0].bytes.resize(16);const AnmInstruction commands[]={{2,8,0,0},{-1,8,0,0}};std::memcpy(resource.scripts[0].bytes.data(),commands,16);
 auto* vm=manager.create(resource,0,0,layer,layer>=36);if(!vm)return -1;if(!manager.update(layer>=36))return -2;
 vm->flags=0;vm->draw_callback=observe;scene.reset_cameras(true,640,480);
 for(u32 i=0;i<4;++i)camera(i).viewport.x=100+i;
 renderer.set_camera(scene.full_camera,true);renderer.offset={123,456};graphics.state.fog=dirty;graphics.state.depthWrite=dirty;graphics.state.depthCompare=touhou::graphics::Compare::LessEqual;
 observed=~0u;calls=0;return scene.draw_animation(renderer,layer)?0:-3;
}
API(wrapper_value) u32 wrapper_value(u32 field){return field==0?observed:field==1?renderer.viewport.x:field==2?calls:field==3?graphics.state.fog:field==4?graphics.state.depthWrite:field==5?u32(graphics.state.depthCompare):field==6?u32(renderer.offset.x):u32(renderer.offset.y);}
API(bind_copies) i32 bind_copies(u32 width){
 manager.clear();resource={};resource.textures.resize(4);resource.textures[2].kind=resource.textures[3].kind=AnmTexture::Kind::RenderTarget;resource.textures[2].first_script=59;resource.textures[3].first_script=65;resource.scripts.resize(71);
 for(auto& s:resource.scripts){s.bytes.resize(28);const AnmInstruction commands[]={{anm_th16_field2_bit11,12,0,0},{2,8,0,0},{-1,8,0,0}}; // Loader-translated opcode311 writes native flags2 bit11.
  std::memcpy(s.bytes.data(),&commands[0],8);const u32 value=1;std::memcpy(s.bytes.data()+8,&value,4);std::memcpy(s.bytes.data()+12,&commands[1],8);std::memcpy(s.bytes.data()+20,&commands[2],8);
 }
 return scene.initialize(resource,width,width*3/4)?0:-1;
}
API(copy_value) u32 copy_value(u32 i,u32 field){return field==0?scene.copies[i].script_index:(scene.copies[i].flags2>>11)&1;}
API(run_composite) i32 run_composite(u32 kind){
 if(bind_copies(640))return -1;manager.clear();auto* layer=manager.create(resource,0,0,34);if(!layer||!manager.update(false))return -2;layer->flags=0;layer->draw_callback=observe;
 sprite={};sprite.texture=0;sprite.width=sprite.height=16;
 for(u32 i=0;i<4;++i){auto& vm=scene.copies[i];vm.initialize();vm.flags=3;vm.set_drawing_mode(0);vm.color=0xff000001+i;vm.resource=&resource;vm.sprite=&sprite;vm.sprite_size={16,16};vm.scale={1,1};vm.position={200,200,0};}
 for(u32 i=0;i<4;++i)camera(i).viewport.x=100+i;
 renderer.invalidate();graphics.data.clear();graphics.submissions.clear();renderer.set_camera(scene.full_camera,true);graphics.state.depthWrite=true;observed=~0u;calls=0;
 return scene.draw(renderer,SceneDrawKind(kind))?0:-3;
}
API(composite_value) u32 composite_value(u32 field){
 if(field==0){if(graphics.data.size()<sizeof(AnmVertex))return 0;return reinterpret_cast<const AnmVertex*>(graphics.data.data())->color&255;}
 return field==1?calls:field==2?observed:field==3?graphics.state.alphaTest:field==4?graphics.submissions.size():field==5?renderer.viewport.x:graphics.state.depthWrite;
}
