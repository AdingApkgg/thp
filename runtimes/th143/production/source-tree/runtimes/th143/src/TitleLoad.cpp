#include "TitleLoad.hpp"
namespace th143 {
namespace {
struct Callbacks:SchedulerHost {bool invoke(u32,u32,u32&)override{return false;}bool release_callback(u32)override{return false;}};
bool initialize(TitleLoadBindings& b,TitleLoadHost& host,i32& result,u32& budget){
    result=0;if(!b.title.global_owner||!b.application.data)return false;auto title=b.title.view();Callbacks callbacks;
    for(auto row:{std::array<u32,4>{0x45fb20,6,0,12},{0x45fb30,66,1,16}}){u32 token,ignored;b.last_entry=row[0];if(!b.storage.allocate_game_storage(40,token)||!token||!b.frames.scheduler.create(token,row[0],b.storage.game_allocation_fill()))return false;auto cb=b.frames.scheduler.at(token);cb.put(4,cb.get(4)&~2u);cb.put(0x24,b.title.global_owner);if(!b.frames.scheduler.add(token,i32(row[1]),row[2]!=0,callbacks,ignored))return false;title.put(row[3],token);}
    b.last_entry=0x482140;for(auto row:{std::array<u32,2>{16,20},{17,24}}){u32 token,cached;if(!b.resources.read(0x72bc7b0c+row[0]*4,&cached,4)||!b.storage.request_game_resource(row[0],row[0]==16?"title.anm":"title_v.anm",token))return false;if(token&&!cached){u32 pending;if(!b.resources.read(token+0x128,&pending,4))return false;while(pending&&!(b.application.get(0x724)&0x180u)){if(!budget--||!host.sleep_title_worker(1)||!b.resources.read(token+0x128,&pending,4))return false;}}title.put(row[1],token);if(!token){result=-1;return host.title_resource_error();}}
    b.last_entry=0x402e00;std::vector<u8> bytes,padding;if(!host.read_title_file("titlemsg.txt",bytes))return false;u32 token;if(!b.resources.allocate_resource_storage(u32(bytes.size()),true,token)||!b.resources.write(token,bytes.data(),u32(bytes.size()))||!host.title_file_padding(token,u32(bytes.size()),padding))return false;const u32 declared=u32(bytes.size());bytes.insert(bytes.end(),padding.begin(),padding.end());
    b.last_entry=0x45f0ca;if(!load_title_messages(title,token,declared,bytes)||!b.resources.write(token,bytes.data(),declared))return false;
    b.last_entry=0x436ba0;u32 cheat;if(!b.cheat.create(cheat))return false;
    title.put(0xf8,1);b.global_538de4=0;auto save=b.save.view();for(u32 i=0;i<4;++i)b.equipment[i]=save.get(0xef9c+i*4);b.alternate=save.data[0xefad];
    b.last_entry=0x4562e0;if(!write_save_file(b.save,b.saved_equipment,b.resources,host,b.loaded_save))return false;
    if(signed_word(save.get(0xef2c))>=75&&!save.data[0xefe0]){const u32 count=save.get(0xf16c);if(count>=16)return false;save.data[0xefe0]=1;save.put(0xf170+count*4,0x27);save.put(0xf16c,count+1);}
    return true;
}
}
bool load_title(TitleLoadBindings& b,TitleLoadHost& host,i32& result,u32 budget){
    i32 initialized;if(!initialize(b,host,initialized,budget))return false;result=0;
    if(initialized){b.application.put(0x6ec,((~(b.application.get(0x724)>>13))&1u)|2u);b.last_entry=0;return true;}
    b.last_entry=0x45ef81;if(b.common.global_owner){while(signed_word(b.common.view().get(0x60c))<180&&!(b.application.get(0x724)&0x180u)){if(!budget--||!host.sleep_title_worker(16)||!b.common.global_owner)return false;}if(!b.resources.unload(1))return false;}
    auto callback=b.frames.scheduler.at(b.title.view().get(12));if(!callback.data)return false;callback.put(4,callback.get(4)|2u);b.globals.presentation=1;b.last_entry=0;return true;
}
}
