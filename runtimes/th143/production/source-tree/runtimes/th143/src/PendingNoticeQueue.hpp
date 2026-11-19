#pragma once
#include "SaveData.hpp"
namespace th143 {
//4476d0 uses a wrapping32-bit index andleaves the consumed slot unchanged.
bool pop_pending_notice(AnmView save,u32& id);
}
