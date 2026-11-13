#!/usr/bin/env python3
"""Repair pinned MoltenVK same-size recreation; expose optional scRGB HDR formats."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
def edit(rel,old,new):
 p=root/rel;s=p.read_text();assert s.count(old)==1,(rel,old[:70]);p.write_text(s.replace(old,new))
p='src/common/platform/ios/i_engine_renderer_handoff.mm'
edit(p,'        builder.RequireExtension(VK_EXT_METAL_SURFACE_EXTENSION_NAME);', '''        builder.RequireExtension(VK_EXT_METAL_SURFACE_EXTENSION_NAME);
        // Custom iOS builder bypasses RequireSurfaceExtensions(), which normally
        // requests this. Without it vk_hdr cannot discover extended-linear formats.
        builder.OptionalExtension(VK_EXT_SWAPCHAIN_COLOR_SPACE_EXTENSION_NAME);''')
with (root/p).open('a') as out: out.write(r'''

// MoltenVK v1.4.1 initCAMetalLayer sets the requested extent BEFORE its
// oldSwapchain completion workaround can set the shared drawableSize to 1x1.
// Repair only a successful recreation, after the old swapchain is destroyed,
// before any new image is acquired. Vulkan remains the sole presenter.
extern "C" void SelacoIOSValidateSwapchainLayer(unsigned width, unsigned height,
                                                unsigned format, unsigned colorSpace)
{
    @autoreleasepool {
        CAMetalLayer *layer = gEngineMetalLayer;
        if (!layer || !width || !height) return;
        const CGSize before = layer.drawableSize;
        const bool repaired = before.width != width || before.height != height;
        if (repaired) layer.drawableSize = CGSizeMake(width, height);
        const CGSize after = layer.drawableSize;
        bool edr = false;
        if (@available(iOS 16.0, *)) edr = layer.wantsExtendedDynamicRangeContent;
        NSString *detail = [NSString stringWithFormat:
            @"extent=%ux%u before=%.0fx%.0f after=%.0fx%.0f repaired=%d vkFormat=%u vkColorSpace=%u metalFormat=%lu edr=%d colorspace=%@",
            width, height, before.width, before.height, after.width, after.height,
            int(repaired), format, colorSpace, (unsigned long)layer.pixelFormat,
            int(edr), (__bridge id)layer.colorspace];
        SelacoIOSReportLicensedAssetProbe("swapchain_layer_output", detail.UTF8String);
    }
}
''')
p='libraries/ZVulkan/src/vulkanswapchain.cpp'
edit(p,'extern "C" void SelacoIOSReportLicensedAssetProbe(const char *phase, const char *detail);', '''extern "C" void SelacoIOSReportLicensedAssetProbe(const char *phase, const char *detail);
extern "C" void SelacoIOSValidateSwapchainLayer(unsigned, unsigned, unsigned, unsigned);''')
anchor='\n#ifdef WIN32\n\tif (exclusivefullscreen)\n\t{\n\t\tresult = vkAcquireFullScreenExclusiveModeEXT'
edit(p,anchor,'''\n#if defined(SELACO_IOS_ENGINE_RENDERER_HANDOFF)
\tSelacoIOSValidateSwapchainLayer(actualExtent.width, actualExtent.height,
\t\t(unsigned)format.format, (unsigned)format.colorSpace);
#endif
'''+anchor)
print('Applied iOS post-recreation drawable repair and optional HDR discovery')
