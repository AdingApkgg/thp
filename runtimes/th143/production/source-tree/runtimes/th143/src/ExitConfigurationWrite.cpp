#include "ExitConfigurationWrite.hpp"
#include <array>
namespace th143 {
bool write_exit_configuration(AnmView app,const u8* prefix,u32 available,ExitConfigurationWriteHost& h){
 if(!app.data||!prefix)return false;u32 n=0;while(n<available&&n<250&&prefix[n])++n;if(n==available||n==250)return false;
 std::array<u8,260> path{};std::memcpy(path.data(),prefix,n);constexpr u8 name[]="th143.cfg";std::memcpy(path.data()+n,name,sizeof name);u32 ignored;return h.exit_configuration_write(path.data(),n+sizeof name,app.sub(0x1d4),92,ignored);
}
}
