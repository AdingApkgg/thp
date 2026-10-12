#include "../../cpp/game/PlayerFrame.hpp"
#include "render-fixture.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static ShtResource shots;static AnmResource file;static AnmManager animations;static GameEconomy economy;struct World:PlayerFrameWorld{};static World world;static PlayerFrame player(shots,file,file,animations,economy,world);static test::RecordingGraphics graphics;static AnmRenderer renderer(graphics);
API(begin) i32 begin(u32 flags,i32 life,float x,float y,float z){player.motion.body.initialize();player.motion.body.position={91,-72,33};player.motion.body.flags&=~1u;player.motion.body.flags2=flags;player.state.life_state=life;player.motion.state.position={x,y,z};return player.draw(renderer);}
API(value) u32 value(u32 n){const auto& vm=player.motion.body;return n==0?float_bits(vm.position.x):n==1?float_bits(vm.position.y):n==2?float_bits(vm.position.z):vm.flags2;}
