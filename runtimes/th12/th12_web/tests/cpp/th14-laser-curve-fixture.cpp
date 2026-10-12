#include "../../cpp/game/LaserCurveTh14.hpp"
#include "../../cpp/game/EclContext.hpp"
#include "../../cpp/game/Timer.hpp"
#include <cstdlib>
using namespace th11;
namespace {Th14CurveSample sample;Th14CurvePath path;std::vector<Th14CurveVertex> mesh;std::vector<Vec3> deliveries;bool marked=false;}
static Timer rectangle_timer;static float rectangle_rate;static std::vector<std::array<u8,0x354>> fragments;
extern "C" {
__attribute__((export_name("allocate"))) void* allocate(u32 size){return std::malloc(size);}
__attribute__((export_name("release"))) void release(void* p){std::free(p);}
__attribute__((export_name("run"))) u32 run(const u32* node,u32 time,const u32* previous,u32 tail){
    Th14CurveNode n;n.start=float_bits(node[2]);n.end=float_bits(node[3]);n.mode=i32(node[4]);
    n.direction={float_bits(node[5]),float_bits(node[6]),float_bits(node[7])};
    n.position={float_bits(node[8]),float_bits(node[9]),float_bits(node[10])};
    n.angle=float_bits(node[11]);n.speed=float_bits(node[12]);n.acceleration=float_bits(node[13]);n.turn=float_bits(node[14]);
    sample.position={float_bits(u32(0x42c80000)),float_bits(u32(0xc2c80000)),float_bits(u32(0x40e00000))};sample.speed=123.f;sample.angle=-123.f;
    Th14CurveSample p;p.position={float_bits(previous[0]),float_bits(previous[1]),float_bits(previous[2])};p.speed=float_bits(previous[3]);p.angle=float_bits(previous[4]);
    return tail?th14_curve_tail(n,float_bits(time),p,sample):th14_curve_head(n,float_bits(time),sample);
}
__attribute__((export_name("value"))) u32 value(u32 n){
    const float values[]={sample.position.x,sample.position.y,sample.position.z,sample.speed,sample.angle};return n<5?float_bits(values[n]):0;
}
__attribute__((export_name("initialize"))) u32 initialize(const u8* request){return path.initialize(request);}
__attribute__((export_name("initialize_inherited"))) u32 initialize_inherited(const u8* request,const u32* payload,u32 count){
 std::vector<Th14CurveNode> nodes;for(u32 j=0;j<count;++j){const u32* p=payload+j*15;Th14CurveNode n;n.start=float_bits(p[2]);n.end=float_bits(p[3]);n.mode=i32(p[4]);n.direction={float_bits(p[5]),float_bits(p[6]),float_bits(p[7])};n.position={float_bits(p[8]),float_bits(p[9]),float_bits(p[10])};n.angle=float_bits(p[11]);n.speed=float_bits(p[12]);n.acceleration=float_bits(p[13]);n.turn=float_bits(p[14]);nodes.push_back(n);}return path.initialize(request,&nodes);
}
__attribute__((export_name("transform_index"))) u32 transform_index(){return path.transform_index;}
__attribute__((export_name("request_word"))) u32 request_word(u32 n){u32 value;std::memcpy(&value,path.request+n*4,4);return value;}
__attribute__((export_name("transforms"))) u32 transforms(){return path.transforms();}
__attribute__((export_name("node_count"))) u32 node_count(){return path.nodes.size();}
__attribute__((export_name("node_word"))) u32 node_word(u32 index,u32 word){
    const auto& n=path.nodes.at(index);
    if(word==4)return u32(n.mode);
    const float values[]={0,0,n.start,n.end,0,n.direction.x,n.direction.y,n.direction.z,n.position.x,n.position.y,n.position.z,n.angle,n.speed,n.acceleration,n.turn};
    return word<15?float_bits(values[word]):0;
}
__attribute__((export_name("sample"))) void sample_path(u32 time){path.sample(float_bits(time));}
__attribute__((export_name("sample_word"))) u32 sample_word(u32 index,u32 word){
    const auto& s=path.samples.at(index);const float values[]={s.position.x,s.position.y,s.position.z,s.auxiliary.x,s.auxiliary.y,s.auxiliary.z,s.angle,s.speed};
    return word<8?float_bits(values[word]):0;
}
__attribute__((export_name("mesh"))) void make_mesh(){
    mesh.resize(path.samples.size()*2);float width;std::memcpy(&width,path.request+0x10,4);
    th14_curve_mesh(path.samples.data(),path.samples.size(),width,.125f,.875f,{224,16},mesh.data());
}
__attribute__((export_name("mesh_word"))) u32 mesh_word(u32 index,u32 word){
    const auto& v=mesh.at(index);if(word==4)return v.color;const float values[]={v.x,v.y,v.z,v.rhw,0,v.u,v.v};return word<7?float_bits(values[word]):0;
}
__attribute__((export_name("load_samples"))) void load_samples(const u32* p,u32 count){
    path.samples.resize(count);for(u32 i=0;i<count;++i){auto& s=path.samples[i];s.position={float_bits(p[i*8]),float_bits(p[i*8+1]),float_bits(p[i*8+2])};s.auxiliary={float_bits(p[i*8+3]),float_bits(p[i*8+4]),float_bits(p[i*8+5])};s.angle=float_bits(p[i*8+6]);s.speed=float_bits(p[i*8+7]);}
}
__attribute__((export_name("cut_circle"))) i32 cut_circle(u32 x,u32 y,u32 z,u32 radius,u32 protection,u32 skip){return path.cut_circle({float_bits(x),float_bits(y),float_bits(z)},float_bits(radius),protection!=0,skip!=0,deliveries,marked);}
__attribute__((export_name("rectangle_request"))) void rectangle_request(const u8* p){std::memcpy(path.request,p,sizeof(path.request));}
__attribute__((export_name("cut_rectangle"))) i32 cut_rectangle(u32 x,u32 y,u32 z,u32 width,u32 height,u32 angle,float rate,u32 protection,u32 skip){rectangle_rate=rate;rectangle_timer={29,30,30.5f,&rectangle_rate,1};return path.cut_rectangle({float_bits(x),float_bits(y),float_bits(z)},{float_bits(width),float_bits(height)},float_bits(angle),protection!=0,skip!=0,rectangle_timer,deliveries,marked,fragments);}
__attribute__((export_name("rectangle_timer"))) u32 rectangle_time(u32 n){const u32 v[]={u32(rectangle_timer.previous),u32(rectangle_timer.current),float_bits(rectangle_timer.fractional)};return v[n];}
__attribute__((export_name("fragment_count"))) u32 fragment_count(){return fragments.size();}
__attribute__((export_name("fragment_word"))) u32 fragment_word(u32 n,u32 k){u32 v;std::memcpy(&v,fragments.at(n).data()+k*4,4);return v;}
__attribute__((export_name("marked"))) u32 cut_marked(){return marked;}
__attribute__((export_name("sample_count"))) u32 sample_count(){return path.samples.size();}
__attribute__((export_name("delivery_count"))) u32 delivery_count(){return deliveries.size();}
__attribute__((export_name("delivery_word"))) u32 delivery_word(u32 index,u32 word){const auto p=deliveries.at(index);return float_bits(word==0?p.x:word==1?p.y:p.z);}
}
