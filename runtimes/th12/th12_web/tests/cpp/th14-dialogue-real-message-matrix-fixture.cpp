#include "../../cpp/game/EnemyAnimations.hpp"
#include <algorithm>
#include "../../cpp/game/Dialogue.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static EnemyAnimations families(manager);static AnmResource resource;static std::vector<AnmVm*> vms;static u32 state[512*22],statuses[16],linked[15],links;static bool alive[16],synchronous;
static u32 bits(float value){u32 result;std::memcpy(&result,&value,4);return result;}
static void capture(){for(u32 i=0;i<vms.size();++i){const auto* vm=vms[i];auto* s=state+i*22;
 s[0]=u32(i32(vm->sprite_index));s[1]=vm->color;s[2]=vm->secondary_color;s[3]=vm->layer;s[4]=u32(vm->timer.current);s[5]=bits(vm->timer.fractional);
 s[6]=bits(vm->script_position.x);s[7]=bits(vm->script_position.y);s[8]=bits(vm->script_position.z);s[9]=bits(vm->scale.x);s[10]=bits(vm->scale.y);s[11]=u32(vm->pending_interrupt);
 s[12]=bits(vm->floats[0]);s[13]=bits(vm->floats[1]);s[14]=bits(vm->texture_scale.x);s[15]=bits(vm->texture_scale.y);
 s[16]=vm->rectangle_columns|(u32(vm->rectangle_rows)<<8);s[17]=vm->flags2&0xa00;s[18]=vm->flags&1;s[19]=vm->instruction?u32(reinterpret_cast<const u8*>(vm->instruction)-reinterpret_cast<const u8*>(vm->script_begin)):0xffffffff;s[20]=vm->parent==vms[0];s[21]=u32(i32(vm->script_index));}}
API(allocate) u8* allocate(u32 n){return new u8[n];}
API(load_resource) i32 load_resource(const u8* p,u32 n){manager.clear();return resource.open(p,n);}
API(begin_family) i32 begin_family(i32 slot,float rate,i32 immediate){manager.clear();manager.rate=rate;resource.templates.reset();if(!manager.prepare_resource(resource,5))return 0;synchronous=immediate;vms.clear();auto* root=manager.create(resource,slot,5,u32(-1));if(!root)return 0;vms.push_back(root);links=0;
 for(auto* node=root->child.next;node;node=node->next){linked[links++]=u32(i32(node->value->script_index));vms.push_back(node->value);}
 std::reverse(vms.begin()+1,vms.end());for(u32 i=0;i<vms.size();++i)alive[i]=true;capture();return 1;}
API(interrupt_family) void interrupt_family(i32 label){if(synchronous)families.interrupt_now(vms[0]->id,label);else families.interrupt(vms[0]->id,i16(label));capture();}
API(step) void step(){for(u32 i=0;i<vms.size();++i){const u32 index=(i+1)%vms.size();statuses[i]=alive[index]?vms[index]->update(manager):1;alive[index]=!statuses[i];}capture();}
API(data) const u32* data(){return state;}
API(status) const u32* status(){return statuses;}
API(chain) const u32* chain(){return linked;}
API(count) u32 count(){return vms.size();}

