#include <assert.h>
#include <stdio.h>
#include "../firmware/MagicToilet/MagicState.h"
int main(){
  using namespace Magic;
  for(uint32_t seed=0;seed<1000;seed++){
    State s;uint32_t t=0xfffffc00u;
    assert(s.ask(t,seed)==Cue::Magic);assert(s.ask(t+1,seed)==Cue::None);
    assert(s.flush(t+1)==Cue::None);assert(s.update(t+2399)==Cue::None);assert(s.phase==Phase::Listen);
    t+=2400;s.update(t);assert(s.phase==Phase::Text);
    t+=s.duration();assert(s.update(t)==Cue::Water);assert(s.phase==Phase::Roll);
    assert(s.order[20]==s.chosen);for(int i=1;i<21;i++)assert(s.order[i]<4&&s.order[i]!=s.order[i-1]);
    t+=2200;assert(s.update(t)==Cue::Fart);assert(s.phase==Phase::Fortune);assert(s.update(t+1)==Cue::None);
    assert(s.ask(t+1,seed)==Cue::Magic);assert(s.question==1);t+=2401;s.update(t);t+=s.duration();assert(s.update(t)==Cue::Water);
    t+=900;s.update(t);assert(s.phase==Phase::Face);assert(s.ask(t,seed)==Cue::None);
    assert(s.flush(t)==Cue::Flush);assert(s.flush(t+1)==Cue::None);t+=2350;s.update(t);assert(s.phase==Phase::Idle&&s.question==0);
  }
  assert(inMic(232,364));assert(!inMic(0,364));assert(!inAperture(0,0));assert(inFace(232,232));
  for(int p=0;p<466;p++)assert(mountedCoordinate(mountedCoordinate(p))==p);
  assert(frameIndex(0,0)==233*233-1);assert(frameIndex(465,465)==0);
  for(int y=0;y<466;y++)for(int x=0;x<466;x++)assert(frameIndex(x,y)>=0&&frameIndex(x,y)<233*233);
  puts("Magic state, cue order, wraparound, roll endpoint, hit regions and rotation tests passed.");
}
