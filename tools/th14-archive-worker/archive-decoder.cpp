// Pure CPU boundary: no game objects, GPU, audio, input or clocks are touched.
#include "Archive.hpp"
#include "AnmTransferTh14.hpp"
#include <emscripten.h>
#include <memory>
using namespace th11;
namespace {
std::unique_ptr<Archive> archive;
std::vector<u8> output;
std::vector<u8> parsed_anm;
u32 failure=0;
}
extern "C" {
EMSCRIPTEN_KEEPALIVE u32 decoder_open(const u8* bytes,u32 size){
    archive=std::make_unique<Archive>();output.clear();parsed_anm.clear();failure=0;
    if(!bytes||!size||size>128u*1024*1024||!archive->open(bytes,size,14)){
        archive.reset();failure=1;return 0;
    }
    return u32(archive->entries.size());
}
EMSCRIPTEN_KEEPALIVE const char* decoder_name(u32 index){
    return archive&&index<archive->entries.size()?archive->entries[index].name.c_str():nullptr;
}
EMSCRIPTEN_KEEPALIVE const u8* decoder_read(const char* name,u32 length){
    output.clear();parsed_anm.clear();failure=0;
    if(!archive||!name||!length||length>128){failure=2;return nullptr;}
    for(u32 i=0;i<archive->entries.size();++i){
        const auto& entry=archive->entries[i];
        if(entry.name.size()!=length||std::memcmp(entry.name.data(),name,length))continue;
        if(!archive->read(i,output)){failure=3;return nullptr;}
        return output.empty()?reinterpret_cast<const u8*>(1):output.data();
    }
    failure=4;return nullptr;
}
EMSCRIPTEN_KEEPALIVE u32 decoder_size(){return u32(output.size());}
EMSCRIPTEN_KEEPALIVE const u8* decoder_anm(){
    parsed_anm.clear();AnmResource resource;
    if(!resource.open(output.data(),u32(output.size()))){failure=5;return nullptr;}
    if(!th14_encode_anm_transfer(resource,output.data(),u32(output.size()),parsed_anm)){failure=6;return nullptr;}
    return parsed_anm.data();
}
EMSCRIPTEN_KEEPALIVE u32 decoder_anm_size(){return u32(parsed_anm.size());}
EMSCRIPTEN_KEEPALIVE u32 decoder_error(){return failure;}
EMSCRIPTEN_KEEPALIVE void decoder_close(){output.clear();parsed_anm.clear();archive.reset();failure=0;}
}
