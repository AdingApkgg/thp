#pragma once
#include "AnmTransform.hpp"
#include <string>
#include <string_view>
namespace th143 {
//40b660 copies one string and snapshots style into the existing ASCII owner.
//40ba50 uses the same queue and marks its latest entry for the interface layer.
// Formatting and glyph rendering are separate from this byte-compatible queue.
bool queue_ascii_text(AnmView owner,const std::array<float,3>& position,std::string_view text,const AnmViewport&,bool interface_layer=false);
//40b810's original unsigned comparisons/divisions and signed decimal groups.
std::string format_ascii_number(u32 value);
}
