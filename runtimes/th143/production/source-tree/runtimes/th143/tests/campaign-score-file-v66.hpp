#pragma once
#include <vector>
// The integration uses successful sequential file operations. Native partial
// write/error/concurrent-reader behavior remains a separate OS boundary.
struct CampaignScoreFile {
 std::vector<th143::u8> pending,committed;th143::u32 handle=0,generation=0;
 bool open(th143::u32 value){if(handle||value!=0x1234)return false;handle=value;pending.clear();return true;}
 bool write(th143::u32 value,const th143::u8* p,th143::u32 n){if(!handle||value!=handle)return false;pending.insert(pending.end(),p,p+n);return true;}
 bool close(th143::u32 value){if(!handle||value!=handle)return false;committed=pending;pending.clear();handle=0;++generation;return true;}
}campaign_score_file;
