#include "GameSavedFile.hpp"
#include <algorithm>
namespace th143 {
namespace {u32 header_word(const u8* p){u32 value;std::memcpy(&value,p,4);return value;}}
bool GameSavedFile::initialize(const u8* input,u32 size,u32 input_token,AnmResourceWorld& memory,Rng& rng,std::array<u32,4>& equipment,std::array<u32,4>& saved,SaveDataHost& host){
    if(file_token||decoded_token||!input_token||(!input&&size))return false;
    const bool valid=size>=24&&header_word(input)==0x31343354&&(header_word(input+8)&0xffff)==1;
    if(!save.initialize(input,size,rng,equipment,saved,host))return false;
    if(valid){
        file_token=input_token;resource_file=true;
        if(!storage.allocate_game_storage(u32(save.decoded.size()),decoded_token)||!decoded_token)return false;
        const u32 written=header_word(input+20);if(written>save.decoded.size())return false;
        // Native reserves four times the declared decoded length. Decode
        // writes only that length; its unused tail retains allocator bytes.
        std::fill(save.decoded.begin()+written,save.decoded.end(),storage.game_allocation_fill());
    }else{
        if(!memory.release_enemy_storage(input_token,true)||!storage.allocate_game_storage(u32(save.file.size()),file_token)||!file_token)return false;
    }
    save.view().put(0,file_token);save.view().put(4,decoded_token);return synchronize(memory);
}
bool GameSavedFile::synchronize(AnmResourceWorld& memory){return !resource_file||memory.write(file_token,save.file.data(),u32(save.file.size()));}
bool GameSavedFile::read(u32 p,void* out,u32 n){
    const auto region=[&](u32 base,const std::vector<u8>& bytes){if(!base||p<base||std::uint64_t(p)+n>std::uint64_t(base)+bytes.size())return false;std::memcpy(out,bytes.data()+p-base,n);return true;};
    return region(file_token,save.file)||region(decoded_token,save.decoded);
}
}
