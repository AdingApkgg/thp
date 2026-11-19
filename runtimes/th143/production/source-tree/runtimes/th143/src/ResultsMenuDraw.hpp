#pragma once
#include "AnmState.hpp"
#include <array>
namespace th143 {
struct ResultsMenuDrawGlobals {u32 scene=0,score=0,graze=0;float scale=1;};
struct ResultsMenuDrawHost {
    virtual ~ResultsMenuDrawHost()=default;
    virtual bool results_child_position(u32& parent,i32 script,std::array<float,3>&)=0;
    virtual bool results_number(const std::array<float,3>&,u32)=0;
    virtual bool results_subpage(u32 entry,AnmView menu)=0;
};
// Actual44b4a0; resource/child position and grouped ASCII output are services.
bool draw_results_menu(AnmView menu,AnmView save,AnmView ascii,const ResultsMenuDrawGlobals&,ResultsMenuDrawHost&);
}
