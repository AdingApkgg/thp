#pragma once
#include "EclVm.hpp"

namespace th143 {
// CPU text bitmap46b590/46b400/46b050. Formats are original D3DFORMAT
// values21(A8R8G8B8),25(A1R5G5B5),26(A4R4G4B4). Bytes remain native order.
struct TextPixels {
    u8* data=nullptr;
    u32 capacity=0,width=0,height=0,stride=0,format=26;
    // 46b400's last-column bottom-right read reaches one word beyond its
    // copied width*rows words. Supply the retained allocator padding bytes.
    u16 scratch_guard=0;
    bool invert_alpha(u32 rows);
    bool blur_alpha(u32 rows);
    bool bleed_color(u32 rows);
};
}
