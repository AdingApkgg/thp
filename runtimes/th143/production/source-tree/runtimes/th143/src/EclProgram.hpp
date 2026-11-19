#pragma once
#include "EclVm.hpp"
#include "EclResource.hpp"
#include <memory>
#include <string>
#include <vector>

namespace th143 {
// Resource parsing is shared; definition insertion and lookup are measured
// against TH143 489880/489a90 rather than borrowed from another title's VM.
class EclProgram {
public:
    struct Definition { th11::EclResource* file; u32 index; };
    std::vector<std::unique_ptr<th11::EclResource>> files;
    std::vector<Definition> definitions;
    bool attach(const u8* data, u32 size);
    Instruction* find(const char* name) const;
    const std::string& name(u32 index) const;
    u32 file_index(u32 definition) const;
    u32 offset(u32 definition) const;
};
}
