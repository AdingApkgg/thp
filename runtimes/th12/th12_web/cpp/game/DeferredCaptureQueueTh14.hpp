#pragma once
#include <array>
#include <cstdint>
namespace th11 {
struct DeferredCaptureRequestTh14 {
 std::int32_t file_index=-1,texture_index=0;
 // Both rectangles retain the original x/y/width/height record words.
 std::array<std::int32_t,4> source{},destination{};
};
static_assert(sizeof(DeferredCaptureRequestTh14)==40);
struct DeferredCaptureQueueTh14 {
 std::array<DeferredCaptureRequestTh14,4> slots{};
 std::int32_t first_file_index()const noexcept{return slots[0].file_index;}
 std::int32_t enqueue(const DeferredCaptureRequestTh14& request) noexcept {
  for(auto& slot:slots)if(slot.file_index<0){slot=request;break;}
  return 0; // Original44bdd0 also returns0 when all slots are occupied.
 }
 template<class Copy> void consume(Copy&& copy){
  for(auto& slot:slots)if(slot.file_index>=0){
   copy(slot); // Null target and GetSurfaceLevel error still retire the record.
   slot.file_index=-1;
  }
 }
};
}
