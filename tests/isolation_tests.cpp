#include "isolation/mock_helper.hpp"
#include "isolation/dpdv_protocol.hpp"

#include <algorithm>
#include <cerrno>
#include <charconv>
#include <csignal>
#include <cstdlib>
#include <cstring>
#include <dirent.h>
#include <fcntl.h>
#include <iostream>
#include <set>
#include <stdexcept>
#include <sys/wait.h>
#include <unistd.h>

namespace {

std::set<int> open_descriptors() {
    DIR* directory = opendir("/dev/fd");
    if (directory == nullptr) {
        throw std::runtime_error("Cannot enumerate parent descriptors");
    }
    const int own_descriptor = dirfd(directory);
    std::set<int> result;
    for (dirent* entry = readdir(directory); entry != nullptr; entry = readdir(directory)) {
        int descriptor = -1;
        const auto parsed = std::from_chars(entry->d_name, entry->d_name + std::strlen(entry->d_name), descriptor);
        if (parsed.ec == std::errc() && parsed.ptr == entry->d_name + std::strlen(entry->d_name) && descriptor != own_descriptor) {
            result.insert(descriptor);
        }
    }
    closedir(directory);
    return result;
}

bool already_reaped(pid_t child) {
    int wait_status = 0;
    errno = 0;
    return waitpid(child, &wait_status, WNOHANG) == -1 && errno == ECHILD;
}

}

