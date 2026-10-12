#include "../../cpp/game/ItemManager.hpp"
#include "../../cpp/game/ItemRewards.hpp"
#include "../../cpp/game/BulletManager.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include "../../cpp/game/EclContext.hpp"
#include "render-fixture.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmEnvironment animations;static AnmResource resource;static GameEconomy economy;
static u32 sound_data[64],sound_size;
static u32 notice_data[24],notice_size;
static ItemRewardEffects effects;static ItemRewards rewards(economy,effects);
struct ItemsWorld:ItemWorld{
    bool collect(ItemState& item,bool& convert)override{return rewards.collect(item,convert);}
    bool sound(i32 id,float x)override{sound_data[sound_size++]=2;sound_data[sound_size++]=u32(id);sound_data[sound_size++]=float_bits(x);return true;}
    i32& item_th14_drop_counter()override{return economy.th14_special_drop_count;}
    bool item_th14_spawn_notice(Vec3 p,i32 type)override{const u32 words[]={4,100,float_bits(p.x),float_bits(p.y),float_bits(p.z),5,type==4||type==5?74u:48u};std::memcpy(notice_data+notice_size,words,sizeof words);notice_size+=7;return true;}
};
static ItemsWorld item_world;static std::unique_ptr<ItemManager> items;
struct BulletsWorld:BulletWorld{
    bool sound(i32,float,bool)override{return true;}
    bool th14_cancel_item(const Vec3& p)override{return items->cancel_reward_th14(p);}
};
static BulletsWorld bullet_world;static std::unique_ptr<BulletManager> bullets;static ItemState* selected;
static void setup(){
    resource={};resource.scripts.resize(294);
    const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};
    for(auto& s:resource.scripts){s.bytes.resize(sizeof code);std::memcpy(s.bytes.data(),code,sizeof code);}
    animations.script_rng={54321,0,123};animations.rate=1;animations.visual_rng={};economy={};economy.power=0;sound_size=notice_size=0;
    item_world.th14_combo={};
    items=std::make_unique<ItemManager>(resource,animations,item_world,7);
    bullets=std::make_unique<BulletManager>(resource,animations,bullet_world,7);bullets->th14_reward_count=19;
    selected=&items->at(ItemManager::capacity-1);
}
API(reward) i32 reward(u32 seed,u32 count,u32 load,i32 full,u32 generation,float x,float y,float z){
    setup();if(full){for(u32 n=0;n<ItemManager::cancel_capacity;++n)items->spawn_cancel_th14(10,{},0,0);for(u32 n=0;n<ItemManager::capacity;++n)std::memset(&items->at(n),0,sizeof(ItemState));}
    animations.visual_rng.seed=u16(seed);items->th14_spawn_count=count;items->th14_cancel_count=load;items->th14_generation=generation;
    auto& b=bullets->at(0);b.flags=0;b.cancel_effect=-1;b.position={x,y,z};
    return bullets->cancel_th14(b,true)?0:-2;
}
API(reward_bits) i32 reward_bits(u32 seed,u32 count,u32 load,i32 full,u32 generation,u32 x,u32 y,u32 z){
    float fx,fy,fz;std::memcpy(&fx,&x,4);std::memcpy(&fy,&y,4);std::memcpy(&fz,&z,4);return reward(seed,count,load,full,generation,fx,fy,fz);
}
API(value) u32 value(u32 n){
    auto& i=*selected;const u32 a[]={float_bits(i.position.x),float_bits(i.position.y),float_bits(i.position.z),float_bits(i.velocity.x),float_bits(i.velocity.y),float_bits(i.velocity.z),float_bits(i.reserved_44c),u32(i.lifetime.previous),u32(i.lifetime.current),float_bits(i.lifetime.fractional),i.lifetime.flags,u32(i.state),u32(i.type),u32(i.display_type),float_bits(i.attraction_speed),u32(i.delay),i.th14_generation,0,items->th14_spawn_count,items->th14_cancel_count,u32(items->th14_free_slot()),bullets->th14_reward_count,animations.visual_rng.seed,animations.visual_rng.calls,items->active_count,u32(economy.score_units),u32(economy.point_value),u32(economy.power),u32(items->th14_ordinary_slot())};return a[n];
}
API(ordinary) i32 ordinary(i32 kind,float rate,float x,float y,float z,float angle){setup();animations.rate=rate;selected=&items->at(599);return items->spawn(kind,{x,y,z},0xffffffff,angle,2.2f);}
API(special_drop) i32 special_drop(i32 counter,i32 full){setup();if(full){for(u32 n=0;n<600;++n)items->spawn(1,{});for(u32 n=0;n<600;++n)std::memset(&items->at(n),0,sizeof(ItemState));}items->th14_spawn_count=0;economy.th14_special_drop_count=counter;selected=&items->at(599);return items->spawn(12,{12.25,99.5,2},0xffffffff,-1.5707963705062866f,2.2f);}
API(special_counter) u32 special_counter(){return u32(economy.th14_special_drop_count);}
API(notice_count) u32 notice_count(){return notice_size;}API(notice_value) u32 notice_value(u32 n){return notice_data[n];}
API(indicator_script) i32 indicator_script(){return selected->th14_indicator.script_index;}
API(tick) i32 tick(i32 state,float rate,u32 variant,float x,float y,float z,float vx,float vy,float vz){
    setup();items->spawn_cancel_th14(10,{},0,0);items->th14_spawn_count=0;
    auto& i=*selected;i.position={x,y,z};i.velocity={vx,vy,vz};i.state=state;i.type=i.display_type=10;i.delay=i32(variant%4)-1;i.attraction_speed=8;
    i.lifetime.set(20,&animations.rate);i.lifetime.previous=19;i.lifetime.fractional=20.5;
    animations.rate=rate;i.vm.flags=1;
    // Native ANM boundaries retain a live VM; the port uses a real synthetic stop script.
    if(state!=5){if(!i.vm.bind_script(resource,104,7,&animations.rate)||i.vm.update(animations)<0)return -2;}
    auto& p=items->player;p.position={0,100,0};p.state=i32(variant%3)==0?1:i32(variant%3)==1?2:4;p.character=variant%3;p.attraction_speed=8;
    const bool collect=variant>=9;p.pickup=collect?ItemBounds{-1000,-1000,1000,1000}:ItemBounds{};
    economy.score_units=collect?999999998:0;economy.point_value=collect?999950:0;economy.max_point_value=1000000;economy.power=7;
    return items->update()?0:-2;
}
API(sound_count) u32 sound_count(){return sound_size;}
API(sound_value) u32 sound_value(u32 n){return sound_data[n];}
API(script) i32 script(){return selected->vm.script_index;}
API(exhaust_begin) void exhaust_begin(){setup();animations.visual_rng.seed=12345;}
API(exhaust_next) i32 exhaust_next(){const i32 slot=items->th14_free_slot();auto& b=bullets->at(0);b.flags=0;b.cancel_effect=-1;b.position={0,100,0};return bullets->cancel_th14(b,true)?slot:-2;}
API(chain) i32 chain(u32 n){return i32(ItemManager::capacity-1-n);}
static th11::test::RecordingGraphics graphics;static AnmRenderer renderer(graphics);
API(draw) i32 draw(i32 state,float y,i32 delay){
    setup();auto& i=*selected;i.state=state;i.delay=delay;i.display_type=10;i.position={17.25,y,2};i.vm.initialize();
    resource.textures.resize(1);resource.textures[0].kind=AnmTexture::Kind::Blank;resource.textures[0].width=resource.textures[0].height=16;
    resource.sprites.push_back({0,0,0,0,16,16,0,0,1,1});i.vm.resource=&resource;if(!i.vm.bind_sprite(0))return -2;i.vm.flags|=3;i.vm.flags2|=0x20000;
    graphics.data.clear();graphics.submissions.clear();graphics.snapshots.clear();
    renderer.viewport={};
    const bool ok=items->draw(renderer);renderer.flush();return ok?0:-2;
}
API(draw_value) u32 draw_value(u32 n){const auto& i=*selected;const u32 a[]={u32(i.display_type),float_bits(i.vm.script_position.x),float_bits(i.vm.script_position.y),float_bits(i.vm.script_position.z),u32(graphics.submissions.size())};return a[n];}

