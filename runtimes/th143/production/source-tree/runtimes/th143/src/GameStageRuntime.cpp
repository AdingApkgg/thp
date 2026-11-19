#include "GameStageRuntime.hpp"
#include <algorithm>
namespace th143 {
AnmView GameStageRuntime::mapped(u32 p,u32 n){
    auto region=[&](u32 token,u8* bytes,u32 count)->AnmView{return bytes&&p>=token&&std::uint64_t(p)+n<=std::uint64_t(token)+count?AnmView{bytes+p-token}:AnmView{nullptr};};
    auto v=region(self,state.data.data(),u32(state.data.size()));if(v.data)return v;
    v=region(0x4e4d84,camera.data(),u32(camera.size()));if(v.data)return v;
    v=region(0x4e5200,reinterpret_cast<u8*>(&script.render_option),4);if(v.data)return v;
    v=region(frames.scheduler.self,frames.scheduler.data.data(),u32(frames.scheduler.data.size()));if(v.data)return v;
    auto it=frames.scheduler.records.upper_bound(p);if(it!=frames.scheduler.records.begin()){--it;v=region(it->first,it->second.data(),u32(it->second.size()));if(v.data)return v;}
    for(auto& b:storage){v=region(b.token,b.bytes.data(),u32(b.bytes.size()));if(v.data)return v;}return {nullptr};
}
bool GameStageRuntime::read(u32 p,void* out,u32 n){auto v=mapped(p,n);if(v.data){std::memcpy(out,v.data,n);return true;}return animations.read(p,out,n);}
bool GameStageRuntime::write(u32 p,const void* in,u32 n){auto v=mapped(p,n);if(v.data){std::memcpy(v.data,in,n);return true;}return animations.write(p,in,n);}
bool GameStageRuntime::allocate_stage_storage(u32 n,bool,u32& token){
    if(!services.allocate_game_storage(n,token)||!token)return false;storage.push_back({token,std::vector<u8>(std::max(1u,n),services.game_allocation_fill())});return true;
}
bool GameStageRuntime::read_stage_file(const std::string& name,u32& token,u32& n){std::vector<u8> raw;if(!files.read_game_stage_file(name,raw))return false;n=u32(raw.size());return allocate_stage_storage(n,true,token)&&write(token,raw.data(),n);}
bool GameStageRuntime::register_stage_callback(u32 entry,i32 priority,bool draw,u32 owner,u32& token){
    if(!allocate_stage_storage(0x28,false,token))return false;const u32 fill=u32(services.game_allocation_fill())*0x01010101u;
    return frames.register_callback(token,entry,owner,priority,draw,(fill&~3u)|1);
}
AnmView GameStageRuntime::stage_animation_template(u32 token,i32 script){auto* r=animations.resource(token);return r&&script>=0&&u32(script)<r->templates.size()?AnmView{r->templates[u32(script)].data()}:AnmView{nullptr};}
bool GameStageRuntime::create(const std::string& name,u32& result){
    result=0;if(created||failed)return false;
    if(!services.reserve_game_owner(self,StageState::bytes)){failed=true;return false;}
    created=true;state.construct();camera=loading.camera_defaults;
    if(!initialize_stage(state,self,name,loading,*this)){failed=true;return false;}result=self;return true;
}
bool GameStageRuntime::activate(){return created&&!failed&&activate_stage(state,*this,animations);}
i32 GameStageRuntime::update(){return created&&!failed?advance_stage_frame(state,self,script,*this,animations,*this):-2;}
}
