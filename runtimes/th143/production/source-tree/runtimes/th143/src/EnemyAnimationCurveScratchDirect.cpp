#include "EnemyAnimationCurveScratchDirect.hpp"
#include <map>
#include "EnemyCurveCallStack.hpp"
namespace th143 {
namespace {struct Binding {std::array<u32,2>* words;u32 ebx;u32* curve_z=nullptr;};std::map<EnemyScripts*,Binding> bindings;}
void bind_enemy_animation_scratch(EnemyScripts& s,std::array<u32,2>* words,u32 ebx){if(words)bindings[&s]={words,ebx};else bindings.erase(&s);}
void bind_enemy_curve_scratch(EnemyScripts& s,u32* p){auto i=bindings.find(&s);if(i!=bindings.end())i->second.curve_z=p;}
// Actual41ecd0 keeps its owner in EBX through4211e0;421319 saves that register.
void enemy_animation_stack_entry(EnemyScripts& s){auto p=bindings.find(&s);if(p!=bindings.end())(*p->second.words)[0]=p->second.ebx;}
// Actual4213b2 pushes the current22-slot animation lookup handle into the
// shared word subsequently read as43ac60's second untouched Z component.
void enemy_animation_stack_lookup(EnemyScripts& s,u32 handle){enemy_animation_stack_lookup(s,handle,false);}
void enemy_animation_stack_lookup(EnemyScripts& s,u32 handle,bool direct){auto p=bindings.find(&s);if(p!=bindings.end()){(*p->second.words)[1]=handle;
 // Actual4213be/4214d8 CALL484280 write their own return PCs into this word.
 // Only this executed lookup path updates it; contact subsequently mutates it.
 if(p->second.curve_z)enemy_curve_stack_lookup(*p->second.curve_z,direct);
 }}
}
