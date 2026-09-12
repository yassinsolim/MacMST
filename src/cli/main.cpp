#include "probe/report.hpp"

#include <exception>
#include <iostream>
#include <string_view>

int main(int argc, char* argv[]) {
    if (argc == 2 && std::string_view(argv[1]) == "--help") {
        std::cout << "Usage: macmst probe [--json]\n"
                     "Read-only host and display observations. No DDC, AUX, or MST transactions.\n";
        return 0;
    }
    if (argc < 2 || std::string_view(argv[1]) != "probe" || argc > 3 ||
        (argc == 3 && std::string_view(argv[2]) != "--json")) {
        std::cerr << "Usage: macmst probe [--json]\n";
        return 2;
    }
    try {
        const auto report = macmst::macos::collect_probe();
        std::cout << (argc == 3 ? report.json : report.text);
        if (!report.complete) {
            std::cerr << "Some observations failed; see the report errors.\n";
            return 1;
        }
        return 0;
    } catch (const std::exception&) {
        std::cerr << "Probe failed to construct a report.\n";
        return 1;
    }
}