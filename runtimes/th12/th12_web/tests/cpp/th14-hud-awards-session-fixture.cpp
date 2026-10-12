#include "th14-session-fixture.cpp"
#include <cmath>
API(awards_setup) u32 awards_setup(u32 result,u32 time,u32 show,i32 bonus,i32 frames,i32 encoded,u32 alpha){
    auto& b=*session.battle;auto& a=session.animations;
    if(auto* vm=a.find(b.result_animation))a.destroy(*vm);
    if(auto* vm=a.find(b.hud.spell_time_animation))a.destroy(*vm);
    b.result_animation=0;b.hud.spell_time_animation=0;b.hud.show_spell_time=false;
    b.completion.state.displayed_bonus=bonus;b.spell_timing.last_frames=frames;b.spell_timing.encoded=encoded;
    if(result){if(!b.stage_result_animation())return 0;auto* vm=a.find(b.result_animation);if(!vm)return 0;vm->color=(alpha<<24)|0xffffff;if(result==3)a.destroy(*vm);}
    if(time){if(!b.hud.notice(1))return 0;auto* vm=a.find(b.hud.spell_time_animation);if(!vm)return 0;vm->color=(alpha<<24)|0xffffff;if(time==3)a.destroy(*vm);}
    b.hud.show_spell_time=show;return 1;
}
API(awards_count) u32 awards_count(){u32 count=0;for(const auto& q:session.battle->ascii.requests)if(q.style.pass==2)++count;return count;}
static const AsciiRequest& awards_request(u32 index){for(const auto& q:session.battle->ascii.requests)if(q.style.pass==2){if(!index)return q;--index;}std::abort();}
API(awards_bytes) const char* awards_bytes(u32 index){return awards_request(index).text.c_str();}
API(awards_word) u32 awards_word(u32 index,u32 field){const auto& q=awards_request(index);const u32 values[]={float_bits(q.position.x),float_bits(q.position.y),float_bits(q.position.z),q.style.color,u32(q.style.font),u32(q.style.pass),float_bits(q.style.scale.x),float_bits(q.style.scale.y)};return values[field];}
API(awards_state) u32 awards_state(u32 field){auto& b=*session.battle;auto* r=session.animations.find(b.result_animation);auto* t=session.animations.find(b.hud.spell_time_animation);const u32 values[]={r?1u:0u,t?1u:0u,u32(b.hud.show_spell_time),r?u32(r->script_index):0,t?u32(t->script_index):0,r?r->layer:0,t?t->layer:0,r?r->color:0,t?t->color:0};return values[field];}
API(awards_animation_tick) u32 awards_animation_tick(){return session.animations.update(false);}
API(awards_render_finite) u32 awards_render_finite(){for(const auto& s:graphics.submissions)for(u32 i=0;i<s.size/s.stride;++i){const auto* p=reinterpret_cast<const float*>(graphics.data.data()+s.start+i*s.stride);for(u32 axis=0;axis<3;++axis)if(!std::isfinite(p[axis]))return 0;}return 1;}
API(awards_submissions) u32 awards_submissions(){return graphics.submissions.size();}
