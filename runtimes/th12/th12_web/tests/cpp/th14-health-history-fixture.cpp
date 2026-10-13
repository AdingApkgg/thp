#include "th14-custom-replay-reference-fixture.cpp"
static std::vector<u32> health_history_row;
API(begin_health_reference) u32 begin_health_reference(const u8* data,u32 size){
    if(!begin_custom_reference(data,size))return 0;
    session.battle->before_player_update=[](const GameBattle& battle){
        observe_reference(battle);health_history_row.clear();
        for(auto* node=battle.enemies.first;node;node=node->next){
            const auto& e=node->value->state;
            const u32 row[]={u32(e.instance_id),u32(e.health),u32(e.max_health),u32(e.interrupt_health),
                u32(e.scaled_health),u32(e.health_baseline),e.health_flags,
                u32(e.damage_immunity.previous),u32(e.damage_immunity.current),float_word(e.damage_immunity.fractional),
                u32(e.timer_2bc.previous),u32(e.timer_2bc.current),float_word(e.timer_2bc.fractional),
                float_word(e.current.position.x),float_word(e.current.position.y)};
            health_history_row.insert(health_history_row.end(),std::begin(row),std::end(row));
        }
    };
    return 1;
}
API(health_history_data) const u32* health_history_data(){return health_history_row.data();}
API(health_history_words) u32 health_history_words(){return u32(health_history_row.size());}
