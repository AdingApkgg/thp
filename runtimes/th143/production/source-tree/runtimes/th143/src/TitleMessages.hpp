#pragma once
#include "AnmState.hpp"
#include <vector>
namespace th143 {
//45f0ca..45f2c4 titlemsg parser. Backing includes readable file-allocation
// padding: native skips '@' without reducing its independent remaining count.
// The title owns all records; unused bytes and failed scanf fields survive.
bool load_title_messages(AnmView title,u32 source_token,u32 declared_bytes,std::vector<u8>& backing);
}
