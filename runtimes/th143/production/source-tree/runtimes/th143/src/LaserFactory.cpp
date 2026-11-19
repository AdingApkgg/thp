#include "LaserFactory.hpp"
namespace th143 {
bool create_laser(u32 manager,u32 kind,u32 parameters,LaserFactoryHost& host,u32& result){
 auto read=[&](u32 p,u32& v){return host.laser_factory_read(p,&v,4);};auto write=[&](u32 p,u32 v){return host.laser_factory_write(p,&v,4);};
 u32 count,id;if(!read(manager+0x5d4,count))return false;if(signed_word(count)>=256){result=0;return true;}
 if(!read(manager+0x5d8,id))return false;++id;if(signed_word(id)<0x10000)id=0x10000;if(!write(manager+0x5d8,id))return false;
 if(kind<=3){
  u32 token;u8* storage;const u32 bytes=laser_storage_bytes(i32(kind));if(!host.laser_factory_allocate(bytes,token,storage)||!token||!construct_laser_storage(storage,bytes,i32(kind)))return false;
  u32 tail;if(!read(manager+0x5d8,id)||!write(token+0x80,id)||!read(manager+0x5d0,tail)||!write(token+4,tail)||!write(tail+8,token)||!read(manager+0x5d4,count)||!write(manager+0x5d4,count+1)||!write(manager+0x5d0,token)||!host.laser_factory_initialize(kind,token,parameters))return false;
 }return read(manager+0x5d8,result);
}
}
