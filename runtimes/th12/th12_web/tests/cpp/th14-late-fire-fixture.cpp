#include "th14-late-collision-fixture.cpp"
static std::vector<u32> observed_fire_words;
extern "C" bool __real__ZN4th1113BulletManager9fire_th14ERKNS_17Th14BulletEmitterE(BulletManager*,const Th14BulletEmitter&);
extern "C" bool __wrap__ZN4th1113BulletManager9fire_th14ERKNS_17Th14BulletEmitterE(BulletManager* manager,const Th14BulletEmitter& emitter){
    const u32 frame=session.battle?session.battle->frame+1:0;
    if(frame>=15850&&frame<=16180){
        observed_fire_words.push_back(frame);
        observed_fire_words.push_back(float_word(session.battle->animations.rate));
        observed_fire_words.push_back(float_word(manager->player.x));
        observed_fire_words.push_back(float_word(manager->player.y));
        observed_fire_words.push_back(float_word(manager->exclusion_squared));
        const auto begin=observed_fire_words.size();observed_fire_words.resize(begin+224);
        std::memcpy(observed_fire_words.data()+begin,&emitter,sizeof emitter);
    }
    return __real__ZN4th1113BulletManager9fire_th14ERKNS_17Th14BulletEmitterE(manager,emitter);
}
static void observe_fire_reference(const GameBattle& battle){
    observe_collision(battle);
    collision_bullets.clear();
    if(reference[0]<15850||reference[0]>16180)return;
    for(auto* s=battle.bullets.first_th14();s;s=s->th14_active_next){
        const u32 row[]={u32(s->state),s->flags,u32(s->collision_delay),
            float_word(s->position.x),float_word(s->position.y),float_word(s->position.z),
            float_word(s->velocity.x),float_word(s->velocity.y),float_word(s->velocity.z),
            float_word(s->speed),float_word(s->angle),float_word(s->hitbox.x),float_word(s->hitbox.y),
            u32(s->lifetime.current),u32(u16(s->sprite))|(u32(u16(s->color))<<16),s->active_transforms};
        collision_bullets.insert(collision_bullets.end(),std::begin(row),std::end(row));
    }
}
API(begin_fire_reference) u32 begin_fire_reference(const u8* data,u32 size){
    if(!begin_custom_reference(data,size))return 0;
    observed_fire_words.clear();session.battle->before_player_update=observe_fire_reference;return 1;
}
API(observed_fire_data) const u32* observed_fire_data(){return observed_fire_words.data();}
API(observed_fire_words_size) u32 observed_fire_words_size(){return u32(observed_fire_words.size());}
