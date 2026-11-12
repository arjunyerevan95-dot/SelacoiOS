#include <al.h>
#include <alc.h>
#include <alext.h>
#include "engine_sfx_format.h"
static void VerifyEngineOutput(const std::vector<uint8_t>& pcm, ChannelConfig chans, SampleType type, int rate) {
 int frameBytes=0; auto format=SelectEngineSfxFormat(chans,type,frameBytes);
 assert(format!=AL_NONE && frameBytes==(chans==ChannelConfig_Mono?2:4));
 auto open=(LPALCLOOPBACKOPENDEVICESOFT)alcGetProcAddress(nullptr,"alcLoopbackOpenDeviceSOFT");assert(open);
 ALCdevice*dev=open(nullptr);assert(dev);
 ALCint attrs[]={ALC_FORMAT_CHANNELS_SOFT,ALC_STEREO_SOFT,ALC_FORMAT_TYPE_SOFT,ALC_SHORT_SOFT,ALC_FREQUENCY,rate,0};
 auto*ctx=alcCreateContext(dev,attrs);assert(ctx&&alcMakeContextCurrent(ctx));
 ALuint buffer,source;alGenBuffers(1,&buffer);alGenSources(1,&source);
 alBufferData(buffer,format,pcm.data(),(ALsizei)pcm.size(),rate);assert(alGetError()==AL_NO_ERROR);
 alSourcei(source,AL_BUFFER,buffer);alSourcePlay(source);
 auto render=(LPALCRENDERSAMPLESSOFT)alcGetProcAddress(dev,"alcRenderSamplesSOFT");assert(render);
 std::vector<short> out(9600);render(dev,out.data(),4800);bool nonzero=false;for(auto v:out)if(v)nonzero=true;
 assert(nonzero&&alGetError()==AL_NO_ERROR);alDeleteSources(1,&source);alDeleteBuffers(1,&buffer);
 alcMakeContextCurrent(nullptr);alcDestroyContext(ctx);alcCloseDevice(dev);
}
