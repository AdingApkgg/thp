#include "th14-custom-replay-reference-fixture.cpp"
static std::array<u32,8> collision_diagnostic{};
static std::vector<u32> collision_bullets;
static void observe_collision(const GameBattle& battle){
    observe_reference(battle);
    const auto& p=*battle.player;
    collision_diagnostic={float_word(p.motion.state.position.x),float_word(p.motion.state.position.y),
        float_word(p.state.hit.minimum.x),float_word(p.state.hit.minimum.y),
        float_word(p.state.hit.maximum.x),float_word(p.state.hit.maximum.y),
        float_word(p.th14_scale.factor),p.th14_scale.flags};
    collision_bullets.clear();
    if(reference[0]<16420||reference[0]>16480)return;
    for(auto* s=battle.bullets.first_th14();s;s=s->th14_active_next){
        const u32 row[]={u32(s->state),s->flags,u32(s->collision_delay),
            float_word(s->position.x),float_word(s->position.y),float_word(s->position.z),
            float_word(s->velocity.x),float_word(s->velocity.y),float_word(s->velocity.z),
            float_word(s->speed),float_word(s->angle),float_word(s->hitbox.x),float_word(s->hitbox.y),
            u32(s->lifetime.current),u32(u16(s->sprite))|(u32(u16(s->color))<<16),s->active_transforms};
        collision_bullets.insert(collision_bullets.end(),std::begin(row),std::end(row));
    }
}
API(begin_collision_reference) u32 begin_collision_reference(const u8* data,u32 size){
    if(!begin_custom_reference(data,size))return 0;
    session.battle->before_player_update=observe_collision;return 1;
}
API(collision_diagnostic_data) const u32* collision_diagnostic_data(){return collision_diagnostic.data();}
API(collision_bullet_data) const u32* collision_bullet_data(){return collision_bullets.data();}
API(collision_bullet_words) u32 collision_bullet_words(){return u32(collision_bullets.size());}
