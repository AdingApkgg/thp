#include "GameDrawScenes.hpp"
#include "AsciiFrame.hpp"
#include <cmath>
namespace th143 {
bool GameDrawRuntime::read_render_memory(u32 p,void* out,u32 n){
    auto region=[&](u32 base,AnmView v,u32 size){if(!v.data||p<base||std::uint64_t(p)+n>std::uint64_t(base)+size)return false;std::memcpy(out,v.data+p-base,n);return true;};
    return region(app_self,{render.application.data()},render.application.size())||region(0x71000000,bindings.ascii,0x191f0)||owners.read(p,out,n)||stage.read(p,out,n)||world.read(p,out,n)||device.read_game_render_memory(p,out,n);
}
bool GameDrawRuntime::write_render_memory(u32 p,const void* in,u32 n){return owners.write(p,in,n)||world.write(p,in,n)||device.write_game_render_memory(p,in,n);}
AnmView GameDrawRuntime::transform_parent(u32 p){
    if(p>=GameOwnerRuntime::player_self&&std::uint64_t(p)+AnmView::bytes<=std::uint64_t(GameOwnerRuntime::player_self)+owners.player.data.size())return {owners.player.data.data()+p-GameOwnerRuntime::player_self};
    return world.state(p);
}
bool GameDrawRuntime::depth_write(u32 value){
    if(render.drawing.depth_write==value)return true;if(!render.flush())return false;render.drawing.depth_write=value;AnmView{render.application.data()}.put(0xa00,value);return device.render_state(28,value);
}
bool GameDrawRuntime::text(const std::array<float,3>& p,const char* f,double value,bool interface_layer){std::string s;return format_ascii_value(f,value,s)&&queue_ascii_text(bindings.ascii,p,s,world.viewport,interface_layer);}
bool GameDrawRuntime::draw_equipment_option(u32 token){
    u32 table;if(!owners.read(token,&table,4))return false;
    // These six original virtual draw bodies are literally xor eax,eax;ret.
    if(table==0x4c6c28||table==0x4c6c7c||table==0x4c6c98||table==0x4c6cd0||table==0x4c6cec||table==0x4c6d40)return true;
    if(table!=0x4c6d08&&table!=0x4c6d5c)return bindings.equipment&&bindings.equipment->draw_equipment_option(token);
    std::array<u8,0x40> bytes;if(!owners.read(token,bytes.data(),bytes.size()))return false;auto o=AnmView{bytes.data()};if(!o.get(0x1c))return true;auto a=bindings.ascii;if(!a.data)return false;
    const std::array<float,3> p{owners.player.floating(0x5e0)-14.f,owners.player.floating(0x5e4)-40.f,owners.player.floating(0x5e8)};a.put(0x191c8,2);a.put(0x191cc,1);
    const i32 elapsed=signed_word(o.get(8));const bool warning=signed_word(o.get(8)-30)>=signed_word(o.get(0x24));a.put(0x191b0,elapsed%6<3?(warning?0xffff8080:0xffffffff):(warning?0xffa00000:0xff808080));
    const float seconds=float(signed_word(o.get(0x24)-o.get(0x30)))/60.f;if(!text(p,"%.2f",double(seconds)))return false;
    a.put(0x191c8,0);a.put(0x191b0,0xffffffff);a.put(0x191cc,0);return true;
}
bool GameDrawRuntime::special(){
    auto o=bindings.special,a=bindings.ascii;if(!o.data||!a.data)return false;if(!(o.get(0x7c)&1))return true;
    auto vm=world.find(o.get(0x1c));if(!vm.data){o.put(0x1c,0);return true;}
    a.put(0x191c8,2);a.data[0x191b3]=vm.data[0x537];a.put(0x191cc,1);
    if(o.get(0x7c)&2){if(!text({114,36,0},"%8d",double(signed_word(o.get(0x80)))))return false;}
    else if(!text({130,36,0},"$",0))return false;
    a.put(0x191c8,0);a.put(0x191cc,0);a.data[0x191b3]=255;return true;
}
bool GameDrawRuntime::menu(){
    auto o=bindings.menu,a=bindings.ascii;if(!o.data||!a.data)return false;a.put(0x191c4,1);
    auto parent=world.find(o.get(0x1ec));if(!parent.data)o.put(0x1ec,0);
    else{auto child=find_animation_child(world,parent,64);if(child.data){if(!bindings.background.data)return false;bindings.background.put(0x534,child.get(0x534)|0xff000000);}}
    const u32 state=o.get(0x3e4),page=o.get(0x3ec);u32 entry=0;
    if(state==3)entry=0x44b4a0;
    else if(state==1){if(page==9)entry=0x449780;else if(page==10)entry=0x449890;}
    else if(state==2){if(page==7)entry=0x449780;else if(page==8)entry=0x449890;}
    if(entry&&!platform.draw_menu_page(entry,o))return false;a.put(0x191c4,0);return true;
}
bool GameDrawRuntime::input(){
    if(bindings.root.data&&(bindings.root.get(0x80)&4))return true;auto o=owners.input.manager.view();if(!bindings.root.data||o.get(0x10)!=1)return true;
    auto a=bindings.ascii;if(!a.data)return false;const u32 value=o.data[0x68];a.put(0x191b0,value<30?0xff5050ff:value<50?0xffa0a0ff:0xffffffff);
    if(!text({real(0x43ef8000),450,0},"%3d",double(value)))return false;a.put(0x191b0,0xffffffff);return true;
}
bool GameDrawRuntime::timing(){
    if(globals.application_state==15||globals.application_state==4||!bindings.ascii.data)return true;
    if(!bindings.timing.data)return false;const float value=bindings.timing.floating(0x34);bindings.ascii.put(0x191b0,value<30.f?0xff5050ff:value<40.f?0xffa0a0ff:0xffffffff);
    if(!text({588,470,0},"%2.1ffps",double(value)+.05,true))return false;bindings.ascii.put(0x191b0,0xffffffff);return true;
}
bool GameDrawRuntime::lasers(){
    if(!bindings.root.data)return false;if(bindings.root.get(0x80)&4)return true;u32 token=AnmView{owners.lasers.data()}.get(0x18),budget=100000;
    while(token){u32 state,next,vtable,entry;if(!budget--||!owners.read(token+0x10,&state,4)||!owners.read(token+8,&next,4))return false;
        if(state!=1&&(!owners.read(token,&vtable,4)||!(vtable==0x4c5ed8?(entry=0x43ae70,true):vtable==0x4c5da0?(entry=0x440720,true):vtable==0x4c5e70?(entry=0x43d150,true):world.read(vtable+0x14,&entry,4))||!platform.draw_laser_virtual(entry,token)))return false;token=next;
    }return true;
}
bool GameDrawRuntime::score(){
    if(!(globals.game_flags&4)&&!depth_write(0))return false;
    auto score=AnmView{owners.scores.data.data()},vm=score.sub(0x18);const u32 camera=AnmView{render.application.data()}.get(0x6e0);
    if(camera<app_self||std::uint64_t(camera)+300>std::uint64_t(app_self)+render.application.size())return false;AnmView view{render.application.data()+camera-app_self};
    for(u32 i=0;i<28;++i){auto item=score.sub(0x5e4+i*0x48);if(!item.data[0x3c])continue;
        float spacing=8.f;if(signed_word(item.get(0x24))<8)spacing/=item.floating(0x28);const u32 digits=item.data[0x3d];if(digits>12)return false;
        float width=float(digits)*spacing;width*=.5f;vm.put(0x59c,word(item.floating(0xc)-width));vm.put(0x5a0,item.get(0x10));vm.put(0x534,item.get(0x1c));
        float x=owners.player.floating(0x5e0)-item.floating(0xc),y=owners.player.floating(0x5e4)-item.floating(0x10);y*=y;x*=x;y+=x;
        const i32 distance=y>=-2147483648.f&&y<2147483648.f?i32(y):i32(0x80000000);const u32 alpha=distance>16384?208:distance>4096?u32((distance-4096)*160/12288+48):48;
        i32 threshold=(28-i32(digits))*2;
        for(u32 d=0;d<digits;++d,threshold+=2){const u32 digit=item.data[digits-d-1];const i32 time=signed_word(item.get(0x24));i32 sprite=i32(digit)+263;bool submit=true;
            if(time>=threshold-4&&digit!=10){if(time<threshold)sprite=i32(digit)+274;else if(time<threshold+4)sprite=i32(digit)+284;else submit=false;}
            if(submit){u32 token;std::array<u32,17> fields;if(!world.sprite(score.get(0x10),sprite,token,fields))return false;AnmView s{reinterpret_cast<u8*>(fields.data())};vm.put(0x2c,token);
                vm.put(0x3b8,s.get(0x24));vm.put(0x3bc,s.get(0x28));vm.put(0x3c0,s.get(0x2c));vm.put(0x3c4,s.get(0x28));vm.put(0x3c8,s.get(0x24));vm.put(0x3cc,s.get(0x30));vm.put(0x3d0,s.get(0x2c));vm.put(0x3d4,s.get(0x30));
                vm.data[0x537]=u8(alpha);vm.put(0x18,vm.get(0x18)|8);vm.put(0x80,s.get(0x38));
                if(!anm_quad_position(vm,world.viewport,*this,render.quad)||!submit_anm_quad(manager,manager,vm,view,render.quad,1,*this,device))return false;
            }
            vm.put(0x59c,word(vm.floating(0x59c)+spacing));
        }
    }
    auto a=bindings.ascii;if(!a.data)return false;
    for(u32 i=28;i<33;++i){auto item=score.sub(0x5e4+i*0x48);if(!item.data[0x3c])continue;
        a.put(0x191c8,2);a.put(0x191cc,2);a.put(0x191b0,item.get(0x1c));a.put(0x191d4,0);a.put(0x191d8,0);std::array<float,3> p{item.floating(0xc)+224.f,item.floating(0x10)+16.f,item.floating(0x14)};
        if(signed_word(item.get(0x40))>=0){if(!text(p,"BONUS %.1f",double(item.floating(0x44))))return false;p[1]+=11.f;if(!text(p,"%d",double(signed_word(item.get(0x40)))))return false;}
        else if(!text(p,"NO BONUS",0))return false;
        a.put(0x191b0,0xffffffff);a.put(0x191cc,0);a.put(0x191c8,0);a.put(0x191d4,1);a.put(0x191d8,1);
    }return true;
}
bool GameDrawRuntime::invoke(u32 entry,u32 owner,u32& result){result=1;if(body(entry,owner))return true;failed_entry=entry;return false;}
bool GameDrawRuntime::body(u32 entry,u32 owner){
    if(owner==manager)return render.draw_pool_callback(entry);
    if(owner==0x71000000){
        if(entry==0x40b590)return advance_ascii_frame(bindings.ascii);
        return render.present_ascii(entry,bindings.ascii);
    }
    switch(entry){
    case 0x433730:{if(owner!=0x6e004000)return false;const u32 zero=0;for(u32 at:{0xc4,0xc8,0xc0,0xcc})if(!world.write(manager+at,&zero,4))return false;return true;}
    case 0x40e840:case 0x40e850:return owner==GameStageRuntime::self&&render.present_stage(entry==0x40e850);
    case 0x44e3f0:return owner==GameOwnerRuntime::player_self&&draw_player(owners.player,owner,bindings.player?*bindings.player:render);
    case 0x450830:return owner==GameOwnerRuntime::equipment_self&&draw_player_equipment(owners.equipment,*this);
    case 0x413b10:return owner==BulletPool::token_base&&draw_bullet_objects(owners.bullets,bindings.root.data?bindings.root.get(0x80):0,render);
    case 0x436000:return owner==ItemPool::token_base&&draw_item_objects(owners.items,bindings.root.data?bindings.root.get(0x80):0,render);
    case 0x41edf0:return owner==0x6b003000; // Actual body is mov eax,1;ret.
    case 0x41af30:return owner==0x6b008000; // Actual body is mov eax,1;ret.
    case 0x42ecf0:return owner==0x6b006000; // Actual body is mov eax,1;ret.
    case 0x418e20:return owner==0x6b009000&&special();
    case 0x439020:return owner==GameOwnerRuntime::laser_self&&lasers();
    case 0x45dae0:return owner==ScorePopups::token&&score();
    case 0x42ed00:return owner==0x6b006000&&draw_hud_text(bindings.hud,bindings.ascii,bindings.enemy,bindings.special,globals.hud,world);
    case 0x438340:return owner==0x6b004000&&draw_cheat_owner(bindings.cheat,bindings.save,bindings.ascii,world,*this);
    case 0x455490:return owner==GameOwnerRuntime::input_self&&input();
    case 0x448180:return owner==0x6b020000&&menu();
    case 0x42bf70:return owner==0x6b00a000&&timing();
    default:return false;
    }
}
}
