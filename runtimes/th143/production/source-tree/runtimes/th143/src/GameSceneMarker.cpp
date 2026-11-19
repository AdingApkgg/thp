#include "GameSceneMarker.hpp"
namespace th143 {
bool set_game_scene_marker(AnmView game,u32 value){if(!game.data)return false;const u32 previous=game.get(0xb4);game.put(0xb4,value);if(previous!=value)game.put(0xbc,0);return true;}
}
