#include "CheatAnimation.hpp"
namespace th143 {
AnmView find_animation_child(AnmWorld& world,AnmView parent,i32 script){
    if(!parent.data)return {nullptr};u32 self=0;
    for(u32 i=0;i<world.states.size();++i)if(world.states[i]->data()==parent.data){self=world.state_tokens[i];break;}
    if(!self)return {nullptr};u32 node=self+0x580,budget=0;
    while(node){
        u32 token,next;if(++budget>100000||!world.read(node,&token,4)||!world.read(node+4,&next,4))return {nullptr};
        auto child=world.state(token);
        if(token!=self&&child.data){
            const i32 id=i32(std::int16_t(child.get(0x4a8)>>16));
            if(id==script||script==-1||(script==-2&&!next))return child;
        }
        node=next;
    }return {nullptr};
}
bool create_cheat_animation(AnmView owner,u32 index,AnmWorld& world,AnmOverlay& overlay){
    if(index>=9)return false;u32 handle;
    if(!overlay.create(world,owner.get(0x10),i32(index),nullptr,0,-1,4,handle))return false;
    owner.put(0x2c4+index*4,handle);return true;
}
bool clear_cheat_animation(AnmView owner,u32 index,AnmWorld& world,AnmSignalHost* callbacks){
    if(index>=9)return false;const u32 slot=0x2c4+index*4;
    if(!signal_animation(world,owner.get(slot),1,false,callbacks))return false;owner.put(slot,0);return true;
}
bool signal_cheat_child(AnmView owner,u32 index,i32 child_script,i32 signal,AnmWorld& world,AnmSignalHost* callbacks){
    if(index>=9)return false;const u32 slot=0x2c4+index*4;
    auto parent=world.find(owner.get(slot));
    if(!parent.data){owner.put(slot,0);return false;}
    // Original resolves the parent again before the child search.
    parent=world.find(owner.get(slot));if(!parent.data){owner.put(slot,0);return false;}
    auto child=find_animation_child(world,parent,child_script);if(!child.data)return false;
    return signal_animation_vm(world,child,signal,true,callbacks);
}
}
