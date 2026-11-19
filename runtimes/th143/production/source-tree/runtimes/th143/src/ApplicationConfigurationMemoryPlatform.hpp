#pragma once
#include "ApplicationConfiguration.hpp"
#include <array>
#include <vector>
namespace th143 {
//Private memory-backed file platform. No host CWD or user filesystem mutation.
struct ApplicationConfigurationMemoryPlatform:ApplicationConfigurationHost {
    std::array<u8,20> keyboard{};std::vector<u8> file,read_storage,written;std::vector<u32> events;
    bool live_read=false,last_read_present=false;u32 loads=0; i32 result=0;
    void reset(){keyboard.fill(0);file.clear();read_storage.clear();written.clear();events.clear();live_read=last_read_present=false;loads=0;result=0;}
    void event(std::initializer_list<u32> v){events.insert(events.end(),v);}
    bool load(AnmView app){ApplicationConfigurationBindings b{app,app,{keyboard.data()}};if(!load_application_configuration(b,*this,result))return false;++loads;return result==0;}
    bool zero_configuration(AnmView out,u32 n)override{if(n!=92)return false;event({0x495300,n});std::memset(out.data,0,n);return true;}
    bool configuration_directory(u32 path)override{if(path!=0x5390cd&&path!=0x53a0cd)return false;event({0x48b1da,path});return true;}
    bool read_configuration(u32 name,u32 external,u32& token,u32& bytes)override{if(name!=0x4c86b8||external!=1||live_read)return false;event({0x402e00,name,external});last_read_present=!file.empty();bytes=file.size();read_storage=file;/* Original444340 copies92 before validating reported length. Keep the actual byte count while furnishing safe backing for that copy. */if(last_read_present&&read_storage.size()<92)read_storage.resize(92,0);live_read=last_read_present;token=last_read_present?0x6e500000:0;return true;}
    bool configuration_region(u32 token,u32 n,AnmView& out)override{if(!live_read||token!=0x6e500000||n>read_storage.size())return false;out={read_storage.data()};return true;}
    bool free_configuration(u32 token)override{if(!live_read||token!=0x6e500000)return false;event({0x48a7bc,token});live_read=false;std::vector<u8>().swap(read_storage);return true;}
    bool log_configuration(bool error,u32 message,u32 argument)override{event({error?0x4034d0u:0x403400u,0x4e20a8,message,argument});return true;}
    bool write_configuration(u32 name,AnmView in,u32 n,u32& result)override{if(name!=0x4c86b8||n!=92)return false;event({0x403040,name,n});written.assign(in.data,in.data+n);file=written;result=0;return true;}
};
}
