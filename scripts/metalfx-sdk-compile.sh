#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source SOURCE_PIN.env
sdk=$(xcrun --sdk iphoneos --show-sdk-path)
version=$(xcrun --sdk iphoneos --show-sdk-version)
[[ ${version%%.*} -ge 26 ]] || { echo "iOS26 SDK required for frame interpolation"; exit 1; }
out="${RUNNER_TEMP:-/tmp}/selaco-metalfx-sdk"
mkdir -p "$out"
git clone --filter=blob:none --no-checkout "$GZSELACO_REPOSITORY" "$out/engine"
git -C "$out/engine" checkout --detach "$GZSELACO_COMMIT"
python3 scripts/patch-gzselaco-metalfx-device.py "$out/engine"
python3 scripts/patch-gzselaco-metalfx-present.py "$out/engine"
e="$out/engine"
flags=(-std=c++17 -target arm64-apple-ios16.0 -isysroot "$sdk" -c
  -Ioverlays/gzselaco-ios -I"$e/libraries/ZVulkan/include"
  -I"$e/libraries/ZVulkan/include/zvulkan" -I"$e/libraries/ZVulkan/src"
  -I"$e/src/common/utility")
failed=0
xcrun --sdk iphoneos clang++ "${flags[@]}" -fobjc-arc tests/metalfx_arc_ownership_test.mm -o "$out/arc-ownership.o" || failed=1
for name in i_metalfx_bridge i_metalfx_interop i_metalfx_backend; do
  xcrun --sdk iphoneos clang++ "${flags[@]}" -fobjc-arc "overlays/gzselaco-ios/$name.mm" -o "$out/$name.o" || failed=1
done
for name in vulkanswapchain vulkandevice vulkaninstance vulkanbuilders; do
  xcrun --sdk iphoneos clang++ "${flags[@]}" "$e/libraries/ZVulkan/src/$name.cpp" -o "$out/$name.o" || failed=1
done
for name in temporal_history temporal_primitive_history temporal_present_pacer temporal_sprite_runtime temporal_view_history temporal_model_history temporal_coverage_gate; do
  clang++ -std=c++17 -Wall -Wextra -Werror -Ioverlays/gzselaco-ios "tests/${name}_test.cpp" -o "$out/$name"
  "$out/$name"
done
python3 scripts/extract-metalfx-kernels.py "$out/backend-kernels.metal"
xcrun --sdk iphoneos metal -target air64-apple-ios16.0 -c "$out/backend-kernels.metal" -o "$out/backend-kernels.air" || failed=1
[[ $failed == 0 ]] || exit 1
printf 'iOS SDK %s: native MetalFX and patched Vulkan compile succeeded; NOT linked/device tested\n' "$version"
