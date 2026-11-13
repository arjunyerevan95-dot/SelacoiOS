#!/usr/bin/env python3
"""Actual opt-in MetalFX temporal callsite; never certifies complete motion.
Apply after scene scale, native modules, device prerequisites and motion diagnostic.
"""
from pathlib import Path
import sys,shutil
root=Path(sys.argv[1]); repo=Path(__file__).resolve().parents[1]; edits={}
def edit(path,old,new,count=1):
    s=edits.get(path,(root/path).read_text()); assert s.count(old)==count,(path,old[:70],s.count(old));edits[path]=s.replace(old,new)
p='libraries/ZVulkan/src/vulkanbuilders.cpp'
edit(p,'\tVkResult result = vmaCreateImage(device->allocator, &imageInfo, &allocInfo, &image, &allocation, nullptr);','''#if defined(VK_USE_PLATFORM_METAL_EXT)
    VkExportMetalObjectCreateInfoEXT metalExport = { VK_STRUCTURE_TYPE_EXPORT_METAL_OBJECT_CREATE_INFO_EXT };
    const void* savedNext = imageInfo.pNext;
    if (device->Instance->EnabledExtensions.count(VK_EXT_METAL_OBJECTS_EXTENSION_NAME)) {
        metalExport.exportObjectType = VK_EXPORT_METAL_OBJECT_TYPE_METAL_TEXTURE_BIT_EXT;
        metalExport.pNext = savedNext; imageInfo.pNext = &metalExport;
    }
#endif
\tVkResult result = vmaCreateImage(device->allocator, &imageInfo, &allocInfo, &image, &allocation, nullptr);
#if defined(VK_USE_PLATFORM_METAL_EXT)
    imageInfo.pNext = savedNext;
#endif''',2)
edit(p,'\tVkResult result = vkCreateImageView(device->device, &viewInfo, nullptr, &view);','''#if defined(VK_USE_PLATFORM_METAL_EXT)
    VkExportMetalObjectCreateInfoEXT metalExport = { VK_STRUCTURE_TYPE_EXPORT_METAL_OBJECT_CREATE_INFO_EXT };
    const void* savedNext = viewInfo.pNext;
    if (device->Instance->EnabledExtensions.count(VK_EXT_METAL_OBJECTS_EXTENSION_NAME)) {
        metalExport.exportObjectType = VK_EXPORT_METAL_OBJECT_TYPE_METAL_TEXTURE_BIT_EXT;
        metalExport.pNext = savedNext; viewInfo.pNext = &metalExport;
    }
#endif
\tVkResult result = vkCreateImageView(device->device, &viewInfo, nullptr, &view);
#if defined(VK_USE_PLATFORM_METAL_EXT)
    viewInfo.pNext = savedNext;
#endif''')
p='src/common/rendering/vulkan/textures/vk_renderbuffers.cpp'
edit(p,'#include "vk_renderbuffers.h"','#include "vk_renderbuffers.h"\n#include "common/platform/ios/i_metalfx_backend.h"')
old='.Usage(VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT)'
# Only pipeline images get UAV usage, not depth/stencil or all texture allocations.
s=edits.get(p,(root/p).read_text());start=s.index('void VkRenderBuffers::CreatePipeline(');end=s.index('void VkRenderBuffers::CreateScene(',start);part=s[start:end];assert part.count(old)==1
part=part.replace(old,old[:-1]+' | (IOSMetalFXRequested() ? VK_IMAGE_USAGE_STORAGE_BIT : 0))');edits[p]=s[:start]+part+s[end:]
p='src/common/rendering/vulkan/textures/vk_imagetransition.cpp'
edit(p,'switch (image->Layout)\n\t{','''switch (image->Layout)
\t{
    case VK_IMAGE_LAYOUT_GENERAL:
        srcAccess = VK_ACCESS_MEMORY_READ_BIT | VK_ACCESS_MEMORY_WRITE_BIT;
        srcStageMask |= VK_PIPELINE_STAGE_ALL_COMMANDS_BIT;
        break;''')
edit(p,'case VK_IMAGE_LAYOUT_GENERAL:\n\t\tdstAccess = 0;\n\t\tdstStageMask |= VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT;','''case VK_IMAGE_LAYOUT_GENERAL:
        dstAccess = VK_ACCESS_MEMORY_READ_BIT | VK_ACCESS_MEMORY_WRITE_BIT;
        dstStageMask |= VK_PIPELINE_STAGE_ALL_COMMANDS_BIT;''')
