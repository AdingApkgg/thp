#include "th14-replay-session-fixture.cpp"
static u32 reference[32]{};
static u32 reference_rewards[3]{};
static u32 reference_next_id_value=0;
static u32 reference_popup_cursor_value=0;
static std::array<u32,324> reference_popups{};
namespace th11 {extern const EclInstruction* ecl_last_integer_access;}
static std::vector<u32> reference_rng_reads;
static void observe_rng_read(i32 id,i32 enemy,u32 calls){
 if(!(calls>=38000&&calls<39000))return;
 const auto* inst=ecl_last_integer_access;
 const u32 row[]={calls,u32(id),u32(enemy),inst?u32(inst->opcode):0,inst?u32(inst->time):0,inst?u32(inst->references):0,
  inst&&inst->length>=20?inst->argument<u32>(0):0,inst&&inst->length>=24?inst->argument<u32>(1):0};
 reference_rng_reads.insert(reference_rng_reads.end(),std::begin(row),std::end(row));
}
static std::vector<u32> reference_shots,reference_enemies,reference_phases,reference_items,reference_bullets,reference_areas,reference_ids;
static u32 float_word(float x){u32 out;std::memcpy(&out,&x,4);return out;}
static void observe_reference(const GameBattle& b){
 if(b.frame>=3326&&b.frame<=3330){
  auto& manager=const_cast<AnmManager&>(b.animations);
  std::printf("anm-debug frame %u calls %u\n",b.frame,b.animations.visual_rng.calls);
  for(u32 i=0;i<anm_creation_count();++i){const u32 id=u32(anm_creation_value(i,5));auto* vm=manager.find(id);if(vm&&vm->th13_effect==7){const auto& p=*static_cast<AnmTh14Particles*>(vm->geometry);std::printf("effect7 id%u script%u file%u age%d timer%d previous%d integer0%d\n",id,u32(vm->script_index),u32(vm->file_index),vm->age.current,p.timer.current,p.timer.previous,vm->integers[0]);}}
 }
 reference_popup_cursor_value=b.popups.cursor;
 for(u32 n=0;n<18;++n){const auto& popup=n<13?b.popups.entries[n]:b.popups.bonuses[n-13];
  std::memcpy(reference_popups.data()+n*18,&popup,sizeof(popup));
  reference_popups[n*18+11]=popup.age.rate?1:0;
 }
 reference_next_id_value=b.enemies.total_created;
 const auto& p=*b.player;const auto& e=b.economy;
 u32 live=0;for(u32 n=0;n<256;++n)if(p.shots.at(n).state)++live;
 // Retail game control has already advanced its stage timer at priority 11;
 // GameBattle::frame counts completed updates and advances at the end.
 const i32 fields[]={wrapping_add(i32(b.frame),1),i32(p.input.movement.held),i32(p.input.movement.pressed),
  p.motion.state.x,p.motion.state.y,p.state.life_state,p.state.state_timer.current,
  p.state.transition_timer.current,p.state.th14_shooting_age.current,p.state.invincibility.current,
  p.shots.schedule.timer.current,p.motion.state.weapon_mode,
  e.score_units,e.graze,e.point_value,e.power,e.lives,e.life_fragments,e.th14_bombs,e.th14_bomb_fragments,e.rank,
  i32(b.animations.script_rng.seed),i32(b.animations.script_rng.calls),
  i32(b.animations.visual_rng.seed),i32(b.animations.visual_rng.calls),i32(b.enemies.count),i32(live),
  session.state.character,session.state.subtype,session.state.difficulty,i32(session.state.stage),i32(p.th14_scale.flags)};
 for(u32 n=0;n<32;++n)reference[n]=u32(fields[n]);
 reference_rewards[0]=p.shots.player.th14_plain_hits;reference_rewards[1]=p.shots.player.th14_focused_hits;reference_rewards[2]=p.shots.player.th14_hits_184bc;
 reference_ids.clear();for(auto* node=b.enemies.first;node;node=node->next)reference_ids.push_back(u32(node->value->state.instance_id));
 reference_shots.clear();reference_enemies.clear();reference_phases.clear();
 if((reference[0]>=3200&&reference[0]<=3550)||reference[0]<=1000||(reference[0]>=1200&&reference[0]<=1400)||(reference[0]>=2920&&reference[0]<=2950)||(reference[0]>=3000&&reference[0]<=3120)||(reference[0]>=3690&&reference[0]<=3705)){
  for(u32 n=0;n<256;++n){const auto& s=p.shots.at(n);if(!s.state)continue;
   const auto* area=s.spec&&s.spec->type==3?p.shots.th14_bomb_area(s.th14_area_slot):nullptr;
   const u32 row[]={n,u32(s.state),u32(s.timer.current),u32(s.damage),
    float_word(s.movement.position.x),float_word(s.movement.position.y),float_word(s.movement.position.z),
    float_word(s.movement.speed),float_word(s.movement.angle),float_word(area?area->size.x:(s.spec?s.spec->hitbox.x:0)),float_word(area?area->size.y:(s.spec?s.spec->hitbox.y:0))};
   reference_shots.insert(reference_shots.end(),std::begin(row),std::end(row));
  }
  for(auto* node=b.enemies.first;node;node=node->next){const auto& s=node->value->state;
   const u32 row[]={u32(s.health),u32(s.max_health),s.flags,float_word(s.current.position.x),float_word(s.current.position.y),
    float_word(s.hitbox.x),float_word(s.hitbox.y),float_word(s.collision_box.x),float_word(s.collision_box.y),u32(s.lifetime.current)};
   reference_enemies.insert(reference_enemies.end(),std::begin(row),std::end(row));
   reference_phases.push_back(u32(s.timer_2bc.current));reference_phases.push_back(u32(s.drops.primary));
   for(u32 n=0;n<13;++n)reference_phases.push_back(u32(s.drops.counts[n]));
   for(const auto& interrupt:s.interrupts)reference_phases.push_back(u32(interrupt.health));
  }
 }
 reference_areas.clear();
 if(reference[0]>=3000&&reference[0]<=3120){
  for(u32 j=0;j<256;++j){const auto* a=p.shots.th14_bomb_area(j);if(!(a->flags&1))continue;
   const ShotState* owner=p.shots.th14_area_owner(j);
   const u32 row[]={j,a->flags,float_word(a->radius),float_word(a->angle),float_word(a->size.x),float_word(a->size.y),
    float_word(a->position.x),float_word(a->position.y),float_word(a->position.z),u32(a->timer.previous),u32(a->timer.current),float_word(a->timer.fractional),
    u32(a->damage),u32(a->total),u32(a->maximum),u32(a->period),a->stamp,u32(a->callback!=0),owner?u32(owner->timer.current):0,owner?owner->th14_shot_flags:0};
   reference_areas.insert(reference_areas.end(),std::begin(row),std::end(row));
  }
 }
 reference_bullets.clear();
 if(reference[0]<=350){
  for(auto* s=b.bullets.first_th14();s;s=s->th14_active_next){
   const u32 row[]={u32(s->state),s->flags,u32(s->collision_delay),float_word(s->position.x),float_word(s->position.y),float_word(s->position.z),
    float_word(s->velocity.x),float_word(s->velocity.y),float_word(s->velocity.z),float_word(s->speed),float_word(s->angle),
    float_word(s->hitbox.x),float_word(s->hitbox.y),u32(s->lifetime.current),u32(u16(s->sprite))|(u32(u16(s->color))<<16),s->active_transforms};
   reference_bullets.insert(reference_bullets.end(),std::begin(row),std::end(row));
  }
 }
 reference_items.clear();
 if(reference[0]>=900&&reference[0]<=1000){
  for(u32 n=0;n<ItemManager::capacity;++n){const auto& s=b.items.at(n);if(!s.state)continue;
   const u32 row[]={u32(s.state),u32(s.type),u32(s.display_type),float_word(s.position.x),float_word(s.position.y),float_word(s.position.z),
    float_word(s.velocity.x),float_word(s.velocity.y),float_word(s.velocity.z),float_word(s.lifetime.fractional),float_word(s.attraction_speed),u32(s.delay)};
   reference_items.insert(reference_items.end(),std::begin(row),std::end(row));
  }
 }
}
API(begin_reference) i32 begin_reference(u32 demo){
 if(!begin_demo(demo))return 0;reference_rng_reads.clear();session.battle->before_player_update=observe_reference;
 if(demo==1||demo==2)session.battle->enemy_environment.th14_random_read=observe_rng_read;return 1;
}
API(reference_data) const u32* reference_data(){return reference;}
API(reference_reward_data) const u32* reference_reward_data(){return reference_rewards;}
API(reference_rng_read_data) const u32* reference_rng_read_data(){return reference_rng_reads.data();}
API(reference_rng_read_words) u32 reference_rng_read_words(){return u32(reference_rng_reads.size());}
API(reference_shot_data) const u32* reference_shot_data(){return reference_shots.data();}
API(reference_shot_words) u32 reference_shot_words(){return u32(reference_shots.size());}
API(reference_enemy_data) const u32* reference_enemy_data(){return reference_enemies.data();}
API(reference_enemy_words) u32 reference_enemy_words(){return u32(reference_enemies.size());}
API(reference_phase_data) const u32* reference_phase_data(){return reference_phases.data();}
API(reference_phase_words) u32 reference_phase_words(){return u32(reference_phases.size());}
API(reference_item_data) const u32* reference_item_data(){return reference_items.data();}
API(reference_item_words) u32 reference_item_words(){return u32(reference_items.size());}
API(reference_bullet_data) const u32* reference_bullet_data(){return reference_bullets.data();}
API(reference_bullet_words) u32 reference_bullet_words(){return u32(reference_bullets.size());}
API(reference_beam_failure) const float* reference_beam_failure(){return session.battle->player->shots.th14_beam_failure.data();}

API(reference_area_data) const u32* reference_area_data(){return reference_areas.data();}
API(reference_area_words) u32 reference_area_words(){return u32(reference_areas.size());}

API(reference_id_data) const u32* reference_id_data(){return reference_ids.data();}
API(reference_id_words) u32 reference_id_words(){return u32(reference_ids.size());}
API(reference_next_id) u32 reference_next_id(){return reference_next_id_value;}
API(reference_popup_data) const u32* reference_popup_data(){return reference_popups.data();}
API(reference_popup_cursor) u32 reference_popup_cursor(){return reference_popup_cursor_value;}
