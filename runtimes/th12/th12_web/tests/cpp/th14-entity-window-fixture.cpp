#include "th14-custom-replay-reference-fixture.cpp"
static std::vector<u32> entity_bullets;
struct ObservedSpawn {u32 frame,count;EnemySpawn descriptor;const char* name;};
static std::vector<ObservedSpawn> observed_spawns;
extern "C" Enemy* __real__ZN4th1112EnemyManager5spawnEPKcRKNS_10EnemySpawnE(EnemyManager*,const char*,const EnemySpawn&);
extern "C" Enemy* __wrap__ZN4th1112EnemyManager5spawnEPKcRKNS_10EnemySpawnE(EnemyManager* manager,const char* name,const EnemySpawn& value){
    const u32 frame=session.battle?session.battle->frame+1:0;
    if(frame>=20540&&frame<=20580)observed_spawns.push_back({frame,manager->count,value,name});
    return __real__ZN4th1112EnemyManager5spawnEPKcRKNS_10EnemySpawnE(manager,name,value);
}
static void observe_entities(const GameBattle& battle){
    observe_reference(battle);entity_bullets.clear();
    if(reference[0]<20540||reference[0]>20580)return;
    for(auto* s=battle.bullets.first_th14();s;s=s->th14_active_next){
        const u32 row[]={u32(s->state),s->flags,u32(s->collision_delay),
            float_word(s->position.x),float_word(s->position.y),float_word(s->position.z),
            float_word(s->velocity.x),float_word(s->velocity.y),float_word(s->velocity.z),float_word(s->speed),float_word(s->angle),
            float_word(s->hitbox.x),float_word(s->hitbox.y),u32(s->lifetime.current),u32(u16(s->sprite))|(u32(u16(s->color))<<16),s->active_transforms};
        entity_bullets.insert(entity_bullets.end(),std::begin(row),std::end(row));
    }
}
API(begin_entity_reference) u32 begin_entity_reference(const u8* data,u32 size){
    if(!begin_custom_reference(data,size))return 0;
    observed_spawns.clear();session.battle->before_player_update=observe_entities;return 1;
}
API(entity_bullet_data) const u32* entity_bullet_data(){return entity_bullets.data();}
API(entity_bullet_words) u32 entity_bullet_words(){return u32(entity_bullets.size());}
API(entity_spawn_count) u32 entity_spawn_count(){return u32(observed_spawns.size());}
API(entity_spawn_data) const u32* entity_spawn_data(u32 index){return index<observed_spawns.size()?&observed_spawns[index].frame:nullptr;}
API(entity_spawn_name) const char* entity_spawn_name(u32 index){return index<observed_spawns.size()?observed_spawns[index].name:nullptr;}
