#pragma once
#include "AnmState.hpp"
#include "Rng.hpp"
#include <array>
#include <vector>
namespace th143 {
//467b30 catalog parsing after trophy.anm request and trophy.txt file read.
// The seven 256-byte strings retain randomized tails and encrypted NULs.
struct TrophyCatalog {
    static constexpr u32 self=0x4e6bd0,count=70,stride=0x704,bytes=count*stride;
    std::array<u8,bytes> data{};
    std::vector<u8> source;
    bool load(const u8*,u32,Rng&);
};
}
