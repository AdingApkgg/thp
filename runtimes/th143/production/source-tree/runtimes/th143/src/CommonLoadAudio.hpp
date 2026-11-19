#pragma once
#include "CommonLoad.hpp"
namespace th143 {
struct CommonLoadAudioServices {
    virtual ~CommonLoadAudioServices()=default;
    virtual bool reload_common_audio(AnmView audio,u32& result)=0;
    virtual bool initialize_common_archive(AnmView audio,u32& result)=0;
};
//4430b0 active-audio fork. Native config flag10 selects cache-path copying;
//when it is clear, the archive initializer is invoked and its result ignored.
bool load_common_with_audio(CommonLoadBindings&,CommonLoadHost&,u8 flags,
                            CommonLoadAudioServices&,i32& result);
}
