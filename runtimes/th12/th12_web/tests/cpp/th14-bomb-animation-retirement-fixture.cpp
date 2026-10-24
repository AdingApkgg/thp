#include "th14-sakuya-b-controller-fixture.cpp"
static u32 retirement_flags[6];
API(retire_bomb) u32 retire_bomb(u32 main_state,u32 aux_state,u32 nonroot,u32 active,u32 flags){
    reset();
    auto* unrelated=animations.create(anm,0,9,0);
    auto* primary=animations.create(anm,16,9,0,false,false,nullptr,nullptr,nonroot?unrelated:nullptr);
    auto* auxiliary=animations.create(anm,19,9,0);
    auto* primary_child=animations.create(anm,0,9,0,false,false,nullptr,nullptr,primary);
    auto* primary_child2=animations.create(anm,0,9,0,false,false,nullptr,nullptr,primary);
    auto* auxiliary_child=animations.create(anm,0,9,0,false,false,nullptr,nullptr,auxiliary);
    if(!unrelated||!primary||!auxiliary||!primary_child||!primary_child2||!auxiliary_child)return 0;
    // The interpreter's child opcode links these nodes after create returns.
    primary->child.next=&primary_child->child;primary_child->child.previous=&primary->child;
    primary_child->child.next=&primary_child2->child;primary_child2->child.previous=&primary_child->child;
    auxiliary->child.next=&auxiliary_child->child;auxiliary_child->child.previous=&auxiliary->child;
    if(nonroot){unrelated->child.next=&primary->child;primary->child.previous=&unrelated->child;}
    AnmVm* vms[]={primary,auxiliary,primary_child,primary_child2,auxiliary_child,unrelated};
    for(auto* vm:vms)vm->flags2=flags;
    auto owned=std::make_unique<BombController>(animations,anm,player,world,9,&anm);
    owned->selection=4;owned->state.active=i32(active);
    owned->state.animation=main_state==1?primary->id:main_state==2?0xffffffffu:0;
    owned->state.auxiliary=aux_state==1?auxiliary->id:aux_state==2?0xffffffffu:0;
    owned.reset();
    for(u32 i=0;i<6;++i)retirement_flags[i]=vms[i]->flags2;
    return 1;
}
API(retirement_value) u32 retirement_value(u32 n){return n<6?retirement_flags[n]:0xffffffffu;}
