#include "../../cpp/game/ImageResample.cpp"
namespace th11 {
static std::vector<Weight> diagnostic;
extern "C" __attribute__((export_name("load"))) u32 load(u32 source,u32 destination){
    diagnostic.clear();
    for(const auto& row:weights(source,destination,true)){
        diagnostic.push_back({u32(row.size()),0});
        diagnostic.insert(diagnostic.end(),row.begin(),row.end());
    }
    return diagnostic.size();
}
extern "C" __attribute__((export_name("data"))) const void* data(){return diagnostic.data();}
}
