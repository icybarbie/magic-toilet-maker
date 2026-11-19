#include <assert.h>
#include <stdio.h>
#include <array>
#include <vector>
#include "../firmware/MagicToilet/MagicWater.h"
struct Canvas {
  uint16_t base=0;
  std::vector<std::array<int,7>> triangles;
  void fillScreen(uint16_t c){base=c;triangles.clear();}
  void fillTriangle(int a,int b,int c,int d,int e,int f,uint16_t color){triangles.push_back({a,b,c,d,e,f,color});}
};
int main(){
  using namespace MagicWater;
  Canvas original;draw(original,0);assert(original.triangles.size()==81);
  int moved=0;
  int minX[17],maxX[17],minY[17],maxY[17];
  for(int i=0;i<17;i++){minX[i]=minY[i]=10000;maxX[i]=maxY[i]=-10000;}
  for(uint32_t t=0;t<=60000;t+=100){
    Canvas current;draw(current,t);assert(current.base==original.base);
    for(int i=0;i<64;i++)assert(current.triangles[i]==original.triangles[i]);
    for(int i=0;i<17;i++){
      auto p=highlight(i,t),start=highlight(i,0);
      int centerX=116+sinf(i*12.7f)*91,centerY=116+cosf(i*7.4f)*103;
      assert(abs(p.x-centerX)<=5&&abs(p.y-centerY)<=2);
      minX[i]=std::min(minX[i],p.x);maxX[i]=std::max(maxX[i],p.x);
      minY[i]=std::min(minY[i],p.y);maxY[i]=std::max(maxY[i],p.y);
      const auto &a=original.triangles[i+64],&b=current.triangles[i+64];
      assert(a[6]==b[6]);
      for(int k=0;k<6;k+=2)assert(b[k]-a[k]==p.x-start.x&&b[k+1]-a[k+1]==p.y-start.y);
      if(p.x!=start.x||p.y!=start.y)++moved;
    }
    if(t==60000)assert(current.triangles==original.triangles);
  }
  assert(moved>0);
  for(int i=0;i<17;i++){assert(maxX[i]-minX[i]>=8);assert(maxY[i]-minY[i]>=3);}
  puts("Original 64 water facets unchanged; 17 highlight shapes/colors preserved; curved drift bounded to 5 x 2 canvas pixels, every highlight travels at least 8 x 3; loop passed.");
}
