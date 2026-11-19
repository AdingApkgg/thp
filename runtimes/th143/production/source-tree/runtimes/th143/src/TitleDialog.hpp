#pragma once
#include "TitleSceneEntry.hpp"
namespace th143 {
struct TitleDialogHost {virtual ~TitleDialogHost()=default;virtual bool title_dialog_text(AnmView,const std::vector<u8>&)=0;};
//45ec10/464360: retire the former frame, create the correct one/two-line
// frame, fill its persistent text VMs and update the frame/text positions.
bool clear_title_dialog(GameTitleRuntime&,AnmResourceWorld&);
bool show_title_dialog(GameTitleRuntime&,AnmResourceWorld&,TitleDialogHost&,const std::vector<u8>& first,const std::vector<u8>& second,float x,float y,float extent);
}
