#include "../../cpp/game/SceneCompositor.hpp"
#include "render-fixture.hpp"
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
using namespace th11;
using namespace th11::test;
static AnmManager manager;
static AnmResource text;
static SceneCompositor compositor(manager);
static RecordingGraphics graphics;
static AnmRenderer renderer(graphics);
#define API(name) extern "C" __attribute__((export_name(#name)))
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(open_resource) i32 open_resource(const void* p,u32 n){return text.open(static_cast<const u8*>(p),n)&&compositor.initialize(text);}
API(copy_count) u32 copy_count(){return sizeof(compositor.copies)/sizeof(compositor.copies[0]);}
API(copy_script) i32 copy_script(u32 i){return compositor.copies[i].script_index;}
API(camera_reset) void camera_reset(u32 restricted){compositor.reset_cameras(restricted);}
API(camera_value) float camera_value(u32 camera,u32 field){const auto& v=camera==0?compositor.full_camera.viewport:camera==1?compositor.play_camera.viewport:compositor.world_camera.viewport;switch(field){case 0:return v.x;case 1:return v.y;case 2:return v.width;case 3:return v.height;case 4:return v.near_depth;default:return v.far_depth;}}
API(pass_count) u32 pass_count(){return sizeof(scene_draw_passes)/sizeof(scene_draw_passes[0]);}
API(pass_value) u32 pass_value(u32 i,u32 field){const auto& p=scene_draw_passes[i];return field==0?p.priority:field==1?u32(p.kind):p.layer;}
API(draw_pass) i32 draw_pass(u32 i){graphics.target_events.clear();graphics.submissions.clear();graphics.data.clear();compositor.clear_color=0;return compositor.draw(renderer,scene_draw_passes[i].kind);}
API(event_count) u32 event_count(){return graphics.target_events.size();}
API(event_value) u32 event_value(u32 i,u32 field){const auto& e=graphics.target_events[i];switch(field){case 0:return e.kind;case 1:return e.target;case 2:return e.color;case 3:return e.count;case 4:return e.rectangle.x;case 5:return e.rectangle.y;case 6:return e.rectangle.width;default:return e.rectangle.height;}}
API(draw_count) u32 draw_count(){return graphics.submissions.size();}
API(draw_value) float draw_value(u32 i,u32 field){const auto& s=graphics.submissions[i];const auto* v=reinterpret_cast<const AnmVertex*>(graphics.data.data()+s.start);switch(field){case 0:return s.target;case 1:return s.texture;case 2:return s.count;case 3:return v->position.x;case 4:return v->position.y;case 5:return v->uv.x;default:return v->uv.y;}}
API(layer_case) i32 layer_case(u32 layer,u32 overlay){manager.clear();auto* vm=manager.create(text,compositor.copies[0].script_index,0,layer,overlay);if(!vm)return -1;vm->layer=layer;const auto id=vm->id;if(!manager.update(overlay))return -2;vm=manager.find(id);if(!vm)return -3;return manager.layer_first(vm->layer)==vm?i32(vm->layer):-4;}
API(anchor_case) i32 anchor_case(u32 x,u32 y){auto vm=compositor.copies[0];vm.flags=(8u<<22)|(x<<18)|(y<<20)|15;vm.position={17,29,41};vm.script_position={};vm.child_position={};vm.scale={.75f,1.5f};vm.rotation={.7f,.2f,.9f};graphics.data.clear();graphics.submissions.clear();return renderer.draw(vm);}
API(anchor_vertex) float anchor_vertex(u32 i,u32 field){float result;std::memcpy(&result,graphics.data.data()+i*20+field*4,4);return result;}
API(world_component) float world_component(u32 field){return graphics.world.m[field];}
API(address_case) i32 address_case(u32 u,u32 v,u32 previous_u,u32 previous_v){
    renderer.invalidate();graphics.data.clear();graphics.submissions.clear();
    using touhou::graphics::Address;
    const auto from_native=[](u32 value){return value==1?Address::Repeat:value==2?Address::Mirror:Address::Clamp;};
    graphics.state.addressU=from_native(previous_u);graphics.state.addressV=from_native(previous_v);
    auto vm=compositor.copies[0];vm.flags=(8u<<22)|15;vm.flags2=u;vm.th13_native_flags=v<<30;
    return renderer.draw(vm);
}
API(address_value) u32 address_value(u32 axis){using touhou::graphics::Address;const auto value=axis?graphics.state.addressV:graphics.state.addressU;return value==Address::Repeat?1:value==Address::Mirror?2:3;}
API(transform_depth) u32 transform_depth(){return graphics.state.depthWrite;}
API(transform_case) i32 transform_case(u32 p,u32 root_offset,u32 depth){
#if PORT_TITLE == 13
    renderer.invalidate();auto vm=compositor.copies[0];AnmVm ancestor{};ancestor.initialize();
    vm.flags=15|(8u<<22)|(depth<<11);vm.flags2=(p==2?0x10000:0)|(root_offset<<18);
    vm.scale={1.5f,.625f};vm.extra_scale={.75f,1.25f};vm.texture_scale={2.5f,.75f};vm.pivot={3.25f,-5};
    vm.rotation={};vm.position={127.25f,200.75f,.375f};vm.script_position={3.25f,-9.5f,.125f};vm.child_position={4.5f,2.25f,.25f};
    vm.sprite_matrix.identity();vm.sprite_matrix.m[0]=.5;vm.sprite_matrix.m[5]=.25;vm.uv_matrix=vm.sprite_matrix;vm.uv[0]={.125f,.25f};vm.uv_offset={};
    if(p){vm.parent=&ancestor;ancestor.flags2=0x40000;ancestor.position={11.25f,-7.5f,10};}else vm.parent=nullptr;
    return renderer.draw(vm);
#else
    return -1;
#endif
}
API(texture_component) float texture_component(u32 field){return graphics.uv.m[field];}
API(rectangle_case) i32 rectangle_case(u32 mode,u32 ax,u32 ay,u32 parent,u32 segments){
#if PORT_TITLE == 13
    renderer.invalidate();graphics.data.clear();graphics.submissions.clear();
    auto vm=compositor.copies[0];AnmVm ancestor{};ancestor.initialize();
    vm.flags=7|(ax<<18)|(ay<<20);vm.th13_native_flags=0;vm.set_drawing_mode(mode);vm.flags2=parent==2?0x10000:0;
    vm.integers[0]=segments;
    vm.color=0x9f123456;vm.secondary_color=0x6134abcd;vm.sprite=nullptr;
    vm.scale={1.5f,.625f};vm.extra_scale={.75f,1.25f};vm.pivot={3.25f,-5};vm.sprite_size={37.5f,23.25f};
    vm.position={127.25f,200.75f,.375f};vm.script_position={3.25f,-9.5f,.125f};vm.child_position={4.5f,2.25f,.25f};vm.rotation={0,0,.375f};
    vm.parent=parent?&ancestor:nullptr;ancestor.flags2=0x40000;ancestor.position={11.25f,-7.5f,10};ancestor.scale={.5f,2};ancestor.extra_scale={3,4};ancestor.rotation.z=-.625f;
    return renderer.draw(vm);
#else
    return -1;
#endif
}
API(rectangle_component) float rectangle_component(u32 draw,u32 vertex,u32 field){float value;const auto& s=graphics.submissions[draw];std::memcpy(&value,graphics.data.data()+s.start+vertex*s.stride+field*4,4);return value;}
API(rectangle_color) u32 rectangle_color(u32 draw,u32 vertex){u32 value;const auto& s=graphics.submissions[draw];std::memcpy(&value,graphics.data.data()+s.start+vertex*s.stride+16,4);return value;}
API(color_case) i32 color_case(u32 mode,u32 tinted){
    renderer.invalidate();graphics.data.clear();graphics.submissions.clear();auto vm=compositor.copies[0];
    vm.flags=7;vm.flags2=0;vm.th13_native_flags=mode<<17;vm.color=0x9f123456;vm.secondary_color=0x6134abcd;
    vm.position={200,200,0};vm.script_position=vm.child_position={};vm.sprite_size={10,10};vm.scale={1,1};
    renderer.tint_enabled=tinted;renderer.tint=0x4080c0ff;
    const auto result=renderer.draw(vm);renderer.flush();renderer.tint_enabled=false;return result;
}
API(ribbon_draw_case) i32 ribbon_draw_case(u32 p,u32 root_offset,u32 depth){
#if PORT_TITLE == 13
    renderer.invalidate();graphics.data.clear();graphics.submissions.clear();graphics.snapshots.clear();
    auto vm=compositor.copies[0];AnmVm ancestor{};AnmRibbon ribbon{};
    vm.flags=7|(depth<<11);vm.th13_native_flags=0;vm.set_drawing_mode(22);vm.flags2=root_offset<<18;vm.th13_effect=5;vm.geometry=&ribbon;
    vm.parent=p?&ancestor:nullptr;vm.color=0xffffffff;vm.scale={1.5f,.625f};vm.extra_scale={.75f,1.25f};vm.texture_scale={2.5f,.75f};vm.pivot={3.25f,-5};
    vm.rotation={};vm.position={127.25f,200.75f,.375f};vm.script_position={3.25f,-9.5f,.125f};vm.child_position={4.5f,2.25f,.25f};
    vm.uv_matrix.identity();vm.uv_matrix.m[0]=.5;vm.uv_matrix.m[5]=.25;vm.uv[0]={.125f,.25f};vm.uv_offset={};
    for(u32 i=0;i<32;++i)ribbon.vertices[i]={{float(i),float(-i32(i)),float(i*2)},0x80123456,{float(i)/32,.25f}};
    return renderer.draw(vm);
#else
    return -1;
#endif
}
API(world_vertex_color) u32 world_vertex_color(u32 vertex){u32 value;std::memcpy(&value,graphics.data.data()+vertex*24+12,4);return value;}
API(draw_metadata) u32 draw_metadata(u32 draw,u32 field){const auto& s=graphics.submissions[draw];const auto& p=graphics.snapshots[draw];switch(field){case 0:return s.count;case 1:return s.topology;case 2:return s.stride;case 3:return p.depth_write;case 4:return p.fog;default:return p.layout;}}
