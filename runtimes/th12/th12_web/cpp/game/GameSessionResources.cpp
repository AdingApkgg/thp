#include "GameSessionResources.hpp"
#include "ShotFiles.hpp"
#if PORT_TITLE == 14
#include "AnmManager.hpp"
#endif

namespace th11 {

namespace {
bool core_error(std::string& error,const char* message) { error=message; return false; }
}

bool GameSessionResources::load_core(GameResources& source) {
    if(core_source==&source)return true;
    error.clear(); stage_number=0;
    // The resource carries the reason it failed, which for an ANM is the opcode of the title's numbering the
    // measured table has no row for. An empty reason leaves the message exactly as it was.
    auto anm=[&](const char* message,const char* file,AnmResource& output){
        if(source.open_anm(file,output))return true;
        return core_error(error,(std::string(message)+output.detail).c_str());
    };
#if PORT_TITLE == 14
    core_deferred=effects&&!effects->core_ready();core_loaded_jobs=0;
    if(core_deferred){
        // Only the original loading screen's resources are needed now. Each
        // remaining decode is a real frame job before its upload/templates.
        core={};
        if(!anm("ascii ANM","ascii.anm",core.ascii)||!anm("text ANM","text.anm",core.text))return false;
        if(animation_manager){auto& a=*animation_manager;a.fallback_sprites=&core.ascii;
            if(!a.prepare_resource(core.text,0)||!a.prepare_resource(core.ascii,2))return core_error(error,a.last_error_text().c_str());}
        core_source=&source;return true;
    }
#endif
    if(!anm("ascii ANM","ascii.anm",core.ascii))return false;
    if(!anm("bullet ANM","bullet.anm",core.bullet))return false;
    if(!anm("enemy ANM","enemy.anm",core.enemy))return false;
#if PORT_TITLE == 14 || PORT_TITLE == 16
    if(!anm("effect ANM","effect.anm",core.effect))return false;
#endif
    if(!anm("front ANM","front.anm",core.front))return false;
    if(!anm("text ANM","text.anm",core.text))return false;
    if(!anm("title ANM","title.anm",core.title))return false;
    if(!anm("title variant ANM","title_v.anm",core.title_variant))return false;
    for(u32 i=0;i<player_file_count;++i)
        if(!anm("player ANM",player_file_name(i),core.players[i]))return false;
    // The name goes into the message: a wrong cipher, a wrong table row and a file the title does not ship all
    // arrive here, and the name is what tells them apart.
    for(u32 i=0;i<shot_file_count;++i)if(!source.open_sht(shot_file_name(i),core.shots[i]))return core_error(error,(std::string("SHT resource ")+shot_file_name(i)+": "+source.error()).c_str());
#if PORT_TITLE == 16
    // Retail 492cb8 / 492cdc, in selection order rather than filename order.
    constexpr const char* season_anm[]={"pl00sub.anm","pl02sub.anm","pl03sub.anm","pl01sub.anm","pl04sub.anm"};
    constexpr const char* season_sht[]={"pl00sub.sht","pl02sub.sht","pl03sub.sht","pl01sub.sht","pl04sub.sht"};
    for(u32 i=0;i<5;++i){
        if(!anm("season player ANM",season_anm[i],core.season_players[i]))return false;
        if(!source.open_sht(season_sht[i],core.season_shots[i]))return core_error(error,(std::string("season SHT ")+season_sht[i]+": "+source.error()).c_str());
    }
#endif
    if(!source.load_ecl("default.ecl",core.defaults))return core_error(error,"default ECL");
#if PORT_TITLE == 14
    if(animation_manager){auto& a=*animation_manager;a.fallback_sprites=&core.ascii;
        if(!a.prepare_resource(core.text,0)||!a.prepare_resource(core.ascii,2))return core_error(error,a.last_error_text().c_str());}
    if((!effects||effects->core_ready())&&!prepare_core())return false;
#endif
    core_source=&source;return true;
}
#if PORT_TITLE == 14
bool GameSessionResources::load_core_job(u32 index){
    if(index>=9)return core_error(error,"TH14 core resource job outside 0..8");
    if(!core_deferred||(core_loaded_jobs&(1u<<index)))return true;
    if(!core_source)return core_error(error,"TH14 core resource source missing");
    AnmResource* files[]={&core.effect,&core.bullet,&core.enemy,&core.front,&core.title,&core.title_variant,&core.players[0],&core.players[1],&core.players[2]};
    const char* names[]={"effect.anm","bullet.anm","enemy.anm","front.anm","title.anm","title_v.anm","pl00.anm","pl01.anm","pl02.anm"};
    if(!core_source->open_anm(names[index],*files[index]))return core_error(error,(std::string(names[index])+": "+files[index]->detail).c_str());
    if(index>=6){const u32 character=index-6;
        for(u32 loadout=0;loadout<shot_loadout_count;++loadout){const u32 slot=shot_file_slot(character,loadout);
            if(!core_source->open_sht(shot_file_name(slot),core.shots[slot]))return core_error(error,(std::string("SHT resource ")+shot_file_name(slot)+": "+core_source->error()).c_str());}
    }
    if(index==8&&!core_source->load_ecl("default.ecl",core.defaults))return core_error(error,"default ECL");
    core_loaded_jobs|=u16(1u<<index);return true;
}
bool GameSessionResources::prepare_core(){
    if(core_deferred){for(u32 index=0;index<9;++index)if(!load_core_job(index))return false;core_deferred=false;}
    if(animation_manager){
        auto& a=*animation_manager;a.fallback_sprites=&core.ascii;
        if(!a.prepare_resource(core.text,0)||!a.prepare_resource(core.ascii,2)||!a.prepare_resource(core.front,5)
           ||!a.prepare_resource(core.bullet,7)||!a.prepare_resource(core.effect,8)||!a.prepare_resource(core.enemy,9)
           ||!a.prepare_resource(core.title,24)||!a.prepare_resource(core.title_variant,25))return core_error(error,a.last_error_text().c_str());
        for(u32 i=0;i<player_file_count;++i)if(!a.prepare_resource(core.players[i],7))return core_error(error,a.last_error_text().c_str());
    }
    return true;
}
#endif

bool GameSessionResources::load_stage(GameResources& source,u32 number) {
    auto next=std::make_unique<StageResources>();
    if(!source.load_stage(number,*next)){error="stage resource "+last_resource+": "+source.error();return false;}
    if(effects&&!effects->prepare(*next)){effects->release(*next);error="stage graphics preparation: "+effects->last_error();return false;}
    retire_previous();previous_stage=std::move(stage);stage=std::move(next);
    stage_number=number;error.clear();
#if PORT_TITLE == 14
    if((!effects||effects->stage_ready())&&!prepare_stage())return false;
#endif
    return true;
}
#if PORT_TITLE == 14
bool GameSessionResources::prepare_stage(){
    if(animation_manager){auto& a=*animation_manager;
        if(!a.prepare_resource(stage->background,u16((stage_number&1)+3))||!a.prepare_resource(stage->logo,6)||!a.prepare_resource(stage->enemies,9)){error=a.last_error_text();return false;}
        for(u32 i=0;i<stage->ecl_animations.size();++i)if(!a.prepare_resource(stage->ecl_animations[i],u16(10+i))){error=a.last_error_text();return false;}
    }
    return true;
}
#endif
void GameSessionResources::retire_previous(){if(previous_stage&&effects)effects->release(*previous_stage);previous_stage.reset();}

}
