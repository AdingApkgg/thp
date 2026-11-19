#pragma once
#include "AnmVm.hpp"
#include <map>
#include <vector>

namespace th143 {
// Original40ab20 copies the 0x540-byte template prefix, preserving the new
// instance's runtime pool slot and child-position fields. Template layer wins.
void anm_copy_template(AnmView target, u32 self, AnmView source, u32 rate_token);
// Original42b770 before483b30 registration. Negative layer retains the template.
bool anm_create_instance(AnmView target, u32 self, AnmView source, i32 layer, AnmVmHost&);

// Original483a70/483b30/483be0/483ca0 external-list registration, including
// full-generation IDs. Regular pool allocation and retirement are separate.
struct AnmRegistry {
    std::map<u32,AnmView> nodes;
    std::vector<AnmView> pool;
    AnmView owner{nullptr};
    u32 primary_head=0,primary_tail=0,secondary_head=0,secondary_tail=0,generation=0;
    void sync_owner();
    bool insert(AnmView, u32 self, bool secondary, bool prepend, u32& handle);
    AnmView find(u32 handle) const;
};
struct AnmInstances {
    AnmRegistry registry;
    std::map<u32,u32> resource_uses;
    bool create(u32 resource, AnmView target, u32 self, AnmView source, i32 layer, AnmVmHost&, u32& handle, bool secondary=false, bool prepend=true);
    // Original484080: execute a parent-linked instance, register according to
    // flags2/4, then insert its child node immediately after the parent node.
    bool child(u32 resource, AnmView target, u32 self, AnmView source, AnmView parent, u32 parent_token, u32 flags, AnmVmHost&, u32& handle);
};
// Original4075e0 and effect-table row7 installation by41af40/508. The host
// owns the allocated buffer and its token. Updates/particles are not implied.
void anm_effect7_initialize(AnmView, u8* data, u32 token, u32 rate_token);
}
