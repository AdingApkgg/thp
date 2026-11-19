#include "HudLoad.hpp"
#include <vector>
namespace th143 {
bool load_hud_scene(AnmView hud,HudLoadGlobals& g,HudLoadHost& h,i32& result){
    auto read=[&](u32 p,u32& value){return h.hud_load_read(p,&value,4);};
    auto error=[&](){if(!h.hud_load_error())return false;result=-1;return true;};
    u32 descriptor=g.descriptor,name;if(!descriptor||!read(descriptor+0x14,name))return false;
    if(name){u32 resource;if(!h.load_hud_scene_animation(name,resource))return false;hud.put(0x14c,resource);if(!resource)return error();descriptor=g.descriptor;}
    if(!descriptor||!read(descriptor+0x10,name))return false;
    if(g.pending_file){hud.put(0x19c,g.pending_file);if(!h.hud_cached_file_log(name))return false;g.pending_file=0;}
    else if(name){
        const u8 zero=0;if(!h.hud_load_write(0x541050,&zero,1))return false;
        std::vector<u8> text;bool terminated=false;
        for(u32 i=0;i<4096;++i){u8 byte;if(!h.hud_load_read(name+i,&byte,1))return false;text.push_back(byte);if(!byte){terminated=true;break;}}
        if(!terminated||!h.hud_load_write(0x541050,text.data(),text.size()))return false;
        u32 file;if(!h.read_hud_message_file(0x541050,file))return false;hud.put(0x19c,file);if(!file)return error();
    }
    const u32 flags=hud.get(0x134);if(!(flags&1)){hud.put(0x130,0x4e40b0);hud.put(0x134,flags|1);}
    hud.put(0x128,0);hud.put(0x12c,0);hud.put(0x124,0xffffffff);hud.put(0x144,g.score);
    hud.put(0x1a0,0xffffffff);hud.put(0x1a8,0xffffffff);result=0;return true;
}
}
