// Bounded read-only pre-Player snapshots. No original values enter the engine.
#include "th14-supervisor-resource-clock-fixture-nov05.cpp"
namespace shot_lifetime_observer {
constexpr u32 stride=96;
static bool installed=false,enabled=false;
static u32 callback=0,stage=0,frame=0,captures=0;
static std::vector<u32> words;
static void(*previous)(const GameBattle&)=nullptr;
bool wanted(u32 s,u32 f){
 if(s==2){for(u32 at:{2144u,5511u,5515u,6286u,6291u,6298u})if(f+2>=at&&f<=at+2)return true;}
 return s==3&&((f>=1475&&f<=1482)||(f>=2081&&f<=2098));
}
void capture(const GameBattle& battle){
 const u32 s=u32(battle.resources.stage_number),f=u32(battle.control_frame());
 if(!enabled||!battle.player||!wanted(s,f))return;
 callback=public_player_observations;stage=s;frame=f;++captures;words.clear();words.reserve(256*stride);
 const auto& space=battle.animations.render_space;
 for(u32 slot=0;slot<256;++slot){
  const auto& shot=battle.player->shots.at(slot);u32 row[stride]{};
  row[0]=slot;row[1]=u32(shot.state);row[2]=shot.animation;row[3]=shot.extra_animation;
  row[4]=u32(shot.timer.previous);row[5]=u32(shot.timer.current);row[6]=float_bits(shot.timer.fractional);
  row[7]=shot.th14_shot_flags;row[8]=shot.th14_area_slot;row[9]=u32(shot.damage);
  row[10]=u32(shot.hit_last_frame);row[11]=u32(shot.hit_this_frame);
  const float motion[]={shot.movement.position.x,shot.movement.position.y,shot.movement.position.z,
   shot.movement.velocity.x,shot.movement.velocity.y,shot.movement.speed,shot.movement.angle};
  for(u32 i=0;i<7;++i)row[12+i]=float_bits(motion[i]);
  // Inactive slots can retain stale specification pointers. Never dereference them.
  if(shot.state&&shot.spec){
   const auto& spec=*shot.spec;row[19]=spec.type;row[20]=spec.option;row[21]=u32(spec.spawn);
   row[22]=u32(spec.update);row[23]=spec.extra_callback;row[24]=u32(spec.animation);
   if(const auto* vm=battle.animations.find(shot.animation)){
    row[25]=1;row[26]=vm->id;row[27]=vm->file_index;row[28]=u32(vm->script_index);
    row[29]=vm->flags;row[30]=vm->flags2;row[31]=u32(vm->pending_interrupt);
    row[32]=u32(vm->timer.previous);row[33]=u32(vm->timer.current);row[34]=float_bits(vm->timer.fractional);
    row[35]=u32(vm->age.current);row[36]=vm->parent?vm->parent->id:0;row[37]=u32(vm->sprite_index);
    row[38]=vm->drawing_mode();row[39]=vm->instruction&&vm->script_begin?u32(uintptr_t(vm->instruction)-uintptr_t(vm->script_begin)):~0u;
    const float geometry[]={vm->position.x,vm->position.y,vm->position.z,vm->script_position.x,vm->script_position.y,vm->script_position.z,
     vm->child_position.x,vm->child_position.y,vm->child_position.z,vm->rotation.z,vm->scale.x,vm->scale.y,
     vm->extra_scale.x,vm->extra_scale.y,vm->sprite_size.x,vm->sprite_size.y,vm->pivot.x,vm->pivot.y};
    for(u32 i=0;i<18;++i)row[40+i]=float_bits(geometry[i]);
    row[58]=u32(vm->random_bound);row[59]=float_bits(vm->random_scale.x);row[60]=float_bits(vm->random_scale.y);
    if(vm->parent){const auto& p=*vm->parent;const float values[]={p.scale.x,p.scale.y,p.extra_scale.x,p.extra_scale.y,p.rotation.z};for(u32 i=0;i<5;++i)row[61+i]=float_bits(values[i]);}
    // This const helper writes only the local output array. It does not call
    // geometry_mode1_call or alter the emulated native-stack scratch state.
    Vec3 quad[4]{};row[66]=u32(anm_quad_positions(*vm,quad,space));
    bool visible=shot.timer.current<10;
    if(row[66])for(u32 i=0;i<4;++i){const auto p=quad[i];row[68+i*3]=float_bits(p.x);row[69+i*3]=float_bits(p.y);row[70+i*3]=float_bits(p.z);
     const float left=space.play_origin.x-192.f,top=space.play_origin.y;
     if(p.x>left&&p.x<left+384.f&&p.y>top&&p.y<top+448.f)visible=true;
    }
    row[67]=u32(visible);for(u32 i=0;i<4;++i){row[80+i]=u32(vm->integers[i]);row[84+i]=float_bits(vm->floats[i]);}
    row[88]=vm->color;row[89]=vm->secondary_color;row[90]=vm->trace_count;
    if(vm->trace_count){const auto& t=vm->trace[(vm->trace_count-1)&(anm_trace_size-1)];row[91]=t.opcode;row[92]=t.offset;}
    row[94]=vm->th13_native_flags;row[95]=u32(vm->age.previous);
   }
  }
  words.insert(words.end(),std::begin(row),std::end(row));
 }
}
}
API(shot_lifetime_install) u32 shot_lifetime_install(u32 enabled){
 using namespace shot_lifetime_observer;
 if(installed||!session.battle||!session.battle->before_player_update)return 0;
 shot_lifetime_observer::previous=session.battle->before_player_update;
 shot_lifetime_observer::enabled=enabled!=0;
 session.battle->before_player_update=[](const GameBattle& b){shot_lifetime_observer::previous(b);shot_lifetime_observer::capture(b);};installed=true;return 1;
}
API(shot_lifetime_meta) u32 shot_lifetime_meta(u32 n){
 using namespace shot_lifetime_observer;const u32 values[]={callback,stage,frame,stride,u32(words.size()/stride),captures};return n<6?values[n]:~0u;
}
API(shot_lifetime_data) const u32* shot_lifetime_data(){return shot_lifetime_observer::words.data();}
