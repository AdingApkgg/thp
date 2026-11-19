#pragma once
#include "AsciiQueue.hpp"
namespace th143 {
// Typed formats used by the gameplay ASCII callers. Unknown formats fail;
// no guest vararg pointers are interpreted as native host pointers.
bool format_ascii_value(std::string_view format,double value,std::string& out);
//40b910: score in units of10, plus the separately supplied final digit.
std::string format_ascii_score(u32 value,u32 final_digit);
}
