#pragma once
#include <algorithm>
#include <cstdint>
#include <limits>
#include <utility>
#include <vector>

namespace th143 {
// Logical allocations keep their address and extent until clear/destruction.
// Byte contents remain writable. Keeping metadata immutable makes the index
// valid even when its vector reallocates or callers retain byte pointers.
class LogicalRegionStorageV148 {
public:
    class Bytes {
        std::vector<std::uint8_t> value;
    public:
        Bytes(std::vector<std::uint8_t> bytes):value(std::move(bytes)){}
        std::uint8_t* data(){return value.data();}
        const std::uint8_t* data()const{return value.data();}
        std::size_t size()const{return value.size();}
        bool empty()const{return value.empty();}
        auto begin(){return value.begin();}
        auto end(){return value.end();}
        auto begin()const{return value.begin();}
        auto end()const{return value.end();}
        std::uint8_t& operator[](std::size_t i){return value[i];}
        const std::uint8_t& operator[](std::size_t i)const{return value[i];}
    };
    struct Storage {const std::uint32_t token;Bytes bytes;};
private:
    std::vector<Storage> entries;
    struct Bounds {std::uint64_t first=std::numeric_limits<std::uint64_t>::max(),last=0;};
    std::vector<Bounds> tree;
    std::size_t capacity=0;
    Bounds bounds(std::size_t i)const{const auto& b=entries[i];return b.bytes.data()?Bounds{b.token,std::uint64_t(b.token)+b.bytes.size()}:Bounds{};}
    void merge(std::size_t at){tree[at]={std::min(tree[at*2].first,tree[at*2+1].first),std::max(tree[at*2].last,tree[at*2+1].last)};}
    void append_bounds(){
        if(entries.size()>capacity){
            capacity=std::max<std::size_t>(1,capacity*2);tree.assign(capacity*2,{});
            for(std::size_t i=0;i<entries.size();++i)tree[capacity+i]=bounds(i);
            for(std::size_t i=capacity-1;i;--i)merge(i);
        }else{auto at=capacity+entries.size()-1;tree[at]=bounds(entries.size()-1);while(at>1){at/=2;merge(at);}}
    }
    std::uint8_t* search(std::size_t at,std::uint32_t p,std::uint32_t n,std::uint64_t end){
        const auto& b=tree[at];if(p<b.first||end>b.last)return nullptr;
        if(at>=capacity)return within(entries[at-capacity],p,n);
        if(auto* bytes=search(at*2,p,n,end))return bytes;
        return search(at*2+1,p,n,end);
    }
    static std::uint8_t* within(Storage& block,std::uint32_t p,std::uint32_t n){
        auto* bytes=block.bytes.data();
        return bytes&&p>=block.token&&std::uint64_t(p)+n<=std::uint64_t(block.token)+block.bytes.size()?bytes+(p-block.token):nullptr;
    }
public:
    void push_back(Storage block){entries.push_back(std::move(block));append_bounds();}
    std::uint8_t* find(std::uint32_t p,std::uint32_t n){
        // Bounds only reject impossible subtrees. Searching insertion order
        // preserves the first match for overlaps and one-past zero-byte reads.
        return entries.empty()?nullptr:search(1,p,n,std::uint64_t(p)+n);
    }
    void clear(){tree.clear();entries.clear();capacity=0;}
    void reserve(std::size_t n){entries.reserve(n);}
    std::size_t size()const{return entries.size();}
    bool empty()const{return entries.empty();}
    Storage& back(){return entries.back();}
    const Storage& back()const{return entries.back();}
    Storage& operator[](std::size_t i){return entries[i];}
    const Storage& operator[](std::size_t i)const{return entries[i];}
    auto begin(){return entries.begin();}
    auto end(){return entries.end();}
    auto begin()const{return entries.begin();}
    auto end()const{return entries.end();}
};
}
