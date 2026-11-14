#define VK_USE_PLATFORM_METAL_EXT
#include <vulkan/vulkan.h>
#if !__has_feature(objc_arc)
#error Compile this ownership regression with Objective-C ARC enabled
#endif
// C API exports borrowed Metal handles: the wrapper must not release them.
#define CHECK(T) static_assert(__is_trivially_destructible(T), #T " must not release borrowed Metal objects")
CHECK(VkExportMetalDeviceInfoEXT);
CHECK(VkExportMetalCommandQueueInfoEXT);
CHECK(VkExportMetalBufferInfoEXT);
CHECK(VkExportMetalTextureInfoEXT);
CHECK(VkExportMetalSharedEventInfoEXT);
CHECK(VkImportMetalBufferInfoEXT);
CHECK(VkImportMetalTextureInfoEXT);
CHECK(VkImportMetalSharedEventInfoEXT);
