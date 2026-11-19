#pragma once
#include "AnmState.hpp"
namespace th143 {
struct NoticeWorkerHost {
 virtual ~NoticeWorkerHost()=default;
 virtual bool notice_resource(u32 slot,const char* name,u32& token)=0;
 virtual bool notice_read_file(const char* name,u32& bytes,u32& token)=0;
 virtual bool notice_resource_error(u32& result)=0;
};
// Actual 446b00/446b60/446bb0 bodies. Resource/file/error calls are host services.
bool run_notice_worker(u32 entry,AnmView notice,AnmView worker,AnmView update,AnmView draw,NoticeWorkerHost&,u32& result);
}
