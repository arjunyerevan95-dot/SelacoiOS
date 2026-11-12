#!/usr/bin/env python3
"""Native pipeline / reduced scene viewport. Exact-anchor, fail-closed patch."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
def edit(path, old, new):
 p=root/path; s=p.read_text(); assert s.count(old)==1,(path,old[:80]); p.write_text(s.replace(old,new))
base='src/common/rendering/vulkan/'
edit(base+'system/vk_renderdevice.h','\tvoid SetSceneRenderTarget(bool useSSAO) override;', '''\t// Selaco iOS: scene-only scaling, native attachments and final pipeline.
\tIntRect iosNativeSceneRect;
\tbool iosSceneScaled = false;
\tvoid SetSceneRenderTarget(bool useSSAO) override;''')
edit(base+'system/vk_renderdevice.cpp','#include "vk_renderdevice.h"','#include "vk_renderdevice.h"\n#include <cstdlib>\n#include <cmath>\nEXTERN_CVAR(Int, gl_ssao)\nEXTERN_CVAR(Float, vid_scalefactor)\nEXTERN_CVAR(Int, vid_scalemode)\n')
edit(base+'system/vk_renderdevice.cpp','void VulkanRenderDevice::BeginFrame()\n{','''static double IOSSceneScale()
{
#ifdef __APPLE__
    const char *v = std::getenv("SELACO_IOS_SCENE_SCALE");
    double s = v ? std::atof(v) : 1.0;
    return std::isfinite(s) && s >= 0.25 && s < 1.0 ? s : 1.0;
#else
    return 1.0;
#endif
}

void VulkanRenderDevice::BeginFrame()
{
    // First implementation intentionally excludes multisample resolve and SSAO.
    // Set before buffer sample selection and before mainview chooses GBUFFER_PASS.
    if (IOSSceneScale() < 1.0) {
        gl_multisample = 0; gl_ssao = 0;
        if (vid_scalefactor != 1.0f) vid_scalefactor = 1.0f;
        if (vid_scalemode != 0) vid_scalemode = 0;
    }
    iosSceneScaled = false;''')
edit(base+'system/vk_renderdevice.cpp','void VulkanRenderDevice::SetSceneRenderTarget(bool useSSAO)\n{','''void VulkanRenderDevice::SetSceneRenderTarget(bool useSSAO)
{
    iosSceneScaled = false;
    if (IOSSceneScale() < 1.0 && GetBuffers() == mScreenBuffers.get())
    {
        iosNativeSceneRect = mSceneViewport;
        const double s = IOSSceneScale();
        mSceneViewport.left = (int)(iosNativeSceneRect.left * s);
        mSceneViewport.top = (int)(iosNativeSceneRect.top * s);
        mSceneViewport.width = max(1, (int)(iosNativeSceneRect.width * s));
        mSceneViewport.height = max(1, (int)(iosNativeSceneRect.height * s));
        iosSceneScaled = true;
        static int lastW = 0, lastH = 0, lastSW = 0, lastSH = 0;
        if (lastW != GetBuffers()->GetWidth() || lastH != GetBuffers()->GetHeight() || lastSW != mSceneViewport.width || lastSH != mSceneViewport.height)
        {
            lastW = GetBuffers()->GetWidth(); lastH = GetBuffers()->GetHeight();
            lastSW = mSceneViewport.width; lastSH = mSceneViewport.height;
            Printf("iOS scene-scale: attachments/pipeline=%dx%d scene=%dx%d at %d,%d native-view=%dx%d MSAA=off SSAO=off\\n", lastW,lastH,lastSW,lastSH,mSceneViewport.left,mSceneViewport.top,iosNativeSceneRect.width,iosNativeSceneRect.height);
        }
    }''')
edit(base+'system/vk_renderdevice.cpp','\tmPostprocess->PostProcessScene(fixedcm, flash, afterBloomDrawEndScene2D);','''    if (iosSceneScaled) { mSceneViewport = iosNativeSceneRect; iosSceneScaled = false; }
\tmPostprocess->PostProcessScene(fixedcm, flash, afterBloomDrawEndScene2D);''')
edit(base+'renderer/vk_postprocess.cpp','\t\tcmdbuffer->blitImage(\n\t\t\tsceneColor->image,', '''        if (fb->iosSceneScaled)
        {
            // Define borders too when a smaller screenblocks viewport is used.
            VkClearColorValue black = {}; black.float32[3] = 1.0f;
            VkImageSubresourceRange range = {};
            range.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
            range.levelCount = 1; range.layerCount = 1;
            cmdbuffer->clearColorImage(buffers->PipelineImage[mCurrentPipelineImage].Image->image,
                VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, &black, 1, &range);
            PipelineBarrier().AddMemory(VK_ACCESS_TRANSFER_WRITE_BIT, VK_ACCESS_TRANSFER_WRITE_BIT)
                .Execute(cmdbuffer, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT);
            const auto &src = fb->mSceneViewport;
            const auto &dst = fb->iosNativeSceneRect;
            blit.srcOffsets[0] = {src.left, src.top, 0};
            blit.srcOffsets[1] = {src.left + src.width, src.top + src.height, 1};
            blit.dstOffsets[0] = {dst.left, dst.top, 0};
            blit.dstOffsets[1] = {dst.left + dst.width, dst.top + dst.height, 1};
        }
\t\tcmdbuffer->blitImage(
\t\t\tsceneColor->image,''')
# Nearest is universally available and deliberately avoids unsupported linear blit formats.
# Leave existing VK_FILTER_NEAREST intact; optional filtered upscale is a later change.
