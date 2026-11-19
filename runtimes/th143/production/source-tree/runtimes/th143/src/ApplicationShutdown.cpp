#include "ApplicationShutdown.hpp"
namespace th143 {
bool shutdown_application(u32 application,ApplicationShutdownHost& h){
 u32 value,result=0;auto read=[&](u32 p,u32& v){return h.shutdown_read(p,v);};auto write=[&](u32 p,u32 v){return h.shutdown_write(p,v);};auto call=[&](u32 entry,u32 owner,std::initializer_list<u32> args){return h.shutdown_call(entry,owner,args,result);};
 if(!read(0x4e6b9c,value))return false;if(value&&!call(0x4562e0,0,{}))return false;
 do{if(!call(0x472df0,0,{}))return false;}while(result!=0);
 if(!write(0x540978,2)||!call(0x403e90,0x4e515c,{}))return false;
 if(!read(0x4e51e4,value))return false;if(value&&(!call(0x48a7bc,0,{value})||!write(0x4e51e4,0)))return false;
 if(!call(0x443c30,0,{})||!read(0x4e6a50,value))return false;if(value&&!call(0x42bd30,value,{value}))return false;
 u32 pool;if(!read(0x538de8,pool)||!read(pool+0xbc81ac,value))return false;if(value&&(!call(8,value,{value})||!write(pool+0xbc81ac,0)))return false;
 if(!call(0x4737b0,0x53b1e0,{4,0,0x4c61a4})||!call(0x46ad40,0,{}))return false;
 constexpr u32 fonts[]={0x540df8,0x540e00,0x540e08,0x540e10,0x540e18,0x540e04,0x540e0c,0x540e14,0x540e1c};for(const u32 p:fonts){if(!read(p,value)||!call(0x4b8038,0,{value}))return false;}
 for(const u32 offset:{0x20u,0x24u}){if(!read(application+offset,value))return false;if(value){if(!call(0x20,value,{value})||!read(application+offset,value))return false;if(value&&(!call(8,value,{value})||!write(application+offset,0)))return false;}}
 if(!read(application+0xc,value))return false;if(value&&(!call(8,value,{value})||!write(application+0xc,0)))return false;
 if(!call(0x468ba0,0x538f50,{}))return false;
 u32 owner;if(!read(0x4e498c,owner))return false;
 for(u32 i=0;i<4;++i){if(owner){if(!read(owner+0x5b4,value))return false;if(value&&!call(0x48a7bc,0,{value}))return false;if(!write(owner+0x5b4,0)||!call(0x48a6e8,0,{owner}))return false;}u32 next=0;if(i<3&&!read(0x4e4990+i*4,next))return false;if(!write(0x4e498c+i*4,0))return false;owner=next;}
 return true;
}
}
