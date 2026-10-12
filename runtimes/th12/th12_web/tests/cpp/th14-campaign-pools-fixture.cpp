#include "th14-campaign-replay-fixture.cpp"
// Serialize explicit numerical gameplay fields, never addresses, padding,
// ANM IDs or render state. The JS driver hashes these bytes per frame.
static std::vector<u32> campaign_pool;
static u32 campaign_pool_rows=0;
static void pool_words(std::initializer_list<u32> values){campaign_pool.insert(campaign_pool.end(),values);}
static void pool_vec(Vec3 v){pool_words({float_bits(v.x),float_bits(v.y),float_bits(v.z)});}
static void pool_timer(const Timer& t){pool_words({u32(t.previous),u32(t.current),float_bits(t.fractional)});}
static void pool_motion(const Movement& m){pool_vec(m.position);pool_vec(m.velocity);pool_words({float_bits(m.speed),float_bits(m.angle),float_bits(m.radius),float_bits(m.radial_velocity),float_bits(m.ellipse_angle),float_bits(m.ellipse_ratio),m.flags});}
API(campaign_pool_read) const u32* campaign_pool_read(u32 kind){
    campaign_pool.clear();campaign_pool_rows=0;campaign_pool.push_back(kind);
    if(!session.battle)return campaign_pool.data();const auto& b=*session.battle;
    if(kind==0)for(auto* s=b.bullets.first_th14();s;s=s->th14_active_next){
        ++campaign_pool_rows;pool_words({u32(s->state),s->flags,u32(s->collision_delay)});pool_vec(s->position);pool_vec(s->velocity);
        pool_words({float_bits(s->speed),float_bits(s->angle),float_bits(s->hitbox.x),float_bits(s->hitbox.y),u32(u16(s->sprite))|(u32(u16(s->color))<<16),s->active_transforms,u32(s->transform_index),u32(s->th14_script_state),u32(s->th14_step_mode),u32(s->th14_step_extra),float_bits(s->th14_size_current),float_bits(s->th14_size)});
        pool_timer(s->lifetime);pool_timer(s->auxiliary_timer);pool_timer(s->th14_wait_timer);pool_timer(s->th14_freeze_timer);
    }
    if(kind==1&&b.player)for(u32 n=0;n<256;++n){const auto& s=b.player->shots.at(n);if(!s.state)continue;
        ++campaign_pool_rows;pool_words({n,u32(s.state),u32(s.damage),u32(s.hit_this_frame),u32(s.hit_last_frame),s.th14_target_id,s.th14_area_flags,s.th14_was_focused,s.th14_shot_flags,float_bits(s.acceleration),float_bits(s.th14_area_radius),float_bits(s.th14_area_growth),float_bits(s.th14_saved_speed),float_bits(s.th14_beam_length),u32(s.th14_homing_target_retired)});
        pool_motion(s.movement);pool_timer(s.timer);pool_timer(s.th14_steering);pool_timer(s.th14_decay);pool_vec(s.th14_attachment_offset);
    }
    if(kind==2)for(auto* node=b.enemies.first;node;node=node->next){const auto& s=node->value->state;
        ++campaign_pool_rows;pool_words({u32(s.instance_id),s.flags,u32(s.health),u32(s.max_health),u32(s.damage_flash),float_bits(s.hitbox.x),float_bits(s.hitbox.y),float_bits(s.collision_box.x),float_bits(s.collision_box.y),u32(s.boss_slot)});
        pool_motion(s.current);pool_motion(s.absolute);pool_motion(s.relative);pool_timer(s.lifetime);pool_timer(s.timer_2bc);pool_timer(s.damage_immunity);pool_timer(s.collision_immunity);
        pool_words({u32(s.drops.primary)});for(u32 i=0;i<19;++i)campaign_pool.push_back(u32(s.drops.counts[i]));
        for(const auto& interrupt:s.interrupts)pool_words({u32(interrupt.health),u32(interrupt.time)});
    }
    if(kind==3)for(u32 n=0;n<ItemManager::capacity;++n){const auto& s=b.items.at(n);if(!s.state)continue;
        ++campaign_pool_rows;pool_words({n,u32(s.state),u32(s.type),u32(s.display_type),s.th14_generation,float_bits(s.attraction_speed),u32(s.delay)});pool_vec(s.position);pool_vec(s.velocity);pool_timer(s.lifetime);
    }
    if(kind==4)for(auto* s=b.lasers.first();s;s=s->next){
        ++campaign_pool_rows;pool_words({u32(s->state),u32(s->type),u32(s->id),u32(s->marked),u32(s->rectangle_enabled),u32(s->transform_index),s->active_transforms,u32(s->protection),u32(u16(s->sprite))|(u32(u16(s->color))<<16)});
        pool_vec(s->position);pool_vec(s->velocity);pool_words({float_bits(s->angle),float_bits(s->length),float_bits(s->width),float_bits(s->speed),float_bits(s->offset)});pool_timer(s->lifetime);pool_timer(s->graze_timer);pool_timer(s->offscreen_timer);
        if(s->type==2){const auto& curve=*reinterpret_cast<const Th14LaserCurve*>(s);pool_timer(curve.curve_timer);pool_words({u32(curve.path.nodes.size()),u32(curve.path.samples.size())});for(const auto& sample:curve.path.samples){pool_vec(sample.position);pool_vec(sample.auxiliary);pool_words({float_bits(sample.angle),float_bits(sample.speed)});}}
    }
    if(kind==5&&b.player)for(u32 n=0;n<256;++n){const auto* a=b.player->shots.th14_bomb_area(n);if(!(a->flags&1))continue;
        ++campaign_pool_rows;pool_words({n,a->flags,float_bits(a->radius),float_bits(a->angle),float_bits(a->size.x),float_bits(a->size.y),u32(a->damage),u32(a->total),u32(a->maximum),u32(a->period),a->stamp,u32(a->callback),u32(a->moving)});pool_vec(a->position);pool_timer(a->timer);
    }
    return campaign_pool.data();
}
API(campaign_pool_words) u32 campaign_pool_words(){return campaign_pool.size();}
API(campaign_pool_count) u32 campaign_pool_count(){return campaign_pool_rows;}
