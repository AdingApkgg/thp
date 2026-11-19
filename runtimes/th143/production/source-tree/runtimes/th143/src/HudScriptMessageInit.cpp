#include "HudScriptMessageInit.hpp"
#include <cstring>
#include <initializer_list>
namespace th143 {
bool initialize_hud_script_message(AnmView s,u32 script,u32 resource,HudScriptMessageInitHost& host){
 std::memset(s.data,0,0x1b8);
 for(u32 at:{0u,0x14u,0x28u}){s.put(at+4,0xffffffff);s.put(at+0x10,0x4e40b0);s.put(at+0x14,1);}
 s.put(0x158,script);
 for(u32 pair=0;pair<2;++pair){
  const u32 first=0x58+pair*8,second=first+4;u32 handle;
  if(!host.message_create_text(resource,i32(pair),handle))return false;s.put(first,handle);
  if(!host.message_create_text(resource,i32(pair),handle))return false;s.put(second,handle);if(!host.message_signal_text(handle,7))return false;
  for(u32 at:{first,second})for(u32 color:{0x528u,0x529u}){auto vm=host.message_text_vm(s.get(at));if(!vm.data)return false;vm.data[color]=0x15;}
 }
 for(u32 at:{0x58u,0x5cu,0x60u,0x64u}){auto vm=host.message_text_vm(s.get(at));if(!vm.data)return false;vm.put(0x1c,vm.get(0x1c)|0x800);}
 for(u32 at:{0x58u,0x5cu,0x60u,0x64u}){auto vm=host.message_text_vm(s.get(at));if(!vm.data)return false;vm.put(0x5bc,0x430740);}
 for(u32 at:{0x15cu,0x168u,0x174u})s.put(at,0x41800000);
 s.put(0x184,0x80);s.put(0x1a0,0x43c00000);s.put(0x1a4,0x44200000);s.put(0x1ac,0x43a00000);return true;
}
}
