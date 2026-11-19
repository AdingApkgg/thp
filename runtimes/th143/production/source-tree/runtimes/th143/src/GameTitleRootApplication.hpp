#pragma once
#include "ApplicationState.hpp"
#include "TitleCleanup.hpp"
namespace th143 {
// Binds application4458a0's Title destructor and Root factory to the same
// live owners and Scheduler. The Root worker remains the platform's thread.
class GameTitleRootApplication final:public ApplicationStateServices {
public:
    GameTitleRootApplication(AnmView application,TitleLoadBindings& title,RootState& root,BackgroundWorker& worker,RootFactoryGlobals& globals,u32& presentation,RootFactoryHost& host,ApplicationStateServices& next):application(application),title(title),root(root),worker(worker),globals(globals),presentation(presentation),host(host),next(next){}
    TitleReplayCleanupHost* replays=nullptr;
    bool lock_application_state(bool acquire)override{return next.lock_application_state(acquire);}
    bool application_state_call(u32,u32,u32,u32&)override;
    bool application_root_mode(u32& mode)override{if(globals.root){mode=root.view().get(0x94);return true;}return next.application_root_mode(mode);}
private:
    AnmView application;TitleLoadBindings& title;RootState& root;BackgroundWorker& worker;RootFactoryGlobals& globals;u32& presentation;RootFactoryHost& host;ApplicationStateServices& next;
};
}
