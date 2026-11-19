#pragma once
#include "OwnedMusicControllerMainHost.hpp"
#include "MusicNotifyRefillThread.hpp"
#include "MusicNotifyDispatch.hpp"
#include "SoundBankRuntime.hpp"
#include <map>
#include <set>
namespace th143 {
struct MusicPlatformBufferV3 {
    u32 token=0,sample=0,position=0,write_position=0,playing=0,volume=0,pan=0,flags=0;
    bool alive=true,locked=false;std::array<u8,18> format{};std::vector<u8> pcm;std::vector<u32> notifications;
};
//Concrete single-thread platform prototype. The caller supplies the playback
//clock/cursors and dispatches actual notification outcomes. No synthetic clock,
//worker quit or successful unsupported service is hidden inside the game pump.
struct OwnedMusicMemoryPlatformV3:OwnedMusicControllerMainHost {
    static constexpr u32 metadata_token=0x73900000,wrapper_token=0x6e033000;
    SoundBankRuntime bank;std::vector<u8> metadata,archive;std::vector<MusicPlatformBufferV3> music_buffers;
    std::map<u32,std::vector<u8>> allocations;std::map<u32,u32> file_positions,free_ranges;u32 reused_buffers=0;
    u32 next_allocation=0xb0000000,next_file=0x6f000000,wrapper_device=SoundBankRuntime::device;
    double clock=0;u32 random_state=1;bool prepared=false,event_live=false,thread_live=false,quit_pending=false;
    u32 notification_outcome=0;bool notification_pending=false;std::array<u8,28> notification_message{};
    MusicNotifyDispatchState worker_state;u32 next_event=0x6d100000,next_thread=0x6d200000,next_thread_id=0x6d300000,current_thread=0,current_thread_id=0,archive_file_base=0;std::set<u32> event_handles;
    struct NotificationHost:MusicNotifyRefillHost {
        OwnedMusicMemoryPlatformV3& p;explicit NotificationHost(OwnedMusicMemoryPlatformV3& p):p(p){notify_query_output_token=0x70011fc0;}
        bool music_fill_region(u32 t,u32 n,AnmView& v)override{return p.music_region(t,n,v);}
        u32 music_fill_file_base()const override{return p.music_file_base();}
        bool music_buffer_status(u32 t,u32& s,u32& h)override{return p.music_buffer_status(t,s,h);}
        bool restore_music_buffer(u32 t,u32& h)override{return p.restore_music_buffer(t,h);}
        bool sleep_music_restore(u32 ms)override{return p.sleep_music_restore(ms);}
        bool lock_music_data(u32 t,u32 n,MusicBufferLock& l,u32& h)override{return p.lock_music_data(t,n,l,h);}
        bool unlock_music_data(u32 t,const MusicBufferLock& l,u32& h)override{return p.unlock_music_data(t,l,h);}
        bool fill_music_bytes(u32 d,u8 v,u32 n)override{return p.fill_music_bytes(d,v,n);}
        bool copy_music_bytes(u32 d,u32 s,u32 n)override{return p.copy_music_bytes(d,s,n);}
        bool seek_music_stream(u32 h,u32 n)override{return p.seek_music_stream(h,n);}
        bool read_music_stream_file(u32 h,u32 d,u32 n,u32& a)override{return p.read_music_stream_file(h,d,n,a);}
        bool close_music_stream_file(u32 h)override{return p.close_music_stream_file(h);}
        bool notify_position_service(u32 t,bool pp,u32& play,bool wp,u32& write,u32& hr)override{auto* b=p.music_buffer(t);if(!b)return false;if(pp)play=b->position;if(wp)write=b->write_position;hr=0;return true;}
        bool lock_music_ring(u32 t,u32 offset,u32 n,MusicRingLock& lock,u32& hr)override{auto* b=p.music_buffer(t);if(!b||offset>=b->pcm.size()||n>b->pcm.size())return false;const u32 first=std::min(n,u32(b->pcm.size())-offset);lock={b->sample+offset,first,n>first?b->sample:0,n-first};b->locked=true;hr=0;return true;}
        bool enter_music_ring()override{return false;}
        bool leave_music_ring()override{return false;}
        bool wait_music_notify(u32 event,u32& result)override{if(!p.notification_pending||event!=p.bank.audio.get(0x5780)||!p.event_handles.count(event))return false;p.notification_pending=false;result=p.notification_outcome;return true;}
        bool peek_music_notify(AnmView msg,bool& available)override{available=p.quit_pending;if(available){std::memset(msg.data,0,28);msg.put(4,0x12);p.quit_pending=false;}return true;}
    } notifier;
    explicit OwnedMusicMemoryPlatformV3(AnmView audio):bank(audio),notifier(*this){}
    void reset(){allocations.clear();file_positions.clear();free_ranges.clear();music_buffers.clear();reused_buffers=0;next_allocation=0xb0000000;next_file=0x6f000000;next_event=0x6d100000;next_thread=0x6d200000;next_thread_id=0x6d300000;current_thread=current_thread_id=0;event_handles.clear();clock=0;random_state=1;prepared=event_live=thread_live=quit_pending=notification_pending=false;notification_message.fill(0);worker_state={};notifier.notify_scratch={};notifier.notify_nesting=0;bank.events.clear();bank.buffers.clear();bank.reads=bank.sleeps=bank.creates=bank.duplicates=bank.frees=0;for(auto& w:bank.waves){w.live.clear();w.alive=false;}}
    bool prepare(){
        if(prepared)return true;if(!bank.audio.data||bank.audio.get(0x5778)||bank.waves.size()!=77||bank.catalog.size()!=1760||metadata.size()<520)return false;
        if(!prepare_sound_catalog(bank.audio,0x57b0,bank.catalog.data(),bank.catalog.size(),0x4e1280))return false;
        bank.audio.put(0,SoundBankRuntime::device);bank.audio.put(12,wrapper_token);bank.audio.put(0x1980,metadata_token);bank.audio.put(0x5788,archive_file_base);bank.audio.put(0x57a4,100);bank.audio.put(0x57a8,100);std::memcpy(bank.audio.data+0x5678,"thbgm.dat",10);
        std::vector<const char*> names;for(const auto& w:bank.waves)names.push_back(w.name.c_str());if(!preload_sound_archive(bank.audio,0x57b0,names.data(),names.size(),bank))return false;
        for(u32 i=0;i<88;++i){const u8* descriptor=nullptr;if(!bank.sound_descriptor(bank.audio.get(0x1a84+i*24+8),descriptor))return false;u32 file=0;std::memcpy(&file,descriptor+4,4);if(file>=77)return false;u32 hr=0;if(!load_sound_voice(bank.audio,0x57b0,i,bank.waves[file].name.c_str(),bank,hr)||signed_word(hr)<0)return false;}
        prepared=true;return true;
    }
    bool dispatch(u32 outcome){if(!thread_live||worker_state.finished||notification_pending)return false;notification_outcome=outcome;notification_pending=true;return dispatch_music_notification({bank.audio.data+0x5778},12,{notification_message.data()},28,worker_state,notifier);}
    MusicPlatformBufferV3* music_buffer(u32 token){if(token<0x9f000000||(token-0x9f000000)%0x1000)return nullptr;const u32 i=(token-0x9f000000)/0x1000;return i<music_buffers.size()&&music_buffers[i].alive?&music_buffers[i]:nullptr;}
    bool allocate_block(u32 n,u32& token){
        if(n>0x08000000)return false;const u32 extent=std::max(4096u,(n+4095)&~4095u);bool found=false;
        for(auto it=free_ranges.begin();it!=free_ranges.end();++it)if(it->second>=extent){token=it->first;const u32 remaining=it->second-extent;free_ranges.erase(it);if(remaining)free_ranges.emplace(token+extent,remaining);found=true;break;}
        if(!found){if(std::uint64_t(next_allocation)+extent>0xf0000000)return false;token=next_allocation;next_allocation+=extent;}
        return allocations.emplace(token,std::vector<u8>(std::max(n,1u),0)).second;
    }
    bool free_block(u32 token){
        if(!token)return true;auto allocation=allocations.find(token);if(allocation==allocations.end())return false;
        u32 start=token,extent=std::max(4096u,(u32(allocation->second.size())+4095)&~4095u);allocations.erase(allocation);
        auto next=free_ranges.lower_bound(start);if(next!=free_ranges.begin()){auto previous=std::prev(next);if(previous->first+previous->second==start){start=previous->first;extent+=previous->second;free_ranges.erase(previous);}}
        next=free_ranges.lower_bound(start);if(next!=free_ranges.end()&&start+extent==next->first){extent+=next->second;free_ranges.erase(next);}
        if(start+extent==next_allocation)next_allocation=start;else free_ranges.emplace(start,extent);return true;
    }
    bool music_region(u32 token,u32 n,AnmView& out)override{
        if(token>=0x53b1e0&&token-0x53b1e0<=0x57b0&&n<=0x57b0-(token-0x53b1e0)){out={bank.audio.data+token-0x53b1e0};return true;}
        if(token==wrapper_token&&n<=4){out={reinterpret_cast<u8*>(&wrapper_device)};return true;}
        if(token>=metadata_token&&token-metadata_token<=metadata.size()&&n<=metadata.size()-(token-metadata_token)){out={metadata.data()+token-metadata_token};return true;}
        auto it=allocations.upper_bound(token);if(it!=allocations.begin()){--it;const u32 at=token-it->first;if(at<=it->second.size()&&n<=it->second.size()-at){out={it->second.data()+at};return true;}}
        for(auto& b:music_buffers)if(b.alive&&token>=b.sample&&token-b.sample<=b.pcm.size()&&n<=b.pcm.size()-(token-b.sample)){out={b.pcm.data()+token-b.sample};return true;}return false;
    }
    AnmView owned_music_audio()override{return bank.audio;}
    bool owned_music_query_output(u32 entry,u32& out)override{if(entry==0x486af0)out=0x7001efd0;else if(entry==0x4863a0)out=0x7001efc4;else return false;return true;}
    bool music_track_table(u32 token,const u8*& out,u32& n)override{if(token!=metadata_token)return false;out=metadata.data();n=metadata.size();return true;}
    bool sound_descriptor(u32 token,const u8*& out)override{return bank.sound_descriptor(token,out);}
    bool query_sound_status(u32 token,u32& status,u32& hr)override{return bank.query_sound_status(token,status,hr);}
    bool music_buffer_status(u32 token,u32& status,u32& hr)override{auto* b=music_buffer(token);if(!b)return false;status=b->playing;hr=0;return true;}
    bool sound_voice_call(u32 token,u32 method,const u32* args,u32 count,u32& hr)override{
        auto* b=music_buffer(token);if(!b)return bank.sound_voice_call(token,method,args,count,hr);hr=0;
        if(method==0x48&&count==0){b->playing=0;bank.event(method,{token,hr});}
        else if(method==0x34&&count==1){u16 align;std::memcpy(&align,b->format.data()+12,2);if(!align||args[0]>=b->pcm.size()){hr=0x80070057;}else b->position=args[0]-args[0]%align;bank.event(method,{token,args[0],hr});}
        else if((method==0x3c||method==0x40)&&count==1){const i32 value=signed_word(args[0]);if(value< -10000||value>(method==0x40?10000:0))hr=0x80070057;else(method==0x3c?b->volume:b->pan)=args[0];bank.event(method,{token,args[0],hr});}
        else if(method==0x30&&count==3){b->flags=args[2];b->playing=1;bank.event(method,{token,args[0],args[1],args[2],hr});}else return false;return true;
    }
    bool music_clock(double& value)override{value=clock;return true;}
    bool music_select_random(u32& value)override{random_state=random_state*214013+2531011;value=(random_state>>16)&32767;return true;}
    u32 music_file_base()const override{return bank.audio.get(0x5788);}
    u32 music_thread_parameter()const override{return 0x6d000000;}
    bool create_cached_music_event(u32& handle)override{event_live=true;handle=next_event;next_event+=16;event_handles.insert(handle);return true;}
    bool create_cached_music_thread(u32 entry,u32,AnmView audio,u32& handle)override{if(entry!=0x473700||(thread_live&&!worker_state.finished))return false;thread_live=true;worker_state={};notifier.notify_scratch={};notification_message.fill(0);current_thread_id=next_thread_id;next_thread_id+=16;audio.put(0x10,current_thread_id);current_thread=next_thread;next_thread+=16;handle=current_thread;return true;}
    bool post_music_thread_quit(u32 id)override{if(id!=current_thread_id)return true;if(thread_live&&!worker_state.finished){quit_pending=true;return dispatch(1);}return true;}
    bool wait_music_thread(u32 handle,u32,u32& status)override{if(handle!=current_thread)return false;status=worker_state.finished?0:0x102;return true;}
    bool close_music_thread(u32 handle)override{if(handle==current_thread)thread_live=false;else if(event_handles.erase(handle))event_live=!event_handles.empty();return true;}
    bool allocate_music_owner_array(u32 n,u32& t)override{return allocate_block(n,t);}
    bool allocate_music_initialize_object(u32 n,u32& t)override{return allocate_block(n,t);}
    bool allocate_music_initialize_notify(u32 n,u32& t)override{return allocate_block(n,t);}
    bool free_music_initialize_notify(u32 t)override{return free_block(t);}
    bool allocate_music_metadata(u32 n,u32& t)override{return allocate_block(n,t);}
    bool free_music_metadata(u32 t)override{return free_block(t);}
    bool free_music_owner_array(u32 t)override{return free_block(t);}
    bool free_music_owner_object(u32 t)override{return free_block(t);}
    bool free_music_initialize_stream(u32 t)override{return free_block(t);}
    bool create_memory_music_buffer(u32 device,const u8* desc,u32& token,u32& hr)override{
        if(device!=wrapper_device||!desc)return false;AnmView v{const_cast<u8*>(desc)},format{nullptr};const u32 n=v.get(8);if(!n||n>=0x1000000||!music_region(v.get(16),18,format))return false;
        u32 slot=0;while(slot<music_buffers.size()&&music_buffers[slot].alive)++slot;if(slot>=16)return false;
        MusicPlatformBufferV3 b;b.token=0x9f000000+slot*0x1000;b.sample=0xa0000000+slot*0x1000000;b.pcm.assign(n,0);std::memcpy(b.format.data(),format.data,18);token=b.token;
        if(slot==music_buffers.size())music_buffers.push_back(std::move(b));else{music_buffers[slot]=std::move(b);++reused_buffers;}
        hr=0;bank.event(0x300,{token,slot,n},format.data,18);return true;
    }
    bool query_memory_music_notify(u32 buffer,u32& notify,u32& hr)override{if(!music_buffer(buffer))return false;notify=0x9e000000+buffer-0x9f000000;hr=0;return true;}
    bool set_memory_music_notifications(u32 notify,u32 count,u32 table,u32& hr)override{auto* b=music_buffer(0x9f000000+notify-0x9e000000);AnmView v{nullptr};if(!b||count>64||!music_region(table,count*8,v))return false;b->notifications.resize(count*2);std::memcpy(b->notifications.data(),v.data,count*8);bank.event(0x303,{b->token,count},v.data,count*8);hr=0;return true;}
    bool release_memory_music_notify(u32,u32& remaining)override{remaining=0;return true;}
    bool query_metadata_notify(u32 b,u32& n,u32& hr)override{return query_memory_music_notify(b,n,hr);}
    bool set_metadata_notifications(u32 n,u32 c,u32 t,u32& hr)override{return set_memory_music_notifications(n,c,t,hr);}
    bool create_metadata_buffer(u32 device,const u8* desc,u32 slot,u32& hr)override{u32 token=0;AnmView v{nullptr};if(!create_memory_music_buffer(device,desc,token,hr)||!music_region(slot,4,v))return false;v.put(0,token);return true;}
    bool release_music_interface(u32 token,u32& remaining)override{if(token>=0x9e000000&&token<0x9f000000)return release_memory_music_notify(token,remaining);return release_destroyed_music_buffer(token,remaining);}
    bool release_destroyed_music_buffer(u32 token,u32& remaining)override{auto* b=music_buffer(token);if(!b)return false;b->playing=0;b->alive=false;std::vector<u8>().swap(b->pcm);std::vector<u32>().swap(b->notifications);remaining=0;bank.event(0x301,{token,0});return true;}
    bool restore_music_buffer(u32 token,u32& hr)override{if(!music_buffer(token))return false;hr=0;return true;}
    bool sleep_music_restore(u32)override{return false;}
    bool lock_music_data(u32 token,u32 n,MusicBufferLock& lock,u32& hr)override{auto* b=music_buffer(token);if(!b||n>b->pcm.size())return false;lock={b->sample,n};b->locked=true;hr=0;return true;}
    bool unlock_music_data(u32 token,const MusicBufferLock& lock,u32& hr)override{auto* b=music_buffer(token);AnmView pcm{nullptr};if(!b||!music_region(lock.first,lock.bytes,pcm))return false;b->locked=false;hr=0;bank.event(0x302,{token,lock.first-b->sample,lock.bytes},pcm.data,lock.bytes);return true;}
    bool fill_music_bytes(u32 destination,u8 value,u32 n)override{AnmView p{nullptr};if(!music_region(destination,n,p))return false;if(n)std::memset(p.data,value,n);return true;}
    bool copy_music_bytes(u32 destination,u32 source,u32 n)override{AnmView d{nullptr},s{nullptr};if(!music_region(destination,n,d)||!music_region(source,n,s))return false;if(n)std::memcpy(d.data,s.data,n);return true;}
    bool free_music_cache(u32 token)override{return free_block(token);}
    bool open_music_file(const char* name,u32,u32,u32,u32,u32& handle)override{if(!name)return false;if(std::strcmp(name,"thbgm.dat")||archive.empty()){handle=0xffffffff;return true;}handle=next_file++;file_positions.emplace(handle,0);return true;}
    bool seek_music_file(u32 handle,u32 offset)override{auto it=file_positions.find(handle);if(it==file_positions.end())return false;it->second=offset;return true;}
    bool allocate_music_cache(u32 n,u32& token)override{return allocate_block(n,token);}
    bool read_archive(u32 handle,u32 destination,u32 n,u32& actual){auto it=file_positions.find(handle);AnmView v{nullptr};if(it==file_positions.end()||!music_region(destination,n,v))return false;const u32 at=it->second;actual=at<archive.size()?std::min(n,u32(archive.size())-at):0;if(actual)std::memcpy(v.data,archive.data()+at,actual);it->second+=actual;return true;}
    bool read_music_file(u32 handle,u32 token,u32 n)override{u32 actual=0;return read_archive(handle,token,n,actual);}
    bool close_music_file(u32 handle)override{return file_positions.erase(handle)==1;}
    bool music_load_progress(u32)override{return true;}
    bool music_load_error(const char*)override{return true;}
    bool seek_music_stream(u32 h,u32 n)override{return seek_music_file(h,n);}
    bool read_music_stream_file(u32 h,u32 d,u32 n,u32& actual)override{return read_archive(h,d,n,actual);}
    bool close_music_stream_file(u32 h)override{return close_music_file(h);}
    bool music_file_position(u32 h,u32& value)override{auto it=file_positions.find(h);if(it==file_positions.end())return false;value=it->second;return true;}
    bool music_file_close(u32 h)override{return close_music_file(h);}
    bool close_destroyed_music_file(u32 h)override{return close_music_file(h);}
    bool log_music_open(u32)override{return true;}
    bool create_music_file(u32 path,u32& handle)override{if(path==0x4c6034)return open_music_file("thbgm.dat",0,0,0,0,handle);AnmView v{nullptr};if(!music_region(path,1,v))return false;return open_music_file(reinterpret_cast<const char*>(v.data),0,0,0,0,handle);}
    bool music_last_error(u32& error)override{error=2;return true;}
    bool format_music_error(u32,u32&)override{return false;}
    bool log_music_error(u32)override{return false;}
    bool free_music_error(u32)override{return false;}
    bool log_music_metadata(u32,u32,u32)override{return true;}
};
}
