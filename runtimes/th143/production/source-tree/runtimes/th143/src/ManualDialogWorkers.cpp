#include "ManualDialogWorkers.hpp"
#include <initializer_list>
namespace th143 {
bool load_manual_dialog_resource(u32& owner,AnmView app,ManualDialogWorkersHost& host){
 if(!app.data)return false;u32 resource;if(!host.manual_request_resource(19,0x4c5884,resource))return false;
 AnmView s;if(!host.manual_region(owner,0x1c0,s)||!s.data)return false;s.put(0x130,resource);
 if(!resource)return host.manual_resource_error(0x4e20a8,0x4c52bc);
 app.put(0x99c,0);app.put(0x998,1);for(u32 at:{8u,12u}){AnmView cb;if(!host.manual_region(s.get(at),0x28,cb)||!cb.data)return false;cb.put(4,cb.get(4)|2u);}return true;
}
bool read_manual_dialog_page(u32& owner,AnmView app,ManualDialogWorkersHost& host){
 if(!app.data)return false;const u32 old=owner;u32 buffer;if(!host.manual_read_page(old+0x13c,old+0x1bc,0,buffer))return false;
 AnmView s;if(!host.manual_region(owner,0x1c0,s)||!s.data)return false;s.put(0x134,buffer);s.put(0x138,3);app.put(0x99c,0);app.put(0x998,1);return true;
}
}
