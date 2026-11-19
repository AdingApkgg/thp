#include "FrameTimingCounter.hpp"
namespace th143 {
bool update_frame_timing_counter(AnmView t,FrameTimingCounterHost& h){
 if(!t.data)return false;auto read=[&](u32 p,u32& v){return h.frame_counter_read(p,&v,4);};auto write=[&](u32 p,u32 v){return h.frame_counter_write(p,&v,4);};auto get_double=[&](u32 at){double v;std::memcpy(&v,t.data+at,8);return v;};auto put_double=[&](u32 at,double v){std::memcpy(t.data+at,&v,8);};double now;if(!h.frame_counter_clock(now))return false;double previous=get_double(0x14);if(previous>now){put_double(0x14,now);previous=now;}const double elapsed=now-previous;
 if(elapsed>=1.){put_double(0x14,previous+elapsed);const float fps=float(double(t.get(0x20))/elapsed);t.put(0x34,word(fps));t.put(0x1c,fps>65.f?t.get(0x1c)+1:0);u32 root;if(!read(0x4e6a5c,root))return false;if(root){u32 clock,flags;if(!read(root+0x14,clock)||!read(root+0x80,flags))return false;if(signed_word(clock)>=20&&!(flags&0x14)){put_double(0x2c,get_double(0x2c)+60.);put_double(0x24,get_double(0x24)+(fps>57.f?60.:double(fps)));}if(!read(root+0x80,flags)||!write(root+0x80,flags&~0x80u))return false;}t.put(0x20,0);}
 u8 skipped;if(!h.frame_counter_read(0x4e49c4,&skipped,1))return false;t.put(0x20,t.get(0x20)+u32(skipped)+1);return true;
}
}
