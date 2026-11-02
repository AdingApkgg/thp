// Finite candidate for an isolated helper experiment, not the game allocator.
#include <cstdint>

namespace {
struct Block { std::uint32_t start,size,stamp; };
struct Allocation { std::uint32_t start,size; bool active; };
Block free_blocks[128]; Allocation allocations[128];
std::uint32_t base_address=0,region_size=0,free_count=0,clock_value=0;
bool error=false;
void remove_free(std::uint32_t index){free_blocks[index]=free_blocks[--free_count];}
}

extern "C" {
void heap_model_reset(std::uint32_t base,std::uint32_t bytes){
    base_address=base;region_size=bytes;free_count=1;clock_value=0;error=false;
    free_blocks[0]={0,bytes,0};for(auto& item:allocations)item={0,0,false};
    if(!bytes||std::uint64_t(base)+bytes>0x100000000ull)error=true;
}
std::uint32_t heap_model_alloc(std::uint32_t requested){
    const std::uint64_t aligned=(std::uint64_t(requested)+8+7)&~std::uint64_t(7);
    if(error||!requested||aligned>0xffffffffull)return 0;
    const auto size=std::uint32_t(aligned);std::uint32_t best=free_count;
    for(std::uint32_t i=0;i<free_count;++i){
        const auto& b=free_blocks[i];if(b.size<size)continue;
        if(best==free_count||b.size<free_blocks[best].size||
#ifdef TH14_HEAP_MODEL_FIFO_CONTROL
           (b.size==free_blocks[best].size&&b.stamp<free_blocks[best].stamp))best=i;
#else
           (b.size==free_blocks[best].size&&b.stamp>free_blocks[best].stamp))best=i;
#endif
    }
    if(best==free_count)return 0;std::uint32_t slot=128;
    for(std::uint32_t i=0;i<128;++i)if(!allocations[i].active){slot=i;break;}
    if(slot==128){error=true;return 0;}
    auto& block=free_blocks[best];const auto start=block.start;
    if(std::uint64_t(base_address)+start+8>0xffffffffull){error=true;return 0;}
    block.start+=size;block.size-=size;if(!block.size)remove_free(best);
    allocations[slot]={start,size,true};return base_address+start+8;
}
int heap_model_free(std::uint32_t address){
    if(error||std::uint64_t(address)<std::uint64_t(base_address)+8)return 0;std::uint32_t slot=128;
    for(std::uint32_t i=0;i<128;++i)if(allocations[i].active&&base_address+allocations[i].start+8==address){slot=i;break;}
    if(slot==128||free_count==128)return 0;
    Block item{allocations[slot].start,allocations[slot].size,++clock_value};allocations[slot].active=false;
#ifndef TH14_HEAP_MODEL_NO_MERGE_CONTROL
    for(std::uint32_t i=0;i<free_count;){
        const auto other=free_blocks[i];
        if(std::uint64_t(other.start)+other.size==item.start){item.start=other.start;item.size+=other.size;remove_free(i);i=0;}
        else if(std::uint64_t(item.start)+item.size==other.start){item.size+=other.size;remove_free(i);i=0;}
        else ++i;
    }
#endif
    free_blocks[free_count++]=item;return 1;
}
int heap_model_ok(){return !error;}
}