int main(int argc, char** argv) {
    using namespace macmst::isolation;
    using namespace std::chrono_literals;
    if (argc != 2) {
        return 2;
    }
    DpdvFrame selected;
    selected.phase = DpdvPhase::DryRunReady;
    selected.reason = DpdvReason::None;
    selected.device_id = 0xfedcba9876543210ULL;
    selected.service_id = 202;
    selected.transport_id = 303;
    const auto dry_frame = dpdv_response(selected);
    const auto dry = parse_dpdv_response(dry_frame);
    if (!dry || dry->device_id != selected.device_id || dry->flags != 0) {
        return 1;
    }
    selected.phase = DpdvPhase::OpenAttempted;
    selected.flags = open_attempted_flag;
    const auto started_frame = dpdv_response(selected);
    if (parse_dpdv_response(started_frame).has_value() || !valid_dpdv_prefix(started_frame)) {
        return 1;
    }
    std::array<std::uint8_t, dpdv_frame_size * 2> operation_frames {};
    std::copy(started_frame.begin(), started_frame.end(), operation_frames.begin());
    for (const auto phase : {DpdvPhase::OpenFailed, DpdvPhase::CloseSucceeded, DpdvPhase::CloseFailed}) {
        selected.phase = phase;
        selected.flags = phase == DpdvPhase::OpenFailed ? 3 : 63;
        selected.open_return = phase == DpdvPhase::OpenFailed ? 0xe00002bcU : 0;
        selected.close_return = phase == DpdvPhase::CloseFailed ? 0xffffffffU : 0;
        selected.open_microseconds = 123;
        selected.close_microseconds = phase == DpdvPhase::OpenFailed ? 0 : 456;
        const auto completed_frame = dpdv_response(selected);
        std::copy(completed_frame.begin(), completed_frame.end(), operation_frames.begin() + dpdv_frame_size);
        const auto completed = parse_dpdv_response(operation_frames);
        if (!completed || completed->phase != phase || completed->open_return != selected.open_return ||
            completed->close_return != selected.close_return || !valid_dpdv_prefix(operation_frames)) {
            return 1;
        }
    }
    for (std::size_t index : {0U, 4U, 5U, 6U, 7U, 24U}) {
        auto invalid = operation_frames;
        invalid[dpdv_frame_size + index] ^= 0xff;
        if (parse_dpdv_response(invalid).has_value()) {
            return 1;
        }
    }
    if (parse_dpdv_response({operation_frames.data(), operation_frames.size() - 1}).has_value()) {
        return 1;
    }
    for (std::uint32_t status : {0U, 0xe00002bcU, 0xffffffffU}) {
        const auto frame = mock_response(status);
        if (parse_mock_response(frame) != status || parse_mock_response({frame.data(), frame.size() - 1}).has_value()) {
            std::cerr << "Mock status frame must preserve every raw bit and reject truncation\n";
            return 1;
        }
    }
    for (std::size_t index = 0; index < mock_header.size(); ++index) {
        auto malformed = mock_response(0);
        malformed[index] ^= 0xff;
        if (parse_mock_response(malformed).has_value()) {
            std::cerr << "Invalid magic/version/operation/reserved fields must be rejected\n";
            return 1;
        }
    }
    const std::array<std::uint8_t, mock_frame_size + 1> oversized {};
    if (parse_mock_response(oversized).has_value()) {
        return 1;
    }
    const int sentinel = open("/dev/null", O_RDONLY);
    if (sentinel < 0 || setenv("MACMST_MOCK_ENV_SENTINEL", "fixture-only", 1) != 0) {
        return 1;
    }
    const auto initial_descriptors = open_descriptors();
    struct TestCase {
        std::string_view scenario;
        MockOutcome expected;
        int signal_number;
    };
    const std::array<TestCase, 13> cases {{
        {"success", MockOutcome::Success, 0}, {"failure", MockOutcome::OperationFailure, 0},
        {"crash", MockOutcome::AbnormalExit, SIGABRT}, {"sigterm", MockOutcome::AbnormalExit, SIGTERM},
        {"sigkill", MockOutcome::AbnormalExit, SIGKILL}, {"hang", MockOutcome::Timeout, SIGKILL},
        {"malformed", MockOutcome::ProtocolFailure, 0}, {"early-exit", MockOutcome::ProtocolFailure, 0},
        {"oversized", MockOutcome::OutputLimit, SIGKILL}, {"cleanup-hang", MockOutcome::Timeout, SIGKILL},
        {"closed-pipes", MockOutcome::Timeout, SIGKILL}, {"stderr-flood", MockOutcome::OutputLimit, SIGKILL},
        {"success-bad-exit", MockOutcome::AbnormalExit, 0}
    }};
    std::set<pid_t> children;
    for (const auto& test : cases) {
        const auto deadline = test.expected == MockOutcome::Timeout ? 1000ms : 2000ms;
        const auto result = run_mock_helper(argv[1], test.scenario, deadline, 1000ms);
        if (result.outcome != test.expected || !result.reaped || result.spawn_attempts != 1 ||
            result.elapsed > deadline + 1500ms || !result.wait_status.has_value() ||
            !already_reaped(result.pid) || open_descriptors() != initial_descriptors || !children.insert(result.pid).second) {
            std::cerr << "Mock case failed: " << test.scenario << "; outcome=" << static_cast<int>(result.outcome)
                      << "; error=" << result.system_error << "; reaped=" << result.reaped << '\n';
            return 1;
        }
        const std::string_view stderr_text(reinterpret_cast<const char*>(result.stderr_bytes.data()), result.stderr_size);
        if (!stderr_text.starts_with("mock-ready\n")) {
            std::cerr << "Mock scenario was not entered: " << test.scenario << '\n';
            return 1;
        }
        if (test.signal_number != 0 && (!WIFSIGNALED(*result.wait_status) || WTERMSIG(*result.wait_status) != test.signal_number)) {
            std::cerr << "Raw terminating signal was not preserved: " << test.scenario << '\n';
            return 1;
        }
        if (test.expected == MockOutcome::Success && (result.mock_ior_return != 0 || result.termination_sent)) {
            return 1;
        }
        if (test.expected == MockOutcome::OperationFailure && (result.mock_ior_return != 0xe00002bcU || result.termination_sent)) {
            std::cerr << "Mock operation failure must preserve raw IOReturn independently of process exit\n";
            return 1;
        }
        if (test.expected == MockOutcome::Timeout &&
            (!result.termination_sent || result.failure_trigger != MockOutcome::Timeout || result.elapsed < deadline)) {
            return 1;
        }
        if (test.scenario == "cleanup-hang" && result.stdout_size != mock_frame_size) {
            std::cerr << "A pre-cleanup response must not bypass the watchdog\n";
            return 1;
        }
        if (test.expected == MockOutcome::OutputLimit &&
            result.stdout_size > result.stdout_bytes.size()) {
            return 1;
        }
        std::cout << "PASS: " << test.scenario << "; one spawn, captured output, reaped, no FD leak; "
                  << result.elapsed.count() << " ms\n";
    }
    const std::array<TestCase, 8> framed_cases {{
        {"dpdv-dry-run", MockOutcome::Success, 0}, {"dpdv-success", MockOutcome::Success, 0},
        {"dpdv-denied", MockOutcome::OperationFailure, 0}, {"dpdv-close-failed", MockOutcome::OperationFailure, 0},
        {"dpdv-hang", MockOutcome::Timeout, SIGKILL}, {"dpdv-cleanup-hang", MockOutcome::Timeout, SIGKILL},
        {"dpdv-malformed", MockOutcome::ProtocolFailure, 0}, {"dpdv-id-mismatch", MockOutcome::ProtocolFailure, 0}
    }};
    for (const auto& test : framed_cases) {
        const auto result = run_mock_helper(argv[1], test.scenario, 1000ms, 1000ms);
        if (result.outcome != test.expected || !result.reaped || result.spawn_attempts != 1 ||
            !already_reaped(result.pid) || open_descriptors() != initial_descriptors || !children.insert(result.pid).second) {
            std::cerr << "M2F-framed mock failed: " << test.scenario << '\n';
            return 1;
        }
        if (test.signal_number != 0 && (!result.wait_status || !WIFSIGNALED(*result.wait_status) ||
            WTERMSIG(*result.wait_status) != test.signal_number || !result.termination_sent)) {
            return 1;
        }
        if (test.expected == MockOutcome::Success && !result.dpdv_reply) {
            return 1;
        }
        std::cout << "PASS: " << test.scenario << "; mock M2F framing, one spawn and reap\n";
    }
    for (unsigned int invocation = 0; invocation < 5; ++invocation) {
        const auto result = run_mock_helper(argv[1], "success", 2000ms, 1000ms);
        if (result.outcome != MockOutcome::Success || result.spawn_attempts != 1 || !result.reaped ||
            !children.insert(result.pid).second || !already_reaped(result.pid) || open_descriptors() != initial_descriptors) {
            std::cerr << "Repeated invocations require fresh, reaped one-shot helpers\n";
            return 1;
        }
    }
    const auto missing = run_mock_helper("/nonexistent-macmst-fixture/macmst_mock_helper", "success", 100ms, 100ms);
    if (missing.outcome != MockOutcome::SpawnFailure || missing.system_error != ENOENT || missing.pid != 0 ||
        missing.spawn_attempts != 1 || open_descriptors() != initial_descriptors) {
        return 1;
    }
    for (const auto& result : {run_mock_helper(argv[1], "dpdv-open-check", 100ms, 100ms),
                               run_mock_helper(argv[1], "success", 0ms, 100ms),
                               run_mock_helper("/bin/sh", "success", 100ms, 100ms),
                               run_dpdv_helper("/bin/sh", true, 1, 2, 3, 100ms, 100ms),
                               run_dpdv_helper("/nonexistent/macmst_dpdv_open_helper", true, 0, 2, 3, 100ms, 100ms)}) {
        if (result.outcome != MockOutcome::InvalidInput || result.spawn_attempts != 0) {
            std::cerr << "Unknown/real operation, invalid deadlines and arbitrary executables must not spawn\n";
            return 1;
        }
    }
    sigset_t blocked;
    sigset_t previous;
    sigemptyset(&blocked);
    sigaddset(&blocked, SIGTERM);
    if (sigprocmask(SIG_BLOCK, &blocked, &previous) != 0) {
        return 1;
    }
    const auto unmasked = run_mock_helper(argv[1], "sigterm", 2000ms, 1000ms);
    const int restored = sigprocmask(SIG_SETMASK, &previous, nullptr);
    if (restored != 0 || unmasked.outcome != MockOutcome::AbnormalExit || !unmasked.reaped ||
        !unmasked.wait_status.has_value() || !WIFSIGNALED(*unmasked.wait_status) || WTERMSIG(*unmasked.wait_status) != SIGTERM ||
        !already_reaped(unmasked.pid) || open_descriptors() != initial_descriptors) {
        std::cerr << "Helper signal mask must not inherit a parent's blocked SIGTERM\n";
        return 1;
    }
    struct sigaction ignored {};
    struct sigaction original {};
    ignored.sa_handler = SIG_IGN;
    sigemptyset(&ignored.sa_mask);
    if (sigaction(SIGCHLD, &ignored, &original) != 0) {
        return 1;
    }
    const auto ownership_lost = run_mock_helper(argv[1], "success", 2000ms, 1000ms);
    const int handler_restored = sigaction(SIGCHLD, &original, nullptr);
    if (handler_restored != 0 || ownership_lost.outcome != MockOutcome::ReapFailure ||
        ownership_lost.system_error != ECHILD || ownership_lost.termination_sent ||
        !already_reaped(ownership_lost.pid) || open_descriptors() != initial_descriptors) {
        std::cerr << "Lost wait ownership must fail without signaling a potentially reused PID\n";
        return 1;
    }
    close(sentinel);
    unsetenv("MACMST_MOCK_ENV_SENTINEL");
    if (!already_reaped(-1)) {
        std::cerr << "No owned child may remain after the mock suite\n";
        return 1;
    }
    std::cout << "PASS: protocol validation, fresh processes, spawn/input failures, signal/environment/FD isolation, lost wait ownership and no owned zombies\n";
    return 0;
}