#include "GameResources.hpp"
#include "StageFiles.hpp"
#include "PortTitle.hpp"
#include <cstdio>
#if PORT_TITLE == 14 && defined(TH14_WEBGPU_BACKEND) && defined(TH14_ARCHIVE_WORKER)
extern "C" {
int th14_webgpu_archive_size(const char* name);
int th14_webgpu_archive_copy(const char* name,void* destination,unsigned size);
}
#endif
#if defined(TH_NATIVE_PLATFORM) && defined(TH_ENABLE_THCRAP)
#include <SDL3/SDL.h>
#endif

namespace th11 {

std::string last_resource;

namespace {
// The archive's generation is the title's own. `archive_crypt_table` maps 12/125/128 to TH12's ciphers, 13 to
// TH13's and everything else to the one table TH14 and later share, so a per-title build has to name its own
// generation. `Archive::open` defaulted to 12 - the generation of the title the port started from - which made a
// th13 archive parse (the 16-byte header is encrypted with fixed parameters) and then fail on entry decryption
// wherever the two cipher tables differ. The observable was "Missing sound: se_tan00.wav" for a name the archive
// demonstrably holds, because a failed decode and a failed lookup report the same message.
constexpr u32 archive_generation = kPortTitle==12?12u:(kPortTitle==13?13u:14u);
}

bool GameResources::fail(const char* message) {
    last_error = message ? message : "resource error";
    return false;
}

bool GameResources::open_archive(const u8* bytes, u32 size) {
    lookup.clear(); animations = {}; last_error.clear();
    if (!archive.open(bytes, size, archive_generation)) return fail("invalid THA1 archive");
    // Retail th12.dat ships `se_cardget.wav` twice. The original manager resolves
    // names by scanning its entry table in order, so the first occurrence wins;
    // mirror that instead of rejecting a real installation.
    for (u32 i=0; i<archive.entries.size(); ++i) {
        const auto& entry = archive.entries[i];
        if (entry.name.empty()) {
            archive.entries.clear(); lookup.clear();
            return fail("empty archive resource name");
        }
        lookup.emplace(entry.name, i);
    }
    return true;
}

bool GameResources::has(const std::string& name) const noexcept {
    return lookup.find(name) != lookup.end();
}

bool GameResources::read(const std::string& name, std::vector<u8>& data) {
    last_resource = name;
    const auto found = lookup.find(name);
    if (found == lookup.end()) return fail("missing archive resource");
#if defined(TH_NATIVE_PLATFORM) && defined(TH_ENABLE_THCRAP)
    // Same boundary as TH10 ResourceFiles: a prepared /thcrap/th11/<entry>
    // overrides one original archive entry; absent files use the retail DAT.
    if (!name.empty() && name.front() != '/' && name.find("..") == std::string::npos &&
        name.find('\\') == std::string::npos && name.find(':') == std::string::npos) {
        const std::string path = "/thcrap/th11/" + name;
        size_t length = 0;
        void* bytes = SDL_LoadFile(path.c_str(), &length);
        if (bytes) {
            if (length > 64u * 1024u * 1024u) { SDL_free(bytes); return fail("oversized THCRAP override"); }
            const auto* begin = static_cast<const u8*>(bytes);
            data.assign(begin, begin + length);
            SDL_free(bytes);
            return true;
        }
    }
#endif
#if PORT_TITLE == 14 && defined(TH14_WEBGPU_BACKEND) && defined(TH14_ARCHIVE_WORKER)
    // A background batch owns immutable decoded bytes only while its loading
    // callback runs. Entries outside that batch keep the ordinary archive path.
    const int prefetched=th14_webgpu_archive_size(name.c_str());
    if(prefetched < -1)return fail("background archive decode failed");
    if(prefetched>=0){
        data.resize(u32(prefetched));
        if(!th14_webgpu_archive_copy(name.c_str(),data.data(),u32(data.size())))
            return fail("background archive delivery failed");
        return true;
    }
#endif
    if (!archive.read(found->second, data)) return fail("resource decode failed");
    return true;
}

bool GameResources::open_anm(const std::string& name, AnmResource& output) {
    std::vector<u8> data;
    if (!read(name, data) || !output.open(data.data(), u32(data.size())))
        return fail("invalid ANM resource");
    return true;
}

bool GameResources::open_sht(const std::string& name, ShtResource& output) {
    std::vector<u8> data;
    if (!read(name, data)) return fail("SHT entry not found");
    if (!output.open(data.data(), u32(data.size())))
        return fail((std::string("invalid SHT resource: ")+sht_parse_reason).c_str());
    // A parse that succeeds says so, with the numbers it read: a sheet accepted under the
    // wrong layout is otherwise as quiet as a right one (the group count is the file's own).
    unsigned long long specs = 0;
    for (const auto& group : output.groups) specs += group.shots.size();
    std::printf("[sht] %s version=%u groups=%u specs=%llu max_power=%d step=%d\n",
                 name.c_str(), unsigned(output.header.version), unsigned(output.header.group_count),
                 specs, output.header.max_power_level, output.header.power_step);
    return true;
}

bool GameResources::load_ecl(const std::string& name, EclProgram& output) {
    output.files.clear(); output.definitions.clear(); output.error.clear();
    if (!output.load(name, *this)) {
        last_error = output.error.empty() ? "invalid ECL resource" : output.error;
        return false;
    }
    return true;
}

bool GameResources::load_stage(u32 stage, StageResources& output) {
#if PORT_TITLE == 14
    output.stage_number=stage;
#endif
    if (stage < 1 || stage > 7) return fail("stage outside TH11 range");
    // The names, and the dialogue shape, are the title's own rows: see StageFiles.hpp.
    char name[64];
    std::vector<u8> scene;
    std::snprintf(name, sizeof name, stage_files.scene, stage);
    if (!read(name, scene)) return false;
    if (!output.scene.open(scene.data(), u32(scene.size()))) return fail(output.scene.error.c_str());
    std::snprintf(name, sizeof name, stage_files.background, stage);
    if (!open_anm(name, output.background)) return false;
    std::snprintf(name, sizeof name, stage_files.logo, stage);
    if (!open_anm(name, output.logo)) return false;
    std::snprintf(name, sizeof name, stage_files.enemies, stage);
    if (!open_anm(name, output.enemies)) return false;
    std::snprintf(name, sizeof name, stage_files.timeline, stage);
    if (!load_ecl(name, output.timeline)) return false;
#if PORT_TITLE == 14 || PORT_TITLE == 16
    // 422500 writes ANIM entry i to EnemyManager +a8+4*i and loads it
    // as ANM file 10+i. Slots 0/1 are reserved; slot 2 is the first include.
    output.ecl_animation_names={};
    for(const auto& file:output.timeline.files){
        if(file->animations.size()>output.ecl_animations.size())return fail("ECL animation slot limit");
        for(u32 i=0;i<file->animations.size();++i)output.ecl_animation_names[i]=file->animations[i];
    }
    for(u32 i=0;i<output.ecl_animations.size();++i){output.ecl_animations[i]={};
        if(!output.ecl_animation_names[i].empty()&&!open_anm(output.ecl_animation_names[i],output.ecl_animations[i]))return false;
    }
#endif
    for (u32 i=0; i<stage_files.dialogue_count && i<output.messages.size(); ++i) {
        stage_dialogue_name(name, sizeof name, stage, i);
        if (!read(name, output.messages[i])) return false;
    }
    output.boss_programs.clear();
    for (const char* suffix : {stage_files.boss, stage_files.midboss}) {
        std::snprintf(name, sizeof name, suffix, stage);
        if (!has(name)) continue;
        output.boss_programs.emplace_back();
        if (!load_ecl(name, output.boss_programs.back())) return false;
    }
    return true;
}

#if PORT_TITLE == 14
bool GameResources::load_stage_hud(u32 stage,StageResources& output,u32 dialogue_selection) {
    if(stage<1||stage>7)return fail("stage outside TH14 range");
    if(dialogue_selection>=stage_files.dialogue_count||dialogue_selection>=output.messages.size())
        return fail("dialogue selection outside TH14 range");
    last_error.clear();output.stage_number=stage;
    char name[64];std::vector<u8> bytes;
    std::snprintf(name,sizeof name,stage_files.logo,stage);
    if(!read(name,bytes))return false;
    if(!output.logo.open(bytes.data(),u32(bytes.size())))
        return fail((std::string(name)+": "+(output.logo.detail.empty()?"invalid ANM resource":output.logo.detail)).c_str());
    for(auto& message:output.messages)message.clear();
    stage_dialogue_name(name,sizeof name,stage,dialogue_selection);
    return read(name,output.messages[dialogue_selection]);
}

bool GameResources::load_stage_scene(u32 stage,StageResources& output) {
    if(stage<1||stage>7)return fail("stage outside TH14 range");
    last_error.clear();output.stage_number=stage;
    char name[64];std::vector<u8> bytes;
    std::snprintf(name,sizeof name,stage_files.scene,stage);
    if(!read(name,bytes))return false;
    if(!output.scene.open(bytes.data(),u32(bytes.size())))return fail(output.scene.error.c_str());
    std::snprintf(name,sizeof name,stage_files.background,stage);
    if(!read(name,bytes))return false;
    if(!output.background.open(bytes.data(),u32(bytes.size())))
        return fail((std::string(name)+": "+(output.background.detail.empty()?"invalid ANM resource":output.background.detail)).c_str());
    return true;
}

bool GameResources::load_stage_timeline_plan(u32 stage,StageResources& output){
    if(stage<1||stage>7)return fail("stage outside TH14 range");
    last_error.clear();output.stage_number=stage;
    char name[64];std::snprintf(name,sizeof name,stage_files.timeline,stage);
    if(!load_ecl(name,output.timeline))return false;
    output.ecl_animation_names={};output.ecl_animations={};output.enemies={};
    for(const auto& file:output.timeline.files){
        if(file->animations.size()>output.ecl_animations.size())return fail("ECL animation slot limit");
        for(u32 i=0;i<file->animations.size();++i)output.ecl_animation_names[i]=file->animations[i];
    }
    output.boss_programs.clear();
    for(const char* suffix:{stage_files.boss,stage_files.midboss}){
        std::snprintf(name,sizeof name,suffix,stage);
        if(!has(name))continue;
        output.boss_programs.emplace_back();
        if(!load_ecl(name,output.boss_programs.back()))return false;
    }
    return true;
}
bool GameResources::load_stage_animation(StageResources& output,u32 slot){
    if(slot>=output.ecl_animations.size())return fail("ECL animation slot limit");
    if(output.ecl_animation_names[slot].empty())return true;
    return open_anm(output.ecl_animation_names[slot],output.ecl_animations[slot]);
}
bool GameResources::complete_stage_timeline(u32 stage,StageResources& output){
    if(stage<1||stage>7)return fail("stage outside TH14 range");
    char name[64];std::snprintf(name,sizeof name,stage_files.enemies,stage);
    for(u32 i=0;i<output.ecl_animation_names.size();++i)if(output.ecl_animation_names[i]==name){
        // This engine retains an independent default-animation owner. The
        // matching ANIM file has already been decoded by the same worker.
        output.enemies=output.ecl_animations[i];output.enemies.templates.reset();return true;
    }
    return open_anm(name,output.enemies);
}
bool GameResources::load_stage_timeline(u32 stage,StageResources& output) {
    if(stage<1||stage>7)return fail("stage outside TH14 range");
    last_error.clear();output.stage_number=stage;
    char name[64];std::vector<u8> bytes;
    std::snprintf(name,sizeof name,stage_files.enemies,stage);
    if(!read(name,bytes))return false;
    if(!output.enemies.open(bytes.data(),u32(bytes.size())))
        return fail((std::string(name)+": "+(output.enemies.detail.empty()?"invalid ANM resource":output.enemies.detail)).c_str());
    std::snprintf(name,sizeof name,stage_files.timeline,stage);
    if(!load_ecl(name,output.timeline))return false;
    output.ecl_animation_names={};
    for(const auto& file:output.timeline.files){
        if(file->animations.size()>output.ecl_animations.size())return fail("ECL animation slot limit");
        for(u32 i=0;i<file->animations.size();++i)output.ecl_animation_names[i]=file->animations[i];
    }
    for(u32 i=0;i<output.ecl_animations.size();++i){
        output.ecl_animations[i]={};
        if(output.ecl_animation_names[i].empty())continue;
        if(!read(output.ecl_animation_names[i],bytes))return false;
        if(!output.ecl_animations[i].open(bytes.data(),u32(bytes.size())))
            return fail((output.ecl_animation_names[i]+": "+(output.ecl_animations[i].detail.empty()?"invalid ANM resource":output.ecl_animations[i].detail)).c_str());
    }
    output.boss_programs.clear();
    for(const char* suffix:{stage_files.boss,stage_files.midboss}){
        std::snprintf(name,sizeof name,suffix,stage);
        if(!has(name))continue;
        output.boss_programs.emplace_back();
        if(!load_ecl(name,output.boss_programs.back()))return false;
    }
    return true;
}
#endif

bool GameResources::animation(u32 slot, const std::string& name) {
    if (slot >= animations.size() || !has(name)) return fail("missing ECL animation");
    animations[slot] = name;
    return true;
}

const std::string& GameResources::animation_name(u32 slot) const noexcept {
    static const std::string empty;
    return slot < animations.size() ? animations[slot] : empty;
}

}
