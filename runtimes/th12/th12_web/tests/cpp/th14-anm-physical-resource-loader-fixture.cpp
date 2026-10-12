#include "th14-anm-all-resource-loader-fixture.cpp"
#include "../../cpp/game/TextureImage.hpp"
static TextureImage physical_texture;
static u32 physical_index=~0u;
API(physical_reset) void physical_reset(){physical_index=~0u;}
API(physical_sprite_word) u32 physical_sprite_word(u32 i,u32 n){
 const auto& s=resource.sprites[i];const auto& t=resource.textures[s.texture];
 if(physical_index!=s.texture){if(!physical_texture.load(t))return ~0u;physical_index=s.texture;}
 const float x=float(physical_texture.width)/t.width,y=float(physical_texture.height)/t.height;
 // The portable sprite stores logical coordinates; retail stores physical
 // coordinates and their scale separately. UV and logical sprite size agree.
 const float right=s.x+s.width,bottom=s.y+s.height;
 const u32 descriptor[]={u32(resource.templates->scripts[0].file_index),s.texture,s.texture,word(s.x*x),word(s.y*y),word(right*x),word(bottom*y),word(float(physical_texture.height)),word(float(physical_texture.width)),word(s.u0),word(s.v0),word(s.u1),word(s.v1),word(s.height),word(s.width),word(x),word(y)};
 return descriptor[n];
}
