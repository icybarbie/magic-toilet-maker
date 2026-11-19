#pragma once
#include <stdint.h>
#include <math.h>
namespace MagicWater {
inline uint16_t rgb(int r,int g,int b){return ((r>>3)<<11)|((g>>2)<<5)|(b>>3);}
struct Point {int x,y;};
inline Point highlight(int i,uint32_t now){
  // Sum smooth traveling waves; canvas pixels map 2:1 to display pixels.
  int x=116+sinf(i*12.7f)*91,y=116+cosf(i*7.4f)*103;
  float t=(now%60000u)*.000104719755f;
  float phase=x*.018f+y*.026f;
  float dx=4*sinf(t*12-phase)+sinf(t*20+i*.37f);
  float dy=1.4f*sinf(t*12-phase+.9f)+.6f*sinf(t*15+i*.61f);
  return {x+int(roundf(dx)),y+int(roundf(dy))};
}
template<class Canvas> void draw(Canvas& canvas,uint32_t now){
  // Restore the exact original palette and static facet layout.
  canvas.fillScreen(rgb(97,190,198));
  for(int j=0;j<8;j++)for(int i=0;i<8;i++){
    int delta=((i*17+j*11)%9-4)*2,x=i*34-12,y=j*34-12;
    canvas.fillTriangle(x,y,x+35,y+((i+j)%2?8:-4),x+10,y+35,
                        rgb(97+delta,190+delta,198+delta));
  }
  for(int i=0;i<17;i++){
    Point p=highlight(i,now);
    canvas.fillTriangle(p.x-7,p.y,p.x,p.y-3,p.x+12,p.y+1,rgb(173,222,222));
  }
}
}
