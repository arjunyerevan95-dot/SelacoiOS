// Static Ogg Vorbis bridge for the exact pinned ZMusic SoundDecoder API.
// Uses ZMusic's already-vendored selaco_stb_vorbis; no dynamic codec library required.
#include "zmusic/sounddecoder.h"
#include <algorithm>
#include <atomic>
#include <climits>
#include <cstring>
#include <limits>
#include <new>
#define STB_VORBIS_NO_STDIO
#define STB_VORBIS_NO_PUSHDATA_API
#define STB_VORBIS_MAX_CHANNELS 2
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <math.h>
#include <limits.h>
#pragma GCC visibility push(hidden)
#include "selaco_stb_vorbis.c"
#pragma GCC visibility pop

namespace {
class SelacoVorbisDecoder final : public SoundDecoder {
    std::vector<unsigned char> compressed;
    selaco_stb_vorbis *stream = nullptr;
    MusicIO::FileInterface *reader = nullptr;
    unsigned rate = 0, channels = 0, frames = 0;
    size_t cursor = 0; // delivered frames, not stb's internally predecoded position
public:
    ~SelacoVorbisDecoder() override {
        if (stream) selaco_stb_vorbis_close(stream);
        if (reader) reader->close();
    }
    bool open(MusicIO::FileInterface *input) override {
        const long start = input->tell(), end = input->filelength();
        if (start < 0 || end <= start || end - start > 64L * 1024 * 1024) return false;
        unsigned char sig[4];
        if (input->read(sig, 4) != 4 || std::memcmp(sig, "OggS", 4)) return false;
        if (input->seek(start, SEEK_SET)) return false;
        compressed.resize(static_cast<size_t>(end - start));
        size_t done = 0;
        while (done < compressed.size()) {
            const int32_t count = static_cast<int32_t>(std::min<size_t>(65536, compressed.size() - done));
            const long got = input->read(compressed.data() + done, count);
            if (got <= 0 || got > count) return false;
            done += static_cast<size_t>(got);
        }
        int error = 0;
        stream = selaco_stb_vorbis_open_memory(compressed.data(), static_cast<int>(compressed.size()), &error, nullptr);
        if (!stream) return false;
        const selaco_stb_vorbis_info info = selaco_stb_vorbis_get_info(stream);
        if ((info.channels != 1 && info.channels != 2) || info.sample_rate == 0) return false;
        rate = info.sample_rate; channels = static_cast<unsigned>(info.channels);
        frames = selaco_stb_vorbis_stream_length_in_samples(stream);
        if (!frames || selaco_stb_vorbis_get_error(stream) != VORBIS__no_error || !selaco_stb_vorbis_seek_start(stream)) return false;
        reader = input; // ownership transfers only after the entire open succeeds
        return true;
    }
    void getInfo(int *sr, ChannelConfig *ch, SampleType *ty) override {
        if (sr) *sr = static_cast<int>(rate);
        if (ch) *ch = channels == 1 ? ChannelConfig_Mono : ChannelConfig_Stereo;
        if (ty) *ty = SampleType_Int16;
    }
    size_t read(char *buffer, size_t bytes) override {
        if (!buffer || !stream) return 0;
        const size_t frameBytes = channels * sizeof(short);
        size_t requested = bytes / frameBytes, written = 0;
        short block[8192];
        while (requested) {
            const int count = static_cast<int>(std::min<size_t>(requested, 8192 / channels));
            const int got = selaco_stb_vorbis_get_samples_short_interleaved(stream, channels, block, count * channels);
            if (got <= 0) break;
            const size_t amount = static_cast<size_t>(got) * frameBytes;
            std::memcpy(buffer + written, block, amount);
            written += amount; requested -= static_cast<size_t>(got); cursor += static_cast<size_t>(got);
        }
        if (written) {
            static std::atomic_flag reported = ATOMIC_FLAG_INIT;
            if (!reported.test_and_set()) fprintf(stderr, "Selaco static Vorbis PCM ready: %u Hz, %u channels\n", rate, channels);
        }
        return written;
    }
    bool seek(size_t offset, bool milliseconds, bool /*mayrestart*/) override {
        if (!stream) return false;
        const long double target = milliseconds ? static_cast<long double>(offset) * rate / 1000 : offset;
        if (target > frames) return false;
        if (!selaco_stb_vorbis_seek(stream, static_cast<unsigned>(target))) return false;
        cursor = static_cast<size_t>(target);
        return true;
    }
    size_t getSampleOffset() override {
        return cursor;
    }
    size_t getSampleLength() override { return frames; }
};
}
SoundDecoder *SelacoCreateVorbisDecoder(MusicIO::FileInterface *reader) {
    if (!reader) return nullptr;
    const long pos = reader->tell();
    SelacoVorbisDecoder *decoder = nullptr;
    try {
        decoder = new SelacoVorbisDecoder;
        if (decoder->open(reader)) return decoder;
    } catch (const std::bad_alloc &) { /* reject oversized/corrupt resource safely */ }
    delete decoder;
    if (pos >= 0) reader->seek(pos, SEEK_SET);
    return nullptr;
}
