#include "ReplaySemanticFileValidationNov14.hpp"
#include "../../th12/th12_web/cpp/game/ResourceCrypt.hpp"
#include "../../th12/th12_web/cpp/game/Lzss.hpp"
#include <array>
#include <memory>
#include <vector>
namespace th143 {
ReplaySemanticValidation validate_replay_decoded_payload(const u8* data,u32 size){
 if(!data||size<0x1b4)return ReplaySemanticValidation::BadInput;
 const auto get=[&](u32 at){u32 v;std::memcpy(&v,data+at,4);return v;};
 const std::array<u32,10> first{1,7,13,20,27,35,43,51,58,66},length{6,6,7,7,8,8,8,7,8,10};
 const u32 day=get(0x88),within=get(0x8c),scene=get(0x90);
 if(day>=10||within>=length[day]||scene!=first[day]+within)return ReplaySemanticValidation::BadMetadata;
 u16 checkpoint;std::memcpy(&checkpoint,data+0xa8,2);
 if(checkpoint!=scene||get(0x94)>=9)return ReplaySemanticValidation::BadMetadata;
 if(get(0x98)>=9&&get(0x98)!=0xffffffff)return ReplaySemanticValidation::BadMetadata;
 const u32 frames=get(0xac),input=get(0xb0);
 const std::uint64_t bytes=std::uint64_t(frames)*6,speeds=(std::uint64_t(frames)+28)/30;
 if(!frames||input>size-0x1b4||bytes+speeds>input)return ReplaySemanticValidation::BadInput;
 const u32 terminal=0x1b4+u32(bytes)-6;
 for(u32 i=0;i<6;++i)if(data[terminal+i]!=0xff)return ReplaySemanticValidation::BadInput;
 return ReplaySemanticValidation::Valid;
}
ReplaySemanticValidation validate_replay_semantic_file(const u8* data,u32 size){
 if(!data||size<36)return ReplaySemanticValidation::Truncated;
 const auto get=[&](u32 at){u32 v;std::memcpy(&v,data+at,4);return v;};
 u16 version;std::memcpy(&version,data+4,2);
 if(get(0)!=0x33343174||version!=1)return ReplaySemanticValidation::BadHeader;
 const u32 compressed=get(0x1c),decoded=get(0x20);
 if(compressed>size-36)return ReplaySemanticValidation::Truncated;
 if(!compressed||compressed>0x4000000||decoded<0xb0||decoded>0x4000000)return ReplaySemanticValidation::BadSize;
 std::vector<u8> first(compressed),second(compressed),output(decoded);u32 written=0;
 if(!th11::resource_crypt(data+36,first.data(),compressed,{0x5c,0xe1,0x400,compressed},false)||
    !th11::resource_crypt(first.data(),second.data(),compressed,{0x7d,0x3a,0x100,compressed},false))return ReplaySemanticValidation::BadPayload;
 auto decoder=std::make_unique<th11::Lzss>();
 if(!decoder->decode(second.data(),compressed,output.data(),decoded,written)||written!=decoded)return ReplaySemanticValidation::BadPayload;
 return validate_replay_decoded_payload(output.data(),decoded);
}
}
