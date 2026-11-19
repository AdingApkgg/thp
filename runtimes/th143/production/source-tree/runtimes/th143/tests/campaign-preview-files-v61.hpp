#pragma once
#include <map>
#include <iterator>
#include <string>
#include <vector>
// Explicit in-memory filesystem for closed successful preview writes. Browser
// persistence, concurrent partial reads, and OS failure modes remain separate.
struct CampaignPreviewFiles {
 std::map<std::string,std::vector<th143::u8>> files;
 th143::u32 commits=0,probes=0,hits=0,reads=0,last_read_bytes=0;
 bool commit(const std::string& name,const std::vector<std::vector<th143::u8>>& chunks){
  const std::string key=name.rfind("savedata/",0)==0?name:"savedata/"+name;
  auto& bytes=files[key];bytes.clear();for(const auto& chunk:chunks)bytes.insert(bytes.end(),chunk.begin(),chunk.end());++commits;return true;
 }
 bool exists(const std::string& name,bool& found){++probes;found=files.count(name)!=0;if(found)++hits;return true;}
 bool read(const std::string& name,std::vector<th143::u8>& out){auto i=files.find(name);if(i==files.end())return false;out=i->second;++reads;last_read_bytes=out.size();return true;}
}campaign_preview_files;
