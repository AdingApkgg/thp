#include "th14-triangle-weights-fixture.cpp"
namespace th11 {
extern "C" __attribute__((export_name("load_high"))) u32 load_high(u32 source,u32 destination){
    diagnostic.clear();
    for(const auto& row:weights(source,destination,true,true)){
        diagnostic.push_back({u32(row.size()),0});
        diagnostic.insert(diagnostic.end(),row.begin(),row.end());
    }
    return diagnostic.size();
}
}
