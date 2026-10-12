#include "th14-physical-texture-image-fixture.cpp"
API(load_high) u32 load_high(u32 index){return index<resource.textures.size()&&image.load(resource.textures[index],false,true);}
