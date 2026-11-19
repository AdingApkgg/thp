#include "EnemyDifficultyInteger.hpp"
namespace th143 {
i32 enemy_difficulty_integer(Vm& vm,VmHost& host,u32 difficulty){
 if(vm.instruction->opcode!=535)return -2;
 i32 values[4];
 for(u32 i=0;i<4;++i){values[i]=vm.integer_argument(i+1,host);if(vm.failed)return -2;}
 auto* destination=vm.reference(0,host,false);if(vm.failed||!destination)return -2;
 const u32 bits=u32(values[difficulty<3?difficulty:3]);
 std::memcpy(destination,&bits,4);return 0;
}
}
