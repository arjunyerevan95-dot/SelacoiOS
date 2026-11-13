# iOS output transition and HDR audit (2026-11-13)

## Model and evidence

UIKit owns one CAMetalLayer; MoltenVK owns its swapchain and output configuration.
GZSelaco recreates the swapchain on VSync/HDR/extent changes. The user's VSync-off
brown output recovers after app switching, which invokes UIKit layout and reapplies
the correct drawableSize. No device log from that transition was captured yet.

Pinned MoltenVK v1.4.1 `MVKSwapchain::initCAMetalLayer` sets drawableSize to the
requested image extent, then calls oldSwapchain->forceUnpresentedImageCompletion
when recreating at the same size. That function sets the shared drawableSize to
1x1 if outstanding presentation callbacks remain. There is no following restore
in initCAMetalLayer. Thus a valid same-size mode change can leave the new swapchain
backed by a 1x1 drawable. DeviceWaitIdle does not guarantee CoreAnimation's present
callbacks have all arrived. This is a concrete source defect matching the symptom,
not yet proof of this particular phone transition.

Upstream reference:
https://github.com/KhronosGroup/MoltenVK/blob/v1.4.1/MoltenVK/MoltenVK/GPUObjects/MVKSwapchain.mm

Competing hypotheses include stale temporal/postprocess history or present-mode
support problems. The new `swapchain_layer_output` marker discriminates them: a
requested full-size extent with before=1x1 and repaired=1 specifically confirms the
MoltenVK path. If before already equals requested, investigate those alternatives.

## Bounded repair

`patch-gzselaco-ios-output-transition.py` adds an iOS-only hook after successful
vkCreateSwapchainKHR and destruction of its old swapchain, before first acquisition.
It restores only a mismatched drawableSize to the actual negotiated Vulkan extent.
It does not create another layer, present separately, reset settings, discard saves,
or change VSync policy. Failures/zero extents never enter the repair. It logs actual
before/after, VkFormat, VkColorSpace, Metal pixel format, colorspace, EDR flag.

## HDR

The custom iOS Vulkan instance bypasses RequireSurfaceExtensions and omitted its
optional VK_EXT_swapchain_colorspace request. Add that optional request; preserve
SDR fallback and the existing user's vk_hdr choice. No automatic HDR toggle.

The engine already chooses R16G16B16A16_SFLOAT + EXTENDED_SRGB_LINEAR when available
and requested, and its present shader converts into scRGB via HdrMode. MoltenVK
maps that pair to RGBA16Float, extended-linear sRGB and wantsExtendedDynamicRange
Content=YES. An iPhone HDR panel alone proves none of this output selection. Verify
in device logs and visually in bright highlights; system brightness/thermal/headroom
and engine tone mapping affect the visible range. HDR option is not itself proof.

## Validation and limits

Source-contract fixture passed using copied cumulatively patched source. It verifies
successful-create ordering and failure exclusion, optional extension and non-owning
layer hook. Apple SDK/full compile and phone VSync on/off/on, HDR off/on, app-switch,
and bright-highlight tests remain required. No performance or device-success claim.
