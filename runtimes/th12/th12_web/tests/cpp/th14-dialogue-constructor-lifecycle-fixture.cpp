#include "th14-dialogue-portrait-sprite-fixture.cpp"
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
