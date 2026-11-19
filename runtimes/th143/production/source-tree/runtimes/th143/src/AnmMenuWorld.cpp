#include "AnmMenuWorld.hpp"
namespace th143 {
u8* AnmMenuWorld::transition_data(u32 token){for(auto& r:regions)if(token==r.token&&r.bytes.size()==anm_effect0_bytes)return r.bytes.data();return nullptr;}
bool AnmMenuWorld::create_screen_transition(u32 resource,u32& handle){
    AnmOverlay overlay;if(!overlay.create(*this,resource,0,nullptr,0,-1,4,handle))return false;auto root=find(handle);u32 extra;if(!root.data||!allocate_resource_storage(anm_effect0_bytes,true,extra))return false;auto* data=transition_data(extra);if(!data||!initialize_anm_effect0(root,data,extra,resource,*this))return false;
    root.put(0x5b8,0x40a310);root.put(0x5bc,0x40a380);root.put(0x5c0,0x40a8e0);root.put(0x5c4,0x40a8f0);return synchronize_resources();
}
bool AnmMenuWorld::callback(u32 entry,AnmView vm,float elapsed,i32& result){
    if(entry==0x40a8e0){result=0;return true;}
    if(entry==0x40a310){auto* data=transition_data(vm.get(0x5b4));if(!data)return false;result=step_anm_effect0(data,static_cast<AnmWorld&>(*this));return result!=-2;}
    return AnmResourceWorld::callback(entry,vm,elapsed,result);
}
bool AnmMenuWorld::animation_signal_callback(u32 entry,AnmView vm,i32 signal){return entry==0x40a8f0&&signal_anm_effect0(vm,transition_data(vm.get(0x5b4)),vm.get(0x5b4),vm.get(0x30),signal,*this);}
}
