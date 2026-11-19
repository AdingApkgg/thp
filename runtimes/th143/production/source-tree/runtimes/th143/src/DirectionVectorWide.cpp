#include "DirectionVector.hpp"
#include <cmath>

namespace th143 {
bool direction_vector(float angle, float speed, DirectionVector& result) {
    if (!std::isfinite(angle) || !std::isfinite(speed) ||
        std::fabs(angle) > real(0x46000000)) return false;
    result.x = float(std::cos(double(angle)) * double(speed));
    result.y = float(std::sin(double(angle)) * double(speed));
    return true;
}
}
