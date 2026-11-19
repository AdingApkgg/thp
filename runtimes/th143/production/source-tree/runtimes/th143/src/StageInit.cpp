#include "StageInit.hpp"
#include <vector>

namespace th143 {
bool initialize_stage(StageState& state,u32 self,const std::string& filename,StageInitGlobals& g,StageInitHost& host){
    auto s=state.view();g.current=self;s.put(0x423c,g.scene);
    u32 source=s.get(0x426c),size=s.get(0x4270);
    if(!source){g.last_filename=filename;if(!host.read_stage_file(filename,source,size))return false;s.put(0x426c,source);s.put(0x4270,size);if(!source)return false;}
    if(size<0x90||size>0x4000000)return false;
    u32 copy;if(!host.allocate_stage_storage(size,true,copy))return false;s.put(0x10,copy);
    std::vector<u8> bytes(size);if(!host.read_stage_memory(source,bytes.data(),size))return false;
    AnmView header{bytes.data()};u16 raw_objects,raw_primitives;std::memcpy(&raw_objects,bytes.data(),2);std::memcpy(&raw_primitives,bytes.data()+2,2);
    const i32 objects=std::int16_t(raw_objects),primitives=std::int16_t(raw_primitives);
    if(objects<0||primitives<0||0x90+u32(objects)*4>size)return false;
    std::string animation;for(u32 i=16;i<0x90&&bytes[i];++i)animation.push_back(char(bytes[i]));if(animation.size()==128)return false;
    // Publish the raw duplicate before the original ANM request boundary.
    if(!host.write_stage_memory(copy,bytes.data(),size))return false;
    u32 resource;if(!host.request_stage_animation((g.scene&1)+3,animation,resource))return false;s.put(0x204,resource);if(!resource)return false;
    s.put(0x14,copy+0x90);s.put(0x18,copy+header.get(4));s.put(0x1c,copy+header.get(8));
    if(header.get(4)>size||header.get(8)>size)return false;
    for(u32 i=0;i<u32(objects);++i){const u32 at=0x90+i*4;const u32 relative=header.get(at);if(relative>=size)return false;header.put(at,relative+copy);}
    if(!host.write_stage_memory(copy,bytes.data(),size))return false;
    u32 animations;const u32 animation_bytes=u32(primitives)*AnmView::bytes;
    if(!host.allocate_stage_storage(animation_bytes,true,animations))return false;s.put(0x208,animations);
    std::vector<u8> zero(animation_bytes);if(animation_bytes&&!host.write_stage_memory(animations,zero.data(),animation_bytes))return false;
    std::memcpy(state.data.data()+0x4274,g.camera_defaults.data(),g.camera_defaults.size());
    for(auto pair:{std::pair<u32,u32>{0x4274,0},{0x4278,0},{0x427c,0xc4160000},{0x4280,0},{0x4284,0x43960000},{0x4288,0x44160000},{0x428c,0},{0x4290,0x3f800000},{0x4294,0},{0x42b0,0},{0x42b4,0},{0x42b8,0},{0x42bc,0},{0x42c0,0},{0x42c4,0}})s.put(pair.first,pair.second);
    s.put(0x308c,0x4b12a310);
    for(auto item:{std::array<u32,4>{0x40e830,17,0,8},{0x40e840,3,1,12},{0x40e850,6,1,0x4268}}){u32 callback;
        if(!host.register_stage_callback(item[0],i32(item[1]),item[2]!=0,self,callback))return false;s.put(item[3],callback);
    }s.put(0x4240,0);
    if(!(s.get(0x48)&1)){s.put(0x44,0x4e40b0);s.put(0x48,s.get(0x48)|1);}
    s.put(0x38,0xffffffff);s.put(0x3c,0);s.put(0x40,0);s.put(0x4224,s.get(0x4224)|1);s.put(0xa0,0);s.put(0xf8,0);return true;
}
}
