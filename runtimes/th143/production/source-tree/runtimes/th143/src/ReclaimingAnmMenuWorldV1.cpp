#include "ReclaimingAnmMenuWorldV1.hpp"
#include <algorithm>
namespace th143 {
ReclaimingAnmMenuWorldV1::ReclaimingAnmMenuWorldV1(AnmResourceServices& s,u32 base):AnmMenuWorld(s,base),runtime_services(s){}
bool ReclaimingAnmMenuWorldV1::allocate_resource_storage(u32 n,bool array,u32& token){
    if(n>0x4000000)return false;
    const u32 capacity=(std::max(1u,n)+15u)&~15u;
    auto best=free_ranges.end();
    for(auto i=free_ranges.begin();i!=free_ranges.end();++i)if(i->second>=capacity&&(best==free_ranges.end()||i->second<best->second))best=i;
    if(best==free_ranges.end()){
        if(!AnmMenuWorld::allocate_resource_storage(n,array,token))return false;
    }else{
        token=best->first;const u32 available=best->second;free_ranges.erase(best);
        if(available>capacity)free_ranges.emplace(token+capacity,available-capacity);
        regions.push_back({token,std::vector<u8>(std::max(1u,n),0xcd)});
        resource_allocations.push_back(token);runtime_services.animation_storage_allocated(token,n,array);++reused_allocations;
    }
    return owned_ranges.emplace(token,capacity).second;
}
void ReclaimingAnmMenuWorldV1::return_range(u32 token,u32 capacity){
    auto next=free_ranges.lower_bound(token);
    if(next!=free_ranges.begin()){
        auto previous=std::prev(next);
        if(std::uint64_t(previous->first)+previous->second==token){token=previous->first;capacity+=previous->second;free_ranges.erase(previous);}
    }
    next=free_ranges.lower_bound(token);
    if(next!=free_ranges.end()&&std::uint64_t(token)+capacity==next->first){capacity+=next->second;free_ranges.erase(next);}
    free_ranges.emplace(token,capacity);
}
bool ReclaimingAnmMenuWorldV1::retire_consumed_storage(){
    if(releases.size()%2)return false;
    if(release_cursor>releases.size())return false;
    for(;release_cursor<releases.size();release_cursor+=2){
        const u32 token=releases[release_cursor+1];if(!token)continue;
        auto region=std::find_if(regions.begin(),regions.end(),[&](const Region& r){return r.token==token;});
        if(region==regions.end())continue;
        const std::uint64_t end=std::uint64_t(token)+region->bytes.size();
        const auto contains=[&](u32 p){return p>=token&&std::uint64_t(p)<end;};
        // A still-published resource is a real ownership error, not permission
        // to retain arbitrarily many retired allocations.
        for(const auto& r:resources)if(contains(r.token)||contains(r.table)||contains(r.template_token)||std::any_of(r.scripts.begin(),r.scripts.end(),contains)){
            ++reference_failures;return false;
        }
        reclaimed_bytes+=region->bytes.size();++reclaimed_regions;regions.erase(region);
        auto own=owned_ranges.find(token);
        if(own!=owned_ranges.end()){const u32 capacity=own->second;owned_ranges.erase(own);return_range(token,capacity);}
        geometry_buffers.erase(std::remove_if(geometry_buffers.begin(),geometry_buffers.end(),[&](const Region& r){return r.token==token;}),geometry_buffers.end());
    }
    return true;
}
u32 ReclaimingAnmMenuWorldV1::storage_diagnostic(u32 field)const{
    std::uint64_t bytes=0,free=0;for(const auto& r:regions)bytes+=r.bytes.size();for(const auto& r:free_ranges)free+=r.second;
    switch(field){case 0:return regions.size();case 1:return u32(bytes);case 2:return u32(bytes>>32);case 3:return reclaimed_regions;case 4:return u32(reclaimed_bytes);case 5:return u32(reclaimed_bytes>>32);case 6:return reused_allocations;case 7:return free_ranges.size();case 8:return u32(free);case 9:return release_cursor;case 10:return releases.size();case 11:return reference_failures;case 12:return resources.size();default:return 0;}
}
}
