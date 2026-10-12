#include "../../cpp/game/ItemRewards.hpp"
#include "../../cpp/game/ItemManager.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <vector>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static GameEconomy economy;
struct Effects final:ItemRewardEffects {
 std::vector<u32> events;
 bool sound(i32 id,float x,bool positional)override{events.insert(events.end(),{0,u32(id),float_bits(x),u32(positional)});return true;}
 bool popup(Vec3 p,i32 value,u32 color)override{events.insert(events.end(),{1,float_bits(p.x),float_bits(p.y),float_bits(p.z),u32(value),color});return true;}
 bool lives_changed(i32 n,i32 f)override{events.insert(events.end(),{2,u32(n),u32(f)});return true;}
 bool bombs_changed(i32 n,i32 f)override{events.insert(events.end(),{3,u32(n),u32(f)});return true;}
 bool notify(i32 id)override{events.insert(events.end(),{4,u32(id)});return true;}
 bool power_changed()override{events.push_back(5);return true;}
} effects;
static ItemRewards rewards(economy,effects);
static void reset(){economy={};economy.point_value=1000000;economy.max_point_value=10000000;effects.events.clear();}
API(score_case) i32 score_case(i32 score,i32 amount,i32 difficulty,i32 extend,i32 lives,i32 fragments){reset();economy.score_units=score;economy.difficulty=difficulty;economy.th16_extend_index=extend;economy.lives=lives;economy.life_fragments=fragments;return rewards.th16_add_score(amount);}
API(stock_case) i32 stock_case(i32 kind,i32 count,i32 fragments){reset();economy.lives=economy.th16_bombs=count;economy.life_fragments=economy.th16_bomb_fragments=fragments;if(kind==0){bool awarded=false;return rewards.th16_life(awarded)?i32(awarded):-1;}return kind==1?rewards.th16_bomb():rewards.th16_bomb_fragment();}
API(pickup_case) i32 pickup_case(i32 kind,i32 power,i32 point,i32 character,float y,i32 state){reset();economy.power=power;economy.point_value=point;ItemState item{};item.type=kind;item.state=state;item.position={17.25f,61.5f,2};ItemPlayer p{};p.character=character;p.position={0,y,2};return rewards.th16_collect(item,p);}
API(value) u32 value(u32 n){const u32 words[]={u32(economy.score_units),u32(economy.power),u32(economy.point_value),u32(economy.lives),u32(economy.life_fragments),u32(economy.th16_extend_index),u32(economy.th16_bombs),u32(economy.th16_bomb_fragments),u32(economy.th16_point_items),u32(economy.th16_auto_total),u32(economy.th16_auto_count),float_bits(economy.th16_auto_position.x),float_bits(economy.th16_auto_position.y),float_bits(economy.th16_auto_position.z)};return words[n];}
API(event_count) u32 event_count(){return effects.events.size();}
API(event) u32 event(u32 n){return effects.events[n];}
