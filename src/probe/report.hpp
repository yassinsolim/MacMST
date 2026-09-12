#pragma once

#include <string>

namespace macmst {

struct ProbeOutput {
    std::string text;
    std::string json;
    bool complete;
};

namespace macos {
ProbeOutput collect_probe();
}

}