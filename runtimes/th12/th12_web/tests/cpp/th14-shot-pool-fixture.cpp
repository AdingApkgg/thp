#include "../../cpp/game/ShotPoolTh14.hpp"
using namespace th11;
static Th14ShotPool pool;static bool active[256]{};static u32 events[256]{},count=0;
#define API(n) extern "C" __attribute__((export_name(#n)))
API(run) i32 run(u32 op,u32 mode,u32 step){count=0;if(!op){const u32 slot=pool.peek();if(slot>=256)return -1;events[count++]=slot;if(mode){pool.consume();active[slot]=true;}return i32(slot);}
 for(u32 slot=0;slot<256;++slot)if(active[slot]){events[count++]=slot;if(mode==2||(mode==1?slot%2==step%2:(slot+step)%11==0)){active[slot]=false;pool.recycle(slot);}}return 0;}
API(head) u32 head(){return pool.peek();}
API(next_slot) u32 next_slot(u32 n){return pool.next[n];}
API(is_active) u32 is_active(u32 n){return active[n];}
API(event_count) u32 event_count(){return count;}
API(event_at) u32 event_at(u32 n){return events[n];}
