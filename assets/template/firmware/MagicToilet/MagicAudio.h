#pragma once
#include <Arduino.h>
#include <ESP_I2S.h>
#include <atomic>
#include "es8311.h"
#include "MagicAssets.h"
#include "MagicState.h"
namespace MagicAudio {
static I2SClass output;
static QueueHandle_t queue=nullptr;
static std::atomic<bool> muted{false};
static std::atomic<uint32_t> cues{0},errors{0},frames{0};
static bool ready=false;
struct Voice {const MagicAssets::Sound* sound=nullptr;size_t offset=0;};
inline const MagicAssets::Sound* soundFor(Magic::Cue cue){
  switch(cue){case Magic::Cue::Magic:return &MagicAssets::magicSound;case Magic::Cue::Water:return &MagicAssets::waterSound;
    case Magic::Cue::Fart:return &MagicAssets::fartSound;case Magic::Cue::Flush:return &MagicAssets::flushSound;default:return nullptr;}
}
static void task(void*){
  Voice voices[3];int16_t stereo[256*2];
  while(true){
    Magic::Cue cue;while(xQueueReceive(queue,&cue,0)==pdTRUE){
      const auto* sound=soundFor(cue);if(!sound)continue;
      int slot=0;for(int i=0;i<3;i++)if(!voices[i].sound){slot=i;break;}
      voices[slot]={sound,0};++cues;
    }
    bool quiet=muted.load();
    for(int i=0;i<256;i++){
      int32_t sample=0;
      for(auto& v:voices)if(v.sound){sample+=v.sound->samples[v.offset++];if(v.offset>=v.sound->count)v.sound=nullptr;}
      sample=quiet?0:sample*32/100;sample=sample>32767?32767:sample<-32768?-32768:sample;
      stereo[2*i]=stereo[2*i+1]=int16_t(sample);
    }
    size_t sent=output.write(reinterpret_cast<uint8_t*>(stereo),sizeof(stereo));
    if(sent!=sizeof(stereo)){++errors;vTaskDelay(pdMS_TO_TICKS(2));}frames+=sent/4;
  }
}
inline bool begin(){
  pinMode(46,OUTPUT);digitalWrite(46,LOW);
  // TX only: no DIN, microphone task or recording buffers.
  output.setPins(9,45,8,-1,16);
  if(!output.begin(I2S_MODE_STD,22050,I2S_DATA_BIT_WIDTH_16BIT,I2S_SLOT_MODE_STEREO,I2S_STD_SLOT_BOTH))return false;
  auto codec=es8311_create(0,ES8311_ADDRRES_0);if(!codec)return false;
  es8311_clock_config_t clock={false,false,true,22050*256,22050};
  if(es8311_init(codec,&clock,ES8311_RESOLUTION_16,ES8311_RESOLUTION_16)!=ESP_OK)return false;
  if(es8311_voice_volume_set(codec,85,nullptr)!=ESP_OK)return false;
  queue=xQueueCreate(8,sizeof(Magic::Cue));if(!queue)return false;
  if(xTaskCreatePinnedToCore(task,"magic-audio",4096,nullptr,2,nullptr,0)!=pdPASS){vQueueDelete(queue);queue=nullptr;return false;}
  digitalWrite(46,HIGH);ready=true;return true;
}
inline void play(Magic::Cue cue){if(ready&&cue!=Magic::Cue::None&&xQueueSend(queue,&cue,0)!=pdTRUE)++errors;}
}
