#include "HudScriptMessageFactory.hpp"
namespace th143 {
bool create_hud_script_message(AnmView hud,AnmView root,u32 flags,i32 id,HudScriptMessageFactoryHost& host){
 if(!(flags&0x400))return true;
 // Negative IDs dispatch music/scene transitions and have separate services.
 if(id<0)return false;root.put(0x80,root.get(0x80)|0x10);
 if(const u32 old=hud.get(0x198)){if(!host.message_factory_destroy(old))return false;hud.put(0x198,0);}
 u32 token;AnmView message{nullptr};if(!host.message_factory_allocate(0x1b8,token,message)||!token||!message.data)return false;
 const u32 file=hud.get(0x19c);u32 offset;if(!host.message_factory_read(file+u32(id)*8+4,offset))return false;
 if(!host.message_factory_construct(token,message,file+offset))return false;
 hud.put(0x198,token);message.put(0,u32(id));return true;
}
}
