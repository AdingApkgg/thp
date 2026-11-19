#include "GameSavedPreviewFiles.hpp"
namespace th143 {
bool GameSavedPreviewFiles::read_saved_preview_file(const std::string& name,u32& token,u32& n){std::vector<u8> bytes;if(!files.read_saved_preview_bytes(name,bytes))return false;n=bytes.size();return allocate_saved_preview_array(n,token)&&world.write(token,bytes.data(),n);}
}
