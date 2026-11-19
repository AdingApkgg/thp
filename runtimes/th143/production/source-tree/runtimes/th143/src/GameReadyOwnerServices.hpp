#pragma once
#include "GameOwnerRuntime.hpp"
#include "GameResourceWait.hpp"
namespace th143 {
// Uses the application's storage and cooperative loading schedule while
// keeping the actual resource request/chunk/template code in the shared world.
class GameReadyOwnerServices:public GameOwnerServices {
public:
    GameReadyOwnerServices(GameOwnerServices& next,AnmResourceWorld& world,GameResourceWaitHost& waits):next(next),world(world),waits(waits){}
    bool reserve_game_owner(u32 p,u32 n)override{return next.reserve_game_owner(p,n);}
    bool allocate_game_storage(u32 n,u32& p)override{return next.allocate_game_storage(n,p);}
    bool release_game_storage(u32 p)override{return next.release_game_storage(p);}
    bool request_game_resource(u32 slot,const char* name,u32& token)override{return request_game_animation_ready(world,slot,name,waits,token);}
    bool read_player_shots(std::vector<u8>& bytes)override{return next.read_player_shots(bytes);}
    u8 game_allocation_fill()const override{return next.game_allocation_fill();}
private:GameOwnerServices& next;AnmResourceWorld& world;GameResourceWaitHost& waits;
};
}
