// Compare actual decoded resources from the synchronous and staged APIs.
#include "../../cpp/game/GameResources.hpp"
#include <cstdio>
#include <cstring>
#include <tuple>
using namespace th11;

namespace {
bool anm(const AnmResource& a,const AnmResource& b){
    if(a.textures.size()!=b.textures.size()||a.sprites.size()!=b.sprites.size()||a.scripts.size()!=b.scripts.size())return false;
    for(u32 i=0;i<a.textures.size();++i){const auto& x=a.textures[i];const auto& y=b.textures[i];
        if(std::tie(x.name,x.kind,x.width,x.height,x.format,x.pixel_width,x.pixel_height,x.pixel_format,x.source_x,x.source_y,x.priority,x.half_resolution,x.first_script,x.script_count)!=
           std::tie(y.name,y.kind,y.width,y.height,y.format,y.pixel_width,y.pixel_height,y.pixel_format,y.source_x,y.source_y,y.priority,y.half_resolution,y.first_script,y.script_count)||x.pixels!=y.pixels)return false;
    }
    static_assert(sizeof(AnmSprite)==40);
    if(!a.sprites.empty()&&std::memcmp(a.sprites.data(),b.sprites.data(),a.sprites.size()*sizeof(AnmSprite)))return false;
    for(u32 i=0;i<a.scripts.size();++i){const auto& x=a.scripts[i];const auto& y=b.scripts[i];
        if(std::tie(x.source_id,x.file_offset,x.load_hash)!=std::tie(y.source_id,y.file_offset,y.load_hash)||x.bytes!=y.bytes)return false;}
    return true;
}
bool ecl(const EclProgram& a,const EclProgram& b){
    if(a.files.size()!=b.files.size()||a.definitions.size()!=b.definitions.size())return false;
    for(u32 i=0;i<a.files.size();++i){const auto& x=*a.files[i];const auto& y=*b.files[i];
        if(x.bytes!=y.bytes||x.animations!=y.animations||x.includes!=y.includes||x.subroutines.size()!=y.subroutines.size())return false;
        for(u32 j=0;j<x.subroutines.size();++j)if(std::tie(x.subroutines[j].name,x.subroutines[j].offset,x.subroutines[j].size)!=std::tie(y.subroutines[j].name,y.subroutines[j].offset,y.subroutines[j].size))return false;
    }
    for(u32 i=0;i<a.definitions.size();++i){
        const auto& x=a.definitions[i];const auto& y=b.definitions[i];if(x.index!=y.index)return false;
        u32 nx=0,ny=0;while(nx<a.files.size()&&a.files[nx].get()!=x.file)++nx;while(ny<b.files.size()&&b.files[ny].get()!=y.file)++ny;
        if(nx!=ny||nx==a.files.size())return false;
    }
    return true;
}
bool scene(const StageResource& a,const StageResource& b){
    if(a.animation_name!=b.animation_name||a.animation_count!=b.animation_count||a.objects.size()!=b.objects.size()||a.instances.size()!=b.instances.size()||a.instructions.size()!=b.instructions.size())return false;
    for(u32 i=0;i<a.objects.size();++i){const auto& x=a.objects[i];const auto& y=b.objects[i];
        if(std::tie(x.id,x.layer,x.flags)!=std::tie(y.id,y.layer,y.flags)||std::memcmp(&x.position,&y.position,sizeof(Vec3))||std::memcmp(&x.size,&y.size,sizeof(Vec3))||x.primitives.size()!=y.primitives.size())return false;
        static_assert(sizeof(StagePrimitive)==28);
        if(!x.primitives.empty()&&std::memcmp(x.primitives.data(),y.primitives.data(),x.primitives.size()*sizeof(StagePrimitive)))return false;
    }
    static_assert(sizeof(StageInstance)==16);
    if(!a.instances.empty()&&std::memcmp(a.instances.data(),b.instances.data(),a.instances.size()*sizeof(StageInstance)))return false;
    for(u32 i=0;i<a.instructions.size();++i){const auto& x=a.instructions[i];const auto& y=b.instructions[i];
        if(std::tie(x.time,x.opcode,x.length,x.offset)!=std::tie(y.time,y.opcode,y.length,y.offset)||x.arguments!=y.arguments)return false;}
    return true;
}
}

int main(int argc,char** argv){
    if(argc!=2)return 2;
    auto* input=std::fopen(argv[1],"rb");if(!input)return 3;
    std::fseek(input,0,SEEK_END);const long length=std::ftell(input);std::rewind(input);
    if(length<=0||length>128*1024*1024){std::fclose(input);return 4;}
    std::vector<u8> bytes(static_cast<u32>(length));const auto count=std::fread(bytes.data(),1,bytes.size(),input);std::fclose(input);
    if(count!=bytes.size())return 5;
    // Archive keeps a borrowed pointer into this buffer for subsequent reads.
    GameResources source;if(!source.open_archive(bytes.data(),u32(bytes.size())))return 6;
    u32 passed=0;
    for(u32 stage=1;stage<=7;++stage)for(u32 selection=0;selection<6;++selection){
        StageResources legacy,deferred;
        const char* phase="legacy";bool loaded=source.load_stage(stage,legacy);
        if(loaded){phase="scene";loaded=source.load_stage_scene(stage,deferred);}
        if(loaded){phase="hud";loaded=source.load_stage_hud(stage,deferred,selection);}
        if(loaded){phase="timeline-plan";loaded=source.load_stage_timeline_plan(stage,deferred);}
        for(u32 slot=0;loaded&&slot<deferred.ecl_animations.size();++slot){phase="animation";loaded=source.load_stage_animation(deferred,slot);}
        if(loaded){phase="complete";loaded=source.complete_stage_timeline(stage,deferred);}
        bool same=loaded&&scene(legacy.scene,deferred.scene)&&anm(legacy.background,deferred.background)&&anm(legacy.logo,deferred.logo)&&anm(legacy.enemies,deferred.enemies)&&ecl(legacy.timeline,deferred.timeline)&&legacy.messages[selection]==deferred.messages[selection]&&legacy.ecl_animation_names==deferred.ecl_animation_names&&legacy.boss_programs.size()==deferred.boss_programs.size();
        for(u32 slot=0;same&&slot<deferred.ecl_animations.size();++slot)same=anm(legacy.ecl_animations[slot],deferred.ecl_animations[slot]);
        for(u32 boss=0;same&&boss<deferred.boss_programs.size();++boss)same=ecl(legacy.boss_programs[boss],deferred.boss_programs[boss]);
        std::printf("{\"stage\":%u,\"selection\":%u,\"loaded\":%s,\"allDecodedResourceValuesEqual\":%s}\n",stage,selection,loaded?"true":"false",same?"true":"false");std::fflush(stdout);
        if(!same){std::fprintf(stderr,"Stage%u selection%u phase%s last%s resource mismatch: %s\n",stage,selection,phase,last_resource.c_str(),source.error().c_str());return 1;}++passed;
    }
    std::printf("{\"passed\":true,\"cases\":%u,\"byteAndFieldComparisons\":true,\"gameplayOrBrowserAcceptance\":false}\n",passed);return 0;
}
