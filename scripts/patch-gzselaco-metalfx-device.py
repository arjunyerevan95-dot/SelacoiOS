#!/usr/bin/env python3
"""Opt-in MetalFX Vulkan device prerequisites. No feature enabled by default.
Apply to exact pinned engine after existing platform patchers. Does not itself
call MetalFX, change presentation, or imply complete motion input.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1])
def edit(rel,old,new):
    p=root/rel;s=p.read_text();assert s.count(old)==1,(rel,old[:70]);p.write_text(s.replace(old,new))
base='libraries/ZVulkan/'
# Backport Vulkan-Headers metal_objects revision2 ARC ownership correction.
# Export output pointers are BORROWED, written by non-ARC Vulkan code. Strong
# typedefs cause scope teardown to release MoltenVK-owned Metal objects.
for protocol in ['MTLDevice','MTLCommandQueue','MTLBuffer','MTLTexture','MTLSharedEvent']:
    edit(base+'include/vulkan/vulkan_metal.h',
         'typedef id<'+protocol+'> '+protocol+'_id;',
         'typedef __unsafe_unretained id<'+protocol+'> '+protocol+'_id;')
edit(base+'include/zvulkan/vulkaninstance.h',
     '\tVkPhysicalDeviceFeatures Features = {};',
     '\tVkPhysicalDeviceFeatures Features = {};\n\tVkPhysicalDeviceTimelineSemaphoreFeatures TimelineSemaphore = { VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TIMELINE_SEMAPHORE_FEATURES };')
edit(base+'src/vulkaninstance.cpp',
     '\t\t\tvkGetPhysicalDeviceFeatures2(dev.Device, &deviceFeatures2);',
     '''\t\t\tif (checkForExtension(VK_KHR_TIMELINE_SEMAPHORE_EXTENSION_NAME))
\t\t\t{
\t\t\t\t*next = &dev.Features.TimelineSemaphore;
\t\t\t\tnext = &dev.Features.TimelineSemaphore.pNext;
\t\t\t}
\t\t\tvkGetPhysicalDeviceFeatures2(dev.Device, &deviceFeatures2);
\t\t\tdev.Features.TimelineSemaphore.pNext = nullptr;''')
edit(base+'src/vulkanbuilders.cpp',
     '\t\tauto& deviceFeatures = dev.Device->Features;',
     '''\t\tauto& deviceFeatures = dev.Device->Features;
\t\tif (dev.EnabledDeviceExtensions.count(VK_KHR_TIMELINE_SEMAPHORE_EXTENSION_NAME))
\t\t\tenabledFeatures.TimelineSemaphore.timelineSemaphore = deviceFeatures.TimelineSemaphore.timelineSemaphore;''')
edit(base+'src/vulkandevice.cpp',
     '\tVkResult result = vkCreateDevice(PhysicalDevice.Device, &deviceCreateInfo, nullptr, &device);',
     '''\tif (SupportsExtension(VK_KHR_TIMELINE_SEMAPHORE_EXTENSION_NAME))
\t{
\t\t*next = &EnabledFeatures.TimelineSemaphore;
\t\tnext = &EnabledFeatures.TimelineSemaphore.pNext;
\t}

\t*next = nullptr;
\tVkResult result = vkCreateDevice(PhysicalDevice.Device, &deviceCreateInfo, nullptr, &device);
\tEnabledFeatures.TimelineSemaphore.pNext = nullptr;''')

edit(base+'src/vulkaninstance.cpp','#include <cstring>','#include <cstring>\n#include <cstdlib>')
edit(base+'src/vulkaninstance.cpp',
     '\t\tresult = vkCreateInstance(&createInfo, nullptr, &Instance);',
     '''#if defined(VK_USE_PLATFORM_METAL_EXT)
\t\t// VK_EXT_metal_objects requires device/queue export intent at INSTANCE
\t\t// creation (not VkDeviceCreateInfo). Preserve any existing pNext chain.
\t\tVkExportMetalObjectCreateInfoEXT exportDevice = { VK_STRUCTURE_TYPE_EXPORT_METAL_OBJECT_CREATE_INFO_EXT };
\t\tVkExportMetalObjectCreateInfoEXT exportQueue = { VK_STRUCTURE_TYPE_EXPORT_METAL_OBJECT_CREATE_INFO_EXT };
\t\tconst char *metalFX = std::getenv("SELACO_IOS_METALFX");
\t\tif (metalFX && std::strcmp(metalFX, "1") == 0)
\t\t{
\t\t\texportDevice.exportObjectType = VK_EXPORT_METAL_OBJECT_TYPE_METAL_DEVICE_BIT_EXT;
\t\t\texportQueue.exportObjectType = VK_EXPORT_METAL_OBJECT_TYPE_METAL_COMMAND_QUEUE_BIT_EXT;
\t\t\texportQueue.pNext = createInfo.pNext;
\t\t\texportDevice.pNext = &exportQueue;
\t\t\tcreateInfo.pNext = &exportDevice;
\t\t}
#endif
\t\tresult = vkCreateInstance(&createInfo, nullptr, &Instance);''')

p='src/common/rendering/vulkan/system/vk_renderdevice.cpp'
edit(p,'#include "vk_renderdevice.h"','#include "vk_renderdevice.h"\n#include <cstdlib>\n#include <cstring>')
edit(p,'\tVulkanDeviceBuilder builder;', '''\tVulkanDeviceBuilder builder;
#if defined(VK_USE_PLATFORM_METAL_EXT)
\t// Explicit opt-in only. Missing either advertised capability keeps later
\t// interop initialization disabled; never force an unsupported extension.
\tconst char *metalFX = std::getenv("SELACO_IOS_METALFX");
\tif (metalFX && std::strcmp(metalFX, "1") == 0)
\t{
\t\tbuilder.OptionalExtension(VK_KHR_TIMELINE_SEMAPHORE_EXTENSION_NAME);
\t\tbuilder.OptionalExtension(VK_EXT_METAL_OBJECTS_EXTENSION_NAME);
\t}
#endif''')
print('MetalFX device prerequisites patched; temporal/framegen runtime remains separate')
