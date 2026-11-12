// Include the unchanged production translation unit and its decoder/stream adapter.
#include "AudioDevice.cpp"
#include <cstdlib>
#include <memory>
using namespace th11;
namespace {
std::vector<u8> layouts;
ma_decoder decoder{};bool opened=false;
std::unique_ptr<sdl::Th14MusicStream> stream;
float samples[4096*2]{};u32 meta[12]{};
ma_result last_result=MA_SUCCESS;
void close_track(){stream.reset();if(opened)ma_decoder_uninit(&decoder);opened=false;}
u32 read_words(const u8* p,u32 at){u32 v;std::memcpy(&v,p+at,4);return v;}
u32 read_half(const u8* p,u32 at){u16 v;std::memcpy(&v,p+at,2);return v;}
}
#define API(name) extern "C" __attribute__((export_name(#name)))
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(set_formats) u32 set_formats(const u8* p,u32 n){close_track();layouts.assign(p,p+n);return n;}
API(open_track) const u32* open_track(u32 index){
 close_track();std::memset(meta,0,sizeof(meta));last_result=MA_INVALID_ARGS;
 if(u64(index+1)*52>layouts.size())return meta;
 const auto* f=layouts.data()+index*52;const auto* end=std::find(f,f+16,u8(0));
 std::string name(reinterpret_cast<const char*>(f),size_t(end-f));
 auto dot=name.find_last_of('.');if(dot==std::string::npos)return meta;name.resize(dot);
 const std::string expected_path=std::string("/music/")+name+".ogg";auto path=expected_path;
 const u32 rate=read_words(f,36),channels=read_half(f,34),align=read_half(f,44);
 if(!align||channels!=2)return meta;
 auto config=ma_decoder_config_init(ma_format_f32,channels,rate);
 last_result=sdl::open_th14_music(path,config,decoder);meta[0]=u32(last_result);
 if(last_result!=MA_SUCCESS)return meta;opened=true;
 ma_uint64 length=0;last_result=ma_decoder_get_length_in_pcm_frames(&decoder,&length);
 meta[1]=u32(length);meta[2]=u32(length>>32);meta[3]=read_words(f,28)/align;
 meta[4]=read_words(f,24)/align;meta[5]=rate;meta[6]=channels;meta[7]=path==expected_path;
 ma_data_source_set_loop_point_in_pcm_frames(&decoder,meta[4],meta[3]);
 stream=std::make_unique<sdl::Th14MusicStream>(decoder,layouts,f);
 meta[8]=stream->initialized;meta[9]=u32(last_result);meta[10]=index;meta[11]=align;
 return meta;
}
API(sample_data) const float* sample_data(){return samples;}
API(read_raw) u32 read_raw(u32 count){
 if(!opened||count>4096)return 0;ma_uint64 got=0;last_result=ma_decoder_read_pcm_frames(&decoder,samples,count,&got);return u32(got);
}
API(seek_stream) i32 seek_stream(u32 frame){return stream?ma_data_source_seek_to_pcm_frame(&stream->base,frame):MA_INVALID_ARGS;}
API(loop_stream) i32 loop_stream(u32 enabled){return stream?ma_data_source_set_looping(&stream->base,enabled):MA_INVALID_ARGS;}
API(read_stream) u32 read_stream(u32 count){
 if(!stream||count>4096)return 0;ma_uint64 got=0;last_result=ma_data_source_read_pcm_frames(&stream->base,samples,count,&got);return u32(got);
}
API(cursor) u32 cursor(){ma_uint64 at=0;if(stream)ma_data_source_get_cursor_in_pcm_frames(&stream->base,&at);return u32(at);}
API(last_error) i32 last_error(){return last_result;}
API(close) void close_fixture(){close_track();layouts.clear();}
