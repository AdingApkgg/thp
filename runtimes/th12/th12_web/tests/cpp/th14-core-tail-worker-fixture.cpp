// Compare actual deferred core jobs against the synchronous production owner.
#define main legacy_fixture_main
#include "th14-initial-stage-decode-fixture.cpp"
#undef main
#include "../../cpp/game/GameSessionResources.hpp"
#include <emscripten.h>
namespace {
struct Effects:StageResourceEffects {bool core_ready()const override{return false;}} effects;
GameResources source;
GameSessionResources expected, actual;
bool sht(const ShtResource& a,const ShtResource& b){
    if(std::memcmp(&a.header,&b.header,sizeof(ShtHeader))||a.groups.size()!=b.groups.size())return false;
    for(u32 i=0;i<a.groups.size();++i){const auto& x=a.groups[i];const auto& y=b.groups[i];
        if(x.metadata!=y.metadata||x.shots.size()!=y.shots.size())return false;
        if(!x.shots.empty()&&std::memcmp(x.shots.data(),y.shots.data(),x.shots.size()*sizeof(ShotSpec)))return false;
    }return true;
}
}
extern "C" {
EMSCRIPTEN_KEEPALIVE int fixture_reset(){
    actual=GameSessionResources{};actual.effects=&effects;
    if(!actual.load_core(source))return 0;
    for(u32 job:{0u,1u,2u,4u,5u})if(!actual.load_core_job(job))return 0;
    return 1;
}
EMSCRIPTEN_KEEPALIVE int fixture_open(const u8* bytes,u32 size){
    return source.open_archive(bytes,size)&&expected.load_core(source)&&fixture_reset();
}
EMSCRIPTEN_KEEPALIVE int fixture_load(u32 index){return actual.load_core_job(index);}
EMSCRIPTEN_KEEPALIVE int fixture_empty(){
    if(!actual.core.enemy.scripts.empty()||!actual.core.defaults.files.empty())return 0;
    for(const auto& file:actual.core.players)if(!file.scripts.empty())return 0;
    for(const auto& file:actual.core.shots)if(!file.groups.empty())return 0;
    return 1;
}
EMSCRIPTEN_KEEPALIVE int fixture_compare(){
    const auto& a=actual.core;const auto& b=expected.core;
    if(!anm(a.ascii,b.ascii)||!anm(a.bullet,b.bullet)||!anm(a.effect,b.effect)||!anm(a.enemy,b.enemy)
        ||!anm(a.front,b.front)||!anm(a.text,b.text)||!anm(a.title,b.title)||!anm(a.title_variant,b.title_variant)
        ||!ecl(a.defaults,b.defaults))return 0;
    for(u32 i=0;i<player_file_count;++i)if(!anm(a.players[i],b.players[i]))return 0;
    for(u32 i=0;i<shot_file_count;++i)if(!sht(a.shots[i],b.shots[i]))return 0;
    return 1;
}
EMSCRIPTEN_KEEPALIVE const char* fixture_error(){return actual.error.c_str();}
}
