#include "EnemyCombat.hpp"
namespace th143 {
void EnemyCombat::begin_frame(){state.enemy_globals.normal_damage=0;state.enemy_globals.bomb_damage=0;}
float EnemyCombat::exchange_rate(float value){const float previous=state.graphics.rate;state.graphics.rate=value;services.frame_rate(value);return previous;}
bool EnemyCombat::slowdown(ActorState& actor,float value){
    for(u32 i=0;i<24;++i){const u32 at=0x124+i*4;auto vm=state.graphics.find(actor.get(at));if(vm.data)vm.put(0x598,word(value));else actor.put(at,0);}return true;
}
bool EnemyCombat::update_actor(ActorState& actor,EclOwner& current,u32 callback,float rate,i32& result){
    // Phase/death ECL can synchronously spawn another actor through this same
    // runtime; restore the outer actor's bindings when that nested call ends.
    struct Restore {EnemyCombat& self;EclOwner* owner;u32 callback;float elapsed,graphics_rate;
        ~Restore(){self.owner=owner;self.owner_callback=callback;self.elapsed=elapsed;self.exchange_rate(graphics_rate);}
    } restore{*this,owner,owner_callback,elapsed,state.graphics.rate};
    owner=&current;owner_callback=callback;elapsed=rate;exchange_rate(rate);result=0;
    if(const u32 entry=actor.get(0x41d8)){if(!services.actor_callback(entry,actor,result))return false;if(result){result=-1;return true;}}
    state.enemy_globals.player_state=state.player.get(0x684);
    if(!contact_enemy(actor,state.enemy_globals,*this,result))return false;
    if(result)return true;
    if(actor.get(0x41bc)&&!services.auxiliary_update(actor))return false;
    return true;
}
bool EnemyCombat::retire_actor(ActorState& actor,EclOwner& current){
    // Native extra graphics collections require their own memory owner.
    if(actor.get(0x41bc))return false;
    for(u32 i=0;i<24;++i){const u32 at=0x124+i*4;if(!state.graphics.mark_retirement(actor.get(at)))return false;actor.put(at,0);}
    auto* node=current.threads.next;while(node){auto* next=node->next;delete node->value;delete node;node=next;}
    current.threads.next=nullptr;current.active=&current.root;return true;
}
bool EnemyCombat::timer_rate(u32 token,float& value){if(token!=global_rate_token())return false;value=elapsed;return true;}
u32 EnemyCombat::global_rate_token()const{return state.graphics.global_rate_token();}
AnmView EnemyCombat::enemy_visual(u32 handle){return state.graphics.find(handle);}
bool EnemyCombat::enemy_visual_script(AnmView vm,i32 script){return services.visual_script(vm,script);}
bool EnemyCombat::incoming_shots(const PlayerShotImpactQuery& query,PlayerShotContactResult& out){return contact_player_shots(state.player,state.shots,state.shooting,state.shot_globals,query,{},state.shot_services,out);}
bool EnemyCombat::damage_callback(u32 entry,ActorState& actor,i32 incoming,i32& extra){return services.damage_callback(entry,actor,incoming,extra);}
bool EnemyCombat::phase_script(ActorState&,u32 token,bool now,i32& result){const char* name;return owner&&death_script_name(token,name)&&restart_enemy_phase(*owner,name,now,elapsed,result);}
bool EnemyCombat::enemy_death(ActorState& actor,i32& result){return owner&&th143::enemy_death(actor,*owner,owner_callback,state.graphics,state.items,state.gameplay_rng,*this,result);}
bool EnemyCombat::body_callback(u32 entry,ActorState& actor){return services.body_callback(entry,actor);}
bool EnemyCombat::body_circle(const std::array<float,3>& p,float radius,i32& result){return services.body_circle(p,radius,result);}
bool EnemyCombat::body_rectangle(const std::array<float,3>& p,float width,float height,float angle,i32& result){return services.body_rectangle(p,width,height,angle,result);}
bool EnemyCombat::body_graze(){return services.body_graze();}
bool EnemyCombat::enemy_sound(i32 id,float x){return services.sound(id,x);}
bool EnemyCombat::death_sound(i32 id,float x){return services.sound(id,x);}
bool EnemyCombat::death_resource(i32 slot,u32& resource){return services.resource(slot,resource);}
bool EnemyCombat::death_script_name(u32 token,const char*& name){
    for(const auto& file:state.program.files){const auto start=std::uintptr_t(file->bytes.data());
        if(token<start||std::uint64_t(token)>=std::uint64_t(start)+file->bytes.size())continue;
        const u32 offset=u32(token-start);const auto* text=file->bytes.data()+offset;
        if(!std::memchr(text,0,file->bytes.size()-offset))return false;name=reinterpret_cast<const char*>(text);return true;
    }return false;
}
bool EnemyCombat::death_callback(u32 entry,ActorState& actor,EclOwner& current){return services.death_callback(entry,actor,current);}
}
