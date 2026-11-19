#include "ReplayPercentFormatV2.hpp"
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <limits>
namespace th143 {
bool format_replay_percent_v2(float value,std::string& out){
 const u32 bits=word(value);if((bits&0x7f800000)==0x7f800000){out=bits&0x80000000?"-1.$":"1.$";return true;}
 double converted=double(value);char buffer[128];
 if(std::fabs(converted)>=1e16){
  // Embedded CRT produces at most17 significant digits before expanding a
  // large fixed number. These binary32 values have no fractional component.
  const int n=std::snprintf(buffer,sizeof buffer,"%.16e",std::fabs(converted));if(n<0||n>=int(sizeof buffer))return false;const char* exponent=std::strchr(buffer,'e');if(!exponent)return false;const int places=std::atoi(exponent+1)+1;
  out=std::signbit(converted)?"-":"";u32 digits=0;for(const char* p=buffer;p<exponent;++p)if(*p!='.'){out+=*p;++digits;}if(places<int(digits))return false;out.append(u32(places)-digits,'0');out+=".0";return true;
 }
 // binary32 times10 is exact in binary64; embedded CRT uses decimal ties
 // away from zero, while the WASI formatter uses ties to even.
 const double scaled=std::fabs(converted*10.);if(scaled-std::floor(scaled)==.5)converted=std::nextafter(converted,std::signbit(converted)?-std::numeric_limits<double>::infinity():std::numeric_limits<double>::infinity());
 const int n=std::snprintf(buffer,sizeof buffer,"%2.1f",converted);if(n<0||n>=int(sizeof buffer))return false;out.assign(buffer,u32(n));return true;
}
}
