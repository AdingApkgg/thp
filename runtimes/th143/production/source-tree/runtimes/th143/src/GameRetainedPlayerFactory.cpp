#include "GameRetainedPlayerFactory.hpp"
#include "AnmInstance.hpp"
namespace th143 {
bool create_player_with_retained_shots(GameOwnerRuntime& owners,GameFrameRuntime& frames,AnmWorld& animations,
    GameOwnerServices& services,u32& cached,GameManagerInitGlobals& game,u32& result){
    result=0;if(owners.failed||(owners.created&1)||!cached||cached!=owners.shots.token||game.game_state[0]+game.game_state[1]!=0)return false;
    auto& player=owners.player;
    if(!services.reserve_game_owner(GameOwnerRuntime::player_self,player.data.size()))return false;
    owners.created|=1;player_construct(player);u32 resource=0;
    if(!services.request_game_resource(9,"pl00.anm",resource)||!resource){owners.failed=true;return false;}
    player.put(0x10,resource);player.put(0x688,cached);cached=0;
    for(auto row:{std::array<u32,4>{0x44e3d0,23,0,8},{0x44e3f0,28,1,12}}){
        u32 token;if(!services.allocate_game_storage(0x28,token)||!token){owners.failed=true;return false;}
        owners.storage.push_back({token,std::vector<u8>(0x28,services.game_allocation_fill())});
        const u32 fill=u32(services.game_allocation_fill())*0x01010101u;
        if(!frames.register_callback(token,row[0],GameOwnerRuntime::player_self,i32(row[1]),row[2]!=0,(fill&~3u)|1)){owners.failed=true;return false;}player.put(row[3],token);
    }
    struct Visual:PlayerInitHost {
        AnmWorld& world;explicit Visual(AnmWorld& w):world(w){}
        bool bind_initial_visual(PlayerState& p)override{auto* r=world.resource(p.get(0x10));if(!r||r->templates.empty())return false;AnmView vm{p.data.data()+0x14};anm_copy_template(vm,GameOwnerRuntime::player_self+0x14,{r->templates[0].data()},world.global_rate_token());vm.put(0x594,0);return anm_step(vm,world)!=-2;}
    }visual(animations);
    if(!player_initialize(player,owners.shots,{GameOwnerRuntime::player_self,resource,player.get(8),player.get(12),animations.global_rate_token()},owners.power,visual)){owners.failed=true;return false;}
    game.game_state[25]=owners.power.maximum;game.game_state[26]=owners.power.step;frames.player=&player;result=GameOwnerRuntime::player_self;return true;
}
}
