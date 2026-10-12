// Fixture for the TH12 ANM comparison. Kept apart from th13-anm-fixture.cpp, whose bytes the TH13 and
// TH14 records pin. The native oracle records the whole 0x700-byte context of this title's own
// original, so this fixture exposes the port's own bytes and the interpreter's own transitions, and the
// checker derives which port offset corresponds to which native slot from the cases themselves, rather
// than declaring a layout that has not been measured for this title.
//
// `reset` presets and `step` executes, so a sweep can read the state it is about to compare against
// instead of remembering it - the reading fault of the two sweeps before this one.
#include "../../cpp/game/AnmVm.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include <cstddef>
#include <cstdlib>
#include <cstring>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmVm vm{};
// The tier-one hatch, in the shape th13-transform-fixture.cpp already uses: a body that allocates
// geometry needs somewhere for the vertices to go, and this harness supplies that place itself, with the
// same update hook shape. Everything else the environment leaves to its defaults, which are the
// integration points the record names.
struct FixtureEnvironment:AnmEnvironment{
    u32 geometry_bytes=0;
    static inline u8 ring[1u<<20];
    bool allocate_geometry(AnmVm& v,u32 bytes)override{
        geometry_bytes=bytes;
        // The original allocates what its operand asks for; the harness touches what it has and still
        // succeeds, so a negative operand (which multiplies to a huge byte count) is not a failure.
        std::memset(ring,0,bytes>sizeof(ring)?sizeof(ring):bytes);
        v.geometry=reinterpret_cast<void*>(ring);
        return true;
    }
    bool update_geometry(AnmVm&)override{return true;}
};
static FixtureEnvironment env;
// The checker hands over the game's own ANM buffers, and a body that binds a sprite needs one to bind.
// The resource is kept rather than opened and dropped, and run() attaches it before the command runs.
static AnmResource resource;
static bool resource_open=false;
alignas(4) static u8 code[64];

