// Opt-in audio candidate. AVAudioSession lives on UIKit; engine audio calls do not.
#import <AVFAudio/AVFAudio.h>
#import <UIKit/UIKit.h>
#include <atomic>
#include "i_sound.h"
static std::atomic<bool> audioReady{false};
@interface SelacoAudioSession : NSObject
@property(nonatomic) BOOL interrupted;
@property(nonatomic) BOOL failedReset;
- (void)refresh;
@end
@implementation SelacoAudioSession
- (void)refresh {
    NSAssert(NSThread.isMainThread, @"Audio session requires main thread");
    if (self.interrupted || self.failedReset || UIApplication.sharedApplication.applicationState != UIApplicationStateActive) {
        audioReady.store(false); return;
    }
    NSError *error = nil;
    AVAudioSession *s = AVAudioSession.sharedInstance;
    BOOL ok = [s setCategory:AVAudioSessionCategoryPlayback mode:AVAudioSessionModeDefault options:0 error:&error];
    if (ok) ok = [s setActive:YES error:&error];
    audioReady.store(ok);
    if (!ok) NSLog(@"Selaco audio session activation failed: %@", error);
}
- (void)inactive:(NSNotification *)n { (void)n; audioReady.store(false); }
- (void)active:(NSNotification *)n { (void)n; [self refresh]; }
- (void)interruption:(NSNotification *)n {
    if (!NSThread.isMainThread) { dispatch_async(dispatch_get_main_queue(), ^{ [self interruption:n]; }); return; }
    auto type = [n.userInfo[AVAudioSessionInterruptionTypeKey] unsignedIntegerValue];
    if (type == AVAudioSessionInterruptionTypeBegan) { self.interrupted = YES; audioReady.store(false); }
    else {
        self.interrupted = NO;
        auto options = [n.userInfo[AVAudioSessionInterruptionOptionKey] unsignedIntegerValue];
        if (options & AVAudioSessionInterruptionOptionShouldResume) [self refresh];
    }
}
- (void)reset:(NSNotification *)n {
    if (!NSThread.isMainThread) { dispatch_async(dispatch_get_main_queue(), ^{ [self reset:n]; }); return; }
    (void)n;
    // Existing OpenAL AudioUnit must be recreated. Fail silent, never reuse it.
    self.failedReset = YES; audioReady.store(false);
    NSLog(@"Selaco audio services reset: restart app to rebuild audio device");
}
@end
extern "C" void SelacoAudioStart() {
    NSCAssert(NSThread.isMainThread, @"Audio setup requires main thread");
    static SelacoAudioSession *owner;
    if (owner) return;
    owner = [SelacoAudioSession new];
    NSNotificationCenter *c = NSNotificationCenter.defaultCenter;
    [c addObserver:owner selector:@selector(inactive:) name:UIApplicationWillResignActiveNotification object:nil];
    [c addObserver:owner selector:@selector(active:) name:UIApplicationDidBecomeActiveNotification object:nil];
    [c addObserver:owner selector:@selector(interruption:) name:AVAudioSessionInterruptionNotification object:nil];
    [c addObserver:owner selector:@selector(reset:) name:AVAudioSessionMediaServicesWereResetNotification object:nil];
    [owner refresh];
}
// Engine-thread only. No engine pointer is ever accessed from UIKit callbacks.
extern "C" void SelacoAudioDrain() {
    static SoundRenderer *last = nullptr;
    static bool previous = false;
    bool ready = audioReady.load();
    if (GSnd && (GSnd != last || ready != previous)) {
        GSnd->SetInactive(ready ? SoundRenderer::INACTIVE_Active : SoundRenderer::INACTIVE_Complete);
        last = GSnd; previous = ready;
    }
    if (!GSnd) last = nullptr;
}
