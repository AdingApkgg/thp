#include "RootCleanup.hpp"

namespace th143 {
bool cleanup_root(RootState& root,RootCleanupGlobals& g,RootCleanupHost& host){
    if(!root.view().get(0x94)&&!host.save_before_cleanup())return false;
    g.game_flags&=~5u;g.rate=1.f;g.auxiliary1=0;g.auxiliary2=0;
    const u32 state=g.application_state;
    if(state==10||state==11||state==19){
        if(!host.cleanup_transition())return false;
        if(g.previous_scene==g.current_scene)g.game_flags|=1;
        else {g.previous_scene=g.current_scene;g.scene_descriptor=0x4ddec0+g.current_scene*0xac;g.game_flags|=0x1000;}
    }else if(state==12){if(!host.cleanup_transition())return false;g.game_flags|=4;}
    else if(state==4||state==16){if(!host.cleanup_transition())return false;}
    else if(state==14){
        if(!host.cleanup_transition())return false;
        if(g.previous_scene!=g.current_scene){const u32 next=g.deaths+1;g.deaths=signed_word(next)>=10?9:next;g.game_flags|=0x10;}
        g.game_flags|=1;
    }
    if(!host.independent_graphics())return false;
    auto destroy=[&](RootOwner kind){const u32 token=g.owner(kind);return !token||(host.destroy_root_owner(kind,token,g)&&host.release_root_storage(token));};
    if(!(g.game_flags&4)){
        if(state!=15&&state!=16&&!destroy(RootOwner::game))return false;
        for(RootOwner kind:{RootOwner::replay,RootOwner::previous_replay,RootOwner::menu,RootOwner::hud,RootOwner::player,RootOwner::player_aux,RootOwner::bullets,RootOwner::items,RootOwner::lasers,RootOwner::scores,RootOwner::cheats})if(!destroy(kind))return false;
    }else if(!host.preserve_gameplay(g))return false;
    if(g.game_flags&0x11){if(!host.reset_root_enemies(g.owner(RootOwner::enemies)))return false;}
    else if(!destroy(RootOwner::enemies))return false;
    if(!host.cleanup_root_effects(g.owner(RootOwner::effects))||!destroy(RootOwner::extra))return false;
    for(u32 at:{8,12}){u32 callback=root.view().get(at);if(callback&&!host.remove_root_callback(callback))return false;}
    g.root=0;
    if(!(g.game_flags&0x1001)&&!host.fade_root_audio())return false;
    if(!host.pause_root_audio())return false;
    g.shutdown=1;g.clear_color=g.game_flags&1?0:0xff000000;return true;
}
bool destroy_current_root(RootState& root,RootCleanupGlobals& g,RootCleanupHost& host){
    g.presentation=0;const u32 token=g.root;
    return !token||(cleanup_root(root,g,host)&&host.release_root_storage(token));
}
}
