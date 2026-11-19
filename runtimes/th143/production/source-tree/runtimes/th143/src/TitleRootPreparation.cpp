#include "TitleRootPreparation.hpp"
namespace th143 {
bool prepare_title_for_root(AnmView title,TitleRootPreparationHost& h,u32 budget){
    if(!title.data)return false;title.put(0xe000,title.get(0xe000)|0x10);
    if(!h.stop_title_preview(title.sub(0xe0f8)))return false;
    auto queue=title.sub(0xe330);
    while(queue.get(0x200)){
        if(!budget--)return false;u32 token=0;
        if(signed_word(queue.get(0x200))>0){token=queue.get(0);queue.put(0x200,queue.get(0x200)-1);std::memmove(queue.data,queue.data+4,127*4);}
        if(!h.title_preview_free(token))return false;
    }
    while(title.get(0xed50)){
        if(!budget--)return false;const u32 object=signed_word(title.get(0xed50))>0?title.get(0xeb50):0;
        AnmView value{nullptr};if(!h.title_preview_region(object+0x74,4,value)||!value.data)return false;
        const u32 pixels=value.get(0);if(pixels&&!h.title_preview_free(pixels))return false;
        if(!h.title_preview_free(object))return false;
    }
    return true;
}
}
