#pragma once
#include "GameEnemyRuntime.hpp"
#include "EnemyScripts.hpp"
#include "PlayerCamera.hpp"
#include "AnmResourceWorld.hpp"
namespace th143 {
// Live primary1 idle aiming uses the actual manager's first boss and player.
// Capture/audio/time-scale/surface/cancellation services remain unbound here;
// entering a path that needs them fails instead of faking those side effects.
bool update_game_player_camera_aim(AnmView option,GameOwnerRuntime&,GameEnemyRuntime&,
    EnemyScripts&,AnmView cheat,PlayerCameraGlobals&,AnmResourceWorld&);
}
