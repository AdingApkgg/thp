#include "th14-dialogue-portrait-lifecycle-fixture.cpp"
static u32 previous_pool_root=0,stale_pool_found=0;
API(begin_pool_cycle) i32 begin_pool_cycle(u32 resource_index,i32 immediate){const u32 previous=previous_pool_root;if(!begin_lifecycle(resource_index,1.f,immediate))return 0;stale_pool_found=manager.find(previous)!=nullptr;previous_pool_root=vms[0]->id;return 1;}
API(reset_pool_history) void reset_pool_history(){previous_pool_root=0;}
API(stale_pool_handle_found) u32 stale_pool_handle_found(){return stale_pool_found;}
