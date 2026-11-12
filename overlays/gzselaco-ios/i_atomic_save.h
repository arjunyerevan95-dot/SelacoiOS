#pragma once
// Private candidate only. The shipped build22 still blocks every save write.
#include <cerrno>
#include <cstdio>
#include <string>
#include <vector>
#include <fcntl.h>
#include <unistd.h>

namespace SelacoIOS {
inline std::string SaveLeaf(const char *path) {
 if (!path) return {};
 std::string leaf(path); auto slash=leaf.find_last_of("/\\");
 if(slash!=std::string::npos)leaf=leaf.substr(slash+1);
 if(leaf.empty()||leaf=="."||leaf=="..")return {};
 return leaf;
}
// Same-directory staging keeps rename atomic. The original survives all failures
// before rename. Writer/validator run synchronously on the engine thread.
template<class Writer, class Validator>
bool AtomicSave(const char *target, Writer write, Validator validate)
{
    if (!target || !*target) return false;
    std::string pattern(target); pattern += ".pending-XXXXXX";
    std::vector<char> path(pattern.begin(), pattern.end()); path.push_back(0);
    int fd = mkstemp(path.data());
    if (fd < 0) return false;
    close(fd);
    struct Cleanup { const char *p; ~Cleanup() { unlink(p); } } cleanup{path.data()};
    if (!write(path.data()) || !validate(path.data())) return false;
    fd = open(path.data(), O_RDONLY);
    if (fd < 0) return false;
    int result;
    do { result = fsync(fd); } while (result < 0 && errno == EINTR);
    int closed = close(fd);
    if (result != 0 || closed != 0) return false;
    return rename(path.data(), target) == 0;
}
}
