// Controlled error at an actual detached background object's VM boundary.
#include "th14-initialization-clock-fixture-nov01.cpp"
namespace {u32 object_fail_point=~0u,object_fail_words[12]{};}
API(stage_object_boundary_fail) u32 stage_object_boundary_fail(u32 point){
    if(public_player_observations!=1||!session.battle||point>1||object_fail_point!=~0u)return 0;
    object_fail_point=point;
    session.stage_load_object_boundary=[](const Stage& owner,const AnmVm& vm,u32 object,u32 primitive,u32 animation,AnmManager::VmBoundaryTh14 point){
        if(u32(point)!=object_fail_point)return true;
        if(animation>=owner.object_animations.size()||&owner.object_animations[animation]!=&vm)return false;
        const u32 values[]={1,public_player_observations,u32(point),session.state.stage,u32(owner.state.stage_number),
            object,primitive,animation,vm.file_index,u32(vm.script_index),vm.id,
            owner.resource.objects[object].primitives[primitive].animation};
        for(u32 i=0;i<12;++i)object_fail_words[i]=values[i];
        return false;
    };
    return 1;
}
API(stage_object_boundary_failure_word) u32 stage_object_boundary_failure_word(u32 word){return word<12?object_fail_words[word]:~0u;}
