// Multiple observed host-clock edges for a single intact Replay. Production
// code and VM callbacks stay unchanged; only this fixture's clock advances.
#include "th14-vm-return-worker-fixture.cpp"
namespace {
struct PassiveVmClock {
    u32 callback=0,file=0,script=0,visits=0,slot=0,delivered=0;
    u64 ready=0;
    bool failed=false;
};
std::array<PassiveVmClock,8> passive_vm_clocks{};
u32 passive_vm_clock_count=0;
std::function<u64()> passive_vm_clock_previous;

void visit_passive_vm_clock(PassiveVmClock& point){
    if(!point.visits){
        auto& manager=session.animations;AnmVm::Node* head=nullptr;
        for(u32 layer=0;layer<34&&!head;++layer){
            auto* seed=manager.layer_first(layer);
            if(!seed||manager.find(seed->id)!=seed)continue;
            head=&seed->registry;u32 limit=0;
            while(head->previous){head=head->previous;if(++limit>8192){point.failed=true;return;}}
        }
        u32 rank=0,budget=0;
        for(auto* node=head;node;node=node->next){
            if(++budget>8192){point.failed=true;return;}
            auto* vm=node->value;
            if(!vm||manager.find(vm->id)!=vm){point.failed=true;return;}
            if((vm->flags&0x4000000)||(vm->flags2&0x20))continue;
            ++rank;
            if(vm->file_index==point.file&&u32(vm->script_index)==point.script){point.slot=rank+1;break;}
        }
        if(!point.slot){point.failed=true;return;}
    }
    ++point.visits;
    if(point.visits==point.slot){
        if(probe_clock_ns>point.ready){point.failed=true;return;}
        probe_clock_ns=point.ready;++point.delivered;
    }
}
}
API(observed_passive_vm_clock_add) u32 observed_passive_vm_clock_add(u32 callback,u64 ready,u32 file,u32 script){
    if(!callback||ready<probe_clock_ns||!session.battle||vm_clock_callback||normal_clock_callback||passive_vm_clock_count>=passive_vm_clocks.size())return 0;
    if(passive_vm_clock_count){const auto& last=passive_vm_clocks[passive_vm_clock_count-1];if(callback<=last.callback||ready<last.ready)return 0;}
    else{
        passive_vm_clock_previous=session.stage_load_clock;
        session.stage_load_clock=[](){
            for(u32 i=0;i<passive_vm_clock_count;++i){auto& point=passive_vm_clocks[i];
                if(!point.delivered&&!point.failed&&public_player_observations==point.callback)visit_passive_vm_clock(point);
            }
            return passive_vm_clock_previous();
        };
    }
    auto& point=passive_vm_clocks[passive_vm_clock_count++];point.callback=callback;point.ready=ready;point.file=file;point.script=script;
    return 1;
}
API(observed_passive_vm_clock_count) u32 observed_passive_vm_clock_count(){return passive_vm_clock_count;}
API(observed_passive_vm_clock_state) u32 observed_passive_vm_clock_state(u32 index,u32 field){
    if(index>=passive_vm_clock_count)return 0xffffffffu;
    const auto& point=passive_vm_clocks[index];
    return field==0?point.delivered:field==1?point.failed:field==2?point.slot:field==3?point.visits:point.callback;
}
