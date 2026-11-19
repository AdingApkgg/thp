#include "TitleActivation.hpp"
#include "AnmSignal.hpp"
namespace th143 {
namespace {
bool enable(TitleActivationBindings& b,AnmView owner,u32 field){auto callback=b.frames.scheduler.at(owner.get(field));if(!callback.data)return false;callback.put(4,callback.get(4)|2u);return true;}
bool hide_resource(AnmResourceWorld& world,u32 resource){for(u32 head:{world.instances.registry.primary_head,world.instances.registry.secondary_head}){u32 budget=0;for(u32 node=head;node;){auto found=world.instances.registry.nodes.find(node-0x570);if(found==world.instances.registry.nodes.end()||++budget>1000000)return false;auto vm=found->second;if(vm.get(0x30)==resource)vm.put(0x1c,vm.get(0x1c)|0x20u);node=vm.get(0x574);}}return true;}
bool music(TitleActivationBindings& b){auto title=b.title.view();if(!(title.get(0xe000)&1))return true;title.put(0xdffc,title.get(0xdffc)+1);if(signed_word(title.get(0xdffc))<10)return true;
    MusicCommandQueue queue;constexpr u32 offset=0x24f8;std::memcpy(queue.data.data(),b.audio.data+offset,queue.data.size());const bool option=(b.application.get(0x20c)&0x10)!=0;MusicScene scene;
    if(!queue.enqueue(option?4:3,0,"dummy"))return false;b.audio.data[0x23f8]=0;if(!scene.load(queue,"th143_01"))return false;if(option&&!queue.enqueue(4,0,"dummy"))return false;if(!queue.enqueue(2,0,"dummy"))return false;
    std::memcpy(b.audio.data+offset,queue.data.data(),queue.data.size());b.save.data[0xef74]=1;title.put(0xe000,title.get(0xe000)&~1u);title.put(0xdffc,0);return true;
}
}
bool advance_title_activation(TitleActivationBindings& b,u32& result){
    auto title=b.title.view();if(!b.title.global_owner||!b.cheat.global_owner||!b.ascii.global_owner||!b.application.data||!b.audio.data||!music(b))return false;
    if(!title.get(0x1c)){
        auto& g=b.globals;if(b.world.find(g.fade_handle).data||g.trophy_owner||g.return_mode)return false;g.fade_handle=0;const auto save=b.save.view();const i32 pending=signed_word(save.get(0xf16c));if(pending>0&&(pending>16||save.get(0xf16c+u32(pending)*4)==39))return false;
        auto ascii=b.ascii.view();if(!signal_animation(b.world,ascii.get(0x191ec),1,false))return false;ascii.put(0x191ec,0);
        for(u32 slot:{5u,7u,2u,0u}){u32 resource;if(!b.world.read(0x72bc7b0c+slot*4,&resource,4)||!hide_resource(b.world,resource))return false;}
        if(!enable(b,b.cheat.view(),8)||!enable(b,b.cheat.view(),12))return false;
        if(g.startup_flags&0x80){title.put(0xe000,title.get(0xe000)&~1u);g.game_state=g.cached_game_state;}else{title.put(0xe000,title.get(0xe000)|1u);title.put(0xdffc,0);}g.startup_flags&=~0x80u;
        title.put(0xe000,title.get(0xe000)|2u);if(!select_title_state(b.title,1))return false;g.return_mode=1;if(!enable(b,title,16))return false;
    }
    return advance_title_main_intro(b.title,b.world,result);
}
}
