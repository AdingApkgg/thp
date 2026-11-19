#include "GameEnemyRuntime.hpp"
namespace th143 {
bool GameEnemyRuntime::allocate(u32 n,u32& token){
    if(!services.allocate_game_storage(n,token)||!token)return false;
    storage.push_back({token,std::vector<u8>(n,services.game_allocation_fill())});return true;
}
bool GameEnemyRuntime::callback(u32 entry,i32 priority,bool draw,u32& token){
    if(!services.allocate_game_storage(0x28,token)||!token||!scheduler.create(token,entry,services.game_allocation_fill()))return false;
    auto cb=scheduler.at(token);cb.put(4,(cb.get(4)&~3u)|1);cb.put(0x24,self);u32 result;return scheduler.add(token,priority,draw,*this,result);
}
bool GameEnemyRuntime::attach(u32 token,const std::vector<u8>& raw){
    const u32 index=u32(program.files.size());if(!program.attach(raw.data(),u32(raw.size())))return false;
    file_tokens.push_back(token);AnmView l{loader.data()};l.put(12+index*4,token);l.put(8,u32(program.definitions.size()));
    u32 table;if(!allocate(u32(program.definitions.size()*8),table))return false;
    const u32 old=l.get(0x8c);l.put(0x8c,table);auto& bytes=storage.back().bytes;AnmView records{bytes.data()};
    // Name pointers reference the original NUL-terminated name bank, not a
    // reconstructed string allocation. Definitions keep native insertion order.
    std::vector<std::vector<u32>> names;
    for(const auto& file:program.files){const auto* b=file->bytes.data();u16 header;std::memcpy(&header,b+6,2);u32 at=36+header+u32(file->subroutines.size())*4;std::vector<u32> offsets;
        for(u32 i=0;i<file->subroutines.size();++i){offsets.push_back(at);at+=u32(file->subroutines[i].name.size())+1;}names.push_back(std::move(offsets));}
    for(u32 i=0;i<program.definitions.size();++i){const u32 f=program.file_index(i),sub=program.definitions[i].index;records.put(i*8,file_tokens[f]+names[f][sub]);records.put(i*8+4,file_tokens[f]+program.offset(i)-16);}
    if(old&&!files.release_enemy_storage(old,true))return false;
    l.put(4,index+1);
    const auto* current=program.files[index].get();
    for(u32 i=0;i<current->animations.size();++i){u32 resource;if(i>=6||!services.request_game_resource(10+i,current->animations[i].c_str(),resource)||!resource)return false;view().put(0xa8+i*4,resource);}
    // Keep the resource object stable while recursive includes extend files.
    for(const auto& name:current->includes)if(!load(name.c_str()))return false;
    return true;
}
bool GameEnemyRuntime::load(const char* name){
    if(failed||!loader_token||!name||std::strlen(name)>=scratch.size()){failed=true;return false;}
    auto& filename_buffer=shared_scratch?*shared_scratch:scratch;filename_buffer[0]=0;std::memcpy(filename_buffer.data(),name,std::strlen(name)+1);
    std::vector<u8> raw;u32 token;if(!files.read_enemy_file(name,raw)||!allocate(u32(raw.size()),token)){failed=true;return false;}
    storage.back().bytes=raw;if(!attach(token,raw)){failed=true;return false;}return true;
}
bool GameEnemyRuntime::create(const char* name,u32 bullet,u32 effect,u32& result){
    result=0;if(failed||global_owner||!services.reserve_game_owner(self,data.size()))return false;
    data.fill(0);view().put(0,2);view().put(0xdc,1);global_owner=self;view().put(0xa0,bullet);view().put(0xa4,effect);
    if(!services.allocate_game_storage(loader.size(),loader_token)||!loader_token){failed=true;return false;}loader.fill(0);AnmView l{loader.data()};l.put(0,0x4c562c);view().put(0xcc,loader_token);
    if(!load(name))return false;
    u32 update,draw;if(!callback(0x41edb0,26,false,update)||!callback(0x41edf0,22,true,draw)){failed=true;return false;}view().put(8,update);view().put(12,draw);
    view().put(0xb8,0xffffffff);view().put(0xc4,0x4e40b0);view().put(0xc8,1);view().put(0xe4,99999);result=self;return true;
}
bool GameEnemyRuntime::activate(){if(failed||!global_owner)return false;for(u32 at:{8,12}){auto cb=scheduler.at(view().get(at));if(!cb.data)return false;cb.put(4,cb.get(4)|2);}return true;}
u32 GameEnemyRuntime::find(const char* name)const{
    auto* p=program.find(name);if(!p)return 0;for(u32 i=0;i<program.files.size();++i){const auto& b=program.files[i]->bytes;const auto address=reinterpret_cast<std::uintptr_t>(p),base=reinterpret_cast<std::uintptr_t>(b.data());if(address>=base&&address-base<b.size())return file_tokens[i]+u32(address-base);}return 0;
}
bool GameEnemyRuntime::read(u32 token,void* out,u32 n){
    auto copy=[&](u32 base,const u8* p,u32 size){if(token<base||token-base>size||n>size-(token-base))return false;std::memcpy(out,p+token-base,n);return true;};
    if(global_owner&&copy(self,data.data(),data.size()))return true;
    if(loader_token&&copy(loader_token,loader.data(),loader.size()))return true;
    const auto& filename_buffer=shared_scratch?*shared_scratch:scratch;
    if(copy(0x541050,filename_buffer.data(),filename_buffer.size())||copy(scheduler.self,scheduler.data.data(),scheduler.data.size()))return true;
    for(const auto& [p,b]:scheduler.records)if(copy(p,b.data(),b.size()))return true;
    for(const auto& s:storage)if(copy(s.token,s.bytes.data(),u32(s.bytes.size())))return true;return false;
}
}
