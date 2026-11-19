#pragma once
#include "AnmState.hpp"
namespace th143 {
struct TitleRootPreparationHost {
    virtual ~TitleRootPreparationHost()=default;
    virtual bool stop_title_preview(AnmView worker)=0;
    virtual bool title_preview_free(u32 token)=0;
    virtual bool title_preview_region(u32 token,u32 bytes,AnmView&)=0;
};
//45f580. Nonempty saved queue only returns when a declared free callback
//changes it; the original does not pop it. Nonreturning/fault inputs excluded.
bool prepare_title_for_root(AnmView title,TitleRootPreparationHost&,u32 budget=4096);
}
