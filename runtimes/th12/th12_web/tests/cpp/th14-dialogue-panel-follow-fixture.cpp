#include "th14-dialogue-panel-geometry-fixture.cpp"
static AnmResource follow_text;static std::unique_ptr<Dialogue> follow_dialogue;static u32 follow_ids[4],follow_positions[13];
API(begin_follow) i32 begin_follow(i32 slot,float display,i32 speaker,i32 immediate,i32 rotation){
 if(follow_dialogue)follow_dialogue->clear();follow_dialogue.reset();
 if(!begin_panel_geometry(slot,1.f,128.f,immediate))return 0;
 manager.render_space.scale=display;vms[0]->position={224,288,0};vms[0]->rotation.z=rotation?.375f:0.f;
 if(rotation)for(auto* node=vms[0]->child.next;node;node=node->next)if(node->value->script_index==slot-48)node->value->flags2|=0x400000;
 follow_text={};follow_text.scripts.resize(2);const AnmInstruction stop[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};for(auto& s:follow_text.scripts){s.bytes.resize(sizeof stop);std::memcpy(s.bytes.data(),stop,sizeof stop);}if(!manager.prepare_resource(follow_text,0))return 0;
 follow_dialogue=std::make_unique<Dialogue>(manager,follow_text,follow_text,resource,follow_text,follow_text,effects);std::vector<u8> bytes(24);const u32 table[]={1,12,0};std::memcpy(bytes.data(),table,12);bytes[14]=11;bytes[15]=4;bytes[16]=0x58;bytes[17]=2;if(!follow_dialogue->begin(bytes,0))return 0;follow_dialogue->state.speaker=speaker;follow_dialogue->th14_text_background=vms[0]->id;follow_dialogue->th14_text_layout=slot-216;
 for(u32 i=0;i<4;++i){follow_ids[i]=follow_dialogue->state.animations[3+i];auto* line=manager.find(follow_ids[i]);if(!line)return 0;line->flags&=~3u;}capture_lifecycle();capture_sprite();return 1;
}
API(follow_step) i32 follow_step(){if(!geometry_step())return 0;follow_positions[0]=follow_dialogue->th14_text_background!=0;for(u32 i=0;i<4;++i){auto* line=manager.find(follow_ids[i]);if(!line)return 0;follow_positions[1+i*3]=bits(line->position.x);follow_positions[2+i*3]=bits(line->position.y);follow_positions[3+i*3]=bits(line->position.z);}return 1;}
API(follow_data) const u32* follow_data(){return follow_positions;}
