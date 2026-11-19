#pragma once
#include "AnmState.hpp"
namespace th143 {
struct ExitConfigurationWriteHost {
 virtual ~ExitConfigurationWriteHost()=default;
 //Raw NUL-terminated path, unmodified live92-byte APP1d4..22f configuration.
 virtual bool exit_configuration_write(const u8* path,u32 path_bytes,AnmView,u32 bytes,u32& result)=0;
};
//UnchangedWinMain46e583..46e5e6; subsequent timeEndPeriod/diagnostics are separate.
//The mapped native prefix must contain NUL within250bytes (MAX_PATH domain).
bool write_exit_configuration(AnmView application,const u8* prefix,u32 available,ExitConfigurationWriteHost&);
}
