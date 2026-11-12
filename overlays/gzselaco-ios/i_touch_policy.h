#pragma once
#include <cmath>
namespace SelacoIOS {
struct AltLatch {
 bool latched=false,suppress=false;double lastTap=-1000,pressedAt=0;
 bool press(double now,double window=.30){
  pressedAt=now;suppress=false;
  if(latched){latched=false;suppress=true;lastTap=-1000;return false;}
  if(now-lastTap<=window){latched=true;lastTap=-1000;}
  return true;
 }
 bool release(double now){if(suppress){suppress=false;return false;}if(!latched&&now-pressedAt<=.25)lastTap=now;else if(!latched)lastTap=-1000;return latched;}
 void reset(){latched=false;suppress=false;lastTap=-1000;pressedAt=0;}
};
inline int RadialSector(double dx,double dy,double inner,double outer,int count){
 if(count<1||!std::isfinite(dx)||!std::isfinite(dy))return -1;
 const double r=std::hypot(dx,dy);if(r<inner||r>outer)return -1;
 const double pi=3.14159265358979323846;double a=std::atan2(dy,dx)+pi/2.;if(a<0)a+=2*pi;
 return static_cast<int>(std::floor(a/(2*pi/count)+.5))%count;
}
inline double StickAxis(double axis,double length,double deadzone,double response){
 if(!std::isfinite(axis)||!std::isfinite(length)||length<=deadzone)return 0;
 double magnitude=std::pow(std::fmin(1.,(length-deadzone)/(1.-deadzone)),response);
 return axis/length*magnitude;
}
}