static AnmResource text_resource;static std::unique_ptr<Dialogue> dialogue;static std::vector<u8> message;
struct Effects:DialogueEffects{bool dialogue_sound(i32)override{return true;}};static Effects effects;
API(begin_dialogue_family) i32 begin_dialogue_family(u32 index,float rate,i32 immediate){
 if(dialogue)dialogue->clear();dialogue.reset();manager.clear();manager.rate=rate;resource.templates.reset();if(!manager.prepare_resource(resource,5))return 0;synchronous=immediate;
 const i32 routes[21][4]={{1,0,1,0},{1,1,1,0},{1,2,1,0},{1,0,2,0},{1,0,20,0},{2,0,2,0},{2,0,20,0},{3,0,2,0},{3,0,20,0},{4,0,2,0},{4,0,20,0},{4,0,2,1},{4,0,20,1},{5,0,2,0},{5,0,20,0},{6,0,2,0},{6,0,20,0},{7,0,2,0},{7,0,20,0},{7,0,2,1},{7,0,2,2}};if(index>=21)return 0;const auto* route=routes[index];
 text_resource={};text_resource.scripts.resize(2);const AnmInstruction stop[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};for(auto& script:text_resource.scripts){script.bytes.resize(sizeof stop);std::memcpy(script.bytes.data(),stop,sizeof stop);}if(!manager.prepare_resource(text_resource,0))return 0;
 message.resize(12);const u32 header[]={1,12,0};std::memcpy(message.data(),header,12);message.push_back(0);message.push_back(0);message.push_back(u8(route[2]));message.push_back(route[2]==1?0:4);if(route[2]!=1){const u32 selection=route[3];const auto* p=reinterpret_cast<const u8*>(&selection);message.insert(message.end(),p,p+4);}const u8 wait[]={0,0,11,4,0x58,2,0,0,0,0,0,0};message.insert(message.end(),wait,wait+sizeof wait);
 i32 file,script;if(route[2]!=1){if(!Dialogue::th14_asset(route[0],route[3],route[2],file,script))return 0;families.resources[file]={&resource,5};}
 dialogue=std::make_unique<Dialogue>(manager,text_resource,resource,text_resource,resource,text_resource,effects);dialogue->stage=route[0];dialogue->character=route[1];dialogue->th14_animations=&families;if(!dialogue->begin(message,0)||dialogue->update(0,0)!=0)return 0;
 const auto handle=route[2]==1?dialogue->state.animations[0]:route[2]==20?dialogue->state.animations[7]:dialogue->th14_enemy_portraits[route[3]];auto* root=manager.find(handle);if(!root)return 0;
 vms.clear();vms.push_back(root);links=0;for(auto* node=root->child.next;node;node=node->next){linked[links++]=u32(i32(node->value->script_index));vms.push_back(node->value);}std::reverse(vms.begin()+1,vms.end());for(u32 i=0;i<vms.size();++i)alive[i]=true;capture();return 1;
}

static u32 lifecycle_ids[512],lifecycle_alive[512],lifecycle_layers[36*513];
static void capture_lifecycle(){capture();for(u32 i=0;i<vms.size();++i){lifecycle_alive[i]=manager.find(lifecycle_ids[i])==vms[i];if(!lifecycle_alive[i])for(u32 j=0;j<22;++j)state[i*22+j]=0;}}
API(begin_lifecycle) i32 begin_lifecycle(u32 resource_index,float rate,i32 immediate){if(!begin_dialogue_family(resource_index,rate,immediate))return 0;for(u32 i=0;i<vms.size();++i)lifecycle_ids[i]=vms[i]->id;capture_lifecycle();return 1;}
API(lifecycle_interrupt) void lifecycle_interrupt(i32 label){interrupt_family(label);capture_lifecycle();}
API(lifecycle_step) i32 lifecycle_step(){if(!manager.update(false)||!manager.update(true))return 0;capture_lifecycle();
 for(u32 layer=0;layer<36;++layer){auto* s=lifecycle_layers+layer*513;u32 n=0;for(auto* vm=manager.layer_first(layer);vm;vm=vm->draw_next){for(u32 i=0;i<vms.size();++i)if(vm==vms[i]){if(n>=16)return 0;s[++n]=i;break;}}s[0]=n;}return 1;}
API(lifecycle_alive_data) const u32* lifecycle_alive_data(){return lifecycle_alive;}
API(lifecycle_layer_data) const u32* lifecycle_layer_data(){return lifecycle_layers;}

static u32 sprite_state[512*38];
static void capture_sprite(){for(u32 i=0;i<vms.size();++i){auto* s=sprite_state+i*38;if(!lifecycle_alive[i]){for(u32 j=0;j<38;++j)s[j]=0;continue;}std::memcpy(s,state+i*22,22*sizeof(u32));auto& vm=*vms[i];s[22]=bits(vm.sprite_size.x);s[23]=bits(vm.sprite_size.y);for(u32 j=0;j<4;++j){s[24+j*2]=bits(vm.uv[j].x);s[25+j*2]=bits(vm.uv[j].y);}s[32]=bits(vm.sprite_matrix.m[0]);s[33]=bits(vm.sprite_matrix.m[5]);s[34]=bits(vm.uv_matrix.m[0]);s[35]=bits(vm.uv_matrix.m[5]);s[36]=bits(vm.transform_matrix.m[0]);s[37]=bits(vm.transform_matrix.m[5]);}}
API(begin_sprite) i32 begin_sprite(u32 resource_index,float rate,i32 immediate){if(!begin_lifecycle(resource_index,rate,immediate))return 0;capture_sprite();return 1;}
API(sprite_interrupt) void sprite_interrupt(i32 label){lifecycle_interrupt(label);capture_sprite();}
API(sprite_step) i32 sprite_step(){if(!lifecycle_step())return 0;capture_sprite();return 1;}
API(sprite_data) const u32* sprite_data(){return sprite_state;}

