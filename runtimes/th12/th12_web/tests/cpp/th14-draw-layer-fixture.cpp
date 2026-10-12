#include "render-fixture.hpp"
using namespace th11;using namespace th11::test;
#define API(name) extern "C" __attribute__((export_name(#name)))
static RenderFixture fixture;static AnmVm vms[6];static u32 events[6],count,mutation,flags[6];
static void callback(AnmVm& vm){events[count++]=u32(vm.integers[0]);auto* target=mutation==1?vm.draw_next:mutation==2?&vm:nullptr;if(target)target->flags2|=0x20;}
API(run) i32 run(u32 order,u32 layer,u32 mask,u32 mutate){(void)layer;mutation=mutate;count=0;fixture.renderer.invalidate();fixture.graphics.data.clear();fixture.graphics.submissions.clear();fixture.graphics.snapshots.clear();
 for(u32 i=0;i<6;++i){auto& vm=vms[i];vm.initialize();vm.flags=0;vm.flags2=mask&(1u<<i)?0x20:0;vm.integers[0]=i;vm.draw_callback=callback;vm.draw_next=nullptr;}
 const u32 chains[2][6]={{0,1,2,3,4,5},{5,2,4,1,3,0}};const auto* chain=chains[order];for(u32 i=0;i<5;++i)vms[chain[i]].draw_next=&vms[chain[i+1]];
 const i32 result=fixture.renderer.draw_layer(&vms[chain[0]]);for(u32 i=0;i<6;++i)flags[i]=vms[i].flags2;return result;}
API(event_count) u32 event_count(){return count;}
API(event_data) const u32* event_data(){return events;}
API(flag_data) const u32* flag_data(){return flags;}