p='src/common/rendering/vulkan/renderer/vk_postprocess.h'
edit(p,'#include <functional>','#include <functional>\n#include "common/platform/ios/i_metalfx_backend.h"')
edit(p,'\tvoid SetActiveRenderTarget();','\tvoid SetActiveRenderTarget();\n\tvoid RetireMetalFX();')
edit(p,'\tint mCurrentPipelineImage = 0;','\tint mCurrentPipelineImage = 0;\n\tIOSMetalFXBackend* iosMetalFX = nullptr;')
p='src/common/rendering/vulkan/renderer/vk_postprocess.cpp'
edit(p,'#include "vk_postprocess.h"','#include "vk_postprocess.h"\n#include "hwrenderer/data/hw_motion_diagnostic.h"')
edit(p,'VkPostprocess::~VkPostprocess()\n{\n}','''VkPostprocess::~VkPostprocess()
{
#if defined(__APPLE__) && TARGET_OS_IPHONE
    IOSMetalFXBackendDestroy(iosMetalFX);
#endif
}
void VkPostprocess::RetireMetalFX()
{
#if defined(__APPLE__) && TARGET_OS_IPHONE
    IOSMetalFXBackendRetire(iosMetalFX);
#endif
}''')
edit(p,'\tmCurrentPipelineImage = 0;\n\n\tVkImageTransition()', '''\tmCurrentPipelineImage = 0;
#if defined(__APPLE__) && TARGET_OS_IPHONE
    // Fullscreen-only first integration; camera targets/reduced screenblocks fall back.
    // CompleteMotion remains owned by the producer, never promoted here.
    const auto temporalMetadata = SelacoMotionMetadata();
    if (IOSMetalFXRequested() && temporalMetadata.complete && fb->iosSceneScaled &&
        buffers->GetSceneSamples() == VK_SAMPLE_COUNT_1_BIT &&
        buffers->SceneMotionDiagnostic.Image && buffers->SceneReactive.Image && buffers->SceneDepthStencil.DepthOnlyView &&
        fb->iosNativeSceneRect.left == 0 && fb->iosNativeSceneRect.top == 0 &&
        fb->iosNativeSceneRect.width == buffers->GetWidth() && fb->iosNativeSceneRect.height == buffers->GetHeight()) {
        VkImageTransition().AddImage(&buffers->SceneColor,VK_IMAGE_LAYOUT_GENERAL,false)
            .AddImage(&buffers->SceneDepthStencil,VK_IMAGE_LAYOUT_GENERAL,false)
            .AddImage(&buffers->SceneMotionDiagnostic,VK_IMAGE_LAYOUT_GENERAL,false)
            .AddImage(&buffers->SceneReactive,VK_IMAGE_LAYOUT_GENERAL,false)
            .AddImage(&buffers->PipelineImage[0],VK_IMAGE_LAYOUT_GENERAL,true).Execute(cmdbuffer);
        IOSMetalFXVkFrame f{}; f.color=buffers->SceneColor.Image->image;
        f.depth=buffers->SceneDepthStencil.DepthOnlyView->view;f.motion=buffers->SceneMotionDiagnostic.Image->image;
        f.reactive=buffers->SceneReactive.Image->image;
        f.output=buffers->PipelineImage[0].Image->image;f.x=fb->mSceneViewport.left;f.y=fb->mSceneViewport.top;
        f.width=fb->mSceneViewport.width;f.height=fb->mSceneViewport.height;
        f.outputWidth=buffers->GetWidth();f.outputHeight=buffers->GetHeight();
        f.completeMotion=temporalMetadata.complete;
        f.jitterX=temporalMetadata.jitterX;f.jitterY=temporalMetadata.jitterY;f.reset=temporalMetadata.reset;
        f.user=fb;f.flushProducer=[](void* p){static_cast<VulkanRenderDevice*>(p)->GetCommands()->FlushCommands(false);};
        const bool consumed=IOSMetalFXBackendConsume(iosMetalFX,fb->device.get(),f);
        cmdbuffer=fb->GetCommands()->GetDrawCommands();
        if(consumed){
            VkImageTransition().AddImage(&buffers->PipelineImage[0],VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,false).Execute(cmdbuffer);
            return;
        }
    }
#endif
\tVkImageTransition()''')
p='src/common/rendering/vulkan/system/vk_commandbuffer.cpp'
edit(p,'\tDeleteFrameObjects(uploadOnly);','''    // Existing fences above cover prior MetalFX work through its GPU timeline wait.
    if (!uploadOnly) fb->GetPostprocess()->RetireMetalFX();
\tDeleteFrameObjects(uploadOnly);''')
p='src/CMakeLists.txt'
edit(p,'\tcommon/platform/ios/i_metalfx_interop.mm )','\tcommon/platform/ios/i_metalfx_interop.mm\n\tcommon/platform/ios/i_metalfx_backend.mm )')
edits[p]+='\nset_source_files_properties(common/platform/ios/i_metalfx_backend.mm PROPERTIES COMPILE_FLAGS "-fobjc-arc")\n'
for p,s in edits.items():(root/p).write_text(s)
for name in ['i_metalfx_backend.h','i_metalfx_backend.mm']:
    shutil.copyfile(repo/'overlays/gzselaco-ios'/name,root/'src/common/platform/ios'/name)
print('Temporal GPU consumption callsite installed; completeMotion remains fail-closed')
