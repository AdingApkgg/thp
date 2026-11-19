#pragma once
#include "MusicCommentLine.hpp"
#include <vector>
namespace th143 {
//466773..46680e original musiccmt.txt record loop, including the independent
// remaining counter that does not account for '@'. Backing includes readable
// allocation padding; records hold a name, title and eight comment lines.
bool parse_music_room_comments(AnmView title,u32 declared_bytes,std::vector<u8>& backing,u32& records);
}