static std::unique_ptr<Dialogue> constructor_dialogue;static u32 constructor_state[10];
API(begin_constructor) i32 begin_constructor(float rate,i32 immediate){
 if(constructor_dialogue)constructor_dialogue->clear();constructor_dialogue.reset();manager.clear();manager.rate=rate;resource.templates.reset();if(!manager.prepare_resource(resource,0))return 0;synchronous=immediate;
 constructor_dialogue=std::make_unique<Dialogue>(manager,resource,resource,resource,resource,resource,effects);std::vector<u8> bytes(24);const u32 table[]={1,12,0};std::memcpy(bytes.data(),table,12);bytes[14]=11;bytes[15]=4;bytes[16]=0x58;bytes[17]=2;if(!constructor_dialogue->begin(bytes,0))return 0;
 vms.clear();for(u32 i=0;i<4;++i){auto* line=manager.find(constructor_dialogue->state.animations[3+i]);if(!line)return 0;vms.push_back(line);lifecycle_ids[i]=line->id;constructor_state[6+i]=line->draw_callback!=nullptr;}links=0;
 constructor_state[0]=bits(constructor_dialogue->text_pair_194.x);constructor_state[1]=bits(constructor_dialogue->text_pair_194.y);constructor_state[2]=bits(constructor_dialogue->th14_text_width);for(u32 i=0;i<3;++i)constructor_state[3+i]=constructor_dialogue->state.colors[i];capture_lifecycle();capture_sprite();return 1;
}
API(constructor_interrupt) void constructor_interrupt(i32 label){for(u32 i=0;i<4;++i){if(synchronous)families.interrupt_now(lifecycle_ids[i],label);else families.interrupt(lifecycle_ids[i],i16(label));}capture_lifecycle();capture_sprite();}
API(constructor_step) i32 constructor_step(){return sprite_step();}
API(constructor_data) const u32* constructor_data(){return constructor_state;}

static AnmResource message_front,message_player,message_enemy,message_logo,message_enemy2,message_enemy3;static u32 message_texture_bases[7],message_program_start;
#include "../../cpp/game/AnmRenderer.hpp"
using namespace touhou::graphics;
struct PortraitGraphics final:ZunGraphics {
 PipelineState state{};u32 handle=0;bool valid=true;std::vector<u32> quads,materials;
 PipelineState& pipeline()override{return state;}
 u32 texture(const AnmResource& file,u32 index)override{return index+message_texture_bases[&file==&message_front?1:&file==&message_player?2:&file==&message_enemy?3:&file==&message_logo?4:&file==&message_enemy2?5:&file==&message_enemy3?6:0]+1;}
 void bind_texture(u32 h)override{handle=h;}
 void set_layout(VertexLayout layout)override{if(layout!=VertexLayout::ScreenColorUv)valid=false;}
 void set_matrix(MatrixKind,const Matrix4&)override{valid=false;}
 void triangles(u32 count,const void* data,u32 stride)override{
  if(stride!=28||count%2){valid=false;return;}const auto* words=static_cast<const u32*>(data);
  for(u32 quad=0;quad<count/2;++quad){for(u32 i:{0,1,2,5})for(u32 f=0;f<7;++f)quads.push_back(words[(quad*6+i)*7+f]);
   const u32 a[]={handle,state.depthWrite,u32(state.sourceBlend)+1,u32(state.destinationBlend)+1,u32(state.blendEquation)+1,state.minFilter==Filter::Nearest?1u:2u,state.magFilter==Filter::Nearest?1u:2u,state.addressU==Address::Repeat?1u:state.addressU==Address::Mirror?2u:3u,state.addressV==Address::Repeat?1u:state.addressV==Address::Mirror?2u:3u};materials.insert(materials.end(),a,a+9);}
 }
 void primitives(Topology,u32,const void*,u32)override{valid=false;}
};
static PortraitGraphics portrait_graphics;static AnmRenderer portrait_renderer(portrait_graphics);
API(begin_geometry) i32 begin_geometry(u32 index,float rate,i32 immediate){portrait_renderer.invalidate();portrait_graphics.state={};portrait_graphics.handle=0;portrait_graphics.valid=true;portrait_graphics.quads.clear();portrait_graphics.materials.clear();portrait_renderer.viewport={0,0,640,480,0,1};portrait_renderer.offset={0,0};portrait_renderer.tint_enabled=false;return begin_sprite(index,rate,immediate);}
API(geometry_step) i32 geometry_step(){if(!sprite_step())return 0;portrait_graphics.quads.clear();portrait_graphics.materials.clear();for(u32 layer=0;layer<36;++layer)if(portrait_renderer.draw_layer(manager.layer_first(layer))!=1)return 0;portrait_renderer.flush();capture_sprite();return portrait_graphics.valid;}
API(geometry_count) u32 geometry_count(){return portrait_graphics.quads.size()/28;}
API(geometry_data) const u32* geometry_data(){return portrait_graphics.quads.data();}
API(geometry_materials) const u32* geometry_materials(){return portrait_graphics.materials.data();}

