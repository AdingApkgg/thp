#include "EclThreadLifetime.hpp"
#include <map>
namespace th143 {
namespace {std::map<EclOwner*,EclThreadRelease> releases;}
void bind_ecl_thread_release(EclOwner& owner,EclThreadRelease release){if(release)releases[&owner]=std::move(release);else releases.erase(&owner);}
void release_ecl_thread_storage(EclOwner& owner,const Vm& vm){const auto i=releases.find(&owner);if(i!=releases.end())i->second(vm);}
}
