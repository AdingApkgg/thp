#include "AnmResourceWorld.hpp"
#include "AnmEffect5.hpp"
#include <algorithm>

namespace th143 {
AnmResourceWorld::AnmResourceWorld(AnmResourceServices& s,u32 base):services(s),heap(base){regions.push_back({0x72bc7b0c,std::vector<u8>(120)});}
AnmView AnmResourceWorld::storage(u32 p,u32 n){
    if(pool&&p>=pool->self&&std::uint64_t(p)+n<=std::uint64_t(pool->self)+AnmPool::bytes)return {pool->data.data()+p-pool->self};
    for(auto& r:regions)if(p>=r.token&&std::uint64_t(p)+n<=std::uint64_t(r.token)+r.bytes.size())return {r.bytes.data()+p-r.token};
    auto i=state_indices.upper_bound(p);if(i!=state_indices.begin()){--i;if(std::uint64_t(p)+n<=std::uint64_t(i->first)+AnmView::bytes)return {states[i->second]->data()+p-i->first};}
    for(auto& r:extras)if(p>=r->token&&std::uint64_t(p)+n<=std::uint64_t(r->token)+r->data.size())return {r->data.data()+p-r->token};
    for(auto& r:geometry_buffers)if(p>=r.token&&std::uint64_t(p)+n<=std::uint64_t(r.token)+r.bytes.size())return {r.bytes.data()+p-r.token};
    return {nullptr};
}
bool AnmResourceWorld::read(u32 p,void* out,u32 n){auto v=storage(p,n);if(!v.data)return false;std::memcpy(out,v.data,n);return true;}
bool AnmResourceWorld::write(u32 p,const void* in,u32 n){auto v=storage(p,n);if(!v.data)return false;std::memcpy(v.data,in,n);return true;}
bool AnmResourceWorld::allocate_resource_storage(u32 n,bool array,u32& token){
    const std::uint64_t end=std::uint64_t(heap)+((std::uint64_t(std::max(1u,n))+15)&~15ull);if(n>0x4000000||end>=0x100000000ull)return false;
    token=heap;heap=u32(end);regions.push_back({token,std::vector<u8>(std::max(1u,n),0xcd)});resource_allocations.push_back(token);services.animation_storage_allocated(token,n,array);return true;
}
bool AnmResourceWorld::release_resource_storage(u32 p){releases.insert(releases.end(),{2,p});return true;}
bool AnmResourceWorld::release_enemy_storage(u32 p,bool array){releases.insert(releases.end(),{array?1u:2u,p});return true;}
bool AnmResourceWorld::read_resource_file(const std::string& name,bool external,u32& token,u32& size){
    std::vector<u8> bytes;if(!services.read_animation_file(name,external,bytes))return false;size=bytes.size();if(!allocate_resource_storage(size,true,token))return false;return write(token,bytes.data(),size);
}
bool AnmResourceWorld::sprite(u32 r,i32 index,u32& token,std::array<u32,17>& d){
    u32 count,table;if(index<0||!read(r+0x118,&count,4)||u32(index)>=count||!read(r+0x11c,&table,4))return false;token=table+u32(index)*72;return read(token,d.data(),68);
}
bool AnmResourceWorld::script(u32 r,i32 index,u32& token,u16& file,bool& ready){
    u32 count,table,id;if(index<0||!read(r+0x114,&count,4)||u32(index)>=count||!read(r+0x120,&table,4)||!read(r,&id,4)||!read(table+u32(index)*4,&token,4))return false;
    file=u16(id);ready=true;return true;
}
bool AnmResourceWorld::fallback_sprite(u32& r,i32& index){index=262;return read(0x72bc7b14,&r,4)&&r;}
bool AnmResourceWorld::build_resource_template(u32 vm,u32 r,u32 index){
    auto v=storage(vm,AnmView::bytes);if(!v.data)return false;
    if(anm_template(v,vm,r,i32(index),static_cast<ResourceLoaderHost&>(*this)))return true;
    u16 opcode=0;read(v.get(0x28),&opcode,2);error=((index+1)<<16)|opcode;return false;
}
bool AnmResourceWorld::materialize(u32 token){
    u32 pending,count,templates,sprites,file,table,script_table;
    if(!read(token+0x128,&pending,4))return false;if(pending)return true;
    if(resource(token))return true;
    if(!read(token+0x114,&count,4)||!read(token+0x10c,&templates,4)||!read(token+0x118,&sprites,4)||!read(token,&file,4)||!read(token+0x11c,&table,4)||!read(token+0x120,&script_table,4))return false;
    Resource r{token,table,sprites,file,templates,{},{}};r.scripts.resize(count);r.templates.resize(count);
    if(count&&!read(script_table,r.scripts.data(),count*4))return false;
    for(u32 i=0;i<count;++i)if(!read(templates+i*AnmView::bytes,r.templates[i].data(),AnmView::bytes))return false;
    resources.push_back(std::move(r));return true;
}
bool AnmResourceWorld::request(u32 file,const std::string& name,u32& token){
    if(!request_anm_resource(0x72000000,file,name,*this,token))return false;
    if(token&&std::find(requested.begin(),requested.end(),token)==requested.end())requested.push_back(token);
    return !token||materialize(token);
}
bool AnmResourceWorld::complete_resource_chunk(u32 token,u32& result){return complete_anm_resource_chunk(token,*this,result)&&(!result||materialize(token));}
bool AnmResourceWorld::find_enemy_visual(u32 handle,u32& token){auto vm=find(handle);token=vm.data?vm.get(0x570):0;return true;}
bool AnmResourceWorld::synchronize_resources(){
    for(auto i=resources.begin();i!=resources.end();){u32 source;if(!read(i->token+0x108,&source,4))return false;
        if(!source){i=resources.erase(i);continue;}
        const u32 uses=instances.resource_uses[i->token];if(!write(i->token+0x134,&uses,4))return false;++i;
    }return true;
}
bool AnmResourceWorld::pump(i32& result){
    const std::array<u32,2> heads{instances.registry.primary_head,instances.registry.secondary_head};
    const bool ok=pump_anm_resources(0x72000000,heads,*this,result);const bool synced=synchronize_resources();return ok&&synced;
}
bool AnmResourceWorld::ready(bool& result){return anm_resources_ready(0x72000000,*this,result);}
bool AnmResourceWorld::unload(u32 file){return unload_anm_slot(0x72000000,file,{instances.registry.primary_head,instances.registry.secondary_head},*this)&&synchronize_resources();}
bool AnmResourceWorld::create(u32 r,i32 script,i32 layer,u32& handle,bool prepend){return AnmWorld::create(r,script,layer,handle,prepend)&&synchronize_resources();}
bool AnmResourceWorld::create_at(u32 r,i32 script,i32 layer,const std::array<float,3>& p,u32& handle){return AnmWorld::create_at(r,script,layer,p,handle)&&synchronize_resources();}
bool AnmResourceWorld::create_effect(i32 script,const std::array<float,3>& p,u32& handle){return create_at(effect_resource,script,-1,p,handle);}
bool AnmResourceWorld::child(AnmView parent,i32 script,u32 flags){return AnmWorld::child(parent,script,flags)&&synchronize_resources();}
bool AnmResourceWorld::detached_child(AnmView parent,i32 script){return AnmWorld::detached_child(parent,script)&&synchronize_resources();}
bool AnmResourceWorld::update(){return AnmWorld::update()&&synchronize_resources();}
bool AnmResourceWorld::effect(AnmView vm,i32 type){
    if(type!=5)return AnmWorld::effect(vm,type);u32 token;if(!allocate_resource_storage(0x418,true,token))return false;
    auto data=storage(token,0x418);if(!data.data)return false;anm_effect5_initialize(vm,data.data,token,global_rate_token(),animation_rng);return true;
}
bool AnmResourceWorld::callback(u32 entry,AnmView vm,float elapsed,i32& result){
    if(entry==0x409ec0){auto data=storage(vm.get(0x5b4),0x418);if(!data.data)return false;const float old=rate;rate=elapsed;
        const bool ok=anm_effect5_step(data.data,static_cast<ResourceLoaderHost&>(*this),animation_rng);rate=old;result=0;return ok;
    }
    if(entry==0x40a1a0||entry==0x40a1b0){result=0;return true;}
    return AnmWorld::callback(entry,vm,elapsed,result);
}
bool AnmResourceWorld::allocate_geometry(u32 n,u32& token){
    if(n>0x10000||geometry_buffers.size()>=512||!allocate_resource_storage(n,true,token))return false;
    geometry_buffers.push_back({token,std::vector<u8>(n,0xcd)});return true;
}
bool AnmResourceWorld::update_geometry(AnmView vm){
    if(!AnmWorld::update_geometry(vm))return false;
    for(auto& b:geometry_buffers)if(b.token==vm.get(0x5b4))return write(b.token,b.bytes.data(),b.bytes.size());return false;
}
}
