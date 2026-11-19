#pragma once
#include "TitleActivation.hpp"
#include "AnmTextureStore.hpp"
namespace th143 {
struct TitlePreviewImageDevice {virtual ~TitlePreviewImageDevice()=default;virtual bool preload_preview_texture(u32 texture)=0;};
// Shared persistent texture images and resource memory; all pixel work runs
// in the portable decoder/converter/alpha-edge fill before device notification.
class GameTitlePreviewImages {
public:
    GameTitlePreviewImages(AnmResourceWorld& memory,AnmTextureStore& images,AnmTextureStoreDevice& notifications,TitlePreviewImageDevice& device):memory(memory),images(images),notifications(notifications),device(device){}
    bool upload_png(u32 texture,u32 source,u32 bytes);
    bool preload(u32 texture){return device.preload_preview_texture(texture);}
private:
    AnmResourceWorld& memory;AnmTextureStore& images;AnmTextureStoreDevice& notifications;TitlePreviewImageDevice& device;
};
//463602..4637b4 PNG response queues, in the pending substate1 frame below20.
// Saved screenshot responses, active page initialization and loading-signal
// cleanup are separate branches and reject until their bodies are bound.
bool advance_title_scene_png_pending(GameTitleRuntime&,AnmResourceWorld&,GameTitlePreviewImages&,u32& result);
}
