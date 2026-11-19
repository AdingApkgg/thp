#pragma once
#include "AnmState.hpp"
namespace th143 {
// Device boundary for the original DrawPrimitiveUP calls. Vertex payloads are
// built or owned by the portable runtime; the device never supplies geometry.
struct AnmPrimitiveDevice {
    virtual ~AnmPrimitiveDevice()=default;
    virtual bool primitive_upload(u32 type,u32 count,u32 stride,const u8*,u32 bytes)=0;
};
}
