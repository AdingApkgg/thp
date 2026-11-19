#pragma once
#include "AnmState.hpp"
#include <array>
#include <string>

namespace th143 {
struct StageState {
    static constexpr u32 bytes=0x43a0;
    std::array<u8,bytes> data{};
    AnmView view(){return {data.data()};}
    void construct(){data.fill(0);view().put(0,2);}
};
struct StageInitGlobals {
    u32 current=0,scene=1;
    std::array<u8,0x12c> camera_defaults{}; //4e4d84
    std::string last_filename;
};
struct StageInitHost {
    virtual ~StageInitHost()=default;
    virtual bool read_stage_memory(u32,void*,u32)=0;
    virtual bool write_stage_memory(u32,const void*,u32)=0;
    virtual bool allocate_stage_storage(u32 bytes,bool array,u32&)=0;
    virtual bool read_stage_file(const std::string&,u32& token,u32& bytes)=0;
    virtual bool request_stage_animation(u32 file,const std::string&,u32& token)=0;
    virtual bool register_stage_callback(u32 entry,i32 priority,bool draw,u32 owner,u32&)=0;
};
// 40cfe0/40d0b0/40ece0. File/resource IO andcallback registration are hosts;
// copied STD pointers, VM storage, camera and owner state are computed here.
bool initialize_stage(StageState&,u32 self,const std::string&,StageInitGlobals&,StageInitHost&);
}
