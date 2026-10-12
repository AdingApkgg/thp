#include "th14-dialogue-portrait-family-fixture.cpp"
static u32 lifecycle_ids[16],lifecycle_alive[16],lifecycle_layers[36*17];
static void capture_lifecycle(){capture();for(u32 i=0;i<vms.size();++i){lifecycle_alive[i]=manager.find(lifecycle_ids[i])==vms[i];if(!lifecycle_alive[i])for(u32 j=0;j<22;++j)state[i*22+j]=0;}}
API(begin_lifecycle) i32 begin_lifecycle(u32 resource_index,float rate,i32 immediate){if(!begin_dialogue_family(resource_index,rate,immediate))return 0;for(u32 i=0;i<vms.size();++i)lifecycle_ids[i]=vms[i]->id;capture_lifecycle();return 1;}
API(lifecycle_interrupt) void lifecycle_interrupt(i32 label){interrupt_family(label);capture_lifecycle();}
API(lifecycle_step) i32 lifecycle_step(){if(!manager.update(false)||!manager.update(true))return 0;capture_lifecycle();
 for(u32 layer=0;layer<36;++layer){auto* s=lifecycle_layers+layer*17;u32 n=0;for(auto* vm=manager.layer_first(layer);vm;vm=vm->draw_next){for(u32 i=0;i<vms.size();++i)if(vm==vms[i]){if(n>=16)return 0;s[++n]=i;break;}}s[0]=n;}return 1;}
API(lifecycle_alive_data) const u32* lifecycle_alive_data(){return lifecycle_alive;}
API(lifecycle_layer_data) const u32* lifecycle_layer_data(){return lifecycle_layers;}
