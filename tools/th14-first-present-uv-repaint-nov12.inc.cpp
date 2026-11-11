// Diagnostic repaint after the first real Player frame. Never resumes updates.
namespace uv_repaint {
Vec2 saved{};bool armed=false;
TransitionType0Th14* owner(){
 if(!current||callbacks!=1||!game||!game->battle||game->battle->control_frame()!=1)return nullptr;
 auto* root=game->animations.find(game->transition_type0);
 return root&&root->th13_effect==1&&root->geometry?static_cast<TransitionType0Th14*>(root->geometry):nullptr;
}
}
API(diagnostic_uv_state) const u32* diagnostic_uv_state(){
 static u32 w[12];auto* t=uv_repaint::owner();if(!t)return nullptr;
 const auto& vm=t->embedded[4];const auto& a=game->animations;
 const u32 values[]={callbacks,game->state.stage,u32(game->battle->control_frame()),t->counter,u32(vm.age.current),
  th14_title_observer::float_bits(vm.uv_offset.x),th14_title_observer::float_bits(vm.uv_offset.y),
  a.script_rng.seed_value(),a.script_rng.call_count(),a.visual_rng.seed_value(),a.visual_rng.call_count(),u32(uv_repaint::armed)};
 std::copy(std::begin(values),std::end(values),w);return w;
}
API(diagnostic_uv_repaint) u32 diagnostic_uv_repaint(u32 mode,u32 x,u32 y){
 auto* t=uv_repaint::owner();if(!t||mode>2)return 0;
 auto& uv=t->embedded[4].uv_offset;
 if(mode==1){if(uv_repaint::armed)return 0;uv_repaint::saved=uv;uv_repaint::armed=true;std::memcpy(&uv.x,&x,4);std::memcpy(&uv.y,&y,4);}
 if(mode==2){if(!uv_repaint::armed)return 0;uv=uv_repaint::saved;uv_repaint::armed=false;}
 // Reuse the actual completed frame's text. No tick, statistics sampling,
 // callback enable, deferred-capture consumption, or input processing.
 if(!current->session.draw(current->renderer,&current->frame_text)){current->error=current->session.error;return 0;}
 current->graphics.present();return 1;
}
