#include "CommonLoadingDraw.hpp"
#include "RootTransition.hpp"
namespace th143 {
bool draw_common_loading(AnmView owner,AnmView ascii,AnmResourceWorld& world,u32& result){
    if(!owner.data||!ascii.data)return false;
    if(owner.get(0x604)==1){u32 handle;if(!world.create_at(owner.get(0x600),0,-1,{0,0,0},handle))return false;owner.put(0x604,owner.get(0x604)+1);owner.put(0x5fc,handle);}
    if(owner.get(0x608)==1){u32 handle=ascii.get(0x191ec);if(!root_transition(world,ascii.get(0x191e4),handle))return false;ascii.put(0x191ec,handle);owner.put(0x608,owner.get(0x608)+1);}
    owner.put(0x60c,owner.get(0x60c)+1);result=1;return world.synchronize_resources();
}
}
