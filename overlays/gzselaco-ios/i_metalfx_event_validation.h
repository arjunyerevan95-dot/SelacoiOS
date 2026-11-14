#pragma once
// Shared Metal events are cross-device; their inherited device property may be
// nil. Require a real target; accept nil event affiliation or the same device.
// Missing/aliased events and wrong command-queue ownership remain rejected by
// IOSMetalFXInteropCreate before this affiliation check.
constexpr bool IOSMetalFXSharedEventDeviceCompatible(const void* eventDevice, const void* targetDevice) {
    return targetDevice && (!eventDevice || eventDevice == targetDevice);
}
constexpr bool IOSMetalFXExportObjectsValid(const void* device, const void* queue, const void* queueDevice,
    const void* ready, const void* done, const void* readyDevice, const void* doneDevice) {
    return device && queue && queueDevice==device && ready && done && ready!=done &&
        IOSMetalFXSharedEventDeviceCompatible(readyDevice,device) &&
        IOSMetalFXSharedEventDeviceCompatible(doneDevice,device);
}
