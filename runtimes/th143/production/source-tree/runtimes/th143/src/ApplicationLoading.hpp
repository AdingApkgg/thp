#pragma once
#include "AnmSignal.hpp"
namespace th143 {
// Application+9ac, globals540de8/ec/f0 and4e6b7c. The application owns these
// words; the transition only signals its live loading visuals and clears them.
struct ApplicationLoading {
    u32 state=0;std::array<u32,3> visuals{};u32 context=0;
};
bool finish_application_loading(ApplicationLoading&,AnmWorld&); //444e00
}
