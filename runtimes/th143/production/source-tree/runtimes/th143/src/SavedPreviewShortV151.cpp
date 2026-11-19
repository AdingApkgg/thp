#include "SavedPreview.hpp"
namespace th143 {
bool load_saved_preview(const std::string& name,th11::Lzss& codec,SavedPreviewHost& host,u32& result){
    result=0;if(!host.saved_preview_directory(false))return false;bool found;if(!host.saved_preview_exists(name,found))return false;if(found){
        u32 file,bytes;if(!host.read_saved_preview_file(name,file,bytes)||!file)return false;
        // An incomplete optional screenshot has no renderable header. Release its
        // owned bytes and finish the normal null-preview path instead of failing
        // the title worker. Complete-header decoding retains its original path.
        if(bytes<0x74){if(!host.release_saved_preview_array(file))return false;return host.saved_preview_directory(true);}std::array<u8,0x78> header{};if(!host.read_saved_preview_memory(file,header.data(),0x74))return false;auto view=AnmView{header.data()};
        if(view.get(0)==0x33545342&&header[4]==1){const u32 n=view.get(0x10);if(n>0x4000000)return false;u32 data;if(!host.allocate_saved_preview_array(0x78,result)||!result||!host.write_saved_preview_memory(result,header.data(),0x74)||!host.allocate_saved_preview_array(n,data)||!data)return false;view.put(0x74,data);if(!host.write_saved_preview_memory(result+0x74,&data,4))return false;
            std::vector<u8> compressed(bytes-0x74),decoded(n);if((!compressed.empty()&&!host.read_saved_preview_memory(file+0x74,compressed.data(),compressed.size()))||(n&&!host.read_saved_preview_memory(data,decoded.data(),n)))return false;u32 written=0;if(!codec.decode(compressed.data(),compressed.size(),decoded.data(),n,written))return false;if(n&&!host.write_saved_preview_memory(data,decoded.data(),n))return false;
        }
        if(!host.release_saved_preview_array(file))return false;
    }
    return host.saved_preview_directory(true);
}
}
