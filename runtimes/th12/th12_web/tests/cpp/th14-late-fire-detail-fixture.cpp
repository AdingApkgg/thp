#include "th14-late-fire-fixture.cpp"
static std::vector<u32> observed_sprite_words;
static void observe_sprite_reference(const GameBattle& battle){
    observe_fire_reference(battle);observed_sprite_words.clear();
    if(reference[0]<15850||reference[0]>16180)return;
    for(auto* s=battle.bullets.first_th14();s;s=s->th14_active_next){
        const u32 row[]={u32(s->vm.sprite_index),s->vm.sprite?s->vm.sprite->source_id:0,
            float_word(s->vm.sprite?s->vm.sprite->width:0),float_word(s->vm.sprite?s->vm.sprite->height:0),
            u32(s->vm.timer.current),float_word(s->vm.timer.fractional),u32(s->vm.integers[0])};
        observed_sprite_words.insert(observed_sprite_words.end(),std::begin(row),std::end(row));
    }
}
API(begin_fire_detail_reference) u32 begin_fire_detail_reference(const u8* data,u32 size){
    if(!begin_fire_reference(data,size))return 0;
    session.battle->before_player_update=observe_sprite_reference;return 1;
}
API(observed_sprite_data) const u32* observed_sprite_data(){return observed_sprite_words.data();}
API(observed_sprite_words_size) u32 observed_sprite_words_size(){return u32(observed_sprite_words.size());}
