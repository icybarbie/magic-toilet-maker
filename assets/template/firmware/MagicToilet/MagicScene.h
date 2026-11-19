#pragma once
#include <Arduino_GFX_Library.h>
#include "MagicAssets.h"
#include "MagicState.h"
#include "MagicWater.h"
#include <string.h>
#include <math.h>
namespace Magic {
inline uint16_t rgb(int r,int g,int b){return ((r>>3)<<11)|((g>>2)<<5)|(b>>3);}
inline uint16_t blend565(uint16_t base,uint16_t top,int a){
  int r=(((top>>11)&31)*a+((base>>11)&31)*(255-a)+127)/255;
  int g=(((top>>5)&63)*a+((base>>5)&63)*(255-a)+127)/255;
  int b=((top&31)*a+(base&31)*(255-a)+127)/255;return (r<<11)|(g<<5)|b;
}
struct Scene {
  void init(Arduino_Canvas& c){MagicWater::draw(c,0);}
  void water(Arduino_Canvas& c,uint32_t now){MagicWater::draw(c,now);}
  void sprite(Arduino_Canvas& c,const MagicAssets::Sprite& s,float cx,float cy,float scale=1,float angle=0,int clipTop=0,int clipBottom=233){
    if(scale<.015f)return;
    float co=cosf(angle),si=sinf(angle),hw=s.w*.5f,hh=s.h*.5f;
    int extent=int((fabsf(co)*hw+fabsf(si)*hh)*scale)+2;
    int extentY=int((fabsf(si)*hw+fabsf(co)*hh)*scale)+2;
    int l=max(0,int(cx)-extent),r=min(232,int(cx)+extent),top=max(clipTop,int(cy)-extentY),bottom=min(clipBottom-1,int(cy)+extentY);
    uint16_t* fb=c.getFramebuffer();
    for(int y=top;y<=bottom;y++)for(int x=l;x<=r;x++){
      float dx=(x+.5f-cx)/scale,dy=(y+.5f-cy)/scale;
      int sx=int(floorf(co*dx+si*dy+hw)),sy=int(floorf(-si*dx+co*dy+hh));
      if(sx<0||sy<0||sx>=s.w||sy>=s.h)continue;
      int at=sy*s.w+sx;int a=s.alpha[at];if(a)fb[y*233+x]=a==255?s.rgb[at]:blend565(fb[y*233+x],s.rgb[at],a);
    }
  }
  void text(Arduino_Canvas& c,const uint8_t* str,int y,int count=100){
    int x=0,row=0,shown=0;uint16_t ink=rgb(23,53,80);uint16_t* fb=c.getFramebuffer();
    while(str[x]!=254){int end=x;while(str[end]!=254&&str[end]!=255)end++;int left=(233-(end-x)*19)/2;
      for(int k=x;k<end;k++){if(shown++>=count)return;const uint8_t* a=MagicAssets::glyphAlpha+str[k]*19*21;
        for(int gy=0;gy<21;gy++)for(int gx=0;gx<19;gx++){int px=left+(k-x)*19+gx,py=y+row*27+gy;if(px>=0&&px<233&&py>=0&&py<233&&a[gy*19+gx])fb[py*233+px]=blend565(fb[py*233+px],ink,a[gy*19+gx]);}}
      if(str[end]==254)break;x=end+1;row++;
    }
  }
  void draw(Arduino_Canvas& c,const State& s,uint32_t now,bool pressed=false,bool calibration=false){
    water(c,now);float p=s.progress(now);
    if(s.phase==Phase::Idle){
      sprite(c,MagicAssets::logo,116,92);c.setTextColor(rgb(41,69,101));c.setTextSize(1);c.setCursor(80,31);c.print("FORTUNE.EXE");
    }else if(s.phase==Phase::Listen){
      for(int i=0;i<11;i++){int h=7+27*fabsf(sinf(p*24+i*.81f))*sinf((i+1)*3.14159f/12);c.fillRect(76+i*8,112-h/2,4,h,i%2?rgb(185,255,93):rgb(111,120,195));}
    }else if(s.phase==Phase::Text){text(c,s.question?MagicAssets::text1:MagicAssets::text0,72,min(100,int(s.elapsed(now)/85)+1));}
    else if(s.phase==Phase::Roll){
      float pos=20*(1-(1-p)*(1-p));int index=min(20,int(pos));float f=pos-index;
      sprite(c,*MagicAssets::items[s.order[index]],116,111-f*112,1,0,55,166);
      if(index<20)sprite(c,*MagicAssets::items[s.order[index+1]],116,111+(1-f)*112,1,0,55,166);
    }else if(s.phase==Phase::Fortune){sprite(c,*MagicAssets::items[s.chosen],116,102);}
    else if(s.phase==Phase::Rise){sprite(c,MagicAssets::face,116,111+(1-p)*24,p);}
    else if(s.phase==Phase::Face){sprite(c,MagicAssets::face,116,109);text(c,MagicAssets::labels[4],190);}
    else if(s.phase==Phase::Flush){
      for(int j=0;j<4;j++)for(int i=1;i<55;i++){float a=i*.18f+p*11+j*1.5708f,b=a-.18f,r=(8+i*.9f)*(1-.6f*p),rr=r-.9f*(1-.6f*p);c.drawLine(116+cosf(b)*rr,121+sinf(b)*rr,116+cosf(a)*r,121+sinf(a)*r,j%2?rgb(208,238,240):rgb(56,125,153));}
      sprite(c,MagicAssets::face,116,115,fmaxf(0,1-p*1.4f),p*9);
    }
    if(s.phase!=Phase::Rise&&s.phase!=Phase::Face&&s.phase!=Phase::Flush){
      bool compact=s.phase==Phase::Fortune;
      sprite(c,MagicAssets::mic,116,182+(pressed?2:0),compact?.68f:1.f);
      if(s.muted)c.drawLine(compact?107:103,compact?176:173,compact?125:130,compact?189:193,rgb(255,107,95));
    }
    if(calibration){
      for(int i=0;i<160;i++){float a=i*6.2831853f/160;c.drawPixel(116.25f+87.8542f*cosf(a),116.25f+106.4899f*sinf(a),rgb(255,60,80));}
      c.drawLine(109,116,123,116,rgb(255,60,80));c.drawLine(116,109,116,123,rgb(255,60,80));
      c.setCursor(95,24);c.setTextColor(rgb(23,53,80));c.print("USB UP");
    }
  }
};
}
