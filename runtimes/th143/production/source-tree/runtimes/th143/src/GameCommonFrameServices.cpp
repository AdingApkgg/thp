#include "GameCommonFrameServices.hpp"
namespace th143 {
bool GameCommonFrameServices::other_game_callback(u32 entry,u32 owner,u32& result){
    if(owner!=GameCommonRuntime::self)return next.other_game_callback(entry,owner,result);
    auto& b=bindings;if(!b.common||b.common->global_owner!=owner||!b.ascii||!b.world)return false;
    if(entry==0x4436b0)return draw_common_loading(b.common->view(),b.ascii->view(),*b.world,result);
    if(entry!=0x4436a0||!b.application.data||!b.targets||!b.globals||!b.memory||!b.graphics)return false;
    return b.common->update(b.application,*b.targets,*b.globals,*b.memory,*b.graphics,*b.ascii,result);
}
}
