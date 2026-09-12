#include "isolation/mock_helper.hpp"

#include <algorithm>
#include <cerrno>
#include <csignal>
#include <cstdlib>
#include <fcntl.h>
#include <sys/resource.h>
#include <unistd.h>

namespace {

bool write_all(int descriptor, std::span<const std::uint8_t> bytes) {
    while (!bytes.empty()) {
        const ssize_t written = write(descriptor, bytes.data(), bytes.size());
        if (written > 0) {
            bytes = bytes.subspan(static_cast<std::size_t>(written));
        } else if (written < 0 && errno == EINTR) {
            continue;
        } else {
            return false;
        }
    }
    return true;
}

[[noreturn]] void hang() {
    for (;;) {
        pause();
    }
}

}

int main(int argc, char** argv) {
    using namespace macmst::isolation;
    if (argc != 2) {
        return 64;
    }
    const std::string_view scenario(argv[1]);
    if (std::find(mock_scenarios.begin(), mock_scenarios.end(), scenario) == mock_scenarios.end() &&
        std::find(dpdv_mock_scenarios.begin(), dpdv_mock_scenarios.end(), scenario) == dpdv_mock_scenarios.end()) {
        return 64;
    }
    const rlimit no_core {0, 0};
    if (setrlimit(RLIMIT_CORE, &no_core) != 0 || std::getenv("MACMST_MOCK_ENV_SENTINEL") != nullptr) {
        return 70;
    }
    for (int descriptor = STDERR_FILENO + 1; descriptor < 256; ++descriptor) {
        if (fcntl(descriptor, F_GETFD) >= 0 || errno != EBADF) {
            return 71;
        }
    }
    std::uint8_t input = 0;
    if (read(STDIN_FILENO, &input, sizeof(input)) != 0) {
        return 72;
    }
    constexpr std::array<std::uint8_t, 11> ready {'m', 'o', 'c', 'k', '-', 'r', 'e', 'a', 'd', 'y', '\n'};
    if (!write_all(STDERR_FILENO, ready)) {
        return 74;
    }
    if (scenario.starts_with("dpdv-")) {
        DpdvFrame frame;
        frame.reason = DpdvReason::None;
        frame.device_id = scenario == "dpdv-id-mismatch" ? 999 : 100;
        frame.service_id = 200;
        frame.transport_id = 300;
        frame.phase = scenario == "dpdv-dry-run" ? DpdvPhase::DryRunReady : DpdvPhase::OpenAttempted;
        frame.flags = scenario == "dpdv-dry-run" ? 0 : 1;
        if (!write_all(STDOUT_FILENO, dpdv_response(frame))) {
            return 74;
        }
        if (scenario == "dpdv-dry-run") {
            return 0;
        }
        if (scenario == "dpdv-hang") {
            hang();
        }
        frame.phase = scenario == "dpdv-denied" ? DpdvPhase::OpenFailed :
            scenario == "dpdv-close-failed" ? DpdvPhase::CloseFailed : DpdvPhase::CloseSucceeded;
        frame.flags = scenario == "dpdv-denied" ? 3 : 63;
        frame.open_return = scenario == "dpdv-denied" ? 0xe00002c1U : 0;
        frame.close_return = scenario == "dpdv-close-failed" ? 0xe00002bcU : 0;
        auto response = dpdv_response(frame);
        if (scenario == "dpdv-malformed") {
            response[0] = 'X';
        }
        if (!write_all(STDOUT_FILENO, response)) {
            return 74;
        }
        if (scenario == "dpdv-cleanup-hang") {
            hang();
        }
        return 0;
    }
    if (scenario == "crash" || scenario == "sigterm" || scenario == "sigkill") {
        const int signal_number = scenario == "crash" ? SIGABRT : scenario == "sigterm" ? SIGTERM : SIGKILL;
        if (signal_number != SIGKILL) {
            std::signal(signal_number, SIG_DFL);
        }
        raise(signal_number);
        return 70;
    }
    if (scenario == "early-exit") {
        return 0;
    }
    if (scenario == "closed-pipes") {
        close(STDOUT_FILENO);
        close(STDERR_FILENO);
        hang();
    }
    if (scenario == "hang") {
        hang();
    }
    if (scenario == "oversized" || scenario == "stderr-flood") {
        std::array<std::uint8_t, 2048> flood {};
        flood.fill('x');
        if (!write_all(scenario == "oversized" ? STDOUT_FILENO : STDERR_FILENO, flood)) {
            return 74;
        }
        hang();
    }
    auto response = mock_response(scenario == "failure" ? 0xe00002bcU : 0U);
    if (scenario == "malformed") {
        response[0] = 'X';
    }
    if (!write_all(STDOUT_FILENO, response)) {
        return 74;
    }
    if (scenario == "cleanup-hang") {
        hang();
    }
    return scenario == "success-bad-exit" ? 7 : 0;
}