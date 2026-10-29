// Only a host clock and an observed call boundary are supplied. The actual
// loader restores its own Replay entry; VM callbacks are never wrapped.
#include "th14-normal-worker-fixture.cpp"
namespace {
u32 vm_clock_callback=0,vm_clock_visits=0,vm_clock_slot=0,vm_clock_delivered=0;
u64 vm_clock_ready=0;
bool vm_clock_failed=false;
std::function<u64()> vm_clock_previous;
}
API(observed_normal_vm_clock) u32 observed_normal_vm_clock(u32 callback,u64 now,u32 file,u32 script){
    if(vm_clock_callback||!callback||now<probe_clock_ns||!session.battle)return 0;
    vm_clock_callback=callback;vm_clock_ready=now;vm_clock_previous=session.stage_load_clock;
    session.stage_load_clock=[file,script](){
        if(!vm_clock_delivered&&public_player_observations==vm_clock_callback){
            if(!vm_clock_visits){
                // Entry still has the previous draw lists. Reach the manager's
                // own normal registry through one valid VM, then count only
                // methods that this production update will actually call.
                auto& manager=session.animations;AnmVm::Node* head=nullptr;
                for(u32 layer=0;layer<34&&!head;++layer){
                    auto* seed=manager.layer_first(layer);
                    if(!seed||manager.find(seed->id)!=seed)continue;
                    head=&seed->registry;u32 limit=0;
                    while(head->previous){head=head->previous;if(++limit>8192){vm_clock_failed=true;return vm_clock_previous();}}
                }
                u32 rank=0,budget=0;
                for(auto* node=head;node;node=node->next){
                    if(++budget>8192){vm_clock_failed=true;break;}
                    auto* vm=node->value;
                    if(!vm||manager.find(vm->id)!=vm){vm_clock_failed=true;break;}
                    if((vm->flags&0x4000000)||(vm->flags2&0x20))continue;
                    ++rank;
                    if(vm->file_index==file&&u32(vm->script_index)==script){vm_clock_slot=rank+1;break;}
                }
                if(!vm_clock_slot)vm_clock_failed=true;
            }
            ++vm_clock_visits;
            if(vm_clock_slot&&vm_clock_visits==vm_clock_slot){
                if(probe_clock_ns>vm_clock_ready)vm_clock_failed=true;
                else probe_clock_ns=vm_clock_ready;
                ++vm_clock_delivered;
            }
        }
        return vm_clock_previous();
    };
    return 1;
}
API(observed_normal_vm_clock_state) u32 observed_normal_vm_clock_state(u32 field){
    return field==0?vm_clock_delivered:field==1?vm_clock_failed:field==2?vm_clock_slot:vm_clock_visits;
}
