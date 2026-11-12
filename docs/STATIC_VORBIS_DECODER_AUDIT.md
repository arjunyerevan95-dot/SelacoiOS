# Static Vorbis recovery

## Root cause

Pinned ZMusic `d3b730795784bff3f97571446101c57c1c6ac9bc` only attempts its
libsndfile decoder when `HAVE_SNDFILE` exists. The iOS build sets
`DYN_SNDFILE=OFF` without supplying static libsndfile. Configuration can succeed
while the common decoder factory has no Ogg Vorbis backend. Both SFX and streamed
music call that factory; successful OpenAL device creation does not prove decoding.
The device observations (OpenAL CoreAudio opens; repeated unable-to-identify
music errors; audio metadata reports Vorbis) support this missing-codec cause.

## Bounded repair

Reuse the pinned dependency's existing `thirdparty/libxmp/src/loaders/vorbis.c`
(stb_vorbis 1.22), not a floating download or extra codec dependency chain. The
patcher preserves its complete MIT/Unlicense text. The isolated generated copy:

- removes libxmp's wrapper, which disables seek and renames symbols for libxmp;
- uses the original stb integer typedef branch instead of libxmp common.h;
- gives symbols a separate `selaco_stb_vorbis_*` prefix and hidden visibility;
- retains seek APIs for music looping and restricts channels to mono/stereo,
  matching ZMusic's public `ChannelConfig` API.

The new bridge registers before optional codecs in `SoundDecoder::CreateDecoder`.
It supplies float PCM, length, frame offset and sample/millisecond seek. Reader
ownership transfers only on successful open; failed probes restore position and
leave ownership with the caller. The compressed resource is capped at 64 MiB;
PCM is decoded incrementally with a fixed 16 KiB scratch buffer, not a full-song
PCM allocation. Compressed input is copied once. This avoids bringing static
libsndfile/libogg/libvorbis and their build configuration into the candidate.

The full-engine configure script fails before expensive engine compilation if
`libzmusic.a` lacks the defined static Vorbis entry point. Dynamic codec loading
remains off; no licensed audio is fetched, copied, committed or embedded.

## Reproduction and results

From this repository, with a fresh checkout at the exact ZMusic pin:

```
python3 scripts/patch-zmusic-ios-m0.py /path/to/ZMusic overlays/zmusic-ios/music_fluidsynth_stub.cpp
bash scripts/test-zmusic-vorbis.sh /path/to/ZMusic
```

The test uses ffmpeg solely as a local synthetic-tone fixture generator; it is
not an application/build dependency. It compiles the real patched decoder
factory and upstream `SndFile_OpenSong` implementation, without libsndfile or
mpg123. Mono and stereo one-second 48 kHz Vorbis tones include loop tags.

Passed:
- nonzero finite float PCM, exact frame count and EOF;
- millisecond seek and repeated exact sample seeks, byte-identical to baseline;
- three seconds of actual upstream music-loop output from a one-second file;
- failed-probe reader ownership and position, including nonzero starting position;
- oversized compressed-resource rejection without allocation;
- ASan and UBSan. LeakSanitizer is unavailable under the sandbox's ptrace and was
  disabled explicitly; no claim of a leak-sanitizer pass;
- Python/shell syntax and diff whitespace checks.

The seek tests exposed stb's internal predecoded offset, which is not the
consumed sample offset expected by ZMusic. The bridge now tracks delivered
frames explicitly. Symbol inspection confirms the independent decoder prefix;
linked decoder internals are local/hidden, not shared libxmp symbols.

## Limits

No new Apple build or on-device audio verification has been performed for this
repair. Existing audio-session/backend behavior is unchanged. The backend is
Vorbis, not Opus/FLAC/MP3. It inherits stb's documented limitations, including
unsupported ancient floor-0 Vorbis and chained streams; files above 64 MiB and
multichannel audio are rejected rather than silently misdecoded. Other optional
backends may handle formats they already support. Existing compressed-data
fixtures are not included in this repository; tests generate their own tones.
