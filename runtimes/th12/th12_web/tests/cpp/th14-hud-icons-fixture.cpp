#include "../../cpp/game/Hud.hpp"
#include "render-fixture.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static AnmResource front,ascii;
static GameEconomy economy;static EnemyCommandEnvironment enemies;
static StageCompletionState completion;static HudEffects effects;
static std::unique_ptr<Hud> hud;
static test::RecordingGraphics graphics;static AnmRenderer renderer(graphics);
API(allocate) void* allocate(u32 size){return std::malloc(size);}
API(open) i32 open(const u8* data,u32 size){return front.open(data,size);}
API(begin) i32 begin(){hud.reset();manager.clear();manager.rate=1;
    hud=std::make_unique<Hud>(manager,front,ascii,economy,enemies,completion,effects);
    return hud->bind_icons_th14();}
API(signal) void signal(u32 n,i32 label){hud->icon_th14(n)->interrupt(label);}
API(tick) i32 tick(){return manager.update(false);}
API(value) u32 value(u32 n,u32 k){const auto& vm=*hud->icon_th14(n);
    const u32 values[]={u32(vm.sprite_index),vm.color,vm.layer,vm.flags2,vm.flags&1,
        u32(vm.timer.current),float_bits(vm.timer.fractional),float_bits(vm.script_position.x),
        float_bits(vm.script_position.y),float_bits(vm.script_position.z)};return values[k];}
API(layer_count) u32 layer_count(){u32 count=0;for(auto* vm=manager.layer_first(24);vm;vm=vm->draw_next)++count;return count;}
API(draw_icons) u32 draw_icons(){graphics.data.clear();graphics.submissions.clear();renderer.viewport={0,0,640,480,0,1};
    if(renderer.draw_layer(manager.layer_first(24))==-2)return 0;renderer.flush();return graphics.data.size()/sizeof(AnmVertex);}
API(vertex) float vertex(u32 n,u32 axis){const auto& v=reinterpret_cast<const AnmVertex*>(graphics.data.data())[n];return axis?v.position.y:v.position.x;}
API(display) void display(i32 lives,i32 fragments,i32 bombs,i32 bomb_fragments){hud->display_lives(lives,fragments);hud->display_bombs(bombs,bomb_fragments);}
API(pending) u32 pending(u32 n){return hud->icon_th14(n)->pending_interrupt;}
API(clear_hud) u32 clear_hud(){hud.reset();return manager.active_count();}
