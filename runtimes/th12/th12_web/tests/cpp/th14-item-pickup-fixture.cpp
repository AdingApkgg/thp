#include "../../cpp/game/ItemRewards.hpp"
#include "../../cpp/game/ItemManager.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <vector>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static std::vector<u32> events;static GameEconomy economy;
struct Effects:ItemRewardEffects {
    bool sound(i32 id,float x,bool positional)override{events.insert(events.end(),{1,u32(id),float_bits(x)});return true;}
    bool popup(Vec3 p,i32 value,u32 color)override{if(p.x!=17.25||p.y!=400)return false;events.insert(events.end(),{0,u32(value),color});return true;}
    bool notify(i32 kind)override{events.insert(events.end(),{2,u32(kind)});return true;}
    bool power_changed()override{events.push_back(3);return true;}
    bool lives_changed(i32 count,i32 fragments)override{events.insert(events.end(),{4,u32(count),u32(fragments)});return true;}
    bool bombs_changed(i32 count,i32 fragments)override{events.insert(events.end(),{5,u32(count),u32(fragments)});return true;}
    bool th14_combo_drop(i32 type,Vec3 p,i32 delay)override{events.insert(events.end(),{6,u32(type),float_bits(p.x),float_bits(p.y),float_bits(p.z),u32(delay)});return true;}
    bool th14_combo_popup(Vec3 p,i32 value,u32 color,float multiplier)override{events.insert(events.end(),{7,u32(value),color,float_bits(multiplier),float_bits(p.x),float_bits(p.y),float_bits(p.z)});return true;}
};
API(begin) i32 begin(i32 kind,i32 character,u32 y,i32 power,i32 score,i32 point){
    events.clear();economy={};economy.power=power;economy.score_units=score;economy.point_value=point;economy.max_power=160;economy.power_step=40;economy.max_point_value=1000000;economy.th14_point_items=INT32_MAX;
    ItemState item{};item.type=kind;item.position={17.25,400,0};item.state=1;ItemPlayer player;player.character=character;player.position.y=float_bits(y);
    Effects effects;ItemRewards rewards(economy,effects);bool convert=false;return rewards.collect(item,convert,&player)&&!convert?0:-2;
}
API(value) u32 value(u32 n){const u32 a[]={u32(economy.power),u32(economy.score_units),u32(economy.point_value),u32(economy.th14_point_items),0,0};return a[n];}
API(fragment) i32 fragment(i32 kind,i32 lives,i32 life_fragments,i32 awards,i32 bombs,i32 bomb_fragments){
 events.clear();economy={};economy.lives=lives;economy.life_fragments=life_fragments;economy.th14_life_awards=awards;economy.th14_bombs=bombs;economy.th14_bomb_fragments=bomb_fragments;ItemState item{};item.type=kind;
 Effects effects;ItemRewards rewards(economy,effects);bool convert=false;return rewards.collect(item,convert)?0:-2;
}
API(fragment_value) u32 fragment_value(u32 n){const u32 values[]={u32(economy.lives),u32(economy.life_fragments),u32(economy.th14_life_awards),u32(economy.th14_bombs),u32(economy.th14_bomb_fragments)};return values[n];}
API(combo_pickup) i32 combo_pickup(i32 kind,i32 character,u32 y,i32 item_state,i32 power,i32 score,i32 point,i32 count,i32 total){
 events.clear();economy={};economy.power=power;economy.score_units=score;economy.point_value=point;economy.max_power=160;economy.power_step=40;economy.max_point_value=1000000;economy.th14_point_items=INT32_MAX;
 economy.th14_combo={total,count,8,{2.25f,3.75f,-1.5f}};ItemState item{};item.type=kind;item.position={17.25,400,0};item.state=item_state;ItemPlayer player;player.character=character;player.position={-33.25f,float_bits(y),3.5f};
 Effects effects;ItemRewards rewards(economy,effects);bool convert=false;return rewards.collect(item,convert,&player)&&!convert?0:-2;
}
API(combo_word) u32 combo_word(u32 n){const auto& c=economy.th14_combo;const u32 words[]={u32(economy.power),u32(economy.score_units),u32(economy.point_value),u32(economy.th14_point_items),u32(c.count),u32(c.total),float_bits(c.position.x),float_bits(c.position.y),float_bits(c.position.z),u32(c.timer)};return words[n];}
struct ComboWorld:ItemWorld{bool dialogue=false;Th14ItemCombo& item_th14_combo_state()override{return economy.th14_combo;}bool item_th14_combo_settle()override{Effects effects;ItemRewards rewards(economy,effects);return rewards.th14_combo_settle(dialogue);}};
API(settlement) i32 settlement(i32 count,i32 total,i32 timer,i32 dialogue){events.clear();economy={};economy.score_units=999999990;economy.th14_combo={total,count,timer,{-33.25f,100.5f,3.5f}};ComboWorld world;world.dialogue=dialogue;AnmResource resource;AnmEnvironment environment;ItemManager manager(resource,environment,world);return manager.update()?0:-2;}
API(settlement_word) u32 settlement_word(u32 n){const auto& c=economy.th14_combo;const u32 words[]={u32(c.count),u32(c.total),u32(c.timer),u32(economy.score_units)};return words[n];}
API(event_count) u32 event_count(){return events.size();}
API(event_value) u32 event_value(u32 n){return events[n];}
