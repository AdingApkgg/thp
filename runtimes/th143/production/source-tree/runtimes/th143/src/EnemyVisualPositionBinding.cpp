#include "EnemyVisualPositionBinding.hpp"
#include "EnemyVisualPosition.hpp"
#include "EnemyAnimationCurveScratchDirect.hpp"
#include <map>
namespace th143 {
namespace {struct Binding{std::function<AnmView(u32)> visual;std::function<float()> rate;};std::map<EnemyScripts*,Binding> bindings;}
void bind_enemy_visual_positions(EnemyScripts& s,std::function<AnmView(u32)> v,std::function<float()> r){if(v&&r)bindings[&s]={std::move(v),std::move(r)};else bindings.erase(&s);}
bool position_enemy_visuals(EnemyScripts& scripts,ActorState& state){
 const auto i=bindings.find(&scripts);if(i==bindings.end())return false;auto& host=i->second;AnmView actor{state.fields.data.data()};const bool direct=(actor.get(0x4100)&0x4000000)!=0;
 enemy_animation_stack_entry(scripts);
 for(u32 slot=0;slot<22;++slot){const u32 handle=actor.get(0x124+slot*4);enemy_animation_stack_lookup(scripts,handle,direct);auto target=host.visual(handle);AnmView parent{nullptr};
  if(target.data&&!direct){const i32 index=signed_word(actor.get(0x2a4+slot*4));if(index>=0){if(index>=24)return false;parent=host.visual(actor.get(0x124+u32(index)*4));}}
  if(!position_enemy_animation(actor,slot,target,parent,direct,host.rate()))return false;
 }return true;
}
}
