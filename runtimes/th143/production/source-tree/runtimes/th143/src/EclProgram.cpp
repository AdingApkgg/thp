#include "EclProgram.hpp"

namespace th143 {
bool EclProgram::attach(const u8* data, u32 size) {
    if (files.size() >= 32) return false;
    auto file = std::make_unique<th11::EclResource>();
    if (!file->open(data, size)) return false;
    auto* current = file.get();
    const bool first = files.empty();
    files.push_back(std::move(file));
    for (u32 i = 0; i < current->subroutines.size(); ++i) {
        Definition definition{current, i};
        if (first) definitions.push_back(definition);
        else {
            const auto& key = current->subroutines[i].name;
            auto at = definitions.begin();
            while (at != definitions.end() && std::strcmp(key.c_str(), at->file->subroutines[at->index].name.c_str()) > 0) ++at;
            definitions.insert(at, definition);
        }
    }
    return true;
}
Instruction* EclProgram::find(const char* key) const {
    if (!key) return nullptr;
    i32 low = 0, high = i32(definitions.size()) - 1;
    while (low <= high) {
        const i32 mid = low + (high - low) / 2;
        const auto& def = definitions[mid];
        const int order = std::strcmp(key, def.file->subroutines[def.index].name.c_str());
        if (!order) return reinterpret_cast<Instruction*>(def.file->bytes.data() + def.file->subroutines[def.index].offset + 16);
        if (order < 0) high = mid - 1;
        else low = mid + 1;
    }
    return nullptr;
}
const std::string& EclProgram::name(u32 i) const {
    const auto& def = definitions.at(i);
    return def.file->subroutines[def.index].name;
}
u32 EclProgram::file_index(u32 i) const {
    for (u32 n = 0; n < files.size(); ++n) if (files[n].get() == definitions.at(i).file) return n;
    return 0xffffffff;
}
u32 EclProgram::offset(u32 i) const {
    const auto& def = definitions.at(i);
    return def.file->subroutines[def.index].offset + 16;
}
}
