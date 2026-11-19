#include "TitlePreviewTask.hpp"
namespace th143 {
namespace {
std::string digits(i32 value){const auto number=std::int64_t(value);auto text=std::to_string(number<0?-number:number);if(text.size()<2)text.insert(0,2-text.size(),'0');return number<0?"-"+text:text;}
u32 first(AnmView q){return signed_word(q.get(0x200))>0?q.get(0):0;}
void pop(AnmView q){if(signed_word(q.get(0x200))>0){q.put(0x200,q.get(0x200)-1);std::memmove(q.data,q.data+4,127*4);}}
bool push(AnmView q,u32 value){const i32 count=signed_word(q.get(0x200)),capacity=signed_word(q.get(0x204));if(count<0||count>128||capacity<0||capacity>128)return false;if(count<capacity){q.put(u32(count)*4,value);q.put(0x200,u32(count)+1);}return true;}
}
i32 TitlePreviewTask::resume(GameTitleRuntime& owner,AnmResourceWorld& world,AnmView app,TitlePreviewWorkerHost& host,u32 budget){
    if(!owner.global_owner||!app.data)return -1;auto title=owner.view();
    auto finish=[&](){app.put(0x99c,0);app.put(0x998,1);phase=11;return 0;};
    auto stopping=[&](){return (app.get(0x724)&0x180)||(title.get(0xe000)&0x10);};
    while(budget--){switch(phase){
    case 0:if(app.get(0x724)&0x180)return finish();phase=1;break;
    case 1:
        if(title.get(0xe000)&0x10)return finish();
        phase=5;if(!title.get(0xe328))break;day=first(title.sub(0xe128));if(signed_word(day)<0)break;
        {std::vector<u8> raw;bool found;if(!host.read_scene_preview("scene"+digits(signed_word(day+1))+".png",raw,found))return -1;
         if(!found){pop(title.sub(0xe128));break;}
         bytes=u32(raw.size());if(!world.allocate_resource_storage(bytes,true,token)||!world.write(token,raw.data(),bytes))return -1;phase=2;}
        break;
    case 2:
        if(title.get(0xe530)){phase=3;if(!host.sleep_scene_preview(10))return -1;return 1;}phase=4;break;
    case 3:
        if(stopping()||!title.get(0xe530)){phase=4;break;}
        if(!host.sleep_scene_preview(10))return -1;return 1;
    case 4:
        if(!push(title.sub(0xe330),token)||!push(title.sub(0xe538),bytes)||!push(title.sub(0xe740),day))return -1;
        pop(title.sub(0xe128));phase=5;break;
    case 5:
        phase=9;if(!title.get(0xeb48))break;encoded=first(title.sub(0xe948));
        {const i32 day=signed_word(encoded)/100,scene=signed_word(encoded)-day*100;
         if(!host.read_saved_preview("savedata/sc"+digits(day)+"_"+digits(scene)+".dat",token))return -1;}
        phase=6;break;
    case 6:
        if(title.get(0xed50)){phase=7;if(!host.sleep_scene_preview(10))return -1;return 1;}phase=8;break;
    case 7:
        if(stopping()||!title.get(0xed50)){phase=8;break;}
        if(!host.sleep_scene_preview(10))return -1;return 1;
    case 8:
        if(!push(title.sub(0xeb50),token)||!push(title.sub(0xed58),encoded))return -1;
        pop(title.sub(0xe948));phase=9;break;
    case 9:phase=10;if(!host.sleep_scene_preview(1))return -1;return 1;
    case 10:if(app.get(0x724)&0x180)return finish();phase=1;break;
    case 11:return 0;
    default:return -1;
    }}return -1;
}
}
