// Only externally observed completion time and a VM identity matcher are set.
#include "th14-initialization-clock-fixture-nov01.cpp"
namespace {
struct ObservedVmBoundaryInput {
    u32 stage,callback,file,script,handle,point;u64 ready;
    u32 delivered=0;u32 values[16]{};
};
ObservedVmBoundaryInput boundary_inputs[16]{};u32 boundary_input_count=0,boundary_input_failed=0;
bool boundary_input_installed=false;
}
API(observed_vm_boundary_input) u32 observed_vm_boundary_input(u32 stage,u32 callback,u32 file,u32 script,u32 handle,u32 point,u64 ready){
    if(public_player_observations!=1||!session.battle||stage<2||stage>6||!callback||!handle||point>1||ready<probe_clock_ns||boundary_input_count==16)return 0;
    auto& input=boundary_inputs[boundary_input_count++];input={stage,callback,file,script,handle,point,ready};
    if(!boundary_input_installed){
        boundary_input_installed=true;
        session.stage_load_vm_boundary=[](const AnmVm& vm,AnmManager::VmBoundaryTh14 point){
            for(u32 i=0;i<boundary_input_count;++i){auto& input=boundary_inputs[i];
                if(input.delivered||input.stage!=session.state.stage||input.callback!=public_player_observations||
                    input.file!=vm.file_index||input.script!=u32(vm.script_index)||input.handle!=vm.id||input.point!=u32(point))continue;
                if(probe_clock_ns>input.ready){boundary_input_failed=1;return false;}
                input.values[0]=session.animations.script_rng.seed;input.values[1]=session.animations.script_rng.calls;
                input.values[2]=session.animations.visual_rng.seed;input.values[3]=session.animations.visual_rng.calls;
                input.values[4]=vm.id;input.values[5]=vm.file_index;input.values[6]=u32(vm.script_index);input.values[7]=public_player_observations;
                input.values[8]=u32(session.battle->stage_loader.phase);
                input.values[9]=u32(session.battle->stage_loader.deadline);input.values[10]=u32(session.battle->stage_loader.deadline>>32);
                input.values[11]=u32(probe_clock_ns);input.values[12]=u32(probe_clock_ns>>32);
                input.values[13]=u32(session.animations.first_deferred_capture_file_index());
                probe_clock_ns=input.ready;++input.delivered;
                input.values[14]=!session.resources.effects||session.resources.effects->stage_worker_wait_ready();
                input.values[15]=probe_clock_ns>=session.battle->stage_loader.deadline;
            }
            return true;
        };
    }
    return 1;
}
API(observed_vm_boundary_state) u32 observed_vm_boundary_state(u32 input,u32 field){
    if(input==16)return field?boundary_input_failed:boundary_input_count;
    if(input>=boundary_input_count)return ~0u;
    return field==0?boundary_inputs[input].delivered:field<=16?boundary_inputs[input].values[field-1]:~0u;
}
