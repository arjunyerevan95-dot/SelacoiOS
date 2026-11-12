#pragma once
#include <cmath>
namespace SelacoIOS {
struct LookDelta { double x,y; };
inline LookDelta GyroAxes(double rx,double ry,bool landscapeRight,bool invertX,bool invertY) {
 const double orientation=landscapeRight?-1.:1.;
 // Corrected from device feedback: opposite of build22 on both axes.
 return {rx*orientation*(invertX?-1.:1.),-ry*orientation*(invertY?-1.:1.)};
}
inline double RenderScale(double requested) {return std::isfinite(requested)&&std::abs(requested-.33)<.001?.33:.5;}
inline int RenderPixels(double points,double screenScale,double requested) {
 if(!std::isfinite(points)||!std::isfinite(screenScale)||points<=0||screenScale<=0)return 1;
 double pixels=std::floor(points*screenScale*RenderScale(requested));
 return static_cast<int>(std::fmax(1.,std::fmin(16384.,pixels)));
}
}
