#pragma once
#include <cstdint>
namespace SelacoTemporal {
struct CoverageEvidence {
 std::uint64_t serial=0,epoch=0;
 unsigned width=0,height=0,outputWidth=0,outputHeight=0;
 bool requested=false,jitterReady=false,drawsComplete=false,producerReset=true;
};
struct CoverageDecision {bool complete=false,reset=true;};
class CoverageGate {
 CoverageEvidence last_{},pending_{};
 bool encoded_=false,pendingValid_=false;
public:
 CoverageDecision Finalize(CoverageEvidence f) {
  pending_=f;pendingValid_=false;
  const bool allowed=f.serial && f.requested && f.jitterReady && f.drawsComplete &&
      f.width && f.height && f.outputWidth && f.outputHeight &&
      (!encoded_ || f.serial>last_.serial);
  if(!allowed)return {};
  pendingValid_=true;
  const bool reset=f.producerReset || !encoded_ || last_.serial==UINT64_MAX ||
      f.serial!=last_.serial+1 || f.epoch!=last_.epoch ||
      f.width!=last_.width || f.height!=last_.height ||
      f.outputWidth!=last_.outputWidth || f.outputHeight!=last_.outputHeight;
  return {true,reset};
 }
 // A source-complete frame is not accepted as history until real GPU encode
 // succeeds. Failed/omitted encodes force reset automatically on recovery.
 void Encoded(bool success) {if(success&&pendingValid_){last_=pending_;encoded_=true;}pendingValid_=false;}
};
}
