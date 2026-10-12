#include "th14-custom-replay-reference-fixture.cpp"
API(natural_shot_detail) u32 natural_shot_detail(u32 slot,u32 field){
 if(!session.battle||!session.battle->player||slot>=256)return 0;
 const auto& s=session.battle->player->shots.at(slot);const auto* p=s.spec;
 if(!p)return 0;
 const u32 values[]{u32(p->type),u32(p->option),float_word(p->angle),float_word(p->speed),u32(p->spawn),u32(p->update),p->extra_callback,s.th14_shot_flags,s.th14_target_id,u32(s.th14_area_slot),float_word(s.movement.angle),u32(s.timer.current),s.th14_area_flags};
 return field<13?values[field]:field<21?p->native_tail[field-13]:0;
}
