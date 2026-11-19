#pragma once
#include "TitleOptionControl.hpp"
namespace th143 {
//4623d0 swaps every duplicate among six pending slots with the old selected
//value, then refreshes461870 and requests sound7. UI callers select slots0..3.
bool assign_title_pad_button(AnmView title,u32 self,u32 slot,i32 button,TitleOptionControlHost&);
}