API(begin_constructor_geometry) i32 begin_constructor_geometry(float rate,i32 immediate){portrait_renderer.invalidate();portrait_graphics.state={};portrait_graphics.handle=0;portrait_graphics.valid=true;portrait_graphics.quads.clear();portrait_graphics.materials.clear();portrait_renderer.viewport={0,0,640,480,0,1};portrait_renderer.offset={0,0};portrait_renderer.tint_enabled=false;return begin_constructor(rate,immediate);}
API(constructor_geometry_step) i32 constructor_geometry_step(){return geometry_step();}

static std::vector<u8> message_bytes;static std::vector<u32> message_writes,message_world;static u32 message_state[21],message_sounds,creation_cursor;
struct MessageEffects:DialogueEffects {
 bool dialogue_text(const DialogueText& r)override{auto* vm=manager.find(r.animation);if(!vm||!constructor_dialogue)return false;u32 line=0;while(line<4&&constructor_dialogue->state.animations[3+line]!=r.animation)++line;if(line==4)return false;message_writes.insert(message_writes.end(),{line,r.color,u32(r.style),u32(r.offset),u32(r.font),vm->flags2&0x800,u32(r.bytes.size())});for(u8 b:r.bytes)message_writes.push_back(b);vm->flags|=1;return true;}
 bool dialogue_sound(i32 id)override{++message_sounds;message_world.insert(message_world.end(),{4,u32(id)});return true;}bool dialogue_music()override{message_world.push_back(1);return true;}bool dialogue_fade(float value)override{message_world.insert(message_world.end(),{2,bits(value)});return true;}bool dialogue_stage_complete()override{message_world.push_back(3);return true;}
};static MessageEffects message_effects;
static bool collect_message_vms(){while(creation_cursor<anm_creation_count()){const u32 id=u32(anm_creation_value(creation_cursor++,5));auto* vm=manager.find(id);if(!vm||vms.size()>=512)return false;lifecycle_ids[vms.size()]=id;vms.push_back(vm);}return true;}
static void capture_message(){const auto& s=constructor_dialogue->state;const u32 words[]={s.flags,u32(s.release_signal),u32(s.next_line),u32(s.lines_initialized),u32(s.speaker),s.colors[0],s.colors[1],s.colors[2],bits(constructor_dialogue->text_pair_194.x),bits(constructor_dialogue->text_pair_194.y),bits(constructor_dialogue->th14_text_width),u32(constructor_dialogue->th14_text_layout),u32(s.elapsed.current),bits(s.elapsed.fractional),u32(s.time.current),bits(s.time.fractional),u32(s.wait.current),bits(s.wait.fractional),u32(s.instruction-(message_bytes.data()+message_program_start)),constructor_dialogue->th14_text_background!=0,message_sounds};std::memcpy(message_state,words,sizeof words);capture_lifecycle();capture_sprite();
 for(u32 layer=0;layer<36;++layer){auto* out=lifecycle_layers+layer*513;u32 n=0;for(auto* vm=manager.layer_first(layer);vm;vm=vm->draw_next){for(u32 i=0;i<vms.size();++i)if(vm==vms[i]&&vm->id==lifecycle_ids[i]){out[++n]=i;break;}}out[0]=n;}}
