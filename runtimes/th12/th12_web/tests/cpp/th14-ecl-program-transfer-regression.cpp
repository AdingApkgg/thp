#include "../../cpp/game/Archive.hpp"
#include "../../cpp/game/EclResource.hpp"
#include "../../cpp/game/AnmTransferTh14.hpp"
#include <array>
#include <emscripten.h>
using namespace th11;
namespace {
struct Provider final:EclResourceProvider {
    Archive archive;std::array<std::string,64> animations;std::vector<std::string> reads;
    bool has(const std::string& name){for(const auto& e:archive.entries)if(e.name==name)return true;return false;}
    bool read(const std::string& name,std::vector<u8>& output)override{
        reads.push_back(name);for(u32 i=0;i<archive.entries.size();++i)if(archive.entries[i].name==name)return archive.read(i,output);return false;
    }
    bool animation(u32 slot,const std::string& name)override{if(slot>=animations.size()||!has(name))return false;animations[slot]=name;return true;}
}provider;
std::vector<u8> output;std::vector<std::string> names;std::string error;
}
extern "C" {
EMSCRIPTEN_KEEPALIVE u32 fixture_open(const u8* bytes,u32 size){
    if(!provider.archive.open(bytes,size,14))return 0;names.clear();for(const auto& e:provider.archive.entries)if(e.name.size()>4&&e.name.substr(e.name.size()-4)==".ecl")names.push_back(e.name);return u32(names.size());
}
EMSCRIPTEN_KEEPALIVE const char* fixture_name(u32 index){return index<names.size()?names[index].c_str():nullptr;}
EMSCRIPTEN_KEEPALIVE const u8* fixture_program(const char* name){
    provider.animations={};provider.reads.clear();EclProgram program;
    if(!program.load(name,provider)||!program.error.empty()){error=program.error;return nullptr;}
    anm_transfer_th14::Writer w;w.word(u32(provider.reads.size()));for(const auto& n:provider.reads)w.text(n);
    for(const auto& n:provider.animations)w.text(n);
    w.word(u32(program.files.size()));w.word(u32(program.definitions.size()));
    for(const auto& ptr:program.files){const auto& f=*ptr;w.blob(f.bytes.data(),f.bytes.size());
        w.word(u32(f.subroutines.size()));for(const auto& s:f.subroutines){w.text(s.name);w.word(s.offset);w.word(s.size);}
        w.word(u32(f.animations.size()));for(const auto& n:f.animations)w.text(n);
        w.word(u32(f.includes.size()));for(const auto& n:f.includes)w.text(n);
    }
    for(const auto& d:program.definitions){u32 file=0;while(file<program.files.size()&&program.files[file].get()!=d.file)++file;
        if(file==program.files.size()){error="unowned definition";return nullptr;}w.word(file);w.word(d.index);
        const auto* found=program.find(d.file->subroutines[d.index].name.c_str());
        u32 resolved_file=0,resolved_offset=0xffffffff;
        for(;resolved_file<program.files.size();++resolved_file){const auto& bytes=program.files[resolved_file]->bytes;
            const auto address=reinterpret_cast<uintptr_t>(found),start=reinterpret_cast<uintptr_t>(bytes.data());
            if(found&&address>=start&&address-start<bytes.size()){resolved_offset=u32(address-start);break;}
        }
        w.word(resolved_file);w.word(resolved_offset);
    }
    if(!w.ok){error="snapshot exceeds budget";return nullptr;}output=std::move(w.bytes);return output.data();
}
EMSCRIPTEN_KEEPALIVE u32 fixture_size(){return u32(output.size());}
EMSCRIPTEN_KEEPALIVE const char* fixture_error(){return error.c_str();}
}
