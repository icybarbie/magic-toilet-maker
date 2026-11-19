#include <Arduino.h>
#include <Wire.h>
#include <Arduino_GFX_Library.h>
#include <TouchDrvCSTXXX.hpp>
#include <esp_heap_caps.h>
#include "TouchInput.h"
#include "MagicState.h"
#include "MagicScene.h"
#include "MagicAudio.h"

Arduino_ESP32QSPI bus(12,38,4,5,6,7);
Arduino_CO5300 display(&bus,1,0,466,466,6,0,0,0);
Arduino_Canvas canvas(233,233,nullptr);
TouchDrvCST92xx touch;
Magic::State state;
Magic::Scene scene;
uint16_t strip[466*12];
volatile bool touchIRQ=false;
bool touchReady=false,redraw=true,dumping=false,debugEnabled=false,calibration=false;
bool held=false,longDone=false,pressMic=false,pressFace=false;
int downX=0,downY=0,lastX=0,lastY=0,flushY=466;
uint32_t downAt=0,lastContact=0,lastPoll=0,lastFrame=0,frames=0,taps=0,touchErrors=0;
uint32_t debugAt=0,lastTouchError=0,dumpAt=0,maxRenderUs=0,maxTouchGap=0,lastTouchUs=0;
size_t dumpOffset=0;

