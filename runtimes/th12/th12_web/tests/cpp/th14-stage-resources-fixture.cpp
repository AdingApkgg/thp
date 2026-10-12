#include "../../cpp/game/GameResources.hpp"
#include "../../cpp/game/StageFiles.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static GameResources source;
static StageResources stage;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(open_archive) int open_archive(const u8* p,u32 n){return source.open_archive(p,n);}
API(load_stage) int load_stage(u32 n){stage={};return source.load_stage(n,stage);}
API(error) const char* error(){return source.error().c_str();}
API(last_file) const char* last_file(){return last_resource.c_str();}
API(background_name) const char* background_name(){return stage.scene.animation_name.c_str();}
API(dialogue_index) u32 dialogue_index(u32 c,u32 p){return stage_dialogue_index(c,p);}
API(message_size) u32 message_size(u32 i){return stage.messages.at(i).size();}
API(message_data) const u8* message_data(u32 i){return stage.messages.at(i).data();}
API(ecl_count) u32 ecl_count(){return stage.timeline.definitions.size();}
API(ecl_animation_name) const char* ecl_animation_name(u32 i){return stage.ecl_animation_names.at(i).c_str();}
API(ecl_animation_scripts) u32 ecl_animation_scripts(u32 i){return stage.ecl_animations.at(i).scripts.size();}
API(provider_animation_name) const char* provider_animation_name(u32 i){return source.animation_name(i).c_str();}
