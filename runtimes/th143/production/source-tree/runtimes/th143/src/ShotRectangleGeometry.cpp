#include "ShotRectangleGeometry.hpp"
#include <array>
#include <cmath>
#include <utility>
namespace th143 {
namespace {
struct Point {float x,y;};
using Quad=std::array<Point,4>;
void rotate(Quad& q,float angle){
    if(angle==0)return;const float sine=float(std::sin(double(angle))),cosine=float(std::cos(double(angle)));
    for(auto& p:q){const float x=p.x,y=p.y;p.x=x*cosine-y*sine;p.y=y*cosine+x*sine;}
}
Quad corners(float x,float y,float width,float height,float angle){
    const float right=width*.5f,bottom=height*.5f,left=width*-.5f,top=height*-.5f;
    Quad q{{{left,top},{left,bottom},{right,bottom},{right,top}}};rotate(q,angle);
    for(auto& p:q){p.x+=x;p.y+=y;}return q;
}
bool contains(float x,float y,float width,float height,float angle,Quad q){
    for(auto& p:q){p.x-=x;p.y-=y;}rotate(q,-angle);const float hx=width*.5f,hy=height*.5f;
    for(const auto& p:q)if(hx>=std::fabs(p.x)&&hy>=std::fabs(p.y))return true;return false;
}
bool edges(Point a,Point b,Point c,Point d){
    const float dx=a.x-b.x,dy=a.y-b.y;
    const float first=(a.x-c.x)*dy+(c.y-a.y)*dx,second=(a.x-d.x)*dy+(d.y-a.y)*dx;
    if(first*second>0)return false;
    if(first==0&&second==0){
        if(a.x>b.x)std::swap(a,b);if(c.x>d.x)std::swap(c,d);
        return d.x>=a.x&&d.y>=a.y&&b.x>=c.x&&b.y>=c.y;
    }
    const float other_x=c.x-d.x,other_y=c.y-d.y;
    const float third=(c.x-a.x)*other_y+(a.y-c.y)*other_x,fourth=(c.x-b.x)*other_y+(b.y-c.y)*other_x;
    // Native JBE accepts unordered products here, unlike the ordered
    // endpoint comparisons in the collinear branch above.
    return !(third*fourth>0);
}
}
bool shot_rectangle_rectangle(float x,float y,float width,float height,float angle,float bx,float by,float bw,float bh,float ba){
    const float dx=x-bx,dy=y-by,hw=width*.5f,hh=height*.5f,bhw=bw*.5f,bhh=bh*.5f;
    const float distance=float(std::sqrt(double(dy*dy+dx*dx))),radius=float(std::sqrt(double(hh*hh+hw*hw))),other_radius=float(std::sqrt(double(bhw*bhw+bhh*bhh)));
    if(distance>=radius+other_radius)return false;
    const auto a=corners(x,y,width,height,angle),b=corners(bx,by,bw,bh,ba);
    if(contains(x,y,width,height,angle,b)||contains(bx,by,bw,bh,ba,a))return true;
    for(unsigned i=0;i<4;++i)for(unsigned j=0;j<4;++j)if(edges(a[i],a[(i+1)%4],b[j],b[(j+1)%4]))return true;return false;
}
}
