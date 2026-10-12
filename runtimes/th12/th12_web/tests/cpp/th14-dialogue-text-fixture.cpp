#include "../../cpp/game/Dialogue.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;
static AnmResource text,front;
static std::vector<u32> output;
static Dialogue* current;
struct Effects:DialogueEffects{
 bool dialogue_text(const DialogueText& r)override{
  u32 slot=0;for(u32 i=3;i<7;++i)if(current->state.animations[i]==r.animation)slot=i;
  const auto* vm=manager.find(r.animation);
  output.insert(output.end(),{slot,r.color,u32(r.offset),u32(r.font),u32(r.style),vm->flags2&0x800,u32(r.bytes.size())});
  for(u8 c:r.bytes)output.push_back(c);return true;
 }
};
static Effects effects;
API(allocate) u8* allocate(u32 n){return new u8[n];}
API(load_front) i32 load_front(const u8* p,u32 n){if(!front.open(p,n))return 0;return manager.prepare_resource(front,5);}
API(run) i32 run(i32 op,i32 speaker,u32 flags,i32 line,i32 initialized,i32 profile){
 manager.clear();text={};text.scripts.resize(4);
 for(auto& s:text.scripts){const AnmInstruction h[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};s.bytes.resize(16);std::memcpy(s.bytes.data(),h,16);}
 Dialogue d(manager,text,text,front,front,front,effects);current=&d;
 const char* profiles[]={"Long text 012345","\x93\x8c\x95\xfb\x92\x6e\x97\xec","|3,2,ruby","A",""};
 std::vector<u8> message(12);const u32 table[]={1,12,0};std::memcpy(message.data(),table,12);
 const std::string plain=profiles[profile];message.insert(message.end(),{0,0,u8(op),u8(plain.size()+1)});
 u8 key=0x77,step=7;for(u32 i=0;i<=plain.size();++i){message.push_back(u8(i<plain.size()?plain[i]:0)^key);key=u8(key+step);step=u8(step+16);}
 if(op==28){const float pairs[][2]={{112,288},{224,144},{-0.f,0.f},{.125f,-3.75f},{-112,288}};message.resize(24);message[15]=8;std::memcpy(message.data()+16,pairs[profile],8);}
 message.insert(message.end(),{1,0,0,0});if(!d.begin(message,0))return -3;
 for(u32 n=0;n<4;++n){auto* vm=manager.find(d.state.animations[3+n]);vm->flags2&=~0x800u;vm->pending_interrupt=0;vm->position={float(50+n),float(70+n),0};}
 auto* old=manager.create(front,216,5,22);if(!old)return -4;d.th14_text_background=old->id;
 d.state.speaker=speaker;d.state.flags=flags;d.state.next_line=line;d.state.lines_initialized=initialized;d.text_pair_194={112,288};d.th14_text_width=60;
 d.state.colors[0]=0xf8f08f;d.state.colors[1]=0x8088ff;d.state.colors[2]=0xd8d8d8;
 output.clear();const auto status=d.update(0,0);if(status<0)return status;
 output.push_back(0xffffffff);
 output.insert(output.end(),{u32(d.state.next_line),u32(d.state.lines_initialized),float_bits(d.th14_text_width),u32(d.th14_text_layout),float_bits(d.text_pair_194.x),float_bits(d.text_pair_194.y)});
 for(u32 n=0;n<4;++n){const auto* vm=manager.find(d.state.animations[3+n]);output.insert(output.end(),{float_bits(vm->position.x),float_bits(vm->position.y),float_bits(vm->position.z),u32(vm->pending_interrupt)});}
 auto* panel=manager.find(d.th14_text_background);output.push_back(panel&&panel!=old);
 if(panel&&panel!=old){output.insert(output.end(),{u32(panel->script_index),float_bits(panel->position.x),float_bits(panel->position.y),float_bits(panel->position.z)});for(i32 script:{168+d.th14_text_layout,200+d.th14_text_layout}){u32 value=0xffffffff;for(auto* node=panel->child.next;node;node=node->next)if(node->value->script_index==script)value=float_bits(node->value->floats[0]);output.push_back(value);}}
 output.push_back(old->flags2&0x20);output.push_back(old->child.next?old->child.next->value->flags2&0x20:0xffffffff);
 output.push_back(panel!=nullptr);
 return status;
}
API(words) u32 words(){return u32(output.size());}
API(data) const u32* data(){return output.data();}
API(initialize) i32 initialize(){
 manager.clear();text={};text.scripts.resize(4);for(auto& s:text.scripts){const AnmInstruction h[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};s.bytes.resize(16);std::memcpy(s.bytes.data(),h,16);}
 Dialogue d(manager,text,text,front,front,front,effects);current=&d;std::vector<u8> message(16);const u32 table[]={1,12,0};std::memcpy(message.data(),table,12);message[12]=1;
 if(!d.begin(message,0))return 0;output.clear();for(u32 i=3;i<7;++i){auto* vm=manager.find(d.state.animations[i]);output.insert(output.end(),{u32(vm->script_index),u32(vm->pending_interrupt),u32(vm->rectangle_columns)|(u32(vm->rectangle_rows)<<8),vm->flags2&0xa00,u32(vm->draw_callback!=nullptr)});}
 output.insert(output.end(),{d.state.colors[0],d.state.colors[1],d.state.colors[2],float_bits(d.text_pair_194.x),float_bits(d.text_pair_194.y),float_bits(d.th14_text_width)});d.clear();return 1;
}
API(position_callback) i32 position_callback(i32 speaker,i32 layout,float display,float sx,i32 sample){
 if(!initialize())return 0;manager.clear();Dialogue d(manager,text,text,front,front,front,effects);current=&d;std::vector<u8> message(16);const u32 table[]={1,12,0};std::memcpy(message.data(),table,12);message[12]=1;if(!d.begin(message,0))return 0;
 auto* panel=manager.create(front,216+layout,5,22);if(!panel)return 0;AnmVm* child=nullptr;for(auto* node=panel->child.next;node;node=node->next)if(node->value->script_index==168+layout)child=node->value;if(!child)return 0;
 panel->flags2=child->flags2=0x100000;panel->parent=nullptr;child->parent=panel;panel->position={224+sample*.25f,288-sample*3.75f,0};panel->script_position={-48,-2,0};panel->child_position={0,0,0};child->position={0,0,0};child->script_position={96,sample*.125f,.25f};child->child_position={sample*.5f,2,.125f};child->scale={sx,1};
 d.state.speaker=speaker;d.th14_text_background=panel->id;d.th14_text_layout=layout;manager.render_space.scale=display;auto* line=manager.find(d.state.animations[3]);line->draw_callback(*line);output={float_bits(line->position.x),float_bits(line->position.y),float_bits(line->position.z)};d.clear();manager.render_space.scale=1;return 1;
}
API(speaker_command) i32 speaker_command(i32 op,i32 selection,u32 flags,i32 value){
 initialize();manager.clear();Dialogue d(manager,text,text,front,front,front,effects);current=&d;
 std::vector<u8> message(28);const u32 table[]={1,12,0};std::memcpy(message.data(),table,12);message[14]=u8(op);message[15]=8;const i32 first=op==8?selection:value;std::memcpy(message.data()+16,&first,4);std::memcpy(message.data()+20,&selection,4);message[24]=1;if(!d.begin(message,0))return -3;
 AnmVm* roots[6];AnmVm* children[6];for(u32 i=0;i<6;++i){roots[i]=manager.create(text,0,0,22);if(!roots[i])return -4;children[i]=manager.create(text,0,0,22,false,false,nullptr,nullptr,roots[i]);if(!children[i])return -5;roots[i]->child.next=&children[i]->child;children[i]->child.previous=&roots[i]->child;roots[i]->pending_interrupt=children[i]->pending_interrupt=0;}
 d.state.animations[0]=roots[0]->id;d.state.animations[2]=roots[1]->id;for(u32 i=0;i<4;++i)d.th14_enemy_portraits[i]=roots[2+i]->id;
 d.state.speaker=2;d.state.flags=flags;d.state.next_line=17;d.state.lines_initialized=19;for(u32 i=0;i<3;++i)d.state.text_positions[i]={float(16+i),float(24+i),float(32+i)};
 for(u32 i=0;i<4;++i){auto* vm=manager.find(d.state.animations[i+3]);vm->position={float(50+i),float(70+i),0};vm->child_position={.5,4,2};}
 const auto result=d.update(0,0);output={u32(d.state.speaker),d.state.flags,u32(d.state.next_line),u32(d.state.lines_initialized)};for(u32 i=0;i<4;++i){auto* vm=manager.find(d.state.animations[i+3]);for(float v:{vm->position.x,vm->position.y,vm->position.z,vm->child_position.x,vm->child_position.y,vm->child_position.z})output.push_back(float_bits(v));}for(u32 i=0;i<6;++i)output.insert(output.end(),{u32(roots[i]->pending_interrupt),u32(children[i]->pending_interrupt)});d.clear();return result;
}
API(lifecycle_command) i32 lifecycle_command(i32 op,i32 selection){
 initialize();manager.clear();Dialogue d(manager,text,text,front,front,front,effects);current=&d;std::vector<u8> message(24);const u32 table[]={1,12,0};std::memcpy(message.data(),table,12);message[14]=u8(op);message[15]=4;std::memcpy(message.data()+16,&selection,4);message[20]=1;if(!d.begin(message,0))return -3;
 AnmVm* roots[13];AnmVm* children[13];for(u32 i=0;i<13;++i){roots[i]=manager.create(text,0,0,22);children[i]=manager.create(text,0,0,22);if(!roots[i]||!children[i])return -4;roots[i]->child.next=&children[i]->child;children[i]->child.previous=&roots[i]->child;roots[i]->pending_interrupt=children[i]->pending_interrupt=0;}
 d.state.animations[0]=roots[0]->id;for(u32 i=0;i<4;++i)d.th14_enemy_portraits[i]=roots[i+1]->id;d.state.animations[2]=roots[5]->id;for(u32 i=0;i<4;++i)d.state.animations[i+3]=roots[i+6]->id;d.state.animations[7]=roots[10]->id;d.th14_text_background=roots[11]->id;
 const auto result=d.update(0,0);const u32 handles[]={d.state.animations[0],d.th14_enemy_portraits[0],d.th14_enemy_portraits[1],d.th14_enemy_portraits[2],d.th14_enemy_portraits[3],d.state.animations[2],d.state.animations[3],d.state.animations[4],d.state.animations[5],d.state.animations[6],d.state.animations[7],d.th14_text_background,roots[12]->id};output.clear();for(u32 i=0;i<13;++i)output.push_back(handles[i]?handles[i]==roots[i]->id?100+i:0xffffffff:0);for(u32 i=0;i<13;++i)output.insert(output.end(),{u32(roots[i]->pending_interrupt),u32(children[i]->pending_interrupt),roots[i]->flags2&32,children[i]->flags2&32});d.clear();return result;
}
