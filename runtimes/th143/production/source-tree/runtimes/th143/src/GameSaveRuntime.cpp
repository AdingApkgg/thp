#include "GameSaveRuntime.hpp"
namespace th143 {
bool GameSaveRuntime::initialize_missing(Rng& random,std::array<u32,4>& gear,std::array<u32,4>& saved,SaveDataHost& host){
    if(file_token||!save.initialize(nullptr,0,random,gear,saved,host)||save.file.empty()||!save.decoded.empty())return false;
    if(!storage.allocate_game_storage(u32(save.file.size()),file_token)||!file_token)return false;
    // Relocate only the typed storage address. All retained file bytes and the
    // complete save object are computed before this allocator binding.
    save.view().put(0,file_token);return true;
}
bool GameSaveRuntime::read(u32 p,void* out,u32 n){
    if(!file_token||p<file_token||std::uint64_t(p)+n>std::uint64_t(file_token)+save.file.size())return false;
    std::memcpy(out,save.file.data()+p-file_token,n);return true;
}
}
