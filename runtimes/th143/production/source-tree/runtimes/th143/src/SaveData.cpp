#include "SaveData.hpp"
#include "../../th12/th12_web/cpp/game/ResourceCrypt.hpp"
#include <algorithm>

namespace th143 {
namespace {
constexpr u32 file_token=0x6c000000,decoded_token=0x6d000000;
u32 word(const u8* p){u32 v;std::memcpy(&v,p,4);return v;}
void put(u8* p,u32 v){std::memcpy(p,&v,4);}
struct Level {u32 count,uses,duration;};
// 4566bd..456f24: each row is a threshold, not an observed result trace.
constexpr Level levels[9][6]={
 {{0,5,60},{3,5,84},{6,6,84},{9,6,106},{14,7,106},{20,7,120}},
 {{0,4,100},{3,5,100},{6,5,120},{9,6,120},{14,6,140},{20,7,140}},
 {{0,7,30},{3,7,60},{8,7,90},{14,7,120},{20,7,150},{}},
 {{0,1,480},{5,1,540},{10,1,600},{15,1,660},{},{}},
 {{0,5,60},{7,6,60},{15,7,60},{},{},{}},
 {{0,3,128},{5,3,154},{10,3,179},{14,3,205},{20,4,205},{}},
 {{0,3,60},{5,3,90},{10,3,120},{15,3,180},{20,4,180},{}},
 {{0,2,720},{5,2,900},{10,2,1080},{15,3,1080},{},{}},
 {{0,3,400},{7,4,400},{15,5,400},{},{},{}}
};
constexpr u32 max_level[9]={6,6,5,4,3,5,5,4,3};
constexpr u32 use_bonus[9]={2,0,2,0,2,0,1,1,1};
constexpr u32 duration_bonus[9]={0,20,0,60,0,51,0,0,0};
}
u32 SaveData::checksum(const u8* p,u32 n){u32 sum=0;for(u32 i=8;i<n;++i)sum+=p[i];return sum;}
bool SaveData::initialize(const u8* raw,u32 n,Rng& rng,std::array<u32,4>& equipment,std::array<u32,4>& saved,SaveDataHost& host){
    data.fill(0);file.clear();decoded.clear();
    if(n){if(!raw)return false;file.assign(raw,raw+n);view().put(0,file_token);}
    auto s=view().sub(stats);s.put(0,0x15453);s.put(8,stats_size);
    std::fill_n(s.data+12,12,u8(' '));s.data[0x66]=1;s.data[0x67]=1;s.data[0x68]=1;
    for(u32 at=0x148;at<stats_size;at+=2){u16 v=rng.next16();std::memcpy(s.data+at,&v,2);}
    for(u32 i=0;i<scene_count;++i){auto r=view().sub(8+i*scene_size);r.put(0,0x14e53);r.put(8,scene_size);r.put(12,i);}
    for(u32 i=0;i<item_count;++i){auto r=view().sub(items+i*item_size);r.put(0,0x14954);r.put(8,item_size);r.put(0x1c,1);
        // The original writes the id AFTER recomputing; all eleven default
        // records therefore receive item zero's level-one parameters.
        r.put(0x20,6);r.put(0x24,5);r.put(0x28,60);r.put(12,i);
    }
    (void)host;return load(equipment,saved);
}
bool SaveData::load(std::array<u32,4>& equipment,std::array<u32,4>& saved){
    if(file.size()<24 || word(file.data())!=0x31343354 || (word(file.data()+8)&0xffff)!=1){
        file.assign(24,0);put(file.data(),0x31343354);put(file.data()+8,1);put(file.data()+12,0x100);view().put(0,file_token);return true;
    }
    const u32 compressed=word(file.data()+16),size=word(file.data()+20);
    // Native trusts its file; reject lengths that would escape owned storage.
    if(compressed>file.size()-24 || size>0x1000000)return false;
    std::vector<u8> plain(compressed);
    if(!th11::resource_crypt(file.data()+24,plain.data(),compressed,{0xac,0x35,16,compressed},false))return false;
    std::copy(plain.begin(),plain.end(),file.begin()+24);
    decoded.assign(std::size_t(size)*4,0);view().put(4,decoded_token);
    u32 written=0;if(size && (!codec.decode(plain.data(),compressed,decoded.data(),u32(decoded.size()),written)||written!=size))return false;
    for(u32 at=0;at<size;){
        if(size-at<12)return false;
        const u8* r=decoded.data()+at;const u32 tag=word(r),length=word(r+8);u32 expected=0,destination=0;
        switch(tag&0xffff){case 0x4e53:expected=scene_size;break;case 0x5453:expected=stats_size;break;case 0x4954:expected=item_size;break;default:at=size;continue;}
        if((tag>>16)==1){
            if(expected>decoded.size()-at)return false;
            if(checksum(r,expected)==word(r+4) && length==expected){
                if(expected==stats_size)destination=stats;
                else{const u32 id=word(r+12);if(id>=(expected==scene_size?scene_count:item_count))return false;destination=expected==scene_size?8+id*scene_size:items+id*item_size;}
                std::memcpy(data.data()+destination,r,expected);
            }
        }
        if(!length)return false;
        if(length>size-at)break;at+=length;
    }
    for(u32 i=0;i<4;++i)equipment[i]=saved[i]=view().get(0xef9c+i*4);
    return true;
}
bool SaveData::item_level(u32 id,bool notify,u32 alternate,SaveDataHost& host){
    if(id>=item_count)return false;auto r=view().sub(items+id*item_size);const u32 previous=r.get(0x1c);
    u32 count=0;for(u32 i=0;i<scene_count;++i)if(view().get(0x18+i*scene_size+id*4))++count;
    r.put(0x18,count);r.put(0x2c,0);r.put(0x30,0);
    if(id<10){u32 base=0;switch(count){case 3:base=30;break;case 10:base=40;break;case 20:base=50;break;case 75:base=60;break;}
        if(base&&!host.achievement(base+id))return false;
    }
    if(id>8)return true;
    u32 level=1;for(u32 i=1;i<max_level[id];++i)if(count>=levels[id][i].count)level=i+1;
    const auto& p=levels[id][level-1];r.put(0x1c,level);r.put(0x20,max_level[id]);r.put(0x24,p.uses);r.put(0x28,p.duration);
    if(data[0xefad]&&alternate==8){r.put(0x24,p.uses+use_bonus[id]);r.put(0x28,p.duration+duration_bonus[id]);r.put(0x2c,use_bonus[id]);r.put(0x30,duration_bonus[id]);}
    if(notify&&previous!=level){
        // Stack arrays: [0,1,0,1,0,1], [0...0,1] and
        // item7's [0,0,0,1] distinguish capacity versus duration notices.
        const bool capacity=(id<2?level%2==0:(id==5||id==6?level==5:id==7?level==4:false));
        const u32 n=view().get(0xf16c);if(n>=(bytes-0xf170)/4)return false;
        view().put(0xf170+n*4,(capacity?20:11)+id);view().put(0xf16c,n+1);
    }
    return true;
}
bool SaveData::serialize(const std::array<u32,4>& saved,std::vector<u8>& output){
    if(file.size()<24 || !view().get(0))return false;
    std::vector<u8> payload;payload.reserve(0xf164);
    auto append=[&](u32 at,u32 size){u8* r=data.data()+at;put(r+4,checksum(r,size));payload.insert(payload.end(),r,r+size);};
    for(u32 i=0;i<scene_count;++i)append(8+i*scene_size,scene_size);
    for(u32 i=0;i<item_count;++i)append(items+i*item_size,item_size);
    for(u32 i=0;i<4;++i)view().put(0xef9c+i*4,saved[i]);append(stats,stats_size);
    const auto compressed=codec.encode(payload.data(),u32(payload.size()));
    put(file.data()+4,u32(compressed.size())+24);put(file.data()+16,u32(compressed.size()));put(file.data()+20,u32(payload.size()));
    output.assign(file.begin(),file.begin()+24);output.resize(24+compressed.size());
    return th11::resource_crypt(compressed.data(),output.data()+24,u32(compressed.size()),{0xac,0x35,16,u32(compressed.size())},true);
}
}
