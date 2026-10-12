#include "th14-hud-resource-fixture.cpp"
static AnmVm notice_animation;
static i32 notice_script=0;
API(notice_animation_begin) u32 notice_animation_begin(i32 script,float rate){
    manager.clear();manager.rate=rate;manager.fallback_sprites=&ascii;
    front.templates.reset();if(!manager.prepare_resource(front,5))return 0;
    notice_script=script;notice_animation.position={};
    if(!notice_animation.copy_script(front,script,5,&manager.rate))return 0;
    notice_animation.layer=0;notice_animation.flags2|=0x200;
    return 1;
}
API(notice_animation_tick) i32 notice_animation_tick(){return notice_animation.update(manager);}
API(notice_animation_state) u32 notice_animation_state(u32 field,u32 templ){
    const auto& v=templ?front.templates->scripts[notice_script]:notice_animation;
    const u32 values[]={v.layer,v.color,u32(v.timer.current),float_bits(v.timer.fractional),u32(v.age.current),float_bits(v.age.fractional),v.flags&2,
        float_bits(v.script_position.x),float_bits(v.script_position.y),float_bits(v.script_position.z),float_bits(v.scale.x),float_bits(v.scale.y),
        float_bits(v.rotation.x),float_bits(v.rotation.y),float_bits(v.rotation.z),v.instruction?u32(reinterpret_cast<const u8*>(v.instruction)-reinterpret_cast<const u8*>(v.script_begin)):0xffffffffu};
    return values[field];
}
