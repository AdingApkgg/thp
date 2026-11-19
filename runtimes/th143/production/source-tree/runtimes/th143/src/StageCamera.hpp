#pragma once
#include "AnmState.hpp"
#include <array>

namespace th143 {
struct StageCamera {
    static constexpr u32 bytes=0x12c;
    std::array<u8,bytes> data{};
    AnmView view(){return {data.data()};}
};
struct StageCameraServices {
    virtual ~StageCameraServices()=default;
    virtual bool has_animation_manager() const=0;
    virtual bool flush_stage_camera_batch()=0;
    virtual bool set_stage_camera_transform(u32 kind,const u8* matrix)=0;
    virtual bool set_stage_camera_origin(u32 x,u32 y)=0;
};
// 4453c0: CPU view/projection construction, two device transform submissions,
// normalized sideways vector, then animation-manager origin publication.
bool prepare_stage_camera(StageCamera&,StageCameraServices&);
}