API(other_rng) u32 other_rng(u32 n){return n?animations.script_rng.calls:animations.script_rng.seed;}
API(attraction_case) i32 attraction_case(i32 kind,i32 state,float rate,u32 variant){setup();selected=&items->at(599);auto& i=*selected;i.position={17.25f,61.5f,2};i.velocity={1.25f,-.75f,.5f};i.attraction_speed=8;i.state=state;i.type=kind;i.delay=variant==6?1:variant==7?2:0;i.lifetime.set(20,&animations.rate);i.lifetime.previous=19;i.lifetime.fractional=20.5f;
 animations.rate=rate;const float ys[]={100,128,148,400,400,400,100,100,400,400,400,400};auto& p=items->player;p.position={0,ys[variant],0};p.character=i32(variant%3);p.state=variant==6||variant==11?2:variant==7?4:1;p.bomb_attract=variant==4;p.force_attract=variant==5;p.focused=variant==9||variant==10;if(variant==8||variant==10||variant==11)p.unfocused_attract={-1000,-1000,1000,1000};if(variant==9)p.focused_attract={-1000,-1000,1000,1000};item_world.th14_combo.timer=8;return items->update()?0:-2;}
API(combo_timer) u32 combo_timer(){return u32(item_world.th14_combo.timer);}
