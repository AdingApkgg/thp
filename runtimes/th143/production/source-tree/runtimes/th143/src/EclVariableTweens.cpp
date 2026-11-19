#include "EclVariableTweens.hpp"
namespace th143 {
void EclVariableTweens::initialize(u8 fill){scalars.fill(fill);origins.fill(nullptr);for(u32 i=0;i<8;++i){AnmView s{scalars.data()+i*0x30};s.put(0x24,s.get(0x24)&~1u);s.put(0x28,0);}}
i32 EclVariableTweens::command(Vm& vm,VmHost& host,AnmTimerHost& rates){
 const u32 op=vm.instruction->opcode;if(op!=91&&op!=92)return -2;
 const u32 slot=u32(vm.integer_argument(0,host));if(vm.failed||slot>=8)return -2;
 origins[slot]=vm.instruction;AnmView s{scalars.data()+slot*0x30};float ignored;if(!scalar_interpolate(s,rates,ignored))return -2;
 const u32 duration=u32(vm.integer_argument(2,host)),mode=u32(vm.integer_argument(3,host));const float start=vm.float_argument(4,host),end=vm.float_argument(5,host);if(vm.failed)return -2;
 s.put(0x28,duration);s.put(0x2c,mode);s.put(0,word(start));s.put(4,word(end));u8* target=vm.reference(1,host,true);if(vm.failed||!target)return -2;const u32 bits=word(start);std::memcpy(target,&bits,4);
 const float from=op==92?vm.float_argument(6,host):0.f,to=op==92?vm.float_argument(7,host):0.f;if(vm.failed)return -2;s.put(8,word(from));s.put(12,word(to));scalar_reset_timer(s,rates);return 0;
}
bool EclVariableTweens::advance(Vm& vm,VmHost& host,AnmTimerHost& rates){
 for(u32 slot=0;slot<8;++slot){AnmView s{scalars.data()+slot*0x30};if(!s.get(0x28))continue;if(!origins[slot])return false;Instruction* current=vm.instruction;vm.instruction=origins[slot];u8* target=vm.reference(1,host,true);vm.instruction=current;if(vm.failed||!target)return false;float value;if(!scalar_interpolate(s,rates,value))return false;const u32 bits=word(value);std::memcpy(target,&bits,4);}
 return true;
}
}
