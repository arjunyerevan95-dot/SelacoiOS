// Previous rendered primitive geometry for Selaco temporal motion.
// Matching/rejection design adapted from RTGL Source/Metal/MetalScene.mm
// commit 1919834a514e15ed14cceaf716f4f572464758c9. See RTGL-MIT-LICENSE.txt.
#pragma once
#include <cstdint>
#include <cstddef>
#include <vector>
#include <map>
#include <tuple>
#include <cmath>
#include <utility>

namespace SelacoTemporal {
// Caller supplies stable object identity AND lifetime generation, not raw address.
// view identifies the main/portal recursion path; primitive identifies a stable
// surface or sprite part, not transient submission order.
struct PrimitiveKey {
    std::uint64_t object=0, generation=0, view=0, primitive=0;
    bool operator<(const PrimitiveKey& b) const {
        return std::tie(object,generation,view,primitive)<std::tie(b.object,b.generation,b.view,b.primitive);
    }
};
struct WorldVertex { float x=0, y=0, z=0; };
struct PrimitiveGeometry {
    // Post-deformation WORLD positions: includes bones/morph/model transform.
    // Vertex order and indices must represent identical corresponding vertices.
    std::vector<WorldVertex> vertices;
    std::vector<std::uint32_t> indices;
    // Caller increments topologyRevision for correspondence changes even when
    // counts and index order stay identical (e.g. replacement model).
    std::uint64_t topologyRevision=0, appearanceRevision=0;
};
enum class PrimitiveReject { None, Missing, Topology, Appearance, Invalid,
                             Duplicate, Budget, NoFrame };
struct PrimitiveHistory {
    PrimitiveReject reason=PrimitiveReject::Missing;
    // Owning result avoids dangling views when cache advances/resets.
    std::vector<WorldVertex> previousWorldVertices;
    bool valid() const { return reason==PrimitiveReject::None; }
};
class PrimitiveGeometryCache {
    struct Entry { PrimitiveGeometry geometry; bool ambiguous=false; };
    std::map<PrimitiveKey,Entry> previous_, pending_;
    std::uint64_t lastCommitted_=0, activeSerial_=0;
    bool hasCommitted_=false, active_=false;
    std::size_t bytes_=0, maxBytes_, maxEntries_;
    static bool Valid(const PrimitiveGeometry& g) {
        if(g.vertices.empty()) return false;
        for(const auto& v:g.vertices)
            if(!std::isfinite(v.x)||!std::isfinite(v.y)||!std::isfinite(v.z)) return false;
        for(auto i:g.indices) if(i>=g.vertices.size()) return false;
        return true;
    }
public:
    explicit PrimitiveGeometryCache(std::size_t maxBytes=32u*1024u*1024u,
                                    std::size_t maxEntries=65536)
        :maxBytes_(maxBytes),maxEntries_(maxEntries) {}
    // Call once per actual main frame. Serial gaps invalidate rather than reuse
    // stale geometry. End-frame Commit is explicit: failed/aborted renders never
    // become history. A single frame may contain multiple view keys.
    bool Begin(std::uint64_t serial) {
        if(active_) return false;
        if(hasCommitted_ && (lastCommitted_==UINT64_MAX || serial!=lastCommitted_+1)) {
            previous_.clear(); hasCommitted_=false;
        }
        pending_.clear(); bytes_=0; activeSerial_=serial; active_=true; return true;
    }
    PrimitiveHistory Capture(const PrimitiveKey& key,const PrimitiveGeometry& g) {
        PrimitiveHistory out;
        if(!active_) {out.reason=PrimitiveReject::NoFrame;return out;}
        auto duplicate=pending_.find(key);
        if(duplicate!=pending_.end()) {
            duplicate->second.ambiguous=true;
            out.reason=PrimitiveReject::Duplicate;return out;
        }
        if(!Valid(g)) {out.reason=PrimitiveReject::Invalid;return out;}
        // Overflow-safe accounting; bound retained dynamic CPU memory.
        if(pending_.size()>=maxEntries_ || g.vertices.size()>maxBytes_/sizeof(WorldVertex) ||
           g.indices.size()>maxBytes_/sizeof(std::uint32_t)) {
            out.reason=PrimitiveReject::Budget;return out;
        }
        const auto vbytes=g.vertices.size()*sizeof(WorldVertex);
        const auto ibytes=g.indices.size()*sizeof(std::uint32_t);
        if(vbytes>maxBytes_-bytes_ || ibytes>maxBytes_-bytes_-vbytes) {
            out.reason=PrimitiveReject::Budget;return out;
        }
        auto p=previous_.find(key);
        if(p!=previous_.end() && !p->second.ambiguous) {
            const auto& old=p->second.geometry;
            if(old.topologyRevision!=g.topologyRevision || old.vertices.size()!=g.vertices.size() || old.indices!=g.indices)
                out.reason=PrimitiveReject::Topology;
            else if(old.appearanceRevision!=g.appearanceRevision)
                out.reason=PrimitiveReject::Appearance;
            else {out.reason=PrimitiveReject::None;out.previousWorldVertices=old.vertices;}
        }
        bytes_+=vbytes+ibytes;
        pending_.emplace(key,Entry{g,false}); return out;
    }
    // Duplicate submissions cannot safely be associated after earlier Capture
    // results have escaped. Caller must check this before encoding velocities.
    bool FrameUnambiguous() const {
        if(!active_) return false;
        for(const auto& e:pending_) if(e.second.ambiguous) return false;
        return true;
    }
    bool Commit() {
        if(!active_) return false;
        previous_=std::move(pending_); pending_.clear();
        lastCommitted_=activeSerial_;hasCommitted_=true;active_=false;return true;
    }
    void Abort() {pending_.clear();active_=false;bytes_=0;}
    void Reset() {previous_.clear();pending_.clear();active_=false;hasCommitted_=false;bytes_=0;}
};
}
