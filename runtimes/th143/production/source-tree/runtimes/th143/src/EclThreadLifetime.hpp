#pragma once
#include "EclOwner.hpp"
#include <functional>
namespace th143 {
using EclThreadRelease=std::function<void(const Vm&)>;
void bind_ecl_thread_release(EclOwner&,EclThreadRelease);
void release_ecl_thread_storage(EclOwner&,const Vm&);
}
