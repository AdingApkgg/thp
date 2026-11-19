#include "EclVariableTweenRuntime.hpp"
#include "EclExternalRootReset.hpp"
#include "EclThreadLifetime.hpp"
#include "EnemyPhaseShooting.hpp"
namespace th143 {
void reset_enemy_threads(EclOwner& owner){
    auto* node=owner.threads.next;
    while(node){auto* next=node->next;campaign_tweens_forget(*node->value);release_ecl_thread_storage(owner,*node->value);delete node->value;delete node;node=next;}
    auto* tweens=const_cast<EclVariableTweens*>(campaign_tweens_state(owner.root));
    // Ordinary secondary-ID progression is not represented by this adapter.
    u32 discarded_secondary_counter=0;
    reset_external_ecl_root(owner,tweens,discarded_secondary_counter);
    owner.root.error_opcode=-1;
}
bool restart_enemy_phase(EclOwner& owner,const char* name,bool now,float elapsed,i32& result){
    reset_enemy_threads(owner);owner.root.instruction=owner.find_subroutine(name);result=0;
    if(now){result=owner.update(elapsed);if(result==-2)return false;}return true;
}
}
