# Build32 ownership correction
Two device crashes matched build31 Mach-O UUID57fbe2aa-18fa-33ee-9bf8-42d2e6b106a2. Both terminate while MoltenVK destroys timeline Metal events after failed export setup. Pinned Vulkan header rev1 declares exported Metal handles as ARC strong fields. The Vulkan-Headers rev2 correction marks those borrowed handles __unsafe_unretained.

Backport only five Objective-C typedef ownership qualifiers, preserving ABI and C++ definitions. Strong fields in our persistent interop wrapper continue retaining exported handles deliberately. Added ObjC++ ARC compiler regression: all8 borrowed import/export structs must be trivially destructible. Old header fails8 assertions, corrected header passes with arm64-apple-ios16 target. Full Apple SDK build and device verification still required. Saves/controls/audio unchanged.
Reference:https://github.com/KhronosGroup/Vulkan-Headers/blob/v1.3.283/include/vulkan/vulkan_metal.h
