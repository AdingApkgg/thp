#pragma once
#include "TitlePreviewImage.hpp"
namespace th143 {
//411b00 screenshot upload into the fixed 288x336 rectangle of title.anm.
class GameTitleSavedPreviewImages {
public:
    GameTitleSavedPreviewImages(AnmResourceWorld& memory,AnmTextureStore& images,AnmTextureStoreDevice& notifications,TitlePreviewImageDevice& device):memory(memory),images(images),notifications(notifications),device(device){}
    bool upload(u32 texture,u32 object);
    bool preload(u32 texture){return device.preload_preview_texture(texture);}
private:
    AnmResourceWorld& memory;AnmTextureStore& images;AnmTextureStoreDevice& notifications;TitlePreviewImageDevice& device;
};
//46382a..4639d8 response consumption in a pending scene-page update below20.
bool advance_title_scene_saved_pending(GameTitleRuntime&,AnmResourceWorld&,GameTitleSavedPreviewImages&,u32& result);
}
