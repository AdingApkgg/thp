#include "../../cpp/game/StageEclTransferTh14.hpp"
#include <emscripten.h>
#include <tuple>
using namespace th11;
namespace {
u32 counts[4]{};
bool same(const StageResource& a,const StageResource& b){
    if(a.animation_name!=b.animation_name||a.animation_count!=b.animation_count||a.objects.size()!=b.objects.size()||a.instances.size()!=b.instances.size()||a.instructions.size()!=b.instructions.size()||!b.error.empty())return false;
    for(u32 i=0;i<a.objects.size();++i){const auto& x=a.objects[i];const auto& y=b.objects[i];
        if(std::tie(x.id,x.layer,x.flags)!=std::tie(y.id,y.layer,y.flags)||std::memcmp(&x.position,&y.position,sizeof(Vec3))||std::memcmp(&x.size,&y.size,sizeof(Vec3))||x.primitives.size()!=y.primitives.size())return false;
        static_assert(sizeof(StagePrimitive)==28);if(!x.primitives.empty()&&std::memcmp(x.primitives.data(),y.primitives.data(),x.primitives.size()*sizeof(StagePrimitive)))return false;
    }
    static_assert(sizeof(StageInstance)==16);if(!a.instances.empty()&&std::memcmp(a.instances.data(),b.instances.data(),a.instances.size()*sizeof(StageInstance)))return false;
    for(u32 i=0;i<a.instructions.size();++i){const auto& x=a.instructions[i];const auto& y=b.instructions[i];
        if(std::tie(x.time,x.opcode,x.length,x.offset)!=std::tie(y.time,y.opcode,y.length,y.offset)||x.arguments!=y.arguments)return false;
    }
    return true;
}
bool same(const EclResource& a,const EclResource& b){
    if(a.bytes!=b.bytes||a.animations!=b.animations||a.includes!=b.includes||a.subroutines.size()!=b.subroutines.size())return false;
    for(u32 i=0;i<a.subroutines.size();++i){const auto& x=a.subroutines[i];const auto& y=b.subroutines[i];if(std::tie(x.name,x.offset,x.size)!=std::tie(y.name,y.offset,y.size))return false;}
    return true;
}
}
extern "C" {
EMSCRIPTEN_KEEPALIVE int fixture_compare(u32 kind,const u8* source,u32 source_size,const u8* packet,u32 size){
    u32 identity_size=0,identity_hash=0;
    if(kind==1){StageResource direct,delivered;if(!direct.open(source,source_size))return -1;
        if(!th14_decode_std_transfer(packet,size,delivered,&identity_size,&identity_hash))return -2;
        if(!same(direct,delivered))return -4;
        counts[0]=u32(direct.objects.size());counts[1]=u32(direct.instances.size());counts[2]=u32(direct.instructions.size());counts[3]=direct.animation_count;
    }else if(kind==2){EclResource direct,delivered;if(!direct.open(source,source_size))return -1;
        if(!th14_decode_ecl_transfer(packet,size,delivered,&identity_size,&identity_hash))return -2;
        if(!same(direct,delivered))return -4;
        counts[0]=u32(direct.subroutines.size());counts[1]=u32(direct.animations.size());counts[2]=u32(direct.includes.size());counts[3]=u32(direct.bytes.size());
    }else return -5;
    return identity_size==source_size&&identity_hash==anm_bytes_hash(source,source_size)?1:-3;
}
EMSCRIPTEN_KEEPALIVE u32 fixture_count(u32 field){return field<4?counts[field]:0;}
EMSCRIPTEN_KEEPALIVE int fixture_reject(u32 kind,const u8* packet,u32 size){
    if(kind==1){StageResource output;output.error="unchanged";output.animation_name="kept";output.objects.resize(1);output.objects[0].id=123;
        if(th14_decode_std_transfer(packet,size,output))return 0;
        return output.error=="unchanged"&&output.animation_name=="kept"&&output.objects.size()==1&&output.objects[0].id==123&&output.instructions.empty()&&output.instances.empty();
    }
    if(kind==2){EclResource output;output.bytes={1,2,3};output.animations={"kept"};
        if(th14_decode_ecl_transfer(packet,size,output))return 0;
        return output.bytes==std::vector<u8>({1,2,3})&&output.animations==std::vector<std::string>({"kept"})&&output.subroutines.empty()&&output.includes.empty();
    }
    return 0;
}
}
