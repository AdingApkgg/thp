#pragma once
#include "TitleActivation.hpp"
#include <string>
namespace th143 {
struct TitlePreviewWorkerHost {
    virtual ~TitlePreviewWorkerHost()=default;
    virtual bool read_scene_preview(const std::string& name,std::vector<u8>& bytes,bool& found)=0;
    //411820's saved screenshot loader; a missing file succeeds with token0.
    virtual bool read_saved_preview(const std::string& name,u32& token)=0;
    virtual bool sleep_scene_preview(u32 milliseconds)=0;
};
//464b20 background queue protocol. Main-thread consumption, image upload and
// the saved screenshot decoder are separate bodies, owned by the caller.
bool run_title_preview_worker(GameTitleRuntime&,AnmResourceWorld&,AnmView application,TitlePreviewWorkerHost&,u32 budget=1000000);
}