API(load_message_front) i32 load_message_front(const u8* p,u32 n){return message_front.open(p,n);}
API(begin_message_scene) i32 begin_message_scene(float rate,u32 stage,u32 character,i32 entry,const u8* code,u32 size){if(constructor_dialogue)constructor_dialogue->clear();constructor_dialogue.reset();manager.clear();manager.rate=rate;resource.templates.reset();message_front.templates.reset();message_player.templates.reset();message_enemy.templates.reset();message_logo.templates.reset();if(!manager.prepare_resource(resource,0)||!manager.prepare_resource(message_front,5)||!manager.prepare_resource(message_player,7)||!manager.prepare_resource(message_enemy,11)||!manager.prepare_resource(message_logo,6))return 0;if(stage==4||stage==7){message_enemy2.templates.reset();if(!manager.prepare_resource(message_enemy2,12))return 0;}if(stage==7){message_enemy3.templates.reset();if(!manager.prepare_resource(message_enemy3,13))return 0;}vms.clear();creation_cursor=anm_creation_count();message_writes.clear();message_sounds=0;portrait_renderer.invalidate();portrait_graphics.state={};portrait_graphics.handle=0;portrait_graphics.valid=true;portrait_graphics.quads.clear();portrait_graphics.materials.clear();portrait_renderer.viewport={0,0,640,480,0,1};portrait_renderer.offset={0,0};portrait_renderer.tint_enabled=false;
 message_bytes.assign(code,code+size);if(entry<0||u32(entry)>=size/8)return 0;std::memcpy(&message_program_start,code+4+entry*8,4);constructor_dialogue=std::make_unique<Dialogue>(manager,resource,message_player,message_front,message_enemy,message_logo,message_effects);if(!constructor_dialogue->begin(message_bytes,entry)||!collect_message_vms())return 0;constructor_dialogue->stage=stage;constructor_dialogue->character=character;constructor_dialogue->th14_animations=&families;families.resources[3]={&message_enemy,11};families.resources[4]={&message_enemy2,12};families.resources[5]={&message_enemy3,13};capture_message();return 1;}
API(message_scene_step) i32 message_scene_step(u32 held,u32 pressed){message_writes.clear();message_world.clear();const i32 result=constructor_dialogue->update(held,pressed);if(result<0)return result;if(!result)constructor_dialogue->state.elapsed.tick();if(!collect_message_vms()||!manager.update(false)||!manager.update(true))return -3;portrait_graphics.quads.clear();portrait_graphics.materials.clear();for(u32 layer=0;layer<36;++layer)if(portrait_renderer.draw_layer(manager.layer_first(layer))!=1)return -4;portrait_renderer.flush();capture_message();return portrait_graphics.valid?result:-5;}
API(message_scene_state) const u32* message_scene_state(){return message_state;}
API(message_scene_writes) const u32* message_scene_writes(){return message_writes.data();}
API(message_scene_write_words) u32 message_scene_write_words(){return message_writes.size();}
API(message_scene_error) const char* message_scene_error(){return constructor_dialogue?constructor_dialogue->error.c_str():"not initialized";}

API(load_real_scene_resource) i32 load_real_scene_resource(u32 index,const u8* p,u32 n,u32 texture_base){AnmResource* files[]={&resource,&message_front,&message_player,&message_enemy,&message_logo,&message_enemy2,&message_enemy3};if(index>=7)return 0;if(index==0){if(constructor_dialogue)constructor_dialogue->clear();constructor_dialogue.reset();manager.clear();}message_texture_bases[index]=texture_base;return files[index]->open(p,n);}

API(message_scene_effects) const u32* message_scene_effects(){return message_world.data();}
API(message_scene_effect_words) u32 message_scene_effect_words(){return message_world.size();}

API(message_scene_active) u32 message_scene_active(){return constructor_dialogue&&constructor_dialogue->active;}
