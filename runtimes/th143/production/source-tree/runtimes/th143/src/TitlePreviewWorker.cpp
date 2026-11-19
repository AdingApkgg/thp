#include "TitlePreviewWorker.hpp"
namespace th143 {
namespace {
std::string digits(i32 value){const auto number=std::int64_t(value);auto s=std::to_string(number<0?-number:number);if(s.size()<2)s.insert(0,2-s.size(),'0');return number<0?"-"+s:s;}
u32 first(AnmView q){return signed_word(q.get(0x200))>0?q.get(0):0;}
void pop(AnmView q){if(signed_word(q.get(0x200))>0){q.put(0x200,q.get(0x200)-1);std::memmove(q.data,q.data+4,127*4);}}
bool push(AnmView q,u32 value){const i32 count=signed_word(q.get(0x200)),capacity=signed_word(q.get(0x204));if(count<0||count>128||capacity<0||capacity>128)return false;if(count<capacity){q.put(u32(count)*4,value);q.put(0x200,u32(count)+1);}return true;}
bool wait(AnmView title,AnmView application,u32 count,TitlePreviewWorkerHost& host,u32& budget){if(!title.get(count))return true;do{if(!budget--||!host.sleep_scene_preview(10))return false;if((application.get(0x724)&0x180)||(title.get(0xe000)&0x10))break;}while(title.get(count));return true;}
}
bool run_title_preview_worker(GameTitleRuntime& owner,AnmResourceWorld& world,AnmView app,TitlePreviewWorkerHost& host,u32 budget){
    if(!owner.global_owner||!app.data)return false;auto title=owner.view();if(!(app.get(0x724)&0x180)){
        while(!(title.get(0xe000)&0x10)){
            if(!budget--)return false;
            if(title.get(0xe328)){const u32 day=first(title.sub(0xe128));if(signed_word(day)>=0){std::vector<u8> bytes;bool found;if(!host.read_scene_preview("scene"+digits(signed_word(day+1))+".png",bytes,found))return false;
                    if(found){u32 token;if(!world.allocate_resource_storage(u32(bytes.size()),true,token)||!world.write(token,bytes.data(),u32(bytes.size()))||!wait(title,app,0xe530,host,budget)||!push(title.sub(0xe330),token)||!push(title.sub(0xe538),u32(bytes.size()))||!push(title.sub(0xe740),day))return false;}
                    pop(title.sub(0xe128));
                }
            }
            if(title.get(0xeb48)){const u32 encoded=first(title.sub(0xe948));const i32 day=signed_word(encoded)/100,scene=signed_word(encoded)-day*100;u32 token;if(!host.read_saved_preview("savedata/sc"+digits(day)+"_"+digits(scene)+".dat",token)||!wait(title,app,0xed50,host,budget)||!push(title.sub(0xeb50),token)||!push(title.sub(0xed58),encoded))return false;pop(title.sub(0xe948));}
            if(!host.sleep_scene_preview(1))return false;if(app.get(0x724)&0x180)break;
        }
    }
    app.put(0x99c,0);app.put(0x998,1);return true;
}
}
