#!/usr/bin/env bash
# Standalone candidate dependency only; never automatically launches a runner.
set -Eeuo pipefail
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
source "${repo_root}/OPENAL_CANDIDATE_PIN.env"
[[ "$(uname -s)" == Darwin ]] || { echo 'Requires macOS/Xcode'; exit 2; }
work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT
out="${repo_root}/build/artifacts/openal-ios-candidate"
mkdir -p "$out"
git init -q "$work/source"
git -C "$work/source" remote add origin "$OPENAL_REPOSITORY"
git -C "$work/source" fetch -q --depth=1 origin "$OPENAL_COMMIT"
git -C "$work/source" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$work/source" rev-parse HEAD)" == "$OPENAL_COMMIT" ]]
cmake -G Xcode -S "$work/source" -B "$work/build" \
 -DCMAKE_SYSTEM_NAME=iOS -DCMAKE_OSX_SYSROOT=iphoneos \
 -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=15.0 \
 -DCMAKE_XCODE_ATTRIBUTE_CODE_SIGNING_ALLOWED=NO -DLIBTYPE=STATIC \
 -DALSOFT_UTILS=OFF -DALSOFT_EXAMPLES=OFF -DALSOFT_TESTS=OFF \
 -DALSOFT_INSTALL=OFF -DALSOFT_BACKEND_COREAUDIO=ON -DALSOFT_REQUIRE_COREAUDIO=ON \
 -DALSOFT_BACKEND_WAVE=OFF -DALSOFT_BACKEND_PIPEWIRE=OFF \
 -DALSOFT_BACKEND_PULSEAUDIO=OFF -DALSOFT_BACKEND_JACK=OFF \
 -DALSOFT_BACKEND_PORTAUDIO=OFF -DALSOFT_BACKEND_SDL2=OFF -DALSOFT_BACKEND_SDL3=OFF
cmake --build "$work/build" --config Release --target OpenAL --parallel 3
lib="$(find "$work/build" -name libopenal.a -print -quit)"
[[ -n "$lib" && -f "$lib" ]]
xcrun lipo -verify_arch arm64 "$lib"
cp "$lib" "$out/libopenal.a"
mkdir -p "$out/include"; cp -R "$work/source/include/AL" "$out/include/"
cp "$work/source/COPYING" "$out/OPENAL-LICENSE.txt"
cp "$work/source/fmt-11.1.1/LICENSE" "$out/FMT-LICENSE.txt"
printf '%s\n' "$OPENAL_COMMIT" > "$out/source-commit.txt"
