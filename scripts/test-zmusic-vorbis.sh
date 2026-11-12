#!/usr/bin/env bash
# CPU-only synthetic test against an already patched exact ZMusic checkout.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
z="$(cd "${1:?pass the patched ZMusic checkout}" && pwd)"
source "${root}/DEPENDENCY_TRIAL_PINS.env"
[[ "$(git -C "$z" rev-parse HEAD)" == "$ZMUSIC_COMMIT" ]]
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
for channels in 1 2; do
  ffmpeg -hide_banner -loglevel error -y -f lavfi \
    -i 'sine=frequency=440:duration=1:sample_rate=48000' -ac "$channels" \
    -c:a libvorbis -metadata LOOP_START=128 -metadata LOOP_END=24000 "$work/$channels.ogg"
done
"${CXX:-c++}" -std=c++11 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -Dstrnicmp=strncasecmp -include strings.h \
  -I"$z/source" -I"$z/source/zmusic" -I"$z/include" -I"$z/thirdparty" \
  "$root/tests/vorbis_decoder_test.cpp" "$z/source/decoder/selaco_vorbis_decoder.cpp" \
  "$z/source/decoder/sounddecoder.cpp" "$z/source/streamsources/music_libsndfile.cpp" \
  -o "$work/test"
# LeakSanitizer cannot run under the cloud sandbox's ptrace. ASan/UBSan stay on.
ASAN_OPTIONS=detect_leaks=0 "$work/test" "$work/1.ogg" "$work/2.ogg"
echo 'PASS: mono/stereo PCM, EOF, sample/ms seek, repeated loops, factory ownership and invalid input'
