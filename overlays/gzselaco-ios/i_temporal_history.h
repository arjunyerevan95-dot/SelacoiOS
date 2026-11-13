#pragma once
// Selaco iOS temporal state. Caller must supply previous-rendered-frame transforms.
#include <cmath>
#include <cstdint>

namespace SelacoTemporal {
struct Extent { unsigned width = 0, height = 0;
    bool operator==(const Extent &b) const { return width == b.width && height == b.height; }
};
struct Jitter { float x, y; }; // input-pixel units, not NDC
inline float Halton(unsigned index, unsigned base) {
    float result = 0.f, fraction = 1.f;
    while (index) { fraction /= float(base); result += fraction * float(index % base); index /= base; }
    return result;
}
inline Jitter SampleJitter(std::uint64_t frame) {
    const unsigned index = unsigned(frame % 16) + 1;
    return {Halton(index, 2) - .5f, Halton(index, 3) - .5f};
}
enum class Reset { None, FirstFrame, Explicit, Resize, CameraCut, ViewChanged, TimeDiscontinuity, MissingMotion };
struct Frame {
    Extent input, output;
    std::uint64_t viewKey = 0;
    double timeSeconds = 0.;
    bool cameraCut = false;
    bool completeMotion = false;
};
struct Decision { bool temporalAllowed; bool interpolateAllowed; Reset reason; Jitter jitter; };
class History {
public:
    void Invalidate() { valid_ = false; explicit_ = true; }
    Decision Begin(const Frame &frame) const {
        if (!frame.input.width || !frame.input.height || !frame.output.width || !frame.output.height ||
            frame.input.width > frame.output.width || frame.input.height > frame.output.height ||
            !std::isfinite(frame.timeSeconds))
            return {false, false, Reset::Resize, {0.f, 0.f}};
        if (!frame.completeMotion) return {false, false, Reset::MissingMotion, {0.f, 0.f}};
        Reset reason = explicit_ ? Reset::Explicit : (valid_ ? Reset::None : Reset::FirstFrame);
        if (valid_) {
            if (!(frame.input == previous_.input) || !(frame.output == previous_.output)) reason = Reset::Resize;
            else if (frame.viewKey != previous_.viewKey) reason = Reset::ViewChanged;
            else if (frame.timeSeconds <= previous_.timeSeconds || frame.timeSeconds - previous_.timeSeconds > .25)
                reason = Reset::TimeDiscontinuity;
        }
        if (frame.cameraCut) reason = Reset::CameraCut;
        // Interpolate only uninterrupted rendered frames with at least 30 Hz base rate.
        const bool interpolate = reason == Reset::None && frame.timeSeconds - previous_.timeSeconds <= 1.0 / 30.0;
        return {true, interpolate, reason, SampleJitter(reason == Reset::None ? frameIndex_ : 0)};
    }
    // Commit only after successful encoding, not on simulation ticks or failed frames.
    void Commit(const Frame &frame, const Decision &decision) {
        if (!decision.temporalAllowed) { Invalidate(); return; }
        frameIndex_ = decision.reason == Reset::None ? frameIndex_ + 1 : 1;
        previous_ = frame; valid_ = true; explicit_ = false;
    }
private:
    bool valid_ = false, explicit_ = false;
    std::uint64_t frameIndex_ = 0;
    Frame previous_;
};
} // namespace SelacoTemporal