void status(){
  Serial.printf("MT_STATUS v=1.5 phase=%u question=%d chosen=%d touch=%d audio=%d muted=%d taps=%lu frames=%lu touch_errors=%lu audio_errors=%lu cues=%lu heap=%lu psram=%lu rotation=180 aperture=33x40\n",
    unsigned(state.phase),state.question,state.chosen,touchReady,MagicAudio::ready,state.muted,(unsigned long)taps,(unsigned long)frames,
    (unsigned long)touchErrors,(unsigned long)MagicAudio::errors.load(),(unsigned long)MagicAudio::cues.load(),(unsigned long)ESP.getFreeHeap(),(unsigned long)ESP.getFreePsram());
}
void dispatch(Magic::Cue cue){MagicAudio::play(cue);if(cue!=Magic::Cue::None)redraw=true;}
void toggleMute(){state.muted=!state.muted;MagicAudio::muted=state.muted;redraw=true;}
void release(uint32_t now){
  if(!held)return;
  if(!longDone&&now-downAt>=25&&abs(lastX-downX)<30&&abs(lastY-downY)<30){
    Magic::Cue cue=Magic::Cue::None;
    if(pressMic&&Magic::inMic(lastX,lastY))cue=state.ask(now,esp_random());
    else if(pressFace&&Magic::inFace(lastX,lastY))cue=state.flush(now);
    if(cue!=Magic::Cue::None){++taps;dispatch(cue);}
  }
  held=false;redraw=true;
}
void readTouch(){
  if(!touchReady)return;
  uint32_t now=millis(),us=micros();if(lastTouchUs)maxTouchGap=max(maxTouchGap,uint32_t(us-lastTouchUs));lastTouchUs=us;
  if(held&&pressMic&&!longDone&&now-downAt>=850&&now-lastContact<1200&&abs(lastX-downX)<30&&abs(lastY-downY)<30){toggleMute();longDone=true;}
  if(held&&now-lastContact>1600){held=false;redraw=true;}
  noInterrupts();bool pending=touchIRQ;touchIRQ=false;interrupts();
  if(!pending){if(now-lastPoll<12)return;if(touchErrors&&now-lastTouchError<100)return;if(!held&&digitalRead(11)!=LOW)return;}
  lastPoll=now;uint8_t packet[15];Wire.beginTransmission(0x5A);Wire.write(0xD0);Wire.write(0x00);
  if(Wire.endTransmission()!=0){++touchErrors;lastTouchError=now;return;}
  size_t n=Wire.requestFrom(uint8_t(0x5A),uint8_t(sizeof(packet)));
  for(size_t i=0;i<n&&i<sizeof(packet);i++)packet[i]=Wire.read();
  if(n!=sizeof(packet)){++touchErrors;lastTouchError=now;return;}
  Wire.beginTransmission(0x5A);Wire.write(0xD0);Wire.write(0x00);Wire.write(0xAB);
  if(Wire.endTransmission()!=0){++touchErrors;lastTouchError=now;return;}
  auto r=decodeTouch(packet,n);if(r.kind==TouchKind::None)return;
  if(r.kind==TouchKind::Up){release(now);return;}
  lastX=Magic::mountedCoordinate(r.x);lastY=Magic::mountedCoordinate(r.y);lastContact=now;
  if(!held){held=true;longDone=false;downAt=now;downX=lastX;downY=lastY;pressMic=state.canAsk()&&Magic::inMic(lastX,lastY);pressFace=state.phase==Magic::Phase::Face&&Magic::inFace(lastX,lastY);redraw=true;
    if(!dumping&&debugEnabled&&now-debugAt<15000)Serial.printf("MT_TOUCH x=%d y=%d mic=%d face=%d\n",lastX,lastY,pressMic,pressFace);}
}
void frameDump(){
  if(!dumping)return;if(millis()-dumpAt>20000){dumping=false;return;}
  constexpr size_t bytes=466*466*2;int space=Serial.availableForWrite();
  if(dumpOffset<bytes&&space>0){
    size_t n=min(bytes-dumpOffset,size_t(min(space,512)));uint8_t out[512];
    for(size_t i=0;i<n;i++){size_t byte=dumpOffset+i,pixel=byte/2;uint16_t c=canvas.getFramebuffer()[Magic::frameIndex(pixel%466,pixel/466)];out[i]=byte%2?c>>8:c;}
    dumpOffset+=Serial.write(out,n);
  }else if(dumpOffset==bytes&&space>20){Serial.print("\nPET_FRAME_END\r\n");dumping=false;}
}
void diagnostics(){
  static char line[64];static unsigned length=0;
  while(Serial.available()){
    char c=Serial.read();if(c=='\n'){
      line[length]=0;length=0;debugEnabled=true;debugAt=millis();
      if(!strcmp(line,"STATUS"))status();
      else if(!strcmp(line,"PERF")){Serial.printf("MT_PERF max_render_us=%lu max_touch_gap_us=%lu audio_frames=%lu\n",(unsigned long)maxRenderUs,(unsigned long)maxTouchGap,(unsigned long)MagicAudio::frames.load());maxRenderUs=maxTouchGap=0;}
      else if(!strcmp(line,"ASK")){dispatch(state.ask(millis(),esp_random()));status();}
      else if(!strcmp(line,"FLUSH")){dispatch(state.flush(millis()));status();}
      else if(!strcmp(line,"RESET")){state.set(Magic::Phase::Idle,millis());state.question=0;redraw=true;status();}
      else if(!strcmp(line,"MUTE")){toggleMute();status();}
      else if(!strcmp(line,"CAL")){calibration=!calibration;redraw=true;status();}
      else if(!strcmp(line,"FRAME")&&!dumping){Serial.printf("PET_FRAME 466 466 %u\n",466*466*2);dumping=true;dumpOffset=0;dumpAt=millis();}
      else if(!strncmp(line,"SOUND ",6)){int id=atoi(line+6);if(id>=1&&id<=4)MagicAudio::play(Magic::Cue(id));}
    }else if(c!='\r'){if(length+1<sizeof(line))line[length++]=c;else length=0;}
  }
}
void setup(){
  Serial.setTxBufferSize(4096);Serial.begin(115200);Serial.setTxTimeoutMs(0);delay(500);
  Wire.begin(15,14);Wire.setTimeOut(10);
  if(!display.begin()||!canvas.begin()){Serial.println("MT_FATAL display");while(true)delay(1000);}
  scene.init(canvas);display.setBrightness(110);
  // Configure codec before touch processing; audio task subsequently uses I2S only.
  if(!MagicAudio::begin())Serial.println("MT_WARN audio unavailable");
  touch.setPins(2,11);touchReady=touch.begin(Wire,0x5A,15,14);
  if(touchReady){touch.reset();touch.setMaxCoordinates(466,466);touch.setMirrorXY(true,true);pinMode(11,INPUT_PULLUP);attachInterrupt(digitalPinToInterrupt(11),[](){touchIRQ=true;},FALLING);}
  scene.draw(canvas,state,millis());flushY=0;status();
}
void loop(){
  readTouch();diagnostics();frameDump();uint32_t now=millis();
  if(!dumping){
    auto before=state.phase;dispatch(state.update(now));if(before!=state.phase)redraw=true;
    uint32_t frameInterval=state.duration()!=0?40:80;
    if(flushY>=466&&(redraw||now-lastFrame>=frameInterval)){
      lastFrame=now;redraw=false;uint32_t begin=micros();scene.draw(canvas,state,now,held&&pressMic,calibration);
      maxRenderUs=max(maxRenderUs,uint32_t(micros()-begin));++frames;flushY=0;readTouch();
    }
    if(flushY<466){int rows=min(12,466-flushY);const uint16_t* fb=canvas.getFramebuffer();
      for(int y=0;y<rows;y++)for(int x=0;x<466;x++)strip[y*466+x]=fb[Magic::frameIndex(x,flushY+y)];
      display.draw16bitRGBBitmap(0,flushY,strip,466,rows);flushY+=rows;}
  }
  delay(1);
}
