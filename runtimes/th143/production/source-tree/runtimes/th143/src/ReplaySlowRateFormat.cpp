#include "ReplaySlowRateFormat.hpp"
#include <cmath>
namespace th143 {
bool format_replay_slow_rate(std::string_view pattern,float value,std::string& out){
 std::string number;const u32 bits=word(value),exponent=bits&0x7f800000,mantissa=bits&0x7fffff;
 if(exponent==0x7f800000){number=bits&0x80000000?"-1.#":"1.#";number+=!mantissa||bits==0xffc00000?'J':'R';}
 else if(!format_ascii_value("%.2f",double(value),number))return false;
 out.clear();bool replaced=false;for(std::size_t i=0;i<pattern.size();){if(pattern[i]!='%'){out+=pattern[i++];continue;}if(pattern.substr(i,5)=="%2.2f"&&!replaced){out+=number;i+=5;replaced=true;}else if(pattern.substr(i,2)=="%%"){out+='%';i+=2;}else return false;}return replaced;
}
}
