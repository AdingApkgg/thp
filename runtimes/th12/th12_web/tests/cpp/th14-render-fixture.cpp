#include "render-fixture.hpp"
#include <cstdlib>
using namespace th11;using namespace th11::test;using namespace touhou::graphics;
static RenderFixture fixture;
static AnmVm vm{},parent{};
#define API(name) extern "C" __attribute__((export_name(#name)))
static void reset(){
    fixture.renderer.invalidate();fixture.graphics.data.clear();fixture.graphics.submissions.clear();fixture.graphics.snapshots.clear();
    vm.initialize();parent.initialize();vm.resource=&fixture.resource;vm.sprite=&fixture.sprite;
    fixture.renderer.viewport={0,0,640,480,0,1};fixture.renderer.offset={.37f,-.61f};
    fixture.graphics.state.depthWrite=true;
}
API(quad_case) int quad_case(u32 mode,u32 color_mode,u32 relation,u32 tinted,u32 visibility,u32 sample){
    reset();vm.flags=3|((sample%3)<<18)|(((sample/3)%3)<<20);vm.set_drawing_mode(mode);vm.th13_native_flags|=color_mode<<17;
    vm.flags2=(relation==2?0x1000000:relation==3?0x1008000:0)|(visibility==4?0x20:0);
    if(visibility==3)vm.flags&=~1u;
    vm.color=visibility==1||visibility==2?0x00123456:0x9f123456;vm.secondary_color=visibility==2?0x0034abcd:0x6134abcd;
    vm.inherited_color=0x11223344;vm.parent=relation?&parent:nullptr;parent.inherited_color=0x4080c0ff;
    parent.scale={.5,2};parent.extra_scale={3,4};parent.position={11.25,-7.5,10};parent.rotation.z=-.625;
    vm.scale={1.1f,-.625f};vm.extra_scale={.75,1.25};vm.texture_scale={1.37f,-.71f};vm.sprite_size={31.75,47.625};vm.pivot={2.3f,-7.1f};
    vm.position={127.25f+sample*7,200.75f-sample*5,.375};vm.script_position={3.25,-9.5,.125};vm.child_position={4.5,2.25,.25};vm.rotation.z=sample%2?0:.375;
    vm.uv_offset={.17f,-.23f};vm.uv[0]={.123f,.234f};vm.uv[1]={.789f,.345f};vm.uv[2]={.246f,.891f};vm.uv[3]={.912f,.987f};
    fixture.renderer.tint=0x4080c0ff;fixture.renderer.tint_enabled=tinted;
    const auto result=fixture.renderer.draw(vm);fixture.renderer.flush();return result;
}
API(cached_color) u32 cached_color(){return vm.inherited_color;}
API(draw_count) u32 draw_count(){return fixture.graphics.submissions.size();}
API(vertex_value) float vertex_value(u32 vertex,u32 field){const u32 indices[]={0,1,2,5};const auto* v=reinterpret_cast<const AnmVertex*>(fixture.graphics.data.data());const auto& a=v[indices[vertex]];switch(field){case 0:return a.position.x;case 1:return a.position.y;case 2:return a.position.z;case 3:return a.reciprocal_w;case 5:return a.uv.x;default:return a.uv.y;}}
API(vertex_color) u32 vertex_color(u32 vertex){const u32 indices[]={0,1,2,5};return reinterpret_cast<const AnmVertex*>(fixture.graphics.data.data())[indices[vertex]].color;}
API(material_case) int material_case(u32 blend,u32 u,u32 v,u32 point,u32 previous){
    reset();vm.flags=3|((blend&7)<<4)|(point<<31);vm.th13_native_flags=((blend&8)<<5)|(v<<30);vm.flags2=u;
    vm.color=0xffffffff;vm.sprite_size={32,32};vm.position={200,200,0};fixture.renderer.tint_enabled=false;
    auto& p=fixture.graphics.state;p.sourceBlend=BlendFactor::DestinationColor;p.destinationBlend=BlendFactor::DestinationAlpha;p.blendEquation=BlendEquation::Subtract;
    p.addressU=previous==0?Address::Repeat:previous==1?Address::Mirror:Address::Clamp;p.addressV=previous==0?Address::Clamp:previous==1?Address::Repeat:Address::Mirror;
    const auto result=fixture.renderer.draw(vm);fixture.renderer.flush();return result;
}
API(state_value) u32 state_value(u32 field){const auto& p=fixture.graphics.state;switch(field){case 0:return u32(p.sourceBlend)+1;case 1:return u32(p.destinationBlend)+1;case 2:return u32(p.blendEquation)+1;case 3:return p.minFilter==Filter::Nearest?1:2;case 4:return p.magFilter==Filter::Nearest?1:2;case 5:return p.addressU==Address::Repeat?1:p.addressU==Address::Mirror?2:3;case 6:return p.addressV==Address::Repeat?1:p.addressV==Address::Mirror?2:3;default:return p.depthWrite;}}
API(strip_case) int strip_case(u32 mode,u32 has_parent,u32 origin,u32 depth,u32 prior_depth,u32 rotation){
    reset();vm.flags=15|(depth<<11);vm.set_drawing_mode(mode);vm.flags2=origin<<17;vm.parent=has_parent?&parent:nullptr;
    vm.color=0x9f123456;vm.secondary_color=0x6134abcd;vm.integers[0]=6;
    vm.scale={1.1f,-.625};vm.extra_scale={.75,1.25};vm.texture_scale={1.37f,-.71f};vm.sprite_size={31.75,47.625};vm.pivot={2.3f,-7.1f};
    vm.position={127.25,200.75,.375};vm.script_position={3.25,-9.5,.125};vm.child_position={4.5,2.25,.25};
    const Vec3 angles[]={{0,0,0},{.375,-.75,1.125},{1.25,.25,-2.75}};vm.rotation=angles[rotation];
    vm.uv_matrix.identity();vm.uv_matrix.m[0]=.5;vm.uv_matrix.m[5]=.25;vm.uv[0]={.123f,.234f};vm.uv_offset={.17f,-.23f};
    static AnmTh14Ribbon ribbon;static AnmVertex screen[12];
    const bool world=mode==22||mode==23||mode==24;const u32 count=mode==22?80:12;
    for(u32 i=0;i<count;++i){const Vec3 p={float(i*.37),float(-double(i)*.71),float(i*1.3)};const Vec2 uv={float(double(i)/count),.25};if(world)ribbon.vertices[i]={p,0x80123456,uv};else screen[i]={p,1,0x80123456,uv};}
    vm.geometry=world?static_cast<void*>(&ribbon):screen;vm.th13_effect=mode==22?8:0;fixture.renderer.tint_enabled=false;
    fixture.graphics.state.depthWrite=prior_depth;fixture.graphics.state.fog=false;
    const auto result=fixture.renderer.draw(vm);fixture.renderer.flush();return result;
}
API(strip_metadata) u32 strip_metadata(u32 field){const auto& s=fixture.graphics.submissions[0];const auto& p=fixture.graphics.snapshots[0];switch(field){case 0:return s.count;case 1:return s.stride;case 2:return p.depth_write;case 3:return p.fog;case 4:return fixture.graphics.state.depthWrite;case 5:return fixture.graphics.state.fog;default:return s.topology;}}
API(strip_matrix) float strip_matrix(u32 texture,u32 field){const auto& s=fixture.graphics.snapshots[0];return (texture?s.uv:s.world).m[field];}
API(strip_component) float strip_component(u32 vertex,u32 field){float v;const auto& s=fixture.graphics.submissions[0];std::memcpy(&v,fixture.graphics.data.data()+s.start+vertex*s.stride+field*4,4);return v;}
API(strip_color) u32 strip_color(u32 vertex){u32 v;const auto& s=fixture.graphics.submissions[0];std::memcpy(&v,fixture.graphics.data.data()+s.start+vertex*s.stride+(s.stride==24?12:16),4);return v;}
API(shape_case) int shape_case(u32 mode,u32 anchor,u32 has_parent,u32 resolution){
    quad_case(22,0,0,0,0,0);fixture.renderer.invalidate();fixture.graphics.data.clear();fixture.graphics.submissions.clear();fixture.graphics.snapshots.clear();
    vm.flags=3|((anchor%3)<<18)|((anchor/3)<<20);vm.set_drawing_mode(mode);vm.flags2=(resolution<<19)|(has_parent==2?0x8000:0);
    vm.parent=has_parent?&parent:nullptr;vm.integers[0]=7;vm.sprite=nullptr;
    const auto result=fixture.renderer.draw(vm);fixture.renderer.flush();return result;
}
API(shape_metadata) u32 shape_metadata(u32 draw,u32 field){const auto& s=fixture.graphics.submissions[draw];const auto& p=fixture.graphics.snapshots[draw];return field==0?s.count:field==1?s.stride:field==2?p.depth_write:s.topology;}
API(shape_component) float shape_component(u32 draw,u32 vertex,u32 field){float v;const auto& s=fixture.graphics.submissions[draw];std::memcpy(&v,fixture.graphics.data.data()+s.start+vertex*s.stride+field*4,4);return v;}
API(shape_color) u32 shape_color(u32 draw,u32 vertex){u32 v;const auto& s=fixture.graphics.submissions[draw];std::memcpy(&v,fixture.graphics.data.data()+s.start+vertex*s.stride+16,4);return v;}
API(world_case) int world_case(u32 has_parent,u32 origin,u32 resolution,u32 order,u32 anchor,u32 depth,u32 color_mode,u32 tinted){
    quad_case(22,color_mode,0,tinted,0,0);fixture.renderer.invalidate();fixture.graphics.data.clear();fixture.graphics.submissions.clear();fixture.graphics.snapshots.clear();
    vm.flags=15|(depth<<11)|((anchor%3)<<18)|((anchor/3)<<20);vm.set_drawing_mode(8);vm.th13_native_flags|=color_mode<<17;
    vm.flags2=(origin<<17)|(resolution<<19)|(order<<2)|(has_parent==2?0x8000:0)|0x400000;
    vm.parent=has_parent?&parent:nullptr;parent.flags2=1<<17;vm.rotation={.375,-.75,1.125};
    vm.sprite_matrix.identity();vm.sprite_matrix.m[0]=.5;vm.sprite_matrix.m[5]=.25;vm.uv_matrix=vm.sprite_matrix;
    fixture.graphics.state.depthWrite=true;const auto result=fixture.renderer.draw(vm);fixture.renderer.flush();return result;
}
API(world_factor) u32 world_factor(){return fixture.graphics.snapshots[0].factor;}
API(screen_strip_case) int screen_strip_case(u32 blend,u32 visibility,u32 count,u32 prior_depth){
 reset();vm.flags=3|((blend&7)<<4);vm.th13_native_flags=(blend&8)<<5;
 vm.flags2=visibility==4?0x20:0;if(visibility==3)vm.flags&=~1u;
 vm.color=visibility==1||visibility==2?0x00123456:0x9f123456;vm.secondary_color=visibility==2?0x0034abcd:0x6134abcd;
 fixture.renderer.tint_enabled=false;auto& p=fixture.graphics.state;p.depthWrite=prior_depth;
 p.sourceBlend=BlendFactor::DestinationColor;p.destinationBlend=BlendFactor::DestinationAlpha;p.blendEquation=BlendEquation::Subtract;
 static AnmVertex data[240];for(u32 i=0;i<count;++i)data[i]={{float(double(i)*.37),float(-double(i)*.71),float(double(i)*1.3)},1,0xffffffff,{float(double(i)/count),.25}};
 return fixture.renderer.draw_th14_screen_strip(vm,data,count);
}
