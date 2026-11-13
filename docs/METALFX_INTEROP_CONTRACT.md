# MetalFX Vulkan/Metal interop contract (implementation groundwork)

## Architectural model and competing explanation

The renderer writes ordinary Vulkan images using MoltenVK. `VK_EXT_metal_objects`
exports the same GPU-backed Metal textures and timeline semaphore shared events.
A caller-owned, distinct Metal queue encodes event wait, MetalFX work, event signal.
Vulkan then consumes output only after its timeline wait. No pixel readback or CPU
wait is needed. Apple and Khronos APIs support this model; device execution remains
unverified. The competing failure mode is ordering/lifetime, rather than an upscaler
shader problem: MoltenVK may submit work asynchronously, so merely committing a
Metal command buffer to its underlying queue is insufficient and may deadlock.
The bridge explicitly rejects the exported Vulkan queue for native Metal work.

Caller logs should include `metalfx-interop-ready`, exported texture dimensions and
formats, scene-ready/done values, and each command buffer completion/error. Distinguish
an encoded call from GPU completion and presentation. Do not log licensed contents.

## Required creation state

Enable `VK_EXT_metal_objects` on the Vulkan instance (it is an instance extension),
and enable timeline semaphores in the device feature chain (Vulkan1.2 or extension
path as appropriate). Load `vkExportMetalObjectsEXT` through the active Vulkan loader.
Do not use deprecated loader-incompatible `vkGetMTL*MVK` entry points.

Chain separate `VkExportMetalObjectCreateInfoEXT` structures into instance creation:
- `VK_EXPORT_METAL_OBJECT_TYPE_METAL_DEVICE_BIT_EXT`
- `VK_EXPORT_METAL_OBJECT_TYPE_METAL_COMMAND_QUEUE_BIT_EXT`

For every exported image/view, declare
`VK_EXPORT_METAL_OBJECT_TYPE_METAL_TEXTURE_BIT_EXT` at its creation. Allocate ordinary
single-sample, non-memoryless2D images with shader-read/write/transfer usage required
by the bridge returned texture-usage flags and subsequent Vulkan passes. The caller
must provide depth-only sampled views/compatible formats where necessary, not stencil.
The bridge supports only non-multiplanar color/depth exports.

Create two distinct timeline semaphores with `VkSemaphoreTypeCreateInfo` specifying
`VK_SEMAPHORE_TYPE_TIMELINE`, and export-create type
`VK_EXPORT_METAL_OBJECT_TYPE_METAL_SHARED_EVENT_BIT_EXT` on both. Do not use a binary
semaphore and assume Metal event values work. The config booleans attest actual
creation flags; this helper cannot introspect creation history.

## Submission sequence

1. Producer Vulkan pass completes stores of color/depth/motion (including applicable
   barriers/layout transitions to a state compatible with external access). Submit
   with sceneReady timeline signalN.
2. Caller obtains a command buffer on its separate Metal queue, calls
   `IOSMetalFXInteropBegin(...,N)`, encodes MetalFX, ends all encoders, then calls
   `IOSMetalFXInteropEnd(...,M)` and commits the command buffer.
3. Consumer Vulkan submission waits for metalDoneM at a stage covering its first
   output read, applies required Vulkan access/layout barriers, then postprocesses,
   composites UI and/or presents. Metal signal is GPU-encoded, not host-side.

Both counters increase strictly and never wrap/reuse. Counters represent reserved
values, not completed ones. Only this producer and consumer own these semaphores.
The Vulkan queue passed at creation must be the cooperating queue. Overlapping
frames need separate image/history slots with lifetime tracking. Begin/End is single
threaded and paired on the same command buffer. No active encoder may span them.
The helper validates the command buffer is not committed, but cannot inspect active
encoders or prove that caller Vulkan barriers are correct.

If encoding fails after Begin, do not submit a consumer waiting for a signal that
will never occur. Either finish an authorized fallback that signals the reserved
value and returns safe output, or discard the unsent command buffer and the unsent
consumer. Recreate interop/reset temporal history after a GPU error or aborted
sequence; do not continue using poisoned history. No queue-idle recovery is hidden.

## Ownership and limits

Interop retains exported Metal objects, but that does not authorize freeing their
Vulkan owners or image memory. Keep device/queue/semaphores/images/views/memory alive
until all referencing GPU work and presentation slots have retired. Texture output
is assigned to a caller-owned ARC reference. Destroy/reconfigure only after tracked
completion; Destroy never waits. No allocation, queue creation, submit/commit,
CPU wait, readback, or presentation is performed here.

Compile `.mm` as Objective-C++ with ARC, Apple Metal framework and current Vulkan
headers including `vulkan_metal.h`. The companion MetalFX bridge needs weak MetalFX
linkage and Xcode26/iOS26 SDK for frame interpolation; runtime guards remain mandatory.
This module alone is not an integrated or device-tested MetalFX feature.

## References

- https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_metal_objects.html
- https://docs.vulkan.org/refpages/latest/refpages/source/VkExportMetalObjectCreateInfoEXT.html
- https://docs.vulkan.org/refpages/latest/refpages/source/VkExportMetalSharedEventInfoEXT.html
- https://github.com/KhronosGroup/MoltenVK/blob/main/Docs/MoltenVK_Configuration_Parameters.md
- https://developer.apple.com/documentation/metal/mtlcommandbuffer/encodewaitforevent(_:value:)
