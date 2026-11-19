#pragma once
#include "TitleOptionControl.hpp"
#include <array>
namespace th143 {
struct TitleOptionViewHost:TitleOptionControlHost {
 // Read-only parent/child resolution, equivalent to the inlined tree searches
 // and45eb70/484c00, in the valid nonnull option-animation domain.
 virtual bool title_option_child(u32 self,u32 parent,i32 script,u32& vm)=0;
};
// Full460540 volume globals/music request and all twelve digit sprites plus
// leading-zero visibility. Sprite binding/queue implementation is supplied.
bool refresh_title_option_view(AnmView title,u32 self,TitleOptionViewHost&);
}
