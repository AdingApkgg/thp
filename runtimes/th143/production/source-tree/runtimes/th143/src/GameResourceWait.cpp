#include "GameResourceWait.hpp"
namespace th143 {
bool request_game_animation_ready(AnmResourceWorld& world,u32 slot,const char* name,GameResourceWaitHost& host,u32& token,u32 budget){
    if(!name||!world.request(slot,name,token))return false;if(!token)return true;
    u32 pending;if(!world.read(token+0x128,&pending,4))return false;
    while(pending){if(!budget--||!host.resource_wait(1)||!world.read(token+0x128,&pending,4))return false;}
    return world.resource(token)!=nullptr;
}
}
