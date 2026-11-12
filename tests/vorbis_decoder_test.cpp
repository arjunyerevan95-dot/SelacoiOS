#include "zmusic/sounddecoder.h"
#include "streamsources/streamsource.h"
#include <cassert>
#include <cmath>
#include <cstring>
#include <fstream>
#include <iterator>
#include <limits>
#include <memory>
#include <vector>
#ifdef SELACO_TEST_OPENAL
#include "vorbis_openal_integration.h"
#endif
extern SoundDecoder *SelacoCreateVorbisDecoder(MusicIO::FileInterface *);
struct TrackedReader : MusicIO::MemoryReader {
    bool &closed;
    TrackedReader(const std::vector<uint8_t> &data, bool &flag) : MemoryReader(data.data(), data.size()), closed(flag) {}
    void close() override { closed = true; delete this; }
};
static std::vector<uint8_t> file(const char *p) {
    std::ifstream in(p, std::ios::binary); assert(in);
    return {std::istreambuf_iterator<char>(in), std::istreambuf_iterator<char>()};
}
int main(int argc, char **argv) {
    assert(argc == 3);
    for (int channels = 1; channels <= 2; ++channels) {
        auto bytes = file(argv[channels]); bool closed = false;
        auto *reader = new TrackedReader(bytes, closed);
        std::unique_ptr<SoundDecoder> d(SoundDecoder::CreateDecoder(reader)); assert(d && !closed);
        int rate; ChannelConfig config; SampleType type;
        d->getInfo(&rate, &config, &type);
        assert(rate == 48000 && config == (channels == 1 ? ChannelConfig_Mono : ChannelConfig_Stereo));
        assert(type == SampleType_Int16 && d->getSampleLength() == 48000);
        auto decoded = d->readAll(); assert(decoded.size() == 48000 * channels * sizeof(int16_t));
        #ifdef SELACO_TEST_OPENAL
        VerifyEngineOutput(decoded,config,type,rate);
        #endif
        double energy = 0;
        for (size_t i = 0; i < decoded.size(); i += sizeof(int16_t)) {
            int16_t f; std::memcpy(&f, decoded.data()+i, sizeof(f)); energy += double(f)*f/(32768.*32768.);
        }
        assert(energy > 1 && d->getSampleOffset() == 48000);
        const size_t frameBytes = channels * sizeof(int16_t);
        std::vector<char> block(256 * frameBytes);
        assert(d->seek(100, true, true) && d->getSampleOffset() == 4800);
        assert(d->read(block.data(), block.size()) == block.size());
        assert(std::memcmp(block.data(), decoded.data()+4800*frameBytes, block.size()) == 0);
        for (int loop = 0; loop < 4; ++loop) {
            assert(d->seek(128, false, true));
            assert(d->read(block.data(), block.size()) == block.size());
            assert(std::memcmp(block.data(), decoded.data()+128*frameBytes, block.size()) == 0);
        }
        assert(!d->seek(std::numeric_limits<size_t>::max(), true, true));
        assert(!d->seek(48001, false, true));
        assert(d->seek(0, false, true));
        assert(d->read(block.data(), frameBytes-1) == 0 && d->getSampleOffset() == 0);
        d.reset(); assert(closed);
        // Actual upstream music route, including loop-tag parsing and repeated looping.
        closed = false;
        std::unique_ptr<StreamSource> song(SndFile_OpenSong(new TrackedReader(bytes, closed)));
        assert(song && !closed); song->SetPlayMode(true);
        auto fmt=song->GetFormatEx(); assert(fmt.mSampleType==SampleType_Int16);
        std::vector<int16_t> music(48000 * channels * 3);
        assert(song->GetData(music.data(), music.size()*sizeof(int16_t)));
        double sum=0; for (int16_t f:music) { sum += double(f)*f/(32768.*32768.); } assert(sum>1);
        song.reset(); assert(closed);
    }
    // Failed opens must restore position and retain caller ownership.
    for (auto bytes : {std::vector<uint8_t>{'b','a','d'}, std::vector<uint8_t>{'O','g','g','S',0,0,0,0}}) {
        bool closed=false; auto *r=new TrackedReader(bytes,closed);
        assert(!SelacoCreateVorbisDecoder(r)); assert(!closed && r->tell()==0); r->close(); assert(closed);
    }
    { // A claimed resource above the compressed cap must not be allocated/read.
        std::vector<uint8_t> data = {'O','g','g','S'}; bool closed = false;
        auto *r = new TrackedReader(data, closed); r->length = 64L * 1024 * 1024 + 1;
        assert(!SelacoCreateVorbisDecoder(r)); assert(!closed && r->tell() == 0); r->close();
    }
    { // Failed probe restores a nonzero reader position too.
        std::vector<uint8_t> data = {'x','b','a','d'}; bool closed = false;
        auto *r = new TrackedReader(data, closed); r->seek(1, SEEK_SET);
        assert(!SelacoCreateVorbisDecoder(r)); assert(!closed && r->tell() == 1); r->close();
    }
    assert(!SelacoCreateVorbisDecoder(nullptr));
}
