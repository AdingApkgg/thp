#include "GameAuxRuntime.hpp"
namespace th143 {
AnmView GameAuxRuntime::mapped(u32 p,u32 n){
    auto region=[&](u32 base,u8* data,u32 size)->AnmView{return data&&p>=base&&p-base<=size&&n<=size-(p-base)?AnmView{data+p-base}:AnmView{nullptr};};
    auto v=effects_reserved?region(effects_self,effects.data(),effects.size()):AnmView{nullptr};if(v.data)return v;
    v=special_reserved?region(special_self,special.data(),special.size()):AnmView{nullptr};if(v.data)return v;
    v=region(scheduler.self,scheduler.data.data(),scheduler.data.size());if(v.data)return v;
    for(auto& [base,b]:scheduler.records){v=region(base,b.data(),b.size());if(v.data)return v;}
    for(auto& s:storage){v=region(s.token,s.bytes.data(),u32(s.bytes.size()));if(v.data)return v;}return {nullptr};
}
bool GameAuxRuntime::read(u32 p,void* out,u32 n){auto v=mapped(p,n);if(v.data){std::memcpy(out,v.data,n);return true;}return animations.read(p,out,n);}
bool GameAuxRuntime::write(u32 p,const void* in,u32 n){auto v=mapped(p,n);if(v.data){std::memcpy(v.data,in,n);return true;}return animations.write(p,in,n);}
bool GameAuxRuntime::allocate(u32 n,u32& token,AnmView& out){if(!services.allocate_game_storage(n,token)||!token)return false;storage.push_back({token,std::vector<u8>(std::max(1u,n),services.game_allocation_fill())});out={storage.back().bytes.data()};return true;}
bool GameAuxRuntime::callback(u32 entry,u32 owner,i32 priority,bool draw,bool enabled,u32& token){
    if(!services.allocate_game_storage(0x28,token)||!token||!scheduler.create(token,entry,services.game_allocation_fill()))return false;
    auto cb=scheduler.at(token);cb.put(4,(cb.get(4)&~3u)|(enabled?3u:1u));cb.put(0x24,owner);u32 result;return scheduler.add(token,priority,draw,*this,result);
}
bool GameAuxRuntime::remove_pair(AnmView owner){for(u32 at:{8,12})if(owner.get(at)&&!scheduler.remove(owner.get(at),*this))return false;return true;}
bool GameAuxRuntime::create_effects(u32& result){
    result=0;if(failed||effects_owner||effects_reserved||!services.reserve_game_owner(effects_self,effects.size()))return false;
    effects_reserved=true;effects.fill(0);effects_view().put(0,2);effects_owner=effects_self;auto v=effects_view();
    for(auto row:{std::array<u32,2>{7,0x14},{8,0x10},{28,0x18}}){u32 token;const char* name=row[0]==7?"bullet.anm":row[0]==8?"effect.anm":"screenswitch.anm";if(!services.request_game_resource(row[0],name,token)||!token){failed=true;return false;}v.put(row[1],token);}
    u32 update,draw;if(!callback(0x41af20,effects_self,32,false,true,update)||!callback(0x41af30,effects_self,37,true,true,draw)){failed=true;return false;}v.put(8,update);v.put(12,draw);result=effects_self;return true;
}
bool GameAuxRuntime::create_special(u32& result){
    result=0;if(failed||special_owner||special_reserved||!services.reserve_game_owner(special_self,special.size()))return false;
    special_reserved=true;special.fill(0);special_view().put(0,2);special_owner=special_self;auto v=special_view();u32 update,draw;
    if(!callback(0x418e10,special_self,31,false,false,update)||!callback(0x418e20,special_self,12,true,false,draw)){failed=true;return false;}v.put(8,update);v.put(12,draw);v.put(0x24,0xffffffff);v.put(0x30,animations.global_rate_token());v.put(0x34,1);result=special_self;return true;
}
bool GameAuxRuntime::activate_special(){if(failed||!special_owner)return false;for(u32 at:{8,12}){auto cb=scheduler.at(special_view().get(at));if(!cb.data)return false;cb.put(4,cb.get(4)|2);}return true;}
bool GameAuxRuntime::bind(AnmView vm,u32 self,i32 script){AnmWorld::Resource* text=nullptr;for(auto& r:animations.resources)if(r.file==0){text=&r;break;}if(!text||script<0||u32(script)>=text->templates.size())return false;anm_copy_template(vm,self,{text->templates[u32(script)].data()},animations.global_rate_token());vm.put(0x594,0);return anm_step(vm,static_cast<AnmWorld&>(animations))!=-2;}
bool GameAuxRuntime::create_independent(u32 display_width,i32& result){
    result=-1;if(failed||independent.resource||independent.pixels)return false;
    u32 resource;if(!services.request_game_resource(25,"bestshot.anm",resource)||!resource){failed=true;return false;}independent.resource=resource;descriptor=0x4e6a10;
    u32 table,texture;if(!animations.read(resource+0x124,&table,4)||!animations.read(table,&texture,4)||!external.auxiliary_surface(texture,0,independent.surface)){failed=true;return false;}
    for(u32 i=0;i<2;++i){AnmView vm;if(!allocate(AnmView::bytes,independent.animations[i],vm)){failed=true;return false;}anm_construct(vm);}
    const i32 script=display_width==640?71:display_width==960?72:display_width==1280?73:-1;
    if(script>=0)for(u32 i=0;i<2;++i){auto vm=mapped(independent.animations[i],AnmView::bytes);if(!bind(vm,independent.animations[i],script+i*6)){failed=true;return false;}}
    width=288;height=336;AnmView pixels;if(!allocate(0x5e800,independent.pixels,pixels)){failed=true;return false;}bytes_per_pixel=4;independent.signals&=~1u;independent.active=0;result=0;return true;
}
bool GameAuxRuntime::release_enemy_storage(u32 p,bool array){for(const auto& s:storage)if(s.token==p)return external.release_auxiliary_storage(p,array);return animations.release_enemy_storage(p,array);}
bool GameAuxRuntime::destroy_independent(){
    //411470 clears the manager's slot25 as well as global4e6a20. The
    // reusable cleanup helper owns the resource, not that separate slot.
    const u32 active=independent.active;if(!cleanup_independent_graphics(independent,heads(),*this))return false;independent.active=active;
    const u32 zero=0;return animations.write(0x72bc7b70,&zero,4)&&animations.synchronize_resources();
}
bool GameAuxRuntime::destroy_special(){if(!special_owner)return true;auto v=special_view();for(u32 at:{0x14,0x18,0x1c}){if(!cleanup_enemy_visual(v.get(at),animations))return false;v.put(at,0);}if(!remove_pair(v))return false;special_owner=0;return services.release_game_storage(special_self);}
bool GameAuxRuntime::destroy_effects(){if(!effects_owner)return true;if(!cleanup_effect_resources(effects_self,heads(),*this)||!remove_pair(effects_view())||!animations.unload(8)||!animations.unload(28))return false;effects_owner=0;return services.release_game_storage(effects_self);}
}
