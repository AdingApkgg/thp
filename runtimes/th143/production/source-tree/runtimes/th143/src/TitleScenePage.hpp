#pragma once
#include "TitleScenePresentation.hpp"
#include "TitleSceneResponses.hpp"
#include "TitleDialog.hpp"
#include "TitleMainControl.hpp"
namespace th143 {
struct TitleScenePageBindings {
    TitleActivationBindings& owners;TitleDialogHost& dialog;TitleMainHost& sound;
    GameTitlePreviewImages& png;GameTitleSavedPreviewImages& saved;
    std::array<u32,4>& equipment;std::array<u32,4>& saved_equipment;
};
//4624e0 pending1 and interactive2, through entry into equipment3/start4/exit6.
// Active achievement overlays and the subsequent transition bodies are separate.
bool advance_title_scene_page(TitleScenePageBindings&,const TitleMainKeys&,u32& result);
}
