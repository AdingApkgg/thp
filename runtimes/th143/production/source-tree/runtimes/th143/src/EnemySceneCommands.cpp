#include "EnemySceneCommands.hpp"
#include <map>
namespace th143 {
namespace {
std::map<EnemyScripts*,EnemySceneCommandService*> services;
struct Host:VmHost {
 EnemyScripts& scripts;explicit Host(EnemyScripts& s):scripts(s){}
 u8* reference(i32 id,bool f)override{auto p=services.find(&scripts);return p==services.end()?nullptr:p->second->scene_reference(scripts,id,f);}
 bool integer(i32 id,i32& v)override{if(auto* p=reference(id,false)){std::memcpy(&v,p,4);return true;}return scripts.integer(id,v);}
 bool floating(i32 id,float& v)override{if(auto* p=reference(id,true)){std::memcpy(&v,p,4);return true;}return scripts.floating(id,v);}
 Instruction* find_subroutine(const char* name)override{return scripts.find_subroutine(name);}
 i32 command(Vm& vm)override{return scripts.command(vm);}
};
std::map<EnemyScripts*,std::unique_ptr<Host>> hosts;
}
VmHost& enemy_scene_vm_host(EnemyScripts& s){auto& p=hosts[&s];if(!p)p=std::make_unique<Host>(s);return *p;}
void bind_enemy_scene_commands(EnemyScripts& s,EnemySceneCommandService* p){if(p)services[&s]=p;else services.erase(&s);}
i32 dispatch_enemy_scene_command(EnemyScripts& s,Vm& vm){auto p=services.find(&s);return p==services.end()?-2:p->second->scene_command(s,vm);}
}
