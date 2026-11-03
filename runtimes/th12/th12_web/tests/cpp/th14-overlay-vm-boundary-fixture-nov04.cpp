// Controlled failure at an actual overlay VM; no RNG or gameplay state writes.
#include "th14-initialization-clock-fixture-nov01.cpp"
namespace {u32 overlay_fail_point=~0u,overlay_fail_words[8]{};}
API(overlay_boundary_fail) u32 overlay_boundary_fail(u32 point){
    if(public_player_observations!=1||!session.battle||point>1||overlay_fail_point!=~0u)return 0;
    overlay_fail_point=point;
    session.stage_load_vm_boundary=[](const AnmVm& vm,AnmManager::VmBoundaryTh14 point){
        if(vm.layer<34||vm.layer>35||u32(point)!=overlay_fail_point)return true;
        overlay_fail_words[0]=1;overlay_fail_words[1]=public_player_observations;
        overlay_fail_words[2]=vm.id;overlay_fail_words[3]=vm.file_index;
        overlay_fail_words[4]=u32(vm.script_index);overlay_fail_words[5]=vm.layer;
        overlay_fail_words[6]=u32(point);overlay_fail_words[7]=session.state.stage;
        return false;
    };
    return 1;
}
API(overlay_boundary_failure_word) u32 overlay_boundary_failure_word(u32 word){
    return word<8?overlay_fail_words[word]:~0u;
}
