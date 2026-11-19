#pragma once
#include <stdint.h>
#include <math.h>
namespace Magic {
enum class Phase : uint8_t { Idle, Listen, Text, Roll, Fortune, Rise, Face, Flush };
enum class Cue : uint8_t { None, Magic, Water, Fart, Flush };
struct State {
  Phase phase=Phase::Idle;
  uint32_t began=0;
  int question=0,chosen=0;
  uint8_t order[21]={};
  bool muted=false;
  bool canAsk() const {return phase==Phase::Idle||phase==Phase::Fortune;}
  uint32_t elapsed(uint32_t now) const {return uint32_t(now-began);}
  uint32_t duration() const {
    switch(phase){case Phase::Listen:return 2400;case Phase::Text:return (question?18:16)*85+1400;
      case Phase::Roll:return 2200;case Phase::Rise:return 900;case Phase::Flush:return 2350;default:return 0;}
  }
  float progress(uint32_t now) const {uint32_t d=duration();return d?fminf(1,float(elapsed(now))/d):1;}
  void set(Phase next,uint32_t now){phase=next;began=now;}
  Cue ask(uint32_t now,uint32_t random){
    if(!canAsk())return Cue::None;
    question=phase==Phase::Idle?0:1;
    if(!question){
      chosen=random%4;
      auto next=[&](){random^=random<<13;random^=random>>17;random^=random<<5;return random;};
      if(!random)random=0x81753;
      order[0]=next()%4;
      for(int i=1;i<20;i++){uint8_t choices[4];int n=0;for(int v=0;v<4;v++)if(v!=order[i-1]&&(i!=19||v!=chosen))choices[n++]=v;order[i]=choices[next()%n];}
      order[20]=chosen;
    }
    set(Phase::Listen,now);return Cue::Magic;
  }
  Cue flush(uint32_t now){if(phase!=Phase::Face)return Cue::None;set(Phase::Flush,now);return Cue::Flush;}
  Cue update(uint32_t now){
    if(!duration()||elapsed(now)<duration())return Cue::None;
    switch(phase){
      case Phase::Listen:set(Phase::Text,now);break;
      case Phase::Text:set(question?Phase::Rise:Phase::Roll,now);return Cue::Water;
      case Phase::Roll:set(Phase::Fortune,now);return Cue::Fart;
      case Phase::Rise:set(Phase::Face,now);break;
      case Phase::Flush:question=0;set(Phase::Idle,now);break;
      default:break;
    }return Cue::None;
  }
};
inline bool inAperture(int x,int y){float dx=(x-232.5f)/175.7084f,dy=(y-232.5f)/212.9799f;return dx*dx+dy*dy<=1;}
inline bool inMic(int x,int y){return inAperture(x,y)&&x>=176&&x<=288&&y>=310&&y<=426;}
inline bool inFace(int x,int y){return inAperture(x,y)&&x>=100&&x<=366&&y>=70&&y<=390;}
inline int mountedCoordinate(int calibrated){return 465-calibrated;}
inline int frameIndex(int rawX,int rawY){return ((465-rawY)/2)*233+(465-rawX)/2;}
}
