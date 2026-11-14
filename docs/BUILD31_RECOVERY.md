# Build31 validation candidate
Corrects VK_EXT_metal_objects from instance-extension checks to device-extension enablement/checks, preserving instance-create export intent. Adds bounded failed-creation retry and skips unused framegen polling in ordinary mode. Control/audio/save implementation unchanged.

Build30 runtime evidence showed experimental mode selected but no temporal consumption or framegen pairs, with prerequisite failure. This identifies an integration defect, not measured performance recovery. Portable retry, materialized device scope, admission and routing contracts pass. Native build and on-device validation remain required.

Retry:0.5/1/2/4seconds capped, independent modes, immediate retry on material configuration change; never sleeps or changes queue/fence retirement. Khronos reference:https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_metal_objects.html