static void preset(i32 value, u32 variant) {
    // Section 353 tried the other direction and the count refused it: seeding the port with the
    // oracle's own zero base plus its two knobs raises the uncandidated slots from 55 to 56 and
    // lowers the comparisons by 3192, one case-set. The sixteen magic words stay, and the
    // measurement stands in the plan as a refuted theory rather than an untried one.
    env.rate = 1;
    vm.timer.set(0, &env.rate);
    vm.flags = 7 | (variant ? 0xc0009000u : 0x40000000u);
    vm.flags2 = variant ? 0xbc0000u : 0x820000u;
    vm.th13_native_flags = 0u;
    vm.layer = 27;
    vm.color = 0xab123456u;
    vm.secondary_color = 0x78345678u;
    vm.scale = {1, -2.5};
    vm.integers[0] = value;
    vm.integers[1] = value ^ 2;
}
static int step(u32 opcode, u32 variant, u32 references, i32 argument, i32 argument2) {
    std::memset(code, 0, sizeof(code));
    auto* command = reinterpret_cast<AnmInstruction*>(code);
    command->opcode = anm_canonical_opcode(opcode);
    command->length = u16(opcode == 312 ? 16 : 12);
    command->references = references;
    std::memcpy(code + 8, &argument, 4);
    std::memcpy(code + 12, &argument2, 4);
    // The oracle feeds the second argument as the four bytes at +0xc, so the harness must not lay a
    // following instruction's header over its high half: the argument area stays exactly what the
    // oracle saw, and the word that the next candidate reads as its time carries the stop.
    const u32 stop = 32760;
    std::memcpy(code + command->length + 4, &stop, 4);
    const u32 terminator = 32767;
    std::memcpy(code + command->length + 12, &terminator, 4);
    vm.script_begin = vm.instruction = command;
    return vm.update(env);
}
API(run) int run(u32 opcode, i32 value, u32 variant, u32 references, i32 argument, i32 argument2) {
    vm = {};
    vm.initialize();
    preset(value, variant);
    // Only the file pointer, not bind_script: binding a script resets the timer, the flags and the
    // instruction pointer, which would disturb the preset every other slot is compared through. A body
    // that binds a sprite needs the resource and nothing else.
    vm.resource = resource_open ? &resource : nullptr;
    return step(opcode, variant, references, argument, argument2);
}
API(reset) int reset(i32 value, u32 variant) {
    vm = {};
    vm.initialize();
    preset(value, variant);
    return 0;
}
API(step) int step_export(u32 opcode, u32 variant, u32 references, i32 argument, i32 argument2) {
    return step(opcode, variant, references, argument, argument2);
}
API(next_update) int next_update() { return vm.update(env); }
API(size) u32 size() { return sizeof(AnmVm); }
API(slot) u32 slot(u32 byteOffset) {
    u32 word = 0;
    const auto* begin = reinterpret_cast<const u8*>(&vm);
    if (byteOffset + 4 > sizeof(AnmVm)) return 0;
    std::memcpy(&word, begin + byteOffset, 4);
    return word;
}
API(real_slot) float real_slot(u32 byteOffset) {
    float value = 0;
    const auto* begin = reinterpret_cast<const u8*>(&vm);
    if (byteOffset + 4 > sizeof(AnmVm)) return 0;
    std::memcpy(&value, begin + byteOffset, 4);
    return value;
}
// The named members, for the record's own reading of the mapping it derives.
API(named) u32 named(u32 which) {
    switch (which) {
    case 0: return vm.flags;
    case 1: return vm.flags2;
    case 2: return vm.th13_native_flags;
    case 3: return vm.layer;
    case 4: return vm.color;
    case 5: return vm.secondary_color;
    case 6: return vm.integers[0];
    case 7: return vm.integers[1];
    case 8: return u32(vm.instruction != nullptr);
    case 9: return u32(vm.timer.current);
#if PORT_TITLE == 14
    case 10: return u32(vm.age.current);
#else
    case 10: return 0;
#endif
    default: return 0;
    }
}
API(named_real) float named_real(u32 which) {
    return which == 0 ? vm.scale.x : which == 1 ? vm.scale.y : vm.timer.fractional;
}
// Where the declared members sit, so a seed or a mirror can be aimed at a field by name rather
// than at a word by guess. Section 353 tried the wholesale seed alignment and its count refused it;
// this is the per-field direction. The first eleven rows keep the index space named() uses, and
// the rest is the whole declared layout, because the derivation finds offsets in every band of it
// and a name for the band is worth more than a number. One table, one name per offset, so the
// name and the offset cannot drift apart.
struct AnmMemberRow {const char* name;u32 offset;};
static const AnmMemberRow kAnmMembers[]={
    {"flags",u32(offsetof(AnmVm,flags))},
    {"flags2",u32(offsetof(AnmVm,flags2))},
    {"title flags",u32(offsetof(AnmVm,th13_native_flags))},
    {"layer",u32(offsetof(AnmVm,layer))},
    {"color",u32(offsetof(AnmVm,color))},
    {"secondary color",u32(offsetof(AnmVm,secondary_color))},
    {"integer 0",u32(offsetof(AnmVm,integers[0]))},
    {"integer 1",u32(offsetof(AnmVm,integers[1]))},
    {"live",u32(offsetof(AnmVm,instruction))},
    {"timer",u32(offsetof(AnmVm,timer))},
#if PORT_TITLE == 14
    {"age",u32(offsetof(AnmVm,age))},
#else
    {"age",0xffffffffu},
#endif
    {"id",u32(offsetof(AnmVm,id))},
    {"draw next",u32(offsetof(AnmVm,draw_next))},
    {"registry",u32(offsetof(AnmVm,registry))},
    {"child",u32(offsetof(AnmVm,child))},
    {"rotation",u32(offsetof(AnmVm,rotation))},
    {"angular velocity",u32(offsetof(AnmVm,angular_velocity))},
    {"scale",u32(offsetof(AnmVm,scale))},
    {"scale velocity",u32(offsetof(AnmVm,scale_velocity))},
    {"sprite size",u32(offsetof(AnmVm,sprite_size))},
    {"uv offset",u32(offsetof(AnmVm,uv_offset))},
    {"uv",u32(offsetof(AnmVm,uv))},
    {"position interpolation",u32(offsetof(AnmVm,position_interpolation))},
    {"color interpolation",u32(offsetof(AnmVm,color_interpolation))},
    {"alpha interpolation",u32(offsetof(AnmVm,alpha_interpolation))},
    {"rotation interpolation",u32(offsetof(AnmVm,rotation_interpolation))},
    {"scale interpolation",u32(offsetof(AnmVm,scale_interpolation))},
    {"color2 interpolation",u32(offsetof(AnmVm,color2_interpolation))},
    {"alpha2 interpolation",u32(offsetof(AnmVm,alpha2_interpolation))},
    {"scroll x interpolation",u32(offsetof(AnmVm,scroll_x_interpolation))},
    {"scroll y interpolation",u32(offsetof(AnmVm,scroll_y_interpolation))},
    {"scroll velocity",u32(offsetof(AnmVm,scroll_velocity))},
    {"sprite matrix",u32(offsetof(AnmVm,sprite_matrix))},
    {"transform matrix",u32(offsetof(AnmVm,transform_matrix))},
    {"uv matrix",u32(offsetof(AnmVm,uv_matrix))},
    {"pending interrupt",u32(offsetof(AnmVm,pending_interrupt))},
    {"saved timer",u32(offsetof(AnmVm,saved_timer))},
    {"saved instruction",u32(offsetof(AnmVm,saved_instruction))},
    {"sprite frame",u32(offsetof(AnmVm,sprite_frame))},
    {"sprite index",u32(offsetof(AnmVm,sprite_index))},
    {"file index",u32(offsetof(AnmVm,file_index))},
    {"script index",u32(offsetof(AnmVm,script_index))},
    {"script begin",u32(offsetof(AnmVm,script_begin))},
    {"instruction",u32(offsetof(AnmVm,instruction))},
    {"sprite",u32(offsetof(AnmVm,sprite))},
    {"resource",u32(offsetof(AnmVm,resource))},
    {"integers",u32(offsetof(AnmVm,integers))},
    {"floats",u32(offsetof(AnmVm,floats))},
    {"extra integers",u32(offsetof(AnmVm,extra_integers))},
    {"script position",u32(offsetof(AnmVm,script_position))},
    {"position",u32(offsetof(AnmVm,position))},
    {"child position",u32(offsetof(AnmVm,child_position))},
    {"geometry",u32(offsetof(AnmVm,geometry))},
    {"reserved 418",u32(offsetof(AnmVm,reserved_418))},
    {"rectangle columns",u32(offsetof(AnmVm,rectangle_columns))},
    {"rectangle rows",u32(offsetof(AnmVm,rectangle_rows))},
    {"parent",u32(offsetof(AnmVm,parent))},
    {"title effect",u32(offsetof(AnmVm,th13_effect))},
    {"reserved 430",u32(offsetof(AnmVm,reserved_430))},
};
API(member_total) u32 member_total(){return u32(sizeof(kAnmMembers)/sizeof(kAnmMembers[0]));}
API(member_name) const char* member_name(u32 which){
    return which<sizeof(kAnmMembers)/sizeof(kAnmMembers[0])?kAnmMembers[which].name:nullptr;
}
API(member_offset) u32 member_offset(u32 which) {
    return which<sizeof(kAnmMembers)/sizeof(kAnmMembers[0])?kAnmMembers[which].offset
                                                          :0xffffffffu;
}
API(member_real_offset) u32 member_real_offset(u32 which) {
    if (which == 0) return u32(offsetof(AnmVm, scale) + 0);
    if (which == 1) return u32(offsetof(AnmVm, scale) + 4);
    if (which == 2) return u32(offsetof(AnmVm, timer) + 4);
    return 0xffffffffu;
}
API(canonical) u32 canonical(u32 op) { return anm_canonical_opcode(op); }
// The native oracle's position slot (its +0x28) is a pointer into the original's code, so what can be
// compared across the two address spaces is how far the handler moved the instruction pointer.
// A body that writes back into the instruction itself changes a byte the VM context cannot show, so the
// harness exposes it: this is the quantity that separates the in-place arithmetic family.
API(code_word) u32 code_word(u32 offset) {
    u32 word = 0;
    if (offset + 4 > sizeof(code)) return 0;
    std::memcpy(&word, code + offset, 4);
    return word;
}
API(delta) u32 delta() {
    if (vm.instruction == nullptr) return 0xffffffffu;
    return u32(reinterpret_cast<const u8*>(vm.instruction) - reinterpret_cast<const u8*>(vm.script_begin));
}
// What the harness actually holds: the checker reads this to see whether a sprite-binding body can be
// satisfied by the files it offers, instead of inferring it from the file list.
API(sprites_open) i32 sprites_open() { return resource_open ? i32(resource.sprites.size()) : -1; }
API(allocate) void* allocate(u32 size) { return std::malloc(size); }
API(release) void release(void* p) { std::free(p); }
API(open_resource) i32 open_resource(const u8* data, u32 size) {
    AnmResource candidate;
    if (!candidate.open(data, size)) return -candidate.last_error;
    // The file with the most sprites wins, and the code now does what it says: a body that binds a
    // sprite picks its index from its own operands, so offering the widest of the game's own tables
    // is the honest choice among the ones the checker hands over.
    if (!resource_open || candidate.sprites.size() > resource.sprites.size()) {
        resource = candidate;
        resource_open = true;
    }
    return i32(candidate.scripts.size());
}
