#include "../../cpp/sdl/FontDevice.hpp"
#include "../../cpp/game/GameSessionResources.hpp"
#include "../../cpp/game/AnmRenderer.hpp"
#include <emscripten.h>
#include <memory>
using namespace th11;
namespace {
GameResources source;std::vector<u8> archive;GameSessionResources resources;AnmManager manager;EnemyAnimations animations(manager);
std::unique_ptr<sdl::GraphicsDevice> graphics;std::unique_ptr<sdl::FontDevice> font;std::unique_ptr<AnmRenderer> renderer;std::unique_ptr<Dialogue> dialogue;
std::string diagnostic;u32 writes,draws,panels,waiting,reads;std::vector<DialogueText> queued;u8 preview[640*480*4];
struct ResourceEffects:StageResourceEffects {
 bool prepare_animation(AnmResource& r)override{return graphics->preload(r);}
 bool prepare_manual_image(AnmResource& r,u32 i,const u8* p,u32 n)override{return graphics->manual_image(r,i,p,n);}
 bool prepare(StageResources& s)override{for(auto* r:{&s.background,&s.logo,&s.enemies})if(!prepare_animation(*r))return false;for(u32 i=0;i<s.ecl_animations.size();++i)if(!s.ecl_animation_names[i].empty()&&!prepare_animation(s.ecl_animations[i]))return false;return true;}
 void release_animation(AnmResource& r)override{renderer->flush();renderer->invalidate();graphics->unload(r);}
 void release(StageResources& s)override{for(auto* r:{&s.background,&s.logo,&s.enemies})release_animation(*r);for(auto& r:s.ecl_animations)release_animation(r);}
 const std::string& last_error()const override{return graphics->error;}
} resource_effects;
struct Effects:DialogueEffects {
 bool dialogue_text(const DialogueText& r)override{++writes;auto* vm=manager.find(r.animation);if(!vm){diagnostic="missing text animation";return false;}if(font->text(*vm,r))return true;if(font->waiting){queued.push_back(r);++waiting;return true;}diagnostic=font->error;return false;}
 bool dialogue_sound(i32)override{return true;}bool dialogue_music()override{return true;}bool dialogue_fade(float)override{return true;}bool dialogue_stage_complete()override{return true;}
} effects;
}
extern "C" {
EMSCRIPTEN_KEEPALIVE int display_open(const u8* p,u32 n){
 graphics=std::make_unique<sdl::GraphicsDevice>();if(!graphics->initialize()){diagnostic=graphics->error;return 0;}renderer=std::make_unique<AnmRenderer>(*graphics);renderer->set_viewport({0,0,640,480,0,1});font=std::make_unique<sdl::FontDevice>(*graphics);FontBitmapTh14 bitmap;if(!font->initialize(&bitmap)){diagnostic=font->error;return 0;}
 archive.assign(p,p+n);resources.animation_manager=&manager;resources.effects=&resource_effects;if(!source.open_archive(archive.data(),u32(archive.size()))||!resources.load_core(source)){diagnostic=resources.error.empty()?source.error():resources.error;return 0;}for(auto* r:{&resources.core.ascii,&resources.core.text,&resources.core.front,&resources.core.bullet,&resources.core.effect,&resources.core.enemy,&resources.core.title,&resources.core.title_variant,&resources.core.players[0],&resources.core.players[1],&resources.core.players[2]})if(!resource_effects.prepare_animation(*r)){diagnostic=graphics->error;return 0;}return 1;
}
EMSCRIPTEN_KEEPALIVE int display_stage(u32 stage){if(dialogue)dialogue->clear();dialogue.reset();manager.clear();queued.clear();if(!resources.load_stage(source,stage)){diagnostic=resources.error;return 0;}for(u32 i=0;i<4;++i)animations.resources[2+i]={resources.stage->ecl_animation_names[i].empty()?nullptr:&resources.stage->ecl_animations[i],u16(10+i)};return 1;}
EMSCRIPTEN_KEEPALIVE u32 display_entries(u32 selection){const auto& msg=resources.stage->messages[selection];u32 n=0;if(msg.size()>=4)std::memcpy(&n,msg.data(),4);return n;}
EMSCRIPTEN_KEEPALIVE int display_run(u32 selection,i32 id){
 if(dialogue)dialogue->clear();manager.clear();queued.clear();diagnostic.clear();writes=draws=panels=waiting=reads=0;std::memset(preview,0,sizeof preview);u32 last_panel=0,last_writes=font->writes;
 dialogue=std::make_unique<Dialogue>(manager,resources.core.text,resources.core.players[selection/2],resources.core.front,resources.stage->enemies,resources.stage->logo,effects);dialogue->character=selection/2;dialogue->stage=resources.stage_number;dialogue->th14_animations=&animations;
 if(!dialogue->begin(resources.stage->messages[selection],id)){diagnostic=dialogue->error;return -1;}
 for(u32 frame=0;frame<20000;++frame){const auto result=dialogue->update(0,frame%60==0?0x80001:0);if(result<0){if(diagnostic.empty())diagnostic=dialogue->error;return -2;}
  if(dialogue->th14_text_background!=last_panel){if(dialogue->th14_text_background)++panels;last_panel=dialogue->th14_text_background;}
  if(!manager.update(false)||!manager.update(true)){diagnostic=manager.last_error_text();return -3;}
  for(auto i=queued.begin();i!=queued.end();){auto* vm=manager.find(i->animation);if(!vm){diagnostic="queued text animation retired";return -4;}if(font->text(*vm,*i))i=queued.erase(i);else if(font->waiting)++i;else{diagnostic=font->error;return -5;}}
  renderer->invalidate();graphics->backend.state.target=sdl::GraphicsDevice::screen;renderer->set_viewport({0,0,640,480,0,1});graphics->clear(0xff42678b);for(u32 layer=0;layer<36;++layer){const auto drawn=renderer->draw_layer(manager.layer_first(layer));if(drawn<0){diagnostic="dialogue ANM draw failure";return -6;}draws+=u32(drawn);}renderer->flush();
  if(result!=1&&dialogue->th14_text_background&&(frame%30==0||font->writes!=last_writes)){graphics->backend.read(sdl::GraphicsDevice::screen);++reads;auto* image=graphics->pixels(sdl::GraphicsDevice::screen);if(!image){diagnostic="missing GPU target";return -7;}for(u32 y=0;y<480;++y)std::memcpy(preview+y*640*4,image->pixels.data()+y*image->pitch,640*4);last_writes=font->writes;}
  if(result==1){if(!queued.empty()){diagnostic="pending text at dialogue completion";return -8;}return i32(frame+1);}
 }diagnostic="dialogue exceeds20000 frames";return -9;
}
EMSCRIPTEN_KEEPALIVE u32 display_value(u32 n){return n==0?writes:n==1?panels:n==2?draws:n==3?waiting:n==5?reads:font->writes;}
EMSCRIPTEN_KEEPALIVE const u8* display_pixels(){return preview;}
EMSCRIPTEN_KEEPALIVE const char* display_error(){return diagnostic.c_str();}
}
