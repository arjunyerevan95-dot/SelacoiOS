from pathlib import Path
import sys
r=Path(sys.argv[1]);z=r/'libraries/ZVulkan/src'
i=(z/'vulkaninstance.cpp').read_text();b=(z/'vulkanbuilders.cpp').read_text()
d=(r/'src/common/rendering/vulkan/system/vk_renderdevice.cpp').read_text()
assert 'OptionalExtensions.insert(VK_EXT_METAL_OBJECTS_EXTENSION_NAME)' not in i
assert 'EnabledExtensions.count(VK_EXT_METAL_OBJECTS_EXTENSION_NAME)' not in i
assert 'exportDevice.pNext = &exportQueue' in i and 'createInfo.pNext = &exportDevice' in i
assert 'builder.OptionalExtension(VK_EXT_METAL_OBJECTS_EXTENSION_NAME)' in d
assert d.index('std::getenv("SELACO_IOS_METALFX")') < d.index('builder.OptionalExtension(VK_EXT_METAL_OBJECTS_EXTENSION_NAME)')
assert b.count('device->SupportsExtension(VK_EXT_METAL_OBJECTS_EXTENSION_NAME)')==3
backend=(r/'src/common/platform/ios/i_metalfx_backend.mm').read_text()
assert 'd->SupportsExtension(VK_EXT_METAL_OBJECTS_EXTENSION_NAME)' in backend
assert 'Instance->EnabledExtensions.count(VK_EXT_METAL_OBJECTS_EXTENSION_NAME)' not in backend
assert 'CreateWithBackoff(d,f)' in backend and 'CreateWithBackoff(d,f,true)' in backend
print('PASS: device-scoped metal_objects enable/export checks; instance export intent; bounded creation')
