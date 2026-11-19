#pragma once
#include "TrophyCatalog.hpp"
namespace th143 {
//468210 and468250 decrypt into the same541360 scratch string, preserving its
//unused tail. Valid catalog indices0..69, unlock0/1 and descriptionline0..2;
//each encrypted256byte field must contain its encrypted NUL.
bool lookup_trophy_name(AnmView catalog,u32 index,AnmView scratch,u32& result);
bool lookup_trophy_description(AnmView catalog,u32 index,u32 unlocked,u32 line,AnmView scratch,u32& result);
}
