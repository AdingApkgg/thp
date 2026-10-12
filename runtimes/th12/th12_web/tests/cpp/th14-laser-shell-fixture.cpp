#include "../../cpp/game/LaserManager.hpp"
#include "../../cpp/game/AnmManager.hpp"
#include "../../cpp/game/AnmRenderer.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmResource resource;static AnmManager animations;static LaserWorld world;static LaserManager lasers(resource,animations,world,7);
static bool freed;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(run) i32 run(const u8* request,u32 count,i32 next,float rate){lasers.clear();freed=false;world.rate=rate;lasers.active_count=count;lasers.next_id=next;return lasers.spawn_th14_shell(request);}
API(value) u32 value(u32 n){auto* b=lasers.first();if(n==0)return lasers.active_count;if(n==1)return u32(lasers.next_id);if(n==2)return b?1:0;if(n==3)return freed?1:0;if(!b)return 0;
 auto& s=*reinterpret_cast<Th14LaserShell*>(b);const u32 values[]={s.native_flags,u32(b->state),u32(b->type),u32(b->lifetime.previous),u32(b->lifetime.current),float_bits(b->lifetime.fractional),float_bits(b->position.x),float_bits(b->position.y),float_bits(b->position.z),float_bits(b->width),float_bits(b->length),float_bits(s.native_scalar_74),u32(b->id),u32(b->protection),u32(s.cursor)};return n-4<15?values[n-4]:0;}
API(history) u32 history(u32 n){return float_bits(reinterpret_cast<Th14LaserShell*>(lasers.first())->history[n]);}
API(copied) u32 copied(u32 n){u32 word;std::memcpy(&word,reinterpret_cast<Th14LaserShell*>(lasers.first())->request+4*n,4);return word;}
API(cancel) i32 cancel(u32 reward,u32 skip){return lasers.first()&&lasers.cancel_object(*lasers.first(),reward,skip)?0:-2;}
API(tick) i32 tick(){const bool alive=lasers.first()!=nullptr;if(!lasers.update())return -2;if(alive&&!lasers.first())freed=true;return 0;}
API(spatial_cancel) i32 spatial_cancel(){const u32 before=lasers.active_count;if(lasers.cancel_rectangle({},{10,10,0},true)!=0||lasers.cancel_circle({},10,1,false)!=0)return -2;return lasers.active_count==before?0:-2;}
