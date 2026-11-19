#include "GameOwnerRuntime.hpp"
#include "AnmInstance.hpp"
#include <algorithm>

namespace th143 {
GameOwnerRuntime::GameOwnerRuntime(GameFrameRuntime& f,AnmWorld& a,GameOwnerServices& s)
    :input(input_self,*this),frames(f),animations(a),services(s){frames.animations=&a;}
AnmView GameOwnerRuntime::mapped(u32 p,u32 n){
    auto region=[&](u32 token,u8* bytes,u32 count)->AnmView{
        return bytes&&p>=token&&std::uint64_t(p)+n<=std::uint64_t(token)+count?AnmView{bytes+p-token}:AnmView{nullptr};
    };
    struct Owner{u32 bit,token;u8* data;u32 bytes;};
    for(auto r:{Owner{1,player_self,player.data.data(),u32(player.data.size())},
        {2,equipment_self,equipment.data.data(),u32(equipment.data.size())},
        {4,input_self,input.manager.data.data(),u32(input.manager.data.size())},
        {8,BulletPool::token_base,bullets.data.data(),BulletPool::bytes},
        {16,ItemPool::token_base,items.data.data(),ItemPool::bytes},
        {32,laser_self,lasers.data(),u32(lasers.size())},
        {64,ScorePopups::token,scores.data.data(),ScorePopups::bytes}}){
        if(created&r.bit){auto v=region(r.token,r.data,r.bytes);if(v.data)return v;}
    }
    auto v=region(shots.token,shots.data.data(),u32(shots.data.size()));if(v.data)return v;
    v=region(frames.scheduler.self,frames.scheduler.data.data(),u32(frames.scheduler.data.size()));if(v.data)return v;
    auto it=frames.scheduler.records.upper_bound(p);
    if(it!=frames.scheduler.records.begin()){--it;v=region(it->first,it->second.data(),u32(it->second.size()));if(v.data)return v;}
    if(auto* bytes=storage.find(p,n))return {bytes};
    return {nullptr};
}
bool GameOwnerRuntime::read(u32 p,void* out,u32 n){auto v=mapped(p,n);if(!v.data)return false;std::memcpy(out,v.data,n);return true;}
bool GameOwnerRuntime::write(u32 p,const void* in,u32 n){auto v=mapped(p,n);if(!v.data)return false;std::memcpy(v.data,in,n);return true;}
bool GameOwnerRuntime::reserve(u32 bit,u32 token,u8* bytes,u32 n){
    if(created&bit)return false;
    if(!services.reserve_game_owner(token,n))return false;
    std::fill(bytes,bytes+n,services.game_allocation_fill());created|=bit;return true;
}
bool GameOwnerRuntime::allocate(u32 n,u32& p){
    if(!services.allocate_game_storage(n,p)||!p)return false;
    storage.push_back({p,std::vector<u8>(std::max(1u,n),services.game_allocation_fill())});return true;
}
bool GameOwnerRuntime::callback(u32 e,i32 priority,bool draw,u32 owner,u32& p){
    const u32 fill=u32(services.game_allocation_fill())*0x01010101u;
    return allocate(0x28,p)&&frames.register_callback(p,e,owner,priority,draw,(fill&~3u)|1);
}
bool GameOwnerRuntime::pair(u32 self,AnmView owner,u32 update,i32 up,u32 draw,i32 dp){
    u32 p;if(!callback(update,up,false,self,p))return false;owner.put(8,p);
    if(!callback(draw,dp,true,self,p))return false;owner.put(12,p);return true;
}
bool GameOwnerRuntime::equipment_allocate(u32 n,u32& p,AnmView& v){if(!allocate(n,p))return false;v=mapped(p,n);return v.data;}
bool GameOwnerRuntime::bind_initial_visual(PlayerState& p){
    auto* r=animations.resource(p.get(0x10));if(!r||r->templates.empty())return false;
    AnmView vm{p.data.data()+0x14};anm_copy_template(vm,player_self+0x14,{r->templates[0].data()},animations.global_rate_token());
    vm.put(0x594,0);return anm_step(vm,animations)!=-2;
}
bool GameOwnerRuntime::create(u32 entry,u32 mode,GameManagerInitGlobals& g,u32& result){
    result=0;if(failed)return false;
    bool okay=false;u32 resource=0;
    switch(entry){
    case 0x44ca60:{
        if(!reserve(1,player_self,player.data.data(),u32(player.data.size())))break;
        player_construct(player);
        if(!services.request_game_resource(9,"pl00.anm",resource)||!resource)break;
        player.put(0x10,resource);std::vector<u8> raw;
        if(!services.read_player_shots(raw)||!services.reserve_game_owner(shots_self,u32(raw.size()))||!shots.load(raw.data(),u32(raw.size()),shots_self))break;
        player.put(0x688,shots_self);
        if(!pair(player_self,{player.data.data()},0x44e3d0,23,0x44e3f0,28))break;
        PlayerInitConfig c{player_self,resource,player.get(8),player.get(12),animations.global_rate_token()};
        if(!player_initialize(player,shots,c,power,*this))break;
        g.game_state[25]=power.maximum;g.game_state[26]=power.step;
        frames.player=&player;result=player_self;okay=true;break;
    }
    case 0x450660:
        if(!reserve(2,equipment_self,equipment.data.data(),u32(equipment.data.size())))break;
        equipment.construct();if(!initialize_player_equipment(equipment,equipment_self,*this))break;
        frames.equipment=&equipment;result=equipment_self;okay=true;break;
    case 0x454740:
        if(mode||!reserve(4,input_self,input.manager.data.data(),u32(input.manager.data.size())))break;
        input.manager.construct();if(!input.initialize_recording(g))break;
        frames.input=&input;result=input_self;okay=true;break;
    case 0x412880:
        if(!reserve(8,BulletPool::token_base,bullets.data.data(),BulletPool::bytes))break;
        std::fill(bullets.data.begin(),bullets.data.end(),0);
        if(!services.request_game_resource(7,"bullet.anm",resource)||!resource)break;
        bullets.put(0x9bf6cc,resource);bullets.put(0x10,BulletPool::bullet(0));bullets.data[0x9beeda]=6;
        if(!pair(BulletPool::token_base,{bullets.data.data()},0x413ae0,28,0x413b10,36))break;
        bullets.initialize(resource,bullets.get(8),bullets.get(12));frames.bullets=&bullets;
        result=BulletPool::token_base;okay=true;break;
    case 0x434fc0:
        if(!reserve(16,ItemPool::token_base,items.data.data(),ItemPool::bytes))break;
        items.construct();if(!pair(ItemPool::token_base,{items.data.data()},0x435fd0,29,0x436000,32))break;
        items.reset_storage();frames.items=&items;result=ItemPool::token_base;okay=true;break;
    case 0x438dd0:{
        if(!reserve(32,laser_self,lasers.data(),u32(lasers.size())))break;
        lasers.fill(0);AnmView s{lasers.data()};s.put(0x5d8,0x10000);
        if(!services.request_game_resource(7,"bullet.anm",resource)||!resource)break;
        s.put(0x5f4,resource);if(!pair(laser_self,s,0x438fb0,27,0x439020,34))break;
        s.put(0x5d0,laser_self+0x10);frames.laser_manager=laser_self;result=laser_self;okay=true;break;
    }
    case 0x45d4e0:{
        if(!reserve(64,ScorePopups::token,scores.data.data(),ScorePopups::bytes))break;
        scores.construct();for(auto& r:animations.resources)if(r.file==2){resource=r.token;break;}
        scores.put(0x10,resource);
        if(!resource||!pair(ScorePopups::token,{scores.data.data()},0x45dad0,21,0x45dae0,45))break;
        const u32 update=scores.get(8),draw=scores.get(12);
        if(!scores.initialize(resource,animations))break;scores.put(8,update);scores.put(12,draw);
        frames.scores=&scores;frames.score_host=static_cast<AnmVmHost*>(&animations);result=ScorePopups::token;okay=true;break;
    }
    default:return false;
    }
    if(!okay)failed=true;return okay;
}
}
