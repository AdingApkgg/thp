#include "../../cpp/game/Hud.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static AnmResource front,ascii;static GameEconomy economy;
static EnemyCommandEnvironment enemies;static StageCompletionState completion;static HudEffects effects;
static std::unique_ptr<Hud> hud;static AnmVm* roots[13];static AnmVm children[13][2];
static std::vector<AnmVm*> created;
static u32* slot(u32 n){return n<8?hud->bonus_digits+n:n<10?hud->bonus_marks+n-8:n==10?&hud->spell_notice:n==11?&hud->item_notice:&hud->spell_time_animation;}
API(begin) i32 begin(i32 type,i32 value,i32 mode){
    hud.reset();manager.clear();front={};ascii={};created.clear();
    const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};
    for(auto* r:{&front,&ascii}){r->scripts.resize(100);r->sprites.resize(512);r->textures.resize(1);r->textures[0].width=r->textures[0].height=256;
        for(auto& s:r->scripts){s.bytes.resize(sizeof code);std::memcpy(s.bytes.data(),code,sizeof code);}}
    // IDs are per-manager; create a fresh registry to make native handle
    // identities deterministic without changing production registry behavior.
    manager.~AnmManager();new(&manager)AnmManager();
    hud=std::make_unique<Hud>(manager,front,ascii,economy,enemies,completion,effects);
    for(u32 i=0;i<13;++i){
        auto* vm=roots[i]=manager.create(ascii,0,2,0);*slot(i)=mode?vm->id:0;
        for(auto& c:children[i]){c.initialize();c.child.value=&c;}
        if(mode>=2){vm->child.next=&children[i][0].child;children[i][0].child.next=&children[i][1].child;}
        if(mode==3)vm->child.previous=&children[i][1].child;
    }
    hud->show_spell_time=mode%2;const u32 first=anm_creation_count();const bool ok=hud->notice(type,value);
    // Normal registry appends roots in allocation order.
    for(u32 n=first;n<anm_creation_count();++n)if(auto* vm=manager.find(u32(anm_creation_value(n,5))))created.push_back(vm);
    return ok?0:-2;
}
API(slot_value) u32 slot_value(u32 n){return n<13?*slot(n):hud->show_spell_time;}
API(erased) u32 erased(u32 n){const auto* vm=n%3?&children[n/3][n%3-1]:roots[n/3];return (vm->flags>>26)&1;}
API(count) u32 count(){return u32(created.size());}
API(created_value) u32 created_value(u32 n,u32 k){const auto& v=*created[n];const u32 a[]={v.file_index,u32(v.script_index),v.flags2&0x200,float_bits(v.position.x),float_bits(v.position.y),float_bits(v.position.z),float_bits(v.rotation.z),v.sprite?u32(v.sprite_index):0xffffffff,v.flags&2};return a[k];}
static AnmVm& icon(u32 n){return *hud->icon_th14(n);}
API(icons_initialize) i32 icons_initialize(){begin(5,0,0);return hud->bind_icons_th14()?0:-2;}
API(icon_value) u32 icon_value(u32 n,u32 k){const auto& v=icon(n);const u32 a[]={v.file_index,u32(v.script_index),v.flags2&0x200,float_bits(v.position.x),float_bits(v.position.y),float_bits(v.position.z),float_bits(v.rotation.z),v.flags&2};return a[k];}
API(display_icons) void display_icons(i32 count,i32 fragments){for(u32 n=0;n<16;++n)icon(n).pending_interrupt=0x12345678;hud->display_lives(count,fragments);hud->display_bombs(count,fragments);}
API(icon_pending) u32 icon_pending(u32 n){return u32(icon(n).pending_interrupt);}
