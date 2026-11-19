#include "ResultsMenu.hpp"
#include "CheatAnimation.hpp"
#include "AnmSignal.hpp"
namespace th143 {
bool open_results_menu(PauseMenu& menu,SaveData& save,GameOverGlobals& g,AnmWorld& world,AnmOverlay& overlay,u32 primary,u32 scene,u32 used,GameOverHost& host){
 if(!game_statistics_time(save,g,host))return false;
 if(g.root_mode==1){g.application_state=(g.config&0x2000)?2:4;return true;}
 if(scene>=SaveData::scene_count)return false;
 auto m=menu.view();menu.state(3);if(!(m.get(0x34)&1)){m.put(0x30,world.global_rate_token());m.put(0x34,m.get(0x34)|1u);}m.put(0x24,0xffffffff);m.put(0x28,0);m.put(0x2c,0);m.put(0x10c,0);g.root_flags|=0x10;
 if(!host.pause_audio()||!host.sound_and_flush(14))return false;
 m.put(0x91bc,m.get(0x91bc)|1);u32 handle;world.rate=g.rate;
 if(!overlay.create(world,g.text_resource,58,nullptr,0,-1,4,handle))return false;m.put(0x1ec,handle);m.put(0x91c0,g.front_resource);m.put(0x1f4,0);m.put(0x2d8,word(g.rate));m.put(0x200,g.presentation);g.rate=world.rate=1;g.presentation=1;
 const u8 unlocked=save.data[0xefac];const i32 script=unlocked==0?231:unlocked==1?232:230;
 if(!overlay.create(world,g.front_resource,script,nullptr,0,-1,4,handle))return false;m.put(0x91b8,handle);
 auto signal_child=[&](i32 child_script,i32 signal){auto parent=world.find(m.get(0x91b8));if(!parent.data){m.put(0x91b8,0);return signal_animation(world,0,signal,true);}parent=world.find(m.get(0x91b8));if(!parent.data)m.put(0x91b8,0);auto child=find_animation_child(world,parent,child_script);return signal_animation(world,child.data?child.get(0x540):0,signal,true);};
 for(u32 i=0;i<10;++i){const i32 selected=primary==i||!used?42:signed_word(save.view().get(scene*SaveData::scene_size+0x18+i*4))<=0?41:40;
  if(!signal_child(i32(250+i),selected+7))return false;
  if(i<6&&!signal_child(i32(244+i),selected+7))return false;
  if(i<3&&!signal_child(i32(241+i),selected+7))return false;
 }
 return true;
}
}
