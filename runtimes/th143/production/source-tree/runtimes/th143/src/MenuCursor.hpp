#pragma once
#include "AnmState.hpp"

namespace th143 {
// The0xd8 selection controller embedded at PauseMenu+38/+110. References the
// owner's bytes, retaining its16-depth state stack and16 disabled entries.
struct MenuCursor {
    static constexpr u32 bytes=0xd8;
    AnmView state;
    bool select(i32 value,u32 budget=100000);
    bool move(i32 amount,i32& result,u32 budget=100000);
    bool disable(i32 value,u32 budget=100000);
    bool push();
    void pop();
    void begin(){state.put(4,state.get(0));}
    void clear_disabled(){state.put(0xd4,0);}
};
}
