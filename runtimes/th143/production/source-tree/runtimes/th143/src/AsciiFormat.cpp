#include "AsciiFormat.hpp"
#include <cmath>
#include <cstdio>
#include <limits>
namespace th143 {
namespace {
bool decimal_half(double value,u32 precision){
    std::uint64_t bits;std::memcpy(&bits,&value,8);const u32 exponent=u32((bits>>52)&2047);std::uint64_t significand=bits&0xfffffffffffffull;if(exponent)significand|=1ull<<52;
    const i32 power=(exponent?i32(exponent)-1023-52:-1074)+i32(precision),denominator=-power;if(denominator<1||denominator>63)return false;
    static constexpr u32 five[]={1,5,25};significand*=five[precision];return (significand&((1ull<<denominator)-1))==(1ull<<(denominator-1));
}
}
bool format_ascii_value(std::string_view format,double value,std::string& out){
    if(format=="M"||format=="$"||format=="."||format=="NO BONUS"){out=std::string(format);return true;}
    if(!std::isfinite(value))return false;char text[256];int n=-1;const std::string f(format);
    if(format=="%d"||format=="%d%%"||format=="%8d"||format=="%3d"||format=="%.2d"||format=="%3d."||format=="%.2ds"){
        if(value<-2147483648.||value>=2147483648.)return false;n=std::snprintf(text,sizeof(text),f.c_str(),i32(value));
    }else if(format=="%2.1ffps"||format=="%.0f%%"||format=="%.2fs"||format=="%.2f"||format=="BONUS %.1f"){
        // The embedded MSVC CRT rounds exact decimal halves away from zero;
        // WASI printf uses ties-to-even. Test the exact binary significand,
        // without a rounded value*10^p that would misclassify e.g.2.675.
        const u32 precision=format=="%.0f%%"?0:(format=="%.2fs"||format=="%.2f")?2:1;
        if(decimal_half(value,precision))value=std::nextafter(value,std::signbit(value)?-std::numeric_limits<double>::infinity():std::numeric_limits<double>::infinity());
        n=std::snprintf(text,sizeof(text),f.c_str(),value);
    }
    if(n<0||n>=int(sizeof(text)))return false;out.assign(text,u32(n));return true;
}
std::string format_ascii_score(u32 value,u32 digit){
    if(value<100)return std::to_string(signed_word(value*10+digit));
    auto group=[](u32 n,u32 width){auto s=std::to_string(n);if(s.size()<width)s.insert(0,width-s.size(),'0');return s;};
    const auto tail=group(value%100,2)+std::to_string(signed_word(digit));value/=100;std::string out;
    while(value>=1000){out=","+group(value%1000,3)+out;value/=1000;}
    return std::to_string(value)+out+","+tail;
}
}
