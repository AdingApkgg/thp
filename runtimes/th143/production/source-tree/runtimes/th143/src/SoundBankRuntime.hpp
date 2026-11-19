#pragma once
#include "SoundCatalogSetup.hpp"
#include "SoundArchivePreload.hpp"
#include "SoundVoiceLoad.hpp"
#include "SoundQueuePump.hpp"
#include "SoundQueue.hpp"
#include <array>
#include <vector>
#include <string>
#include <memory>
#include <cstdlib>
#include <cstring>
namespace th143 {
//Prototype reusable binding forked from the frozen resource proof fixture.
//The CPU buffer model deliberately has no playback clock/mixer; a platform
//subclass must supply those before enabling this in a live game graph.
struct SoundBankWave {std::string name;std::vector<u8> original,live;bool alive=false;};
struct SoundBankBuffer {u32 token=0,sample=0,playing=0,position=0,pan=0,volume=0,flags=0;std::array<u8,18> format{};std::shared_ptr<std::vector<u8>> bytes;};
struct SoundBankRuntime:SoundArchivePreloadHost,SoundVoiceLoadHost,SoundQueuePumpHost {
    static constexpr u32 source=0x50000000,device=0x73800000,buffers_base=0x74000000,samples_base=0x78000000,stride=0x400000;
    std::vector<u8> catalog,events;std::vector<SoundBankWave> waves;std::vector<SoundBankBuffer> buffers;u32 reads=0,sleeps=0,creates=0,duplicates=0,frees=0;
    AnmView audio;
    explicit SoundBankRuntime(AnmView audio):audio(audio){}
    AnmView view(){return audio;}
    void word(u32 v){for(u32 i=0;i<4;++i)events.push_back(u8(v>>(i*8)));}
    void event(u32 op,std::initializer_list<u32> args,const u8* payload=nullptr,u32 bytes=0){word(op);word(args.size());word(bytes);for(u32 v:args)word(v);if(bytes)events.insert(events.end(),payload,payload+bytes);}
    u32 voice_index(AnmView v){return u32(v.data-audio.data-0x1a84)/24;}
    SoundBankBuffer* buffer(u32 p){if(p<buffers_base||(p-buffers_base)%0x1000)return nullptr;const u32 i=(p-buffers_base)/0x1000;return i<buffers.size()?&buffers[i]:nullptr;}
    bool read_sound_file(const char* name,u32& token)override{if(reads>=waves.size()||waves[reads].name!=name)return false;auto& w=waves[reads];w.live=w.original;w.alive=true;token=source+reads*stride;event(0x100,{reads,token},reinterpret_cast<const u8*>(name),std::strlen(name)+1);++reads;return true;}
    bool wait_sound_preload(u32 ms,AnmView a)override{if(ms!=1||reads!=77||++sleeps!=1)return false;a.put(0x5798,1);event(0x101,{1,1});return true;}
    bool log_sound_file_failure(const char*)override{return false;}
    bool sound_descriptor(u32 token,const u8*& p)override{if(token<0x4e1280||(token-0x4e1280)%20||token-0x4e1280>catalog.size()||catalog.size()-(token-0x4e1280)<20)return false;p=catalog.data()+token-0x4e1280;return true;}
    bool sound_resource(u32 token,const u8*& p,u32& n)override{if(token<source||(token-source)%stride)return false;const u32 i=(token-source)/stride;if(i>=waves.size()||!waves[i].alive)return false;p=waves[i].live.data();n=waves[i].live.size();return true;}
    bool wait_sound_resource(u32,AnmView)override{return false;}
    bool release_sound_buffer(u32,u32&)override{return false;}
    bool create_sound_buffer(u32 d,u32 flags,u32 n,const u8* format,AnmView target,u32& hr)override{if(d!=device||n>=stride)return false;SoundBankBuffer b;b.token=buffers_base+buffers.size()*0x1000;b.sample=samples_base+buffers.size()*stride;b.bytes=std::make_shared<std::vector<u8>>(n,0xcd);std::memcpy(b.format.data(),format,18);const u32 token=b.token;buffers.push_back(std::move(b));target.put(0,token);++creates;hr=0;event(0x200,{d,flags,n,token,voice_index(target)},format,18);return true;}
    bool duplicate_sound_buffer(u32 d,u32 original,AnmView target,u32& hr)override{auto* p=buffer(original);if(d!=device||!p)return false;SoundBankBuffer b=*p;b.token=buffers_base+buffers.size()*0x1000;const u32 token=b.token;buffers.push_back(std::move(b));target.put(0,token);++duplicates;hr=0;event(0x201,{d,original,token,voice_index(target)});return true;}
    bool lock_sound_buffer(u32 token,u32 n,SoundVoiceLock& lock,u32& hr)override{auto* b=buffer(token);if(!b||n!=b->bytes->size())return false;const u32 first=n/2,second=n-first;lock={b->sample,first,second?b->sample+first:0,second};hr=0;event(0x2c,{token,0,n,lock.first,lock.first_bytes,lock.second,lock.second_bytes,0,0});return true;}
    bool copy_sound_bytes(u32 d,u32 s,u32 n)override{if(d<samples_base||s<source)return false;const u32 destination=(d-samples_base)/stride,offset=(d-samples_base)%stride,slot=(s-source)/stride,at=(s-source)%stride;if(destination>=buffers.size()||slot>=waves.size()||!waves[slot].alive)return false;auto& output=*buffers[destination].bytes;const auto& input=waves[slot].live;if(offset>output.size()||n>output.size()-offset||at>input.size()||n>input.size()-at)return false;event(0x102,{d,s,n});if(n)std::memcpy(output.data()+offset,input.data()+at,n);return true;}
    bool unlock_sound_buffer(u32 token,const SoundVoiceLock& lock,u32& hr)override{hr=0;event(0x4c,{token,lock.first,lock.first_bytes,lock.second,lock.second_bytes,0});return true;}
    bool free_sound_resource(u32 token)override{if(token<source||(token-source)%stride)return false;const u32 i=(token-source)/stride;if(i>=waves.size()||!waves[i].alive)return false;waves[i].alive=false;std::vector<u8>().swap(waves[i].live);++frees;event(0x103,{token});return true;}
    bool log_sound_wave(u32 kind,const char* name)override{if(kind!=2)return false;event(0x104,{2},reinterpret_cast<const u8*>(name),std::strlen(name)+1);return true;}
    bool query_sound_status(u32 token,u32& status,u32& hr)override{auto* b=buffer(token);if(!b)return false;status=b->playing;hr=0;event(0x24,{token,status,0});return true;}
    bool sound_voice_call(u32 token,u32 method,const u32* args,u32 count,u32& hr)override{auto* b=buffer(token);if(!b)return false;hr=0;if(method==0x48&&count==0){b->playing=0;event(method,{token,0});}else if(method==0x34&&count==1){b->position=args[0];event(method,{token,args[0],0});}else if(method==0x40&&count==1){b->pan=args[0];event(method,{token,args[0],0});}else if(method==0x3c&&count==1){b->volume=args[0];event(method,{token,args[0],0});}else if(method==0x30&&count==3){b->flags=args[2];b->playing=1;event(method,{token,args[0],args[1],args[2],0});}else return false;return true;}
};
}
