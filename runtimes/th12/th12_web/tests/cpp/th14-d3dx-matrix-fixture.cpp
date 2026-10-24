#include "../../cpp/game/GraphicsMath.hpp"
using namespace th11;
static Matrix4 matrices[3];
extern "C" {
__attribute__((export_name("input"))) void input(unsigned matrix,unsigned index,unsigned bits){if(matrix<2&&index<16)std::memcpy(matrices[matrix].m+index,&bits,4);}
__attribute__((export_name("multiply"))) void multiply(){matrices[2]=GraphicsMath::multiply(matrices[0],matrices[1]);}
__attribute__((export_name("rotation"))) void rotation(unsigned axis,unsigned bits){float angle;std::memcpy(&angle,&bits,4);matrices[2]=GraphicsMath::rotation(axis,angle);}
__attribute__((export_name("value"))) unsigned value(unsigned index){unsigned bits=0;if(index<16)std::memcpy(&bits,matrices[2].m+index,4);return bits;}
}
