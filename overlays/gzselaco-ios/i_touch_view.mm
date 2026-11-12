#import <UIKit/UIKit.h>
#import <CoreMotion/CoreMotion.h>
#import <QuartzCore/QuartzCore.h>
#include "i_touch_input.h"
#include "i_touch_math.h"
#include <cmath>
// Scan codes match Selaco's existing default keyboard bindings, not new gameplay commands.
static const int keys[]={0x39,0x101,0x13,0x2a,-1,0x12,-2,0x100};
static NSArray *labels(){return @[@"JUMP",@"ALT",@"RELOAD",@"DASH",@"WHEEL",@"USE",@"GYRO",@"FIRE"];}
static double defaults[8][3]={{.812,.09,56},{.924,.134,44},{.741,.24,44},{.875,.27,54},{.817,.335,44},{.898,.418,52},{.76,.455,70},{.85,.54,76}};
@interface SelacoTouchView:UIView {
 __weak UIViewController *_owner; CMMotionManager *_motion; CADisplayLink *_link;
 NSMutableDictionary *_touches; NSMutableArray *_layout; NSMutableDictionary *_settings;
 UITouch *_moveTouch; CGPoint _origin,_stick; bool _menu,_suspended,_editing; int _selected,_radial;
 CGPoint _wheelCenter; double _last,_biasX,_biasY,_calUntil,_sumX,_sumY; int _samples;
 UIInterfaceOrientation _orientation; UIView *_panel;
}
@end
@implementation SelacoTouchView
- (instancetype)initWithOwner:(UIViewController*)owner {
 if((self=[super initWithFrame:owner.view.bounds])){
  _owner=owner;self.multipleTouchEnabled=YES;self.backgroundColor=UIColor.clearColor;self.autoresizingMask=UIViewAutoresizingFlexibleWidth|UIViewAutoresizingFlexibleHeight;
  _touches=[NSMutableDictionary new];_layout=[NSMutableArray new];_selected=7;
  for(int i=0;i<8;i++)[_layout addObject:[@{@"x":@(defaults[i][0]),@"y":@(defaults[i][1]),@"size":@(defaults[i][2]),@"opacity":@.72} mutableCopy]];
  _settings=[@{@"swipe":@3,@"gyroGain":@3,@"gyro":@NO,@"gyroInvertX":@NO,@"gyroInvertY":@NO} mutableCopy];
  NSDictionary *saved=[NSUserDefaults.standardUserDefaults dictionaryForKey:@"SelacoTouch.v1"];
  if([saved[@"layout"] isKindOfClass:NSArray.class]&&[saved[@"layout"] count]==8){for(int i=0;i<8;i++){NSDictionary*d=saved[@"layout"][i];if(![d isKindOfClass:NSDictionary.class])continue;for(NSString*k in @[@"x",@"y",@"size",@"opacity"])if([d[k] isKindOfClass:NSNumber.class])_layout[i][k]=d[k];}}
  for(NSString*k in @[@"swipe",@"gyroGain",@"gyro",@"gyroInvertX",@"gyroInvertY"])if([saved[k] isKindOfClass:NSNumber.class])_settings[k]=saved[k];
  _motion=[CMMotionManager new];_motion.deviceMotionUpdateInterval=1./120.;
  _link=[CADisplayLink displayLinkWithTarget:self selector:@selector(tick:)];[_link addToRunLoop:NSRunLoop.mainRunLoop forMode:NSRunLoopCommonModes];
  [NSNotificationCenter.defaultCenter addObserver:self selector:@selector(suspend:) name:UIApplicationWillResignActiveNotification object:nil];
  [NSNotificationCenter.defaultCenter addObserver:self selector:@selector(resume:) name:UIApplicationDidBecomeActiveNotification object:nil];
 }return self;
}
- (double)number:(NSString*)k fallback:(double)f low:(double)lo high:(double)hi {double v=[_settings[k] doubleValue];return std::isfinite(v)?fmax(lo,fmin(hi,v)):f;}
- (CGRect)area{return UIEdgeInsetsInsetRect(self.bounds,self.safeAreaInsets);}
- (CGPoint)center:(int)i {CGRect a=[self area];return CGPointMake(a.origin.x+fmax(.04,fmin(.96,[_layout[i][@"x"] doubleValue]))*a.size.width,a.origin.y+fmax(.07,fmin(.9,[_layout[i][@"y"] doubleValue]))*a.size.height);}
- (double)radius:(int)i {return fmax(22.,fmin(55.,[_layout[i][@"size"] doubleValue]*[self area].size.height/400./2.));}
- (void)save {NSMutableDictionary*d=[_settings mutableCopy];d[@"layout"]=_layout;[NSUserDefaults.standardUserDefaults setObject:d forKey:@"SelacoTouch.v1"];}
- (void)reset {[_touches removeAllObjects];_moveTouch=nil;_radial=0;SelacoTouchReset();[self setNeedsDisplay];}
- (void)suspend:(NSNotification*)n{_suspended=true;[self reset];[_motion stopDeviceMotionUpdates];}
- (void)resume:(NSNotification*)n{_suspended=false;_last=0;[self reset];}
- (void)tick:(CADisplayLink*)link {
 bool menu=SelacoTouchMenu();UIInterfaceOrientation orientation=self.window.windowScene.interfaceOrientation;
 if(menu!=_menu||orientation!=_orientation){[self reset];_menu=menu;_orientation=orientation;_last=0;_biasX=_biasY=0;}
 double now=CACurrentMediaTime(),dt=_last?fmin(.05,now-_last):0;_last=now;
 BOOL active=!_menu&&!_suspended&&!_editing&&!_panel&&!_radial&&[_settings[@"gyro"] boolValue];
 if(active&&_motion.deviceMotionAvailable&&!_motion.deviceMotionActive)[_motion startDeviceMotionUpdates];
 if(!active&&_motion.deviceMotionActive)[_motion stopDeviceMotionUpdates];
 CMDeviceMotion*m=_motion.deviceMotion;
 if(active&&m&&fabs(NSProcessInfo.processInfo.systemUptime-m.timestamp)<.15){
  auto axes=SelacoIOS::GyroAxes(m.rotationRate.x,m.rotationRate.y,orientation==UIInterfaceOrientationLandscapeRight,[_settings[@"gyroInvertX"] boolValue],[_settings[@"gyroInvertY"] boolValue]);
  double x=axes.x,y=axes.y;
  if(_calUntil>now){_sumX+=x;_sumY+=y;_samples++;}
  else {if(_calUntil){if(_samples){_biasX=_sumX/_samples;_biasY=_sumY/_samples;}_calUntil=0;}
   double gain=[self number:@"gyroGain" fallback:3 low:.1 high:12]*60.;
   SelacoTouchLook((x-_biasX)*dt*gain,(y-_biasY)*dt*gain);
  }
 }
 if(!_editing&&!_menu&&!_panel)for(NSValue*k in [_touches.allKeys copy]){NSMutableDictionary*d=_touches[k];if([d[@"role"] intValue]==4&&!_radial&&now-[d[@"start"] doubleValue]>.35){_radial=1;[self setNeedsDisplay];}}
 [self setNeedsDisplay];
}
- (void)circle:(CGPoint)c radius:(double)r text:(NSString*)text opacity:(double)alpha selected:(BOOL)selected {
 UIColor*color=[UIColor colorWithRed:.91 green:.69 blue:.29 alpha:alpha];UIBezierPath*p=[UIBezierPath bezierPathWithOvalInRect:CGRectMake(c.x-r,c.y-r,r*2,r*2)];
 [[UIColor colorWithWhite:0 alpha:selected?.35:.08] setFill];[p fill];[color setStroke];p.lineWidth=selected?2:1;[p stroke];
 NSDictionary*at=@{NSForegroundColorAttributeName:color,NSFontAttributeName:[UIFont systemFontOfSize:11 weight:UIFontWeightSemibold]};CGSize size=[text sizeWithAttributes:at];[text drawAtPoint:CGPointMake(c.x-size.width/2,c.y-size.height/2) withAttributes:at];
}
- (void)drawRect:(CGRect)r {
 CGRect a=[self area];if(_menu){NSArray*t=@[@"↑",@"↓",@"←",@"→",@"OK",@"BACK"];double xy[][2]={{.16,.52},{.16,.8},{.09,.66},{.23,.66},{.86,.58},{.86,.80}};for(int i=0;i<6;i++)[self circle:CGPointMake(a.origin.x+a.size.width*xy[i][0],a.origin.y+a.size.height*xy[i][1]) radius:25 text:t[i] opacity:.8 selected:NO];return;}
 for(int i=0;i<8;i++){NSString*t=labels()[i];if(i==6)t=[_settings[@"gyro"] boolValue]?@"GYRO ON":@"GYRO OFF";[self circle:[self center:i] radius:[self radius:i] text:t opacity:fmax(.2,fmin(1.,[_layout[i][@"opacity"] doubleValue])) selected:_editing&&i==_selected];}
 if(_moveTouch){[self circle:_origin radius:48 text:@"" opacity:.45 selected:NO];[self circle:_stick radius:17 text:@"" opacity:.6 selected:NO];}
 if(_editing)[self circle:CGPointMake(a.origin.x+55,a.origin.y+28) radius:29 text:@"DONE" opacity:1 selected:YES];
 if(_radial){NSArray*t=_radial==1?@[@"WEAPONS",@"KICK",@"GRENADE",@"CROUCH",@"LIGHT",@"SETTINGS"]:@[@"1",@"2",@"3",@"4",@"5",@"6",@"7",@"8"];
  for(NSUInteger i=0;i<t.count;i++){double angle=-M_PI_2+i*2*M_PI/t.count;[self circle:CGPointMake(_wheelCenter.x+95*cos(angle),_wheelCenter.y+95*sin(angle)) radius:28 text:t[i] opacity:.95 selected:NO];}[self circle:_wheelCenter radius:30 text:@"CANCEL" opacity:.8 selected:NO];}
}
- (int)button:(CGPoint)p {for(int i=7;i>=0;i--){CGPoint c=[self center:i];if(hypot(p.x-c.x,p.y-c.y)<[self radius:i]+4)return i;}return -1;}
- (void)touchesBegan:(NSSet<UITouch*>*)ts withEvent:(UIEvent*)event {
 if(_suspended||_panel)return;CGRect a=[self area];
 for(UITouch*t in ts){CGPoint p=[t locationInView:self];NSValue*k=[NSValue valueWithNonretainedObject:t];int role=-3;
  if(_editing&&p.x<a.origin.x+90&&p.y<a.origin.y+65){_editing=false;[self save];[self reset];return;}
  if(_menu){double xy[][2]={{.16,.52},{.16,.8},{.09,.66},{.23,.66},{.86,.58},{.86,.80}};int codes[]={0xc8,0xd0,0xcb,0xcd,0x1c,1};for(int i=0;i<6;i++)if(hypot(p.x-a.origin.x-a.size.width*xy[i][0],p.y-a.origin.y-a.size.height*xy[i][1])<35){SelacoTouchPulse(codes[i]);break;}continue;}
  if(_radial)role=-5;else role=[self button:p];
  if(_editing){if(role>=0)_selected=role;else continue;}
  else if(role>=0){if(keys[role]>=0)SelacoTouchKey(keys[role],true);if(role==4)_wheelCenter=CGPointMake(fmax(a.origin.x+130,fmin(CGRectGetMaxX(a)-130,p.x)),fmax(a.origin.y+130,fmin(CGRectGetMaxY(a)-130,p.y)));}
  else if(role!=-5&&p.x<a.origin.x+a.size.width*.43&&!_moveTouch){role=-4;_moveTouch=t;_origin=_stick=p;}
  else if(role!=-5)role=-3;
  _touches[k]=[@{@"role":@(role),@"last":[NSValue valueWithCGPoint:p],@"start":@(CACurrentMediaTime())} mutableCopy];
 }[self setNeedsDisplay];
}
- (void)touchesMoved:(NSSet<UITouch*>*)ts withEvent:(UIEvent*)event {
 for(UITouch*t in ts){NSMutableDictionary*d=_touches[[NSValue valueWithNonretainedObject:t]];if(!d)continue;int role=[d[@"role"] intValue];CGPoint p=[t locationInView:self],last=[d[@"last"] CGPointValue];
  if(_editing&&role>=0){CGRect a=[self area];_layout[role][@"x"]=@((p.x-a.origin.x)/a.size.width);_layout[role][@"y"]=@((p.y-a.origin.y)/a.size.height);}
  else if(role==-4){double x=(p.x-_origin.x)/48,y=(p.y-_origin.y)/48,length=hypot(x,y);if(length>1){x/=length;y/=length;}if(length<.1)x=y=0;_stick=CGPointMake(_origin.x+x*48,_origin.y+y*48);SelacoTouchMove(-y,-x);}
  else if(!_radial&&(role==-3||role==7)){double g=[self number:@"swipe" fallback:3 low:.25 high:12];SelacoTouchLook((p.x-last.x)*g,(p.y-last.y)*g);}
  d[@"last"]=[NSValue valueWithCGPoint:p];
 }[self setNeedsDisplay];
}
- (void)radialSelect:(CGPoint)p {
 double dx=p.x-_wheelCenter.x,dy=p.y-_wheelCenter.y,r=hypot(dx,dy);if(r<38||r>145){_radial=0;return;}
 int count=_radial==1?6:8;double angle=atan2(dy,dx)+M_PI_2;if(angle<0)angle+=2*M_PI;int i=(int)floor(angle/(2*M_PI/count)+.5)%count;
 if(_radial==2){SelacoTouchPulse(2+i);_radial=0;return;}
 int codes[]={0,0x10,0x22,0x2e,0x21,0};if(i==0){_radial=2;return;}_radial=0;if(i==5)[self settings];else SelacoTouchPulse(codes[i]);
}
- (void)touchesEnded:(NSSet<UITouch*>*)ts withEvent:(UIEvent*)event {
 for(UITouch*t in ts){NSValue*k=[NSValue valueWithNonretainedObject:t];NSMutableDictionary*d=_touches[k];if(!d)continue;int role=[d[@"role"] intValue];CGPoint p=[t locationInView:self];
  if(_editing){[self save];}
  else {if(role>=0&&keys[role]>=0){BOOL another=NO;for(NSValue*other in _touches)if(![other isEqual:k]&&[_touches[other][@"role"] intValue]==role)another=YES;if(!another)SelacoTouchKey(keys[role],false);}
   if(role==-4){_moveTouch=nil;SelacoTouchMove(0,0);}
   if(role==6&&[self button:p]==6){_settings[@"gyro"]=@(![_settings[@"gyro"] boolValue]);[self save];}
   if((role==4&&_radial)||role==-5)[self radialSelect:p];else if(role==4&&[self button:p]==4)SelacoTouchPulse(0x198);
  }[_touches removeObjectForKey:k];
 }[self setNeedsDisplay];
}
- (void)touchesCancelled:(NSSet<UITouch*>*)ts withEvent:(UIEvent*)event {[self reset];}
- (UIButton*)option:(NSString*)title y:(CGFloat)y tag:(NSInteger)tag {UIButton*b=[UIButton buttonWithType:UIButtonTypeSystem];b.frame=CGRectMake(12,y,300,32);[b setTitle:title forState:UIControlStateNormal];b.tag=tag;[b addTarget:self action:@selector(optionPressed:) forControlEvents:UIControlEventTouchUpInside];[_panel addSubview:b];return b;}
- (void)slider:(NSString*)title key:(NSString*)key y:(CGFloat)y low:(float)low high:(float)high value:(float)value tag:(NSInteger)tag {UILabel*l=[[UILabel alloc]initWithFrame:CGRectMake(12,y,300,20)];l.text=title;l.textColor=UIColor.whiteColor;l.font=[UIFont systemFontOfSize:12];[_panel addSubview:l];UISlider*s=[[UISlider alloc]initWithFrame:CGRectMake(12,y+20,300,25)];s.minimumValue=low;s.maximumValue=high;s.value=value;s.tag=tag;[s addTarget:self action:@selector(sliderChanged:) forControlEvents:UIControlEventValueChanged];[_panel addSubview:s];}
- (void)settings {[self reset];_panel=[[UIScrollView alloc]initWithFrame:CGRectMake(0,0,324,fmin(380,self.bounds.size.height-12))];_panel.center=CGPointMake(self.bounds.size.width/2,self.bounds.size.height/2);_panel.backgroundColor=[UIColor colorWithWhite:.05 alpha:.96];_panel.layer.cornerRadius=12;[self addSubview:_panel];
 [self slider:@"Swipe sensitivity" key:@"swipe" y:4 low:.25 high:12 value:[_settings[@"swipe"] floatValue] tag:0];
 [self slider:@"Gyro sensitivity" key:@"gyroGain" y:49 low:.1 high:12 value:[_settings[@"gyroGain"] floatValue] tag:1];
 [self slider:[NSString stringWithFormat:@"%@ size (select by dragging in Edit)",labels()[_selected]] key:@"size" y:94 low:44 high:100 value:[_layout[_selected][@"size"] floatValue] tag:2];
 [self slider:@"Selected control opacity" key:@"opacity" y:139 low:.2 high:1 value:[_layout[_selected][@"opacity"] floatValue] tag:3];
 [self option:@"Edit positions / select control" y:185 tag:0];[self option:@"Calibrate gyro (hold still 1 second)" y:217 tag:1];[self option:@"Pause / game menu" y:249 tag:2];[self option:[NSString stringWithFormat:@"Invert gyro horizontal: %@",[_settings[@"gyroInvertX"] boolValue]?@"ON":@"OFF"] y:281 tag:4];[self option:[NSString stringWithFormat:@"Invert gyro vertical: %@",[_settings[@"gyroInvertY"] boolValue]?@"ON":@"OFF"] y:313 tag:5];[self option:@"Done" y:345 tag:3];((UIScrollView*)_panel).contentSize=CGSizeMake(324,389);
}
- (void)sliderChanged:(UISlider*)s {if(s.tag<2)_settings[s.tag==0?@"swipe":@"gyroGain"]=@(s.value);else _layout[_selected][s.tag==2?@"size":@"opacity"]=@(s.value);[self save];[self setNeedsDisplay];}
- (void)optionPressed:(UIButton*)b {if(b.tag==4||b.tag==5){NSString*k=b.tag==4?@"gyroInvertX":@"gyroInvertY";_settings[k]=@(![_settings[k] boolValue]);_biasX=_biasY=0;_calUntil=0;[self save];[b setTitle:[NSString stringWithFormat:@"Invert gyro %@: %@",b.tag==4?@"horizontal":@"vertical",[_settings[k] boolValue]?@"ON":@"OFF"] forState:UIControlStateNormal];return;}[_panel removeFromSuperview];_panel=nil;[self reset];if(b.tag==0)_editing=true;if(b.tag==1){_settings[@"gyro"]=@YES;_calUntil=CACurrentMediaTime()+1;_sumX=_sumY=0;_samples=0;[self save];}if(b.tag==2)SelacoTouchPulse(1);}
@end
UIView *SelacoCreateTouchView(UIViewController*controller){return [[SelacoTouchView alloc]initWithOwner:controller];}
