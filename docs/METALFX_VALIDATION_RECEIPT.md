# Validation receipt: 2026-11-13

- Native compile run43438052730, source54699dc, Xcode26.3 build17C529.
- Three Objective-C++ modules (bridge, interop, actual consumption backend) and
  patched Vulkan swapchain/device/instance/builders compiled for arm64 iPhoneOS.
- Overall workflow conclusion FAILURE: subsequent standalone portable test compile
  lacked the overlays include directory. Fixed locally in4c8f0ba. This is not a
  successful full-engine/iOS application build or linked/device-tested artifact.
- Initial run43437825990 caught backend callback quoting syntax, fixed54699dc.
- All six standalone history/pacing/sprite/view/model helpers compile with MSVC
  C++17 /W4 /WX and execute successfully after corrected include path locally.
- Actual patched Vulkan swapchain and Metal-export image builders also compiled
  under MSVC. Apple compile covers base device setup + presentation and native
  MetalFX backend; it does not yet compile complete motion shader permutations or
  the complete postprocess callsite within the game engine.
- World-temporal and frame-generation completeness remain fail-closed.
- No IPA produced, no user data touched, no graphics or latency improvement claimed.

https://github.com/arjunyerevan95-dot/SelacoiOS/actions/runs/43438052730
