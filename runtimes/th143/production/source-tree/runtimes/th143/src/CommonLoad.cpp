#include "CommonLoad.hpp"
#include <utility>
namespace th143 {
namespace {
bool enable(CommonLoadBindings& b,u32 field){auto callback=b.frames.scheduler.at(b.common.view().get(field));if(!callback.data)return false;callback.put(4,callback.get(4)|2u);return true;}
bool raw(CommonLoadBindings& b,CommonLoadHost& host,const char* name,u32& token,std::vector<u8>& bytes){bool found;if(!host.read_common_file(name,false,bytes,found)||!found||bytes.empty()||!b.resources.allocate_resource_storage(u32(bytes.size()),true,token))return false;return b.resources.write(token,bytes.data(),u32(bytes.size()));}
}
bool load_common(CommonLoadBindings& b,CommonLoadHost& host,i32& result){
    result=0;if(!b.common.global_owner||b.ascii.global_owner||b.auxiliary.effects_owner||b.save_owner||!b.application.data||!b.audio.data)return false;
    //472a90 waits/stops existing workers, then initializes a physical device.
    // The verified cold no-device branch has no jobs and no device pointer.
    if(b.audio.get(0x578c)||b.audio.get(0xc))return false;
    auto owner=b.common.view();u32 resource;b.last_entry=0x4430bc;
    if(!b.storage.request_game_resource(1,"sig.anm",resource)||!resource)return false;owner.put(0x600,resource);
    if(!enable(b,12))return false;owner.put(0x604,1);
    b.last_entry=0x40b4e0;u32 ascii;if(!b.ascii.create(b.application.data[0x1f3],ascii)||!ascii)return false;owner.put(0x608,1);
    if(!b.storage.request_game_resource(0,"text.anm",resource)||!resource)return false;b.application.put(0x71c,resource);
    b.last_entry=0x443170;std::vector<u8> bytes;u32 token;if(!raw(b,host,"../../bgm/thbgm.fmt",token,bytes))return false;b.audio.put(0x1980,token);
    std::memset(b.audio.data+0x1c,0xff,48); //472a90, device+0xc==0 returns-1.
    bool archive;if(!host.common_archive_exists("thbgm.dat",archive))return false;
    if(archive){
        // Both the config10 copy and472560's no-device branch write this
        // same buffer; the latter returns-1 after the copy, ignored by4430b0.
        static constexpr char name[]="thbgm.dat";std::memcpy(b.audio.data+0x5678,name,sizeof name);
    }
    b.last_entry=0x442f00;for(auto r:{std::pair<u32,const char*>{5,"front.anm"},{7,"bullet.anm"},{8,"effect.anm"},{28,"screenswitch.anm"},{26,"itemequip.anm"},{9,"pl00.anm"},{27,"trophy.anm"}})if(!b.storage.request_game_resource(r.first,r.second,resource)||!resource)return false;
    if(!raw(b,host,"trophy.txt",token,bytes)||!b.trophies.load(bytes.data(),u32(bytes.size()),b.resources.animation_rng)||!b.resources.write(token,b.trophies.source.data(),u32(b.trophies.source.size()))||!b.resources.release_enemy_storage(token,true))return false;
    b.last_entry=0x41ae60;u32 effects;if(!b.auxiliary.create_effects(effects)||!effects||!enable(b,8))return false;
    static constexpr u32 save_self=0x6d000000;
    b.last_entry=0x455f90;if(!b.storage.reserve_game_owner(save_self,SaveData::bytes))return false;
    b.save_owner=save_self;bool found;if(!host.read_common_file("scoreth143.dat",true,bytes,found))return false;
    if(found){
        if(!b.loaded_save||!b.resources.allocate_resource_storage(u32(bytes.size()),true,token)||!b.resources.write(token,bytes.data(),u32(bytes.size()))||!b.loaded_save->initialize(bytes.data(),u32(bytes.size()),token,b.resources,b.gameplay,b.equipment,b.saved_equipment,host))return false;
    }else if(!b.save_runtime.initialize_missing(b.gameplay,b.equipment,b.saved_equipment,host))return false;
    b.last_entry=0;return true;
}
}
