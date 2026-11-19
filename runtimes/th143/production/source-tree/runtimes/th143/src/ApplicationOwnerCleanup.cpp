#include "ApplicationOwnerCleanup.hpp"
namespace th143 {
bool cleanup_application_owners(ApplicationOwnerCleanupHost& h){
 if(!h.cleanup_global_write(0x53b150,0))return false;
 constexpr u32 owners[][2]={{0x4e6a5c,0x432a30},{0x4e6bb4,0x45f370},{0x4e6b70,0x443280},{0x4e6a44,0x41bda0},{0x4e6b98,0x4545d0},{0x4e6a40,0x41ad40},{0x4e6b60,0x4346c0},{0x4e6bc8,0x468510},{0x4e6b68,0x436aa0},{0x4e6b80,0x446d00},{0x4e6bc4,0x467a30}};
 for(const auto& row:owners){u32 owner;if(!h.cleanup_global_read(row[0],owner))return false;if(owner&&(!h.cleanup_destructor(row[1],owner)||!h.cleanup_free(owner)))return false;}return true;
}
}
