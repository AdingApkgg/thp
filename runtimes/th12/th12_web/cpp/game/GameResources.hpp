#pragma once
#include "Archive.hpp"
#include "AnmResource.hpp"
#include "EclResource.hpp"
#include "ShtResource.hpp"
#include "StageResource.hpp"
#include <array>
#include <string>
#include <unordered_map>
#include <vector>

namespace th11 {

// The last archive entry a loader asked for. It exists so that a stall during load can be attributed to a resource
// from outside the module: the browser harness reads it out of the running page, which turns "initialization never
// returned" into "the last thing it asked for was this file". It is an observation of load order, not a result.
extern std::string last_resource;

struct StageResources {
#if PORT_TITLE == 14
    u32 stage_number=0;
#endif
    StageResource scene;
    AnmResource background;
    AnmResource logo;
    AnmResource enemies;
    EclProgram timeline;
    std::array<std::vector<u8>,6> messages{};
    std::vector<EclProgram> boss_programs;
#if PORT_TITLE == 14 || PORT_TITLE == 16
    std::array<AnmResource,4> ecl_animations;
    std::array<std::string,4> ecl_animation_names;
#endif
};

// Owns the decoded TH11 archive index and provides the same named-resource
// boundary to ANM, ECL and SHT loaders. Gameplay managers receive these
// decoded objects later; they do not know about archive offsets or ciphers.
class GameResources final : public EclResourceProvider {
public:
    bool open_archive(const u8* bytes, u32 size);
    bool read(const std::string& name, std::vector<u8>& data) override;
    bool has(const std::string& name) const noexcept;
    bool open_anm(const std::string& name, AnmResource& output);
    bool open_sht(const std::string& name, ShtResource& output);
    bool load_ecl(const std::string& name, EclProgram& output);
    bool load_stage(u32 stage, StageResources& output);
    bool animation(u32 slot, const std::string& name) override;
    const std::string& error() const noexcept { return last_error; }
    u32 resource_count() const noexcept { return u32(archive.entries.size()); }
    const std::string& animation_name(u32 slot) const noexcept;
    // Name of one decoded archive entry. Needed to tell whether a resource a caller asks for by name
    // exists at all, instead of only learning that opening it failed.
    const std::string& entry_name(u32 index) const noexcept {
        static const std::string empty;
        return index < archive.entries.size() ? archive.entries[index].name : empty;
    }

private:
    Archive archive;
    std::unordered_map<std::string,u32> lookup;
    std::array<std::string,64> animations{};
    std::string last_error;
    bool fail(const char* message);
};

}
