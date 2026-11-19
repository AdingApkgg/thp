#include "LaserConstructor.hpp"
namespace th143 {
u32 laser_storage_bytes(i32 kind){static constexpr u32 sizes[]={0x1a78,0x14d0,0x14f0,0x1ee4};return kind==-1?0x5c0:kind>=0&&kind<4?sizes[kind]:0;}
bool construct_laser_storage(u8* data,u32 bytes,i32 kind){
 const u32 needed=laser_storage_bytes(kind);if(!data||!needed||bytes<needed)return false;
 std::memset(data,0,0x5c0);AnmView v{data};v.put(0x18,0xffffffff);v.put(0x24,0x4e40b0);v.put(0x28,1);
 if(kind==-1)return true;
 static constexpr u32 tables[]={0x4c5ed8,0x4c5e70,0x4c5da0,0x4c5e08};v.put(0,tables[kind]);
 std::memset(data+0x5c0,0,kind==1?0x374:0x354);
 if(kind==1){v.put(0x5ec,word(8.f));anm_construct({data+0x938});anm_construct({data+0xf04});}
 else{anm_construct({data+0x914});if(kind!=3)anm_construct({data+0xee0});if(kind==0)anm_construct({data+0x14ac});}
 return true;
}
}
