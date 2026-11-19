#include "AnmHandles.hpp"

namespace th143 {
AnmNode* AnmHandles::find(u32 id) const {
    if (!id) return nullptr;
    const u32 index = id & 8191;
    if (index != 8191) {
        AnmNode* node = pool[index];
        return node && node->active && node->id == id ? node : nullptr;
    }
    for (auto* node : primary) if (node->id == id) return node;
    for (auto* node : secondary) if (node->id == id) return node;
    return nullptr;
}
void AnmHandles::flag2(u32 id, bool set) {
    auto* node = find(id);
    if (!node) return;
    auto apply = [set](AnmNode& vm) { vm.flags = set ? vm.flags | 2 : vm.flags & ~2u; };
    apply(*node);
    if (!node->child_barrier) for (auto* child : node->children) apply(*child);
}
}
