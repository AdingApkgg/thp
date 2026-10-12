// The query the per-title no-op gates use, exported for the dispatch checkers.
// NoopOpcodes.hpp already takes the title number, so one build can be asked about every column, and this
// fixture adds nothing but the C boundary. Build with -DPORT_TITLE=<title> to make runtime_noop_opcode
// answer with that title's table; the checkers do that for 16, 17 and 18.
#include "../../cpp/game/NoopOpcodes.hpp"
#define EXPORT(name) extern "C" __attribute__((used,visibility("default"))) name
EXPORT(int noop_probe(unsigned title,unsigned opcode)){return title_noop_opcode(title,uint16_t(opcode))?1:0;}
EXPORT(int noop_runtime(unsigned opcode)){return runtime_noop_opcode(uint16_t(opcode))?1:0;}
EXPORT(unsigned noop_build_title()){return unsigned(kPortTitle);}
