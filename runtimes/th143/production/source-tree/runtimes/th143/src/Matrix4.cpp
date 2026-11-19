#include "Matrix4.hpp"
#include <cmath>
namespace th143 {
Matrix4 matrix_identity(){Matrix4 result{};for(u32 i=0;i<4;++i)result[i*5]=1.f;return result;}
Matrix4 matrix_multiply(const Matrix4& a,const Matrix4& b){Matrix4 out;
    for(u32 i=0;i<4;++i)for(u32 j=0;j<4;++j){const float p=a[i*4]*b[j],q=a[i*4+1]*b[4+j],r=a[i*4+2]*b[8+j],s=a[i*4+3]*b[12+j];float value=p+q;if(i==0||i==3)value+=r+s;else{value+=r;value+=s;}out[i*4+j]=value;}return out;
}
Matrix4 matrix_rotation(u32 axis,float angle){auto out=matrix_identity();const float c=float(std::cos(double(angle))),s=float(std::sin(double(angle)));
    if(axis==0){out[5]=c;out[6]=s;out[9]=-s;out[10]=c;}else if(axis==1){out[0]=c;out[2]=-s;out[8]=s;out[10]=c;}else{out[0]=c;out[1]=s;out[4]=-s;out[5]=c;}return out;
}
}
