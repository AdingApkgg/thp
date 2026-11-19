#include "ReplayFileValidationNov14.hpp"
#include "../../th12/th12_web/cpp/game/ResourceCrypt.hpp"
#include "../../th12/th12_web/cpp/game/Lzss.hpp"
#include <vector>
#include <memory>
namespace th143 {
ReplayFileValidation validate_replay_file(const u8* data,u32 size){
 if(!data||size<36)return ReplayFileValidation::Truncated;
 const auto get=[&](u32 at){u32 v;std::memcpy(&v,data+at,4);return v;};
 u16 version;std::memcpy(&version,data+4,2);
 if(get(0)!=0x33343174||version!=1)return ReplayFileValidation::BadHeader;
 const u32 compressed=get(0x1c),decoded=get(0x20);
 if(compressed>size-36)return ReplayFileValidation::Truncated;
 if(!compressed||compressed>0x4000000||decoded<0xb0||decoded>0x4000000)return ReplayFileValidation::BadSize;
 std::vector<u8> first(compressed),second(compressed),output(decoded);u32 written=0;
 if(!th11::resource_crypt(data+36,first.data(),compressed,{0x5c,0xe1,0x400,compressed},false)||
    !th11::resource_crypt(first.data(),second.data(),compressed,{0x7d,0x3a,0x100,compressed},false))return ReplayFileValidation::BadPayload;
 auto decoder=std::make_unique<th11::Lzss>();
 if(!decoder->decode(second.data(),compressed,output.data(),decoded,written)||written!=decoded)return ReplayFileValidation::BadPayload;
 return ReplayFileValidation::Valid;
}
}
