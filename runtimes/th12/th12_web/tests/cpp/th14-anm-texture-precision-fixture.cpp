#include "../../cpp/game/AnmVm.hpp"
#include "th14-startup-fixture.cpp"
static u32 reference_observation[6];
API(reference) const u32* reference(u32 seed,float value,u32 high){
    AnmEnvironment environment;environment.texture_high_precision=high;
    environment.script_rng={u16(seed),0,0};environment.visual_rng={12345,0,0};
    AnmVm vm;vm.initialize();vm.integers[0]=7;vm.floats[0]=.25f;
    vm.random_scale={1.75f,-2.5f};vm.random_bound=31;
    const float result=float(vm.float_value(value,environment));
    reference_observation[0]=float_bits(result);reference_observation[1]=environment.texture_high_precision;
    std::memcpy(reference_observation+2,&environment.script_rng,16);return reference_observation;
}
API(core_precision) u32 core_precision(){return core_session->animations.texture_high_precision;}
