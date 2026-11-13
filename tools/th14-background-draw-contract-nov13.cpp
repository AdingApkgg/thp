// Controlled background geometry/material input; no reference VM injection.
#include "../runtimes/th12/th12_web/tests/cpp/th14-render-fixture.cpp"
API(background_case) int background_case(float uv){
    reset();fixture.renderer.offset={};fixture.renderer.tint_enabled=false;
    vm.flags=3|(7u<<4)|(1u<<18)|(1u<<20);
    vm.th13_native_flags=0x00a040e7;vm.flags2=0x00804000;
    vm.set_drawing_mode(0);vm.color=0xffffffff;vm.secondary_color=0;
    vm.inherited_color=0xffffffff;vm.scale=vm.extra_scale=vm.texture_scale={1,1};
    vm.sprite_size={1280,960};vm.position=vm.script_position=vm.child_position={};
    vm.rotation={};vm.pivot={};vm.uv_offset={uv,uv};
    vm.uv[0]={0,0};vm.uv[1]={5,0};vm.uv[2]={0,3.75};vm.uv[3]={5,3.75};
    const auto result=fixture.renderer.draw(vm);fixture.renderer.flush();return result;
}
