#include "../../cpp/game/ShotTh16.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
API(run) i32 run(i32 kind,float x,float y,float w,float h,float angle,float radius,float ow,float oh,float other_angle){return kind?shot_th16_rectangles({2.25,300.5,0},{w,h},angle,{x,y,0},{ow,oh},other_angle):shot_th16_circle_rectangle({2.25,300.5,0},{w,h},angle,{x,y,0},radius);}
