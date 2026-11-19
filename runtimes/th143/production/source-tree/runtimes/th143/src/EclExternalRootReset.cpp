#include "EclExternalRootReset.hpp"
namespace th143 {
void reset_external_ecl_root(EclOwner& owner,EclVariableTweens* tweens,u32& secondary_counter){
 auto& root=owner.root;root.flags&=~1u;root.time=0.f;root.instruction=nullptr;root.top=0;root.frame=0;root.thread_id=-1;root.state=0;root.failed=false;
 if(tweens){AnmView state{tweens->scalars.data()};for(u32 i=0;i<8;++i)state.put(i*0x30+0x28,0);}
 owner.active=&root;owner.threads.value=&root;owner.threads.next=nullptr;owner.threads.previous=nullptr;
 secondary_counter=0;
}
}
