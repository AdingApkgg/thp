#pragma once
#include "PlayerBomb.hpp"
#include "SceneCancellation.hpp"
namespace th143 {
// Connect the real primary5 update to the live bullet/enemy/item world.
// Refresh SceneCancellation actor bindings before each equipment callback.
// Other option, audio and laser services retain the session's ownership.
class PlayerBombScene final:private PlayerBombHost {
public:
    PlayerBombScene(SceneCancellation& cancellation,PlayerBombHost& services):cancellation(cancellation),services(services){}
    bool update(AnmView option,AnmView equipment,PlayerState*,AnmView cheat,PlayerBombGlobals&,const u32& special_flags,AnmWorld&);
private:
    SceneCancellation& cancellation;PlayerBombHost& services;const u32* flags=nullptr;
    bool timer_rate(u32 token,float& rate)override{return services.timer_rate(token,rate);}
    u32 global_rate_token()const override{return services.global_rate_token();}
    bool bomb_option_busy(u32 token,bool& busy)override{return services.bomb_option_busy(token,busy);}
    bool bomb_alternate_release()override{return services.bomb_alternate_release();}
    bool bomb_sound(u32 id,float x)override{return services.bomb_sound(id,x);}
    bool bomb_stop_sound(u32 id)override{return services.bomb_stop_sound(id);}
    bool bomb_bullets(AnmView position,float radius)override;
    bool bomb_lasers(AnmView position,float radius)override{return services.bomb_lasers(position,radius);}
};
}
