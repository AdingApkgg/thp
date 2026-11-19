#pragma once
#include "EclVm.hpp"
#include <array>
namespace th143 {
using Matrix4=std::array<float,16>;
Matrix4 matrix_identity();
// Pinned D3DX SSE multiplication: rows0/3 add two pairs, rows1/2 sequentially.
Matrix4 matrix_multiply(const Matrix4&,const Matrix4&);
Matrix4 matrix_rotation(u32 axis,float angle);
}
