#include "th14-stage-asset-anm-fixture.cpp"
#include "../../cpp/game/AnmOpcodes.hpp"
API(template_word) u32 template_word(u32 i,u32 n){return fields(resource.templates->scripts[i])[n];}
API(texture_count) u32 texture_count(){return resource.textures.size();}
API(sprite_count) u32 sprite_count(){return resource.sprites.size();}
API(script_count) u32 script_count(){return resource.scripts.size();}
API(sprite_word) u32 sprite_word(u32 i,u32 n){
 const auto& s=resource.sprites[i];const auto& t=resource.textures[s.texture];
 const float right=s.x+s.width,bottom=s.y+s.height;
 const u32 descriptor[]={u32(resource.templates->scripts[0].file_index),s.texture,s.texture,word(s.x),word(s.y),word(right),word(bottom),word(float(t.height)),word(float(t.width)),word(s.u0),word(s.v0),word(s.u1),word(s.v1),word(s.height),word(s.width),word(1),word(1)};
 return descriptor[n];
}
API(script_id) i32 script_id(u32 i){return resource.scripts[i].source_id;}
API(script_offset) u32 script_offset(u32 i){return resource.scripts[i].file_offset;}
API(script_size) u32 script_size(u32 i){return resource.scripts[i].bytes.size();}
API(script_data) const u8* script_data(u32 i){return resource.scripts[i].bytes.data();}
API(canonical) u32 canonical(u32 op){return anm_canonical_opcode(u16(op));}
