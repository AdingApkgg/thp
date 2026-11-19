#pragma once
#include "AnmState.hpp"
namespace th143 {
struct ApplicationConfigurationBindings {
    AnmView application; //caller ECX, 0xa34 bytes
    AnmView global_application; //4e47d0, config is +1d4..+230
    AnmView keyboard; //4e1c04, 20 bytes
};
struct ApplicationConfigurationHost {
    virtual ~ApplicationConfigurationHost()=default;
    virtual bool zero_configuration(AnmView,u32 bytes)=0;
    virtual bool configuration_directory(u32 path)=0;
    virtual bool read_configuration(u32 name,u32 external,u32& token,u32& bytes)=0;
    virtual bool configuration_region(u32 token,u32 bytes,AnmView&)=0;
    virtual bool free_configuration(u32 token)=0;
    virtual bool log_configuration(bool error,u32 message,u32 argument)=0;
    virtual bool write_configuration(u32 name,AnmView,u32 bytes,u32& result)=0;
};
//444340, one unused caller ABI word. Config and caller ECX may alias or differ.
//A nonnull read must provide92 mapped bytes even when reported size is invalid:
//the original copies before validating size. Short unmapped files are excluded.
bool load_application_configuration(ApplicationConfigurationBindings&,ApplicationConfigurationHost&,i32& result);
}
