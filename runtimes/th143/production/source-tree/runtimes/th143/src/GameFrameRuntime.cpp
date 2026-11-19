#include "GameFrameRuntime.hpp"
namespace th143 {
bool GameFrameRuntime::register_callback(u32 token,u32 entry,u32 owner,i32 priority,bool draw,u32 flags){
    if(!scheduler.create(token,entry))return false;auto v=scheduler.at(token);v.put(4,flags);v.put(0x24,owner);u32 result;return scheduler.add(token,priority,draw,*this,result);
}
bool GameFrameRuntime::dispatch(bool draw,i32& result,u32 budget){failed_entry=failed_owner=0;return scheduler.dispatch(draw,*this,result,budget);}
bool GameFrameRuntime::invoke(u32 entry,u32 owner,u32& result){
    if(!services.before_game_callback(entry,owner)||!body(entry,owner,result)||!services.after_game_callback(entry,owner,result)){failed_entry=entry;failed_owner=owner;return false;}return true;
}
bool GameFrameRuntime::body(u32 entry,u32 owner,u32& result){
    GameInputFrame g;if(!services.frame_input(g))return false;result=1;
    switch(entry){
    case 0x4839e0:return animations&&overlay&&overlay->update(*animations);
    case 0x455420:return input&&input->frame(g);
    case 0x455440:if(!input)return false;result=u32(input->replay_control(g.root_present,g.root_flags,g.raw_keys));return true;
    case 0x45dad0:return scores&&score_host&&scores->update(*score_host);
    case 0x450820:return animations&&equipment&&fresh&&equipment_host&&update_player_equipment(*equipment,animations->rate,*fresh,*equipment_host);
    case 0x450830:return equipment&&equipment_host&&draw_player_equipment(*equipment,*equipment_host);
    case 0x44e3d0:if(!player||!player_globals||!player_host)return false;result=u32(player_frame(*player,*player_globals,*player_host));return signed_word(result)!=-2;
    case 0x41edb0:
        if(!g.root_present||(g.root_flags&0x407))return true;
        return animations&&enemies&&enemies->update(animations->rate);
    case 0x413ae0:
        if(g.root_present&&(g.root_flags&5))return true;
        return bullets&&bullet_host&&bullet_manager_step(*bullets,g.root_present?g.root_flags:0,*bullet_host);
    case 0x438fb0:return animations&&laser_manager&&laser_host&&frame_laser_manager(laser_manager,g.root_present?g.root_flags:0,animations->rate,*laser_host);
    case 0x418e10:
        if(!special_flags)return false;
        if(!(*special_flags&1))return true;
        return services.other_game_callback(entry,owner,result);
    case 0x41af20:return true; // The original body is literally return1.
    case 0x435fd0:
        if(g.root_present&&(g.root_flags&0x405))return true;
        return animations&&items&&item_player&&item_host&&item_manager_step(*items,*item_player,animations->rate,*item_host);
    case 0x4839b0:
        if(g.root_present&&(g.root_flags&5)&&(g.root_flags&2))return true;
        return animations&&animations->update();
    default:return services.other_game_callback(entry,owner,result);
    }
}
}
