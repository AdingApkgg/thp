#include "GameRenderRuntime.hpp"
#include "AnmFanDraw.hpp"
#include "DirectionVector.hpp"
namespace th143 {
namespace {
//47db40 modes18/19 ->47e9c0/47eb90: an untextured circle or paired ring vertices.
i32 circle_sprite(u32 manager,AnmView vm,const AnmViewport& viewport,u32& depth,AnmRenderMemory& memory,GameRenderDevice& device,AnmSpriteDrawHost& host){
    if(!vm.data)return -2;if(vm.get(0x5bc)&&!host.draw_callback(vm.get(0x5bc),vm))return -2;if(!(vm.get(0x18)&1)||!(vm.get(0x18)&2)||(vm.get(0x1c)&0x20))return -1;
    if(depth){if(!flush_anm_quads(manager,manager,memory,device))return -2;depth=0;if(!device.render_state(14,0))return -2;}
    float radius=vm.floating(0x80)*vm.floating(0x60),thickness=vm.floating(0x84)*vm.floating(0x64),angle=vm.floating(0x50);std::array<float,3> position;if(!anm_position(vm,viewport,host,position))return -2;
    if(vm.get(0x594)&&!(vm.get(0x1c)&0x8000)){auto parent=host.transform_parent(vm.get(0x594));if(!parent.data)return -2;radius=parent.floating(0x60)*radius;thickness=parent.floating(0x64)*thickness;angle=parent.floating(0x50)+angle;}
    const u32 space=(vm.get(0x1c)>>19)&7;if(space==1||space==2){const float scale=space==2?viewport.scale*.5f:viewport.scale;radius=scale*radius;thickness=scale*thickness;}
    if(!configure_anm_render(manager,manager,vm,memory,device))return -2;const bool ring=((vm.get(0x18)>>25)&31)==19;const u32 count=vm.get(0x4ac),sides=ring?2:1;if(signed_word(count)<0||count>1000000)return -2;const u32 bytes=(count+1)*20*sides;u32 cursor;if(!memory.read_render_memory(manager+0xfe8210,&cursor,4))return -2;if(std::uint64_t(cursor)+bytes>=std::uint64_t(manager)+0xfe8210)return 0;
    if(!flush_anm_quads(manager,manager,memory,device))return -2;const float half=thickness*.5f,inner=radius-half,outer=half+radius,tau=real(0x40c90fdb),step=tau/float(signed_word(count));std::vector<u8> data(bytes);
    for(u32 i=0;i<=count;++i){for(u32 side=0;side<sides;++side){DirectionVector p;if(!direction_vector(angle,ring?(side?outer:inner):radius,p))return -2;auto vertex=AnmView{data.data()+(i*sides+side)*20};vertex.put(0,word(p.x+position[0]));vertex.put(4,word(p.y+position[1]));vertex.put(8,0);vertex.put(12,word(1.f));vertex.put(16,vm.get(0x534));}angle+=step;u32 turns=0;while(angle>real(0x40490fdb)){angle-=tau;if(turns++>32)break;}while(real(0xc0490fdb)>angle){angle+=tau;if(turns++>32)break;}}
    if(!memory.write_render_memory(cursor,data.data(),bytes))return -2;u8 configured;if(!memory.read_render_memory(manager+0xbc81a3,&configured,1))return -2;if(configured){if(!device.texture_stage_state(0,4,3)||!device.texture_stage_state(0,1,3))return -2;configured=0;if(!memory.write_render_memory(manager+0xbc81a3,&configured,1))return -2;}
    u8 kind;if(!memory.read_render_memory(manager+0xbc819e,&kind,1))return -2;if(kind!=1){if(!device.texture_stage_state(0,6,0)||!device.texture_stage_state(0,3,0))return -2;kind=1;if(!memory.write_render_memory(manager+0xbc819e,&kind,1))return -2;}
    if(!device.vertex_format(0x44)||!device.primitive_upload(ring?5:3,count*sides,20,data.data(),bytes))return -2;cursor+=bytes;u32 draws;if(!memory.write_render_memory(manager+0xfe8210,&cursor,4)||!memory.read_render_memory(manager+0xcc,&draws,4))return -2;++draws;return memory.write_render_memory(manager+0xcc,&draws,4)?0:-2;
}
}
bool GameRenderRuntime::initialize(const u8* cameras,u32 n,const AnmPoolGlobals& pool,bool static_mesh){
    if(!cameras||n!=0x6e0||!world.pool)return false;application.fill(0);std::memcpy(application.data(),cameras,n);
    AnmView app{application.data()};app.put(8,device.game_device_token());
    std::memcpy(quad.vertices.data(),pool.transforms.data()+0x60,112);
    frame={};frame.width=world.width;frame.height=world.height;frame.device=device.game_device_token();submitted=error=depth_test=0;drawing={};static_scratch.fill(0);
    if(static_mesh){i32 result;if(!initialize_anm_static_mesh(manager,static_scratch,*this,device,result)||result)return false;}return true;
}
bool GameRenderRuntime::read_render_memory(u32 p,void* out,u32 n){
    if(p>=app_self&&std::uint64_t(p)+n<=std::uint64_t(app_self)+application.size()){std::memcpy(out,application.data()+p-app_self,n);return true;}
    return owners.read(p,out,n)||stage.read(p,out,n)||world.read(p,out,n)||device.read_game_render_memory(p,out,n);
}
bool GameRenderRuntime::write_render_memory(u32 p,const void* in,u32 n){
    if(p>=app_self&&std::uint64_t(p)+n<=std::uint64_t(app_self)+application.size()){std::memcpy(application.data()+p-app_self,in,n);return true;}
    return owners.write(p,in,n)||stage.write(p,in,n)||world.write(p,in,n)||device.write_game_render_memory(p,in,n);
}
AnmView GameRenderRuntime::transform_parent(u32 p){
    if(p>=GameOwnerRuntime::player_self&&std::uint64_t(p)+AnmView::bytes<=std::uint64_t(GameOwnerRuntime::player_self)+owners.player.data.size())return {owners.player.data.data()+p-GameOwnerRuntime::player_self};
    if(p>=GameStageRuntime::self&&std::uint64_t(p)+AnmView::bytes<=std::uint64_t(GameStageRuntime::self)+stage.state.data.size())return {stage.state.data.data()+p-GameStageRuntime::self};
    return world.state(p);
}
bool GameRenderRuntime::begin_frame(){
    submitted=error=0;auto app=AnmView{application.data()};std::memcpy(application.data()+0x5b4,stage.camera.data(),stage.camera.size());
    frame.clear_color=stage.script.render_option;frame.first_origin=world.viewport.first_origin;std::memcpy(frame.stage_viewport.data(),application.data()+0x694,16);
    if(!initialize_anm_batches(manager,*this)||!begin_application_frame(app,app_self,manager,frame,*this,device,device))return false;
    world.viewport.first_origin=frame.first_origin;depth_test=app.get(0xa04);drawing.camera_token=app.get(0x6e0);drawing.camera_kind=app.get(0x6e4);drawing.depth_write=app.get(0xa00);drawing.depth_test=depth_test;drawing.origin_x=playfield_origin[0];drawing.origin_y=playfield_origin[1];std::memcpy(render_camera.data.data(),stage.camera.data(),stage.camera.size());return true;
}
bool GameRenderRuntime::draw_player_visual(u32 token,AnmView vm){
    const u32 camera=AnmView{application.data()}.get(0x6e0);
    if(camera<app_self||std::uint64_t(camera)+300>std::uint64_t(app_self)+application.size())return false;
    ++submitted;const i32 result=render_animation(vm,{application.data()+camera-app_self});
    depth_test=drawing.depth_test;AnmView{application.data()}.put(0xa04,depth_test);AnmView{application.data()}.put(0xa00,drawing.depth_write);if(result==-2){error=token;return false;}return true;
}
bool GameRenderRuntime::flush(){return flush_anm_quads(manager,manager,*this,device);}
bool GameRenderRuntime::draw_ascii_glyph(AnmView vm){
    const u32 camera=AnmView{application.data()}.get(0x6e0);if(camera<app_self||std::uint64_t(camera)+300>std::uint64_t(app_self)+application.size())return false;
    ++submitted;return anm_quad_position(vm,world.viewport,*this,quad)&&submit_anm_quad(manager,manager,vm,{application.data()+camera-app_self},quad,1,*this,device);
}
bool GameRenderRuntime::present_ascii(u32 entry,AnmView owner){
    const u32 layer=entry==0x40b5b0?0:entry==0x40b5c0?1:entry==0x40b5d0?2:3;if(layer==3)return false;
    if(layer==1&&!flush())return false;if(layer==2&&!select_camera(0x230,0))return false;
    if(!draw_ascii_layer(owner,layer,world,*this)||!flush()||!select_camera(0x488,2))return false;
    if(layer==1&&!flush())return false;return !layer||select_camera(0x488,2);
}
AnmView GameRenderRuntime::storage(u32 p,u32 n){
    auto region=[&](u32 base,u8* bytes,u32 size)->AnmView{return p>=base&&std::uint64_t(p)+n<=std::uint64_t(base)+size?AnmView{bytes+p-base}:AnmView{nullptr};};
    auto v=region(GameStageRuntime::self,stage.state.data.data(),stage.state.data.size());if(v.data)return v;
    v=region(GameOwnerRuntime::player_self,owners.player.data.data(),owners.player.data.size());if(v.data)return v;
    for(auto& b:stage.storage){v=region(b.token,b.bytes.data(),b.bytes.size());if(v.data)return v;}
    if(world.pool){v=region(world.pool->self,world.pool->data.data(),world.pool->data.size());if(v.data)return v;}
    for(auto& b:world.regions){v=region(b.token,b.bytes.data(),b.bytes.size());if(v.data)return v;}
    return world.state(p);
}
void GameRenderRuntime::publish_drawing(){
    auto app=AnmView{application.data()};app.put(0x6e0,drawing.camera_token);app.put(0x6e4,drawing.camera_kind);app.put(0xa00,drawing.depth_write);app.put(0xa04,drawing.depth_test);depth_test=drawing.depth_test;
    std::memcpy(stage.camera.data(),render_camera.data.data(),stage.camera.size());std::memcpy(application.data()+0x5b4,stage.camera.data(),stage.camera.size());
}
bool GameRenderRuntime::present_stage(bool foreground){
    if(!present_stage_background(stage.state,render_camera,drawing,*this,foreground))return false;publish_drawing();return true;
}
bool GameRenderRuntime::draw_background_layer(i32 layer){return draw_stage_layer(stage.state,GameStageRuntime::self,layer,render_camera,drawing,*this,*this);}
bool GameRenderRuntime::draw_animation_layer(u32 layer){
    if(layer>=42)return false;u32 token;if(!world.read(manager+0xfe87b8+layer*0x5cc,&token,4))return false;
    for(u32 budget=0;token;){if(++budget>1000000)return false;auto vm=storage(token);if(!vm.data)return false;if(!(vm.get(0x1c)&0x20)&&!submit_stage_animation(token,vm))return false;token=vm.get(0x590);}return true;
}
bool GameRenderRuntime::submit_stage_animation(u32 token,AnmView vm){
    ++submitted;const i32 result=render_animation(vm,{render_camera.data.data()});if(result==-2){error=token;return false;}return true;
}
i32 GameRenderRuntime::render_animation(AnmView vm,AnmView camera){
    const u32 mode=(vm.get(0x18)>>25)&31;
    if(mode==18||mode==19)return circle_sprite(manager,vm,world.viewport,drawing.depth_test,*this,device,*this);
    if(mode==17)return draw_anm_fan_sprite(manager,manager,vm,world.viewport,drawing.depth_test,*this,device,device,*this);
    if(mode>=9&&mode<=14&&mode!=10)return draw_anm_geometry_sprite(manager,manager,vm,drawing.depth_test,*this,device,device,*this);
    return draw_anm_sprite(manager,manager,vm,camera,quad,world.viewport,drawing.depth_test,*this,device,*this);
}
bool campaign_hud_message_draw(u32,AnmView);
bool GameRenderRuntime::draw_callback(u32 entry,AnmView vm){
    if(entry==0x430740)return campaign_hud_message_draw(entry,vm);
    if(entry==0x4081e0)return true; // Actual effect7 draw callback is xor eax,eax;ret.
    if(entry==0x40a120)return draw_anm_effect5(manager,manager,vm,world.viewport,drawing.depth_test,drawing.depth_write,*this,device,device,device);error=entry;return false;
}
bool GameRenderRuntime::select_camera(u32 offset,u32 kind){
    if(offset+StageCamera::bytes>application.size())return false;
    auto app=AnmView{application.data()},camera=app.sub(offset);app.put(0x6e0,app_self+offset);drawing.camera_token=app_self+offset;
    //445190 flushes before installing both matrices and the manager origin.
    if(!flush()||!device.application_transform(device.game_device_token(),2,camera.data+0x60)||!device.application_transform(device.game_device_token(),3,camera.data+0xa0)||!set_stage_camera_origin(camera.get(0xfc),camera.get(0x100))||!device.application_viewport(device.game_device_token(),camera.data+0xe0))return false;
    drawing.camera_kind=kind;app.put(0x6e4,kind);return true;
}
bool GameRenderRuntime::set_depth_state(u32 kind,u32 value){
    u32& cached=kind==28?drawing.depth_write:drawing.depth_test;if(cached==value)return true;
    if(!flush())return false;cached=value;auto app=AnmView{application.data()};app.put(kind==28?0xa00:0xa04,value);depth_test=drawing.depth_test;return device.render_state(kind,value);
}
bool GameRenderRuntime::draw_pool_layer(u32 layer){
    if(layer>=42)return false;u32 token;if(!world.read(manager+0xfe87b8+layer*0x5cc,&token,4))return false;
    for(u32 budget=0;token;){if(++budget>1000000)return false;auto vm=storage(token);if(!vm.data)return false;if(!(vm.get(0x1c)&0x20)&&!draw_player_visual(token,vm))return false;token=vm.get(0x590);}return true;
}
bool GameRenderRuntime::draw_pool_callback(u32 entry){
    struct Binding{u32 entry,layer;};static constexpr Binding ordinary[]={
        {0x4831a0,0},{0x4831b0,1},{0x4831c0,2},{0x4831d0,4},
        {0x483270,5},{0x483280,6},{0x483290,7},{0x4832a0,8},{0x4832b0,9},{0x4832c0,10},{0x4832d0,11},
        {0x4832e0,13},{0x4832f0,14},{0x483300,15},{0x483310,16},{0x483320,17},{0x483330,18},{0x483340,12},
        {0x483350,19},{0x483360,21},{0x483370,22},{0x483380,23},{0x483390,29},{0x4833a0,30},{0x4833b0,28},
        {0x4833c0,26},{0x4833d0,25},{0x4833e0,36},{0x4833f0,37},{0x483400,39},{0x483410,40},{0x483420,41}};
    for(auto b:ordinary)if(b.entry==entry)return draw_pool_layer(b.layer);
    if(entry==0x4831e0){
        if(!initialize_pixel_camera({application.data()+0x5b4}))return false;
        std::memcpy(stage.camera.data(),application.data()+0x5b4,stage.camera.size());std::memcpy(render_camera.data.data(),stage.camera.data(),stage.camera.size());
        return select_camera(0x5b4,3)&&set_depth_state(28,0)&&draw_pool_layer(3);
    }
    if(entry==0x483430||entry==0x4834d0||entry==0x483610){
        const bool secondary=entry!=0x483430;
        if(!select_camera(secondary?0x488:0x35c,secondary?2:1)||!set_depth_state(14,0)||!flush()||!device.render_state(23,8))return false;
        if(entry==0x4834d0&&!set_stage_camera_origin(0,0))return false;
        return draw_pool_layer(entry==0x483430?20:entry==0x4834d0?24:35);
    }
    if(entry==0x483580||entry==0x4836b0){
        return select_camera(0x230,0)&&draw_pool_layer(entry==0x483580?27:38)&&select_camera(0x488,2);
    }
    error=entry;return false;
}
}
