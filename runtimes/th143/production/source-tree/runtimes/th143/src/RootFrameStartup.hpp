#pragma once
#include "RootStartup.hpp"

namespace th143 {
// Compose startup with the existing live frame, preserving the immediate
// error return rather than running the score/background/timer tail afterward.
i32 root_frame_with_startup(RootState&,AnmView hud,RootFrameGlobals&,
                            RootStartupGlobals&,RootFrameHost&,RootStartupHost&);
}
