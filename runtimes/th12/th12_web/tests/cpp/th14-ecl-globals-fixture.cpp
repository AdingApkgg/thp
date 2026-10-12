#include "../../cpp/game/EnemyScript.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static EnemyState enemy,boss;static EnemyEnvironment environment;static EnemyCommandEnvironment commands;static EclContext context;
static u32* storage(u32 n){
 if(n<4)return reinterpret_cast<u32*>(enemy.integers+n);
 if(n<8)return reinterpret_cast<u32*>(enemy.floats+n-4);
 if(n<12)return reinterpret_cast<u32*>(enemy.extra_floats+n-8);
 if(n<16){float* p[]={&enemy.absolute.position.x,&enemy.absolute.position.y,&enemy.relative.position.x,&enemy.relative.position.y};return reinterpret_cast<u32*>(p[n-12]);}
 if(n<20)return reinterpret_cast<u32*>(boss.integers+n-16);
 if(n<24)return reinterpret_cast<u32*>(boss.floats+n-20);
 if(n<27)return reinterpret_cast<u32*>(environment.shared_integers+n-24);
 if(n<31)return reinterpret_cast<u32*>(environment.th14_shared_integers+n-27);
 return reinterpret_cast<u32*>(environment.th14_shared_floats+n-31);
}
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(run) i32 run(const u8* code,u32 present){
 enemy={};boss={};environment={};context={};environment.boss=present?&boss:nullptr;
 for(u32 n=0;n<39;++n)*storage(n)=n+11;
 context.instruction=reinterpret_cast<const EclInstruction*>(code);EnemyScriptServices services(enemy,environment,commands);return context.update(0,services);
}
API(value) u32 value(u32 n){return n<39?*storage(n):context.stack.local<u32>(n==39?4:12);}
API(flag_read) i32 flag_read(const u8* code,u32 flags){
 enemy={};environment={};context={};enemy.flags=flags;
 context.instruction=reinterpret_cast<const EclInstruction*>(code);EnemyScriptServices services(enemy,environment,commands);return context.update(0,services);
}
API(random_read) i32 random_read(const u8* code,u32 seed){
 enemy={};environment={};context={};environment.random={u16(seed),0,0};
 context.instruction=reinterpret_cast<const EclInstruction*>(code);EnemyScriptServices services(enemy,environment,commands);return context.update(0,services);
}
API(random_word) u32 random_word(u32 n){return n==0?context.stack.local<u32>(4):n==1?environment.random.seed:environment.random.calls;}
