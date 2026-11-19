#pragma once
#include "EclVm.hpp"
#include <array>
#include <vector>

namespace th143 {
struct AnmNode {
    u32 id = 0, flags = 0, secondary_flags = 0, child_barrier = 0;
    bool active = false;
    std::vector<AnmNode*> children;
};
// TH143 484280 uses the low 13 bits as a pool slot, with 8191 reserved
// for an ordered search of two external lists. Full IDs validate generations.
struct AnmHandles {
    std::array<AnmNode*, 8191> pool{};
    std::vector<AnmNode*> primary, secondary;
    AnmNode* find(u32 id) const;
    void flag2(u32 id, bool set);
};
}
