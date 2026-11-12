#include "i_atomic_save.h"
#include <cassert>
#include <fstream>
#include <filesystem>
#include <stdexcept>
#include <iostream>
namespace fs=std::filesystem;
std::string read(const fs::path &p) { std::ifstream f(p); return {std::istreambuf_iterator<char>(f),{}}; }
bool writeSave(const char *p) { std::ofstream f(p); f << "valid-new-save"; f.close(); return bool(f); }
bool valid(const char *p) { return read(p)=="valid-new-save"; }
int main() {
 assert(SelacoIOS::SaveLeaf("/outside/old.zds")=="old.zds");
 assert(SelacoIOS::SaveLeaf("../old.zds")=="old.zds");
 assert(SelacoIOS::SaveLeaf("..").empty());
 char temp[]="/tmp/selaco-save-test-XXXXXX"; const char *dir=mkdtemp(temp); assert(dir);
 fs::path root(dir), target=root/"save.zds"; std::ofstream(target)<<"old-save";
 auto count=[&] {return std::distance(fs::directory_iterator(root),fs::directory_iterator{});};
 assert(!SelacoIOS::AtomicSave(target.c_str(),[](const char*p){std::ofstream(p)<<"partial";return false;},valid));
 assert(read(target)=="old-save" && count()==1);
 assert(!SelacoIOS::AtomicSave(target.c_str(),writeSave,[](const char*){return false;}));
 assert(read(target)=="old-save" && count()==1);
 try {SelacoIOS::AtomicSave(target.c_str(),[](const char*)->bool{throw std::runtime_error("serialization failed");},valid);assert(false);}catch(const std::runtime_error&){}
 assert(read(target)=="old-save" && count()==1);
 assert(SelacoIOS::AtomicSave(target.c_str(),writeSave,valid));assert(read(target)=="valid-new-save"&&count()==1);
 fs::path fresh=root/"fresh.zds";assert(SelacoIOS::AtomicSave(fresh.c_str(),writeSave,valid));assert(valid(fresh.c_str()));
 fs::path blocked=root/"directory";fs::create_directory(blocked);assert(!SelacoIOS::AtomicSave(blocked.c_str(),writeSave,valid));assert(fs::is_directory(blocked));
 assert(!SelacoIOS::AtomicSave((root/"missing"/"save.zds").c_str(),writeSave,valid));
 assert(!SelacoIOS::AtomicSave(nullptr,writeSave,valid));
 assert(count()==3);fs::remove_all(root);std::cout<<"atomic save tests passed\n";
}
