#pragma once
#include "PlayerBomb.hpp"
namespace th143 {
//45cb10 primary8, including44ba30 flags and44f410 attack allocation.
//45d190 draw is a literal return0; ANM owns its visuals.
bool update_player_mallet(AnmView,AnmView equipment,PlayerState*,AnmView cheat,PlayerBombGlobals&,AnmWorld&,PlayerBombHost&);
}
