#include "GameReplayFileLoad.hpp"
#include "../../th12/th12_web/cpp/game/ResourceCrypt.hpp"
#include <vector>
namespace th143 {
bool load_game_replay_file(GameManagerState& manager,th11::Lzss& decoder,const u8* name,u32 available,GameReplayFileHost& h,u32& result){
 if(!name)return false;u32 n=0;while(n<available&&n<256&&name[n])++n;if(n==available||n>=256)return false;auto m=manager.view();std::memcpy(m.data+0x7c,name,n+1);result=0xffffffff;
 const auto failed=[&](){return h.replay_directory(0x53a0cd);};u32 flags,body=0;if(!h.replay_game_flags(flags))return false;
 if(!(flags&0x80)){
  if(!h.replay_directory(0x5390cd))return false;constexpr u8 prefix[]="replay/";std::vector<u8> path(prefix,prefix+sizeof prefix-1);path.insert(path.end(),name,name+n+1);bool exists;if(!h.replay_exists(path.data(),path.size(),exists))return false;if(!exists)return failed();u32 status;if(!h.replay_open(path.data(),path.size(),status))return false;if(status)return failed();
  u32 header;if(!h.replay_read(36,header))return false;m.put(0x18,header);AnmView view;if(!h.replay_region(header,36,view))return false;u16 version;std::memcpy(&version,view.data+4,2);if(view.get(0)!=0x33343174||version!=1)return h.replay_close()&&failed();
  if(!h.replay_read(view.get(0x1c),body)||!h.replay_close())return false;
 }else{u32 token,file_bytes;if(!h.replay_archive(name,n+1,token,file_bytes))return false;m.put(0x18,token);body=token+36;}
 AnmView header;if(!h.replay_region(m.get(0x18),36,header))return false;const u32 decoded_size=header.get(0x20);if(decoded_size<0xb0)return false;u32 decoded;if(!h.replay_allocate(decoded_size,decoded))return false;m.put(0x64,decoded);
 const u32 compressed=header.get(0x1c);AnmView input,output;if(!h.replay_region(body,compressed,input)||!h.replay_region(m.get(0x64),decoded_size,output))return false;std::vector<u8> first(compressed),second(compressed);
 if(!th11::resource_crypt(input.data,first.data(),compressed,{0x5c,0xe1,0x400,compressed},false)||!th11::resource_crypt(first.data(),second.data(),compressed,{0x7d,0x3a,0x100,compressed},false))return false;std::memcpy(input.data,second.data(),compressed);u32 written=0;if(!decoder.decode(input.data,compressed,output.data,decoded_size,written)||written!=decoded_size)return false;
 m.put(0x1c,m.get(0x64));const u32 checkpoint=m.get(0x1c)+0xa8;m.put(0x4c,checkpoint);m.put(0x3c,checkpoint+0x10c);m.put(0x44,m.get(0x3c)+output.get(0xac)*6);
 if(!h.replay_game_flags(flags))return false;if(!(flags&0x80)&&body&&!h.replay_free(body))return false;if(!h.replay_directory(0x53a0cd))return false;result=0;return true;
}
}
