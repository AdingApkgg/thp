#include "th14-stage-asset-update-fixture.cpp"
#include "th14-stage-pass-graphics-fixture.hpp"
#include "../../cpp/game/ScreenFade.hpp"
static th11::test::PassGraphics graphics;
static AnmRenderer renderer(graphics);
static ScreenFades fades;
static std::vector<u32> submissions,draw_states,pass_values,clears;
extern "C" int __real__ZN4th1111AnmRenderer4drawERNS_5AnmVmE(AnmRenderer*,AnmVm&);
extern "C" int __wrap__ZN4th1111AnmRenderer4drawERNS_5AnmVmE(AnmRenderer* r,AnmVm& v){
 const auto p=uintptr_t(&v),first=uintptr_t(stage->object_animations.data());u32 index;
 if(p>=first&&p<first+stage->object_animations.size()*sizeof(AnmVm))index=u32(&v-stage->object_animations.data());
 else {const auto embedded=uintptr_t(stage->state.script_animations);if(p<embedded||p>=embedded+sizeof(stage->state.script_animations))return 0;index=0x80000000u+u32((p-embedded)/sizeof(AnmVm));}
 draw_states.insert(draw_states.end(),{index,u32(graphics.state.depthWrite),u32(graphics.state.fog)});
 return __real__ZN4th1111AnmRenderer4drawERNS_5AnmVmE(r,v);
}
static void observe_pass(){const auto& s=stage->state;const auto& p=graphics.state;
 pass_values.insert(pass_values.end(),{s.tint,s.draw_flags,u32(s.fade_timer.previous),u32(s.fade_timer.current),word(s.fade_timer.fractional),s.effects_enabled,s.drawn_objects,s.culled_objects,s.drawn_primitives,u32(renderer.tint_enabled),renderer.tint,u32(p.depthWrite),u32(p.depthCompare)+1,u32(p.fog),p.fogColor,word(p.fogNear),word(p.fogFar)});
}
API(render_reset) void render_reset(){renderer.invalidate();graphics=th11::test::PassGraphics{};graphics.state.depthWrite=false;graphics.state.depthCompare=touhou::graphics::Compare::Always;renderer.tint_enabled=false;renderer.tint=0x80808080;fades.effects.clear();}
API(render_draw) u32 render_draw(){
 graphics.data.clear();graphics.submissions.clear();graphics.snapshots.clear();graphics.extras.clear();graphics.target_events.clear();submissions.clear();draw_states.clear();pass_values.clear();clears.clear();
 if(!stage->draw_background(renderer,camera,fades))return 0;observe_pass();
 if(!stage->draw_foreground(renderer,camera))return 0;observe_pass();renderer.flush();
 for(u32 i=0;i<graphics.submissions.size();++i){const auto& draw=graphics.submissions[i];const auto& p=graphics.snapshots[i];const auto* words=reinterpret_cast<const u32*>(graphics.data.data()+draw.start);
  if(draw.stride==28){for(u32 q=0;q<draw.count/2;++q){submissions.insert(submissions.end(),{0,p.depth_write,p.fog});for(u32 index:{0u,1u,2u,5u})submissions.insert(submissions.end(),words+(q*6+index)*7,words+(q*6+index)*7+7);}}
  else if(draw.stride==20&&p.layout==u32(touhou::graphics::VertexLayout::ScreenColor)){submissions.insert(submissions.end(),{3,p.depth_write,p.fog,draw.count});submissions.insert(submissions.end(),words,words+draw.size/4);}
  else{if(draw.stride==24)submissions.insert(submissions.end(),{1,draw.topology+1,draw.count,draw.stride,p.depth_write,p.fog});else if(draw.stride==20)submissions.insert(submissions.end(),{2,draw.topology+1,draw.count,p.depth_write,p.fog,p.factor});else return 0;
   submissions.insert(submissions.end(),graphics.extras[i].begin(),graphics.extras[i].end());const auto* w=reinterpret_cast<const u32*>(p.world.m);const auto* uv=reinterpret_cast<const u32*>(p.uv.m);submissions.insert(submissions.end(),w,w+16);submissions.insert(submissions.end(),uv,uv+16);submissions.insert(submissions.end(),words,words+draw.size/4);}
 }
 for(const auto& e:graphics.target_events)if(e.kind==1){const auto& r=e.rectangle;clears.insert(clears.end(),{3,e.color,u32(r.x),u32(r.y),u32(r.x+r.width),u32(r.y+r.height)});}return 1;
}
API(render_words) u32 render_words(){return submissions.size();}
API(render_data) const u32* render_data(){return submissions.data();}
API(draw_state_words) u32 draw_state_words(){return draw_states.size();}
API(draw_state_data) const u32* draw_state_data(){return draw_states.data();}
API(pass_words) u32 pass_words(){return pass_values.size();}
API(pass_data) const u32* pass_data(){return pass_values.data();}
API(clear_words) u32 clear_words(){return clears.size();}
API(clear_data) const u32* clear_data(){return clears.data();}
