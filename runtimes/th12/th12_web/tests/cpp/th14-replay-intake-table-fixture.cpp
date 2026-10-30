#include "Replay.hpp"
#include <cstdio>
using namespace th11;
int main(int argc,char** argv){
    if(argc!=3)return 2;FILE* f=std::fopen(argv[1],"rb");if(!f)return 3;
    std::fseek(f,0,SEEK_END);const long size=std::ftell(f);std::rewind(f);
    if(size<=0||size>64*1024*1024)return 4;std::vector<u8> bytes(size);
    const auto read=std::fread(bytes.data(),1,bytes.size(),f);std::fclose(f);if(read!=bytes.size())return 5;
    Replay replay;if(!replay.open(bytes.data(),u32(bytes.size()))){std::fprintf(stderr,"%s\n",replay.error().c_str());return 6;}
    const auto& raw=replay.decoded();f=std::fopen(argv[2],"wb");if(!f)return 7;
    const bool written=std::fwrite(raw.data(),1,raw.size(),f)==raw.size();const int closed=std::fclose(f);if(!written||closed)return 8;
    std::printf("{\"decodedBytes\":%u,\"stageCount\":%u,\"character\":%u,\"subtype\":%u,\"difficulty\":%u,\"stages\":[",u32(raw.size()),replay.stage_count(),replay.character(),replay.subtype(),replay.difficulty());
    bool first=true;for(u32 n=1;n<=7;++n){const auto* s=replay.stage(n);if(!s)continue;
        std::printf("%s{\"stage\":%u,\"headerOffset\":%u,\"frames\":%u,\"payloadBytes\":%u,\"inputOffset\":%u,\"fpsOffset\":%u}",first?"":",",s->number,s->offset,s->frames,s->payload_size,s->offset+kReplayStageHeader,s->offset+kReplayStageHeader+s->frames*6);first=false;}
    std::printf("]}\n");return 0;
}
