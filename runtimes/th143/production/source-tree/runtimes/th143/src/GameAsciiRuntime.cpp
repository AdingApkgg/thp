#include "GameAsciiRuntime.hpp"
namespace th143 {
bool GameAsciiRuntime::create(u8 font,u32& result){
    result=0;if(global_owner||!storage.reserve_game_owner(self,bytes))return false;
    // The original constructor's final memset overwrites its preceding vtable
    // and two inline-VM constructors, then publishes these exact style fields.
    data.fill(0);auto o=view();o.put(4,2);global_owner=self;o.put(0x191b0,0xffffffff);o.put(0x191b4,word(1.f));o.put(0x191b8,word(1.f));o.put(0x191dc,9);o.put(0x191d4,1);o.put(0x191d8,1);
    static constexpr const char* names[]={"ascii.anm","ascii_960.anm","ascii_1280.anm"};u32 resource;
    if(!storage.request_game_resource(2,names[font%3],resource)||!resource)return false;o.put(0x191e4,resource);
    struct Callback{u32 entry,field; i32 priority;bool draw;};
    for(auto c:{Callback{0x40b590,0xc,4,false},{0x40b5b0,0x10,78,true},{0x40b5c0,0x191f0,51,true},{0x40b5d0,0x191f4,63,true}}){
        u32 token;if(!storage.allocate_game_storage(0x28,token)||!token||!frames.scheduler.create(token,c.entry,storage.game_allocation_fill()))return false;
        auto callback=frames.scheduler.at(token);callback.put(4,callback.get(4)&~2u);callback.put(0x24,self);u32 ignored;if(!frames.scheduler.add(token,c.priority,c.draw,*this,ignored))return false;o.put(c.field,token);
    }
    for(auto pair:{std::array<u32,2>{0x14,0},{0x5e0,98}}){auto vm=o.sub(pair[0]);anm_reset(vm,self+pair[0]);vm.put(0x30,resource);if(!anm_bind_sprite(vm,i32(pair[1]),static_cast<AnmWorld&>(world)))return false;}
    result=self;return true;
}
bool GameAsciiRuntime::activate(){
    if(!global_owner)return false;
    for(u32 at:{0xc,0x10,0x191f0,0x191f4}){auto cb=frames.scheduler.at(view().get(at));if(!cb.data)return false;cb.put(4,cb.get(4)|2u);}return true;
}
bool GameAsciiRuntime::destroy(){
    if(!global_owner)return true;
    auto o=view();o.put(0,0x4c4d74);
    for(u32 at:{0xc,0x10,0x191f0,0x191f4})if(!frames.scheduler.remove(o.get(at),*this))return false;
    if(!world.unload(2)||!world.unload(0))return false;
    global_owner=0;
    for(u32 at:{0xb94,0x5c8}){const u32 p=o.get(at);if(p&&!world.release_enemy_storage(p,true))return false;o.put(at,0);}
    return storage.release_game_storage(self);
}
}
