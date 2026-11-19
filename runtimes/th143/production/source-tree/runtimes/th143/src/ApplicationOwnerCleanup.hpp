#pragma once
#include "EclVm.hpp"
namespace th143 {
struct ApplicationOwnerCleanupHost {
 virtual ~ApplicationOwnerCleanupHost()=default;
 virtual bool cleanup_global_read(u32,u32&)=0;
 virtual bool cleanup_global_write(u32,u32)=0;
 virtual bool cleanup_destructor(u32 entry,u32 owner)=0;
 virtual bool cleanup_free(u32 owner)=0;
};
//443c30 reads each global after the preceding destructor/free pair. Each free
//receives the cached owner even if the destructor replaces its global.
bool cleanup_application_owners(ApplicationOwnerCleanupHost&);
}
