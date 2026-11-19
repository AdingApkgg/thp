#include "AnmTextureRegion.hpp"
namespace th143 {
bool upload_anm_texture_region(AnmTexturePixels& target,const std::array<i32,4>& d,u32 sf,u32 sw,u32 sh,const u8* source,u32 bytes,const std::array<i32,4>& s,u32 filter,i32& hr){
    const u32 sb=anm_texture_pixel_bytes(sf),db=anm_texture_pixel_bytes(target.format);hr=i32(0x8876086cu);
    auto valid=[](const std::array<i32,4>& r,u32 w,u32 h){return r[0]>=0&&r[1]>=0&&r[2]>=r[0]&&r[3]>=r[1]&&u32(r[2])<=w&&u32(r[3])<=h;};
    if(!sb||!db||!source||std::uint64_t(sw)*sh*sb>bytes||std::uint64_t(target.width)*target.height*db!=target.data.size())return false;
    if(!valid(d,target.width,target.height))return true;if(!valid(s,sw,sh))return false;
    const u32 source_w=u32(s[2]-s[0]),source_h=u32(s[3]-s[1]),width=u32(d[2]-d[0]),height=u32(d[3]-d[1]);
    if((!width||!height||!source_w||!source_h)&&filter!=1){hr=i32(0x80004005u);return true;}
    if(!width||!height){hr=0;return true;}if(!source_w||!source_h){for(u32 y=0;y<height;++y)std::memset(target.data.data()+((u32(d[1])+y)*target.width+u32(d[0]))*db,0,width*db);hr=0;return true;}
    std::vector<u8> cropped(source_w*source_h*sb);for(u32 y=0;y<source_h;++y)std::memcpy(cropped.data()+y*source_w*sb,source+((u32(s[1])+y)*sw+u32(s[0]))*sb,source_w*sb);
    AnmTexturePixels converted;bool ok;if(filter==1)ok=convert_anm_texture_pixels(sf,source_w,source_h,cropped.data(),cropped.size(),target.format,width,height,converted);else if(filter==0x30004)ok=filter_anm_texture_pixels(sf,source_w,source_h,cropped.data(),cropped.size(),target.format,width,height,converted);else return false;
    if(!ok)return false;for(u32 y=0;y<height;++y)std::memcpy(target.data.data()+((u32(d[1])+y)*target.width+u32(d[0]))*db,converted.data.data()+y*width*db,width*db);hr=0;return true;
}
}
