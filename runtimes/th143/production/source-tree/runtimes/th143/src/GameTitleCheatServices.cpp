#include "GameTitleCheatServices.hpp"
#include "SoundQueue.hpp"
#include "AsciiFormat.hpp"
namespace th143 {
bool GameTitleCheatServices::cheat_sound(u32 id){if(!audio.data)return false;SoundQueue queue;std::memcpy(queue.data.data(),audio.data+0x1c,queue.data.size());if(!queue.request(id,false))return false;std::memcpy(audio.data+0x1c,queue.data.data(),queue.data.size());return true;}
bool GameTitleCheatServices::cheat_draw_format(const std::array<float,3>& p,const char* format,double value){std::string text;return format_ascii_value(format,value,text)&&queue_ascii_text(ascii,p,text,world.viewport);}
bool GameTitleCheatServices::cheat_draw_number(const std::array<float,3>& p,i32 value){return queue_ascii_text(ascii,p,format_ascii_number(u32(value)),world.viewport);}
}
