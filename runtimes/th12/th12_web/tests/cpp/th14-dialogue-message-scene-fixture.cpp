#include "th14-dialogue-constructor-lifecycle-fixture.cpp"
static AnmResource message_front;
#include "../../cpp/game/AnmRenderer.hpp"
using namespace touhou::graphics;
struct PortraitGraphics final:ZunGraphics {
 PipelineState state{};u32 handle=0;bool valid=true;std::vector<u32> quads,materials;
 PipelineState& pipeline()override{return state;}
 u32 texture(const AnmResource& file,u32 index)override{return index+(&file==&message_front?5:1);}
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

static std::vector<u8> message_bytes;static std::vector<u32> message_writes;static u32 message_state[21],message_sounds,creation_cursor;
struct MessageEffects:DialogueEffects {
 bool dialogue_text(const DialogueText& r)override{auto* vm=manager.find(r.animation);if(!vm||!constructor_dialogue)return false;u32 line=0;while(line<4&&constructor_dialogue->state.animations[3+line]!=r.animation)++line;if(line==4)return false;message_writes.insert(message_writes.end(),{line,r.color,u32(r.style),u32(r.offset),u32(r.font),vm->flags2&0x800,u32(r.bytes.size())});for(u8 b:r.bytes)message_writes.push_back(b);vm->flags|=1;return true;}
 bool dialogue_sound(i32)override{++message_sounds;return true;}
};static MessageEffects message_effects;
static bool collect_message_vms(){while(creation_cursor<anm_creation_count()){const u32 id=u32(anm_creation_value(creation_cursor++,5));auto* vm=manager.find(id);if(!vm||vms.size()>=16)return false;lifecycle_ids[vms.size()]=id;vms.push_back(vm);}return true;}
static void capture_message(){const auto& s=constructor_dialogue->state;const u32 words[]={s.flags,u32(s.release_signal),u32(s.next_line),u32(s.lines_initialized),u32(s.speaker),s.colors[0],s.colors[1],s.colors[2],bits(constructor_dialogue->text_pair_194.x),bits(constructor_dialogue->text_pair_194.y),bits(constructor_dialogue->th14_text_width),u32(constructor_dialogue->th14_text_layout),u32(s.elapsed.current),bits(s.elapsed.fractional),u32(s.time.current),bits(s.time.fractional),u32(s.wait.current),bits(s.wait.fractional),u32(s.instruction-(message_bytes.data()+12)),constructor_dialogue->th14_text_background!=0,message_sounds};std::memcpy(message_state,words,sizeof words);capture_lifecycle();capture_sprite();
 for(u32 layer=0;layer<36;++layer){auto* out=lifecycle_layers+layer*17;u32 n=0;for(auto* vm=manager.layer_first(layer);vm;vm=vm->draw_next){for(u32 i=0;i<vms.size();++i)if(vm==vms[i]){out[++n]=i;break;}}out[0]=n;}}
API(load_message_front) i32 load_message_front(const u8* p,u32 n){return message_front.open(p,n);}
API(begin_message_scene) i32 begin_message_scene(float rate,u32 flags,const u8* code,u32 size){if(constructor_dialogue)constructor_dialogue->clear();constructor_dialogue.reset();manager.clear();manager.rate=rate;resource.templates.reset();message_front.templates.reset();if(!manager.prepare_resource(resource,0)||!manager.prepare_resource(message_front,5))return 0;vms.clear();creation_cursor=anm_creation_count();message_writes.clear();message_sounds=0;portrait_renderer.invalidate();portrait_graphics.state={};portrait_graphics.handle=0;portrait_graphics.valid=true;portrait_graphics.quads.clear();portrait_graphics.materials.clear();portrait_renderer.viewport={0,0,640,480,0,1};portrait_renderer.offset={0,0};portrait_renderer.tint_enabled=false;
 message_bytes.resize(12);const u32 header[]={1,12,0};std::memcpy(message_bytes.data(),header,12);message_bytes.insert(message_bytes.end(),code,code+size);constructor_dialogue=std::make_unique<Dialogue>(manager,resource,resource,message_front,message_front,resource,message_effects);if(!constructor_dialogue->begin(message_bytes,0)||!collect_message_vms())return 0;constructor_dialogue->state.flags=flags;capture_message();return 1;}
API(message_scene_step) i32 message_scene_step(){message_writes.clear();const i32 result=constructor_dialogue->update(0,0);if(result<0)return result;if(!result)constructor_dialogue->state.elapsed.tick();if(!collect_message_vms()||!manager.update(false)||!manager.update(true))return -3;portrait_graphics.quads.clear();portrait_graphics.materials.clear();for(u32 layer=0;layer<36;++layer)if(portrait_renderer.draw_layer(manager.layer_first(layer))!=1)return -4;portrait_renderer.flush();capture_message();return portrait_graphics.valid?result:-5;}
API(message_scene_state) const u32* message_scene_state(){return message_state;}
API(message_scene_writes) const u32* message_scene_writes(){return message_writes.data();}
API(message_scene_write_words) u32 message_scene_write_words(){return message_writes.size();}
API(message_scene_error) const char* message_scene_error(){return constructor_dialogue?constructor_dialogue->error.c_str():"not initialized";}
