#pragma once
#include "AnmState.hpp"
#include "Rng.hpp"
#include "../../th12/th12_web/cpp/game/Lzss.hpp"
#include <array>
#include <vector>

namespace th143 {
struct SaveDataHost {
    virtual ~SaveDataHost()=default;
    // 467e00 is owned by the achievement service, not the save record.
    virtual bool achievement(u32 id)=0;
};
struct SaveData {
    static constexpr u32 bytes=0xf1b0,scene_count=77,item_count=11;
    static constexpr u32 scene_size=0x314,item_size=0x34,stats_size=0x224;
    static constexpr u32 items=0xed0c,stats=0xef48;
    std::array<u8,bytes> data{};
    std::vector<u8> file,decoded;
    th11::Lzss codec;
    AnmView view(){return {data.data()};}
    // Caller owns the persistent gameplay RNG and the two equipment banks.
    bool initialize(const u8*,u32,Rng&,std::array<u32,4>& equipment,std::array<u32,4>& saved_equipment,SaveDataHost&);
    bool load(std::array<u32,4>& equipment,std::array<u32,4>& saved_equipment);
    bool item_level(u32 id,bool notify,u32 alternate,SaveDataHost&);
    bool serialize(const std::array<u32,4>& saved_equipment,std::vector<u8>& output);
    static u32 checksum(const u8*,u32);
};
}
