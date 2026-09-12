#include "isolation/mock_helper.hpp"

#include <bit>
#include <cerrno>
#include <charconv>
#include <cstring>
#include <fcntl.h>
#include <iostream>
#include <string_view>
#include <sys/wait.h>
#include <unistd.h>

namespace {

const char* outcome_name(macmst::isolation::MockOutcome outcome) {
    using macmst::isolation::MockOutcome;
    switch (outcome) {
    case MockOutcome::Success: return "success";
    case MockOutcome::OperationFailure: return "operation_failure";
    case MockOutcome::InvalidInput: return "invalid_input";
    case MockOutcome::SpawnFailure: return "spawn_failure";
    case MockOutcome::ProtocolFailure: return "protocol_failure";
    case MockOutcome::OutputLimit: return "output_limit";
    case MockOutcome::AbnormalExit: return "abnormal_exit";
    case MockOutcome::Timeout: return "timeout";
    case MockOutcome::ReapFailure: return "reap_failure";
    case MockOutcome::ReapTimeout: return "reap_timeout";
    case MockOutcome::IoFailure: return "io_failure";
    }
    return "unknown";
}

const char* phase_name(macmst::isolation::DpdvPhase phase) {
    using macmst::isolation::DpdvPhase;
    switch (phase) {
    case DpdvPhase::PrecheckFailed: return "PRECHECK_FAILED";
    case DpdvPhase::DryRunReady: return "DRY_RUN_READY";
    case DpdvPhase::OpenAttempted: return "OPEN_ATTEMPTED";
    case DpdvPhase::OpenFailed: return "OPEN_FAILED";
    case DpdvPhase::CloseSucceeded: return "CLOSE_SUCCEEDED";
    case DpdvPhase::CloseFailed: return "CLOSE_FAILED";
    case DpdvPhase::InternalError: return "INTERNAL_ERROR";
    }
    return "UNKNOWN";
}

bool parse_id(const char* text, std::uint64_t& result) {
    const auto end = text + std::strlen(text);
    const auto parsed = std::from_chars(text, end, result);
    return parsed.ec == std::errc() && parsed.ptr == end && result != 0;
}

bool reserve_attempt(const char* path) {
    if (path[0] != '/') {
        errno = EINVAL;
        return false;
    }
    const int descriptor = open(path, O_CREAT | O_EXCL | O_WRONLY | O_CLOEXEC | O_NOFOLLOW, 0600);
    if (descriptor < 0) {
        return false;
    }
    constexpr std::string_view text = "M2F one-shot attempt reserved; never remove or reuse this marker.\n";
    const bool written = write(descriptor, text.data(), text.size()) == static_cast<ssize_t>(text.size());
    const bool synced = written && fsync(descriptor) == 0;
    const int error = errno;
    close(descriptor);
    errno = error;
    return synced;
}

void raw_result(std::uint32_t result, bool valid) {
    if (valid) {
        std::cout << std::bit_cast<std::int32_t>(result);
    } else {
        std::cout << "null";
    }
}

}

int main(int argc, char** argv) {
    using namespace macmst::isolation;
    using namespace std::chrono_literals;
    std::array<std::uint64_t, 3> expected {};
    if (argc < 6 || (std::string_view(argv[1]) != "--no-open" && std::string_view(argv[1]) != "--open-once") ||
        !parse_id(argv[3], expected[0]) || !parse_id(argv[4], expected[1]) || !parse_id(argv[5], expected[2])) {
        std::cerr << "Invalid explicit M2F parent arguments\n";
        return 2;
    }
    const bool no_open = std::string_view(argv[1]) == "--no-open";
    if (argc != (no_open ? 6 : 7)) {
        return 2;
    }
    if (!no_open && !reserve_attempt(argv[6])) {
        std::cout << "{\"runner_outcome\":\"attempt_marker_refused\",\"system_error\":" << errno
                  << ",\"spawn_attempts\":0,\"selector_calls\":0}\n";
        return 0;
    }
    const auto result = run_dpdv_helper(argv[2], no_open, expected[0], expected[1], expected[2], 30000ms, 5000ms);
    const std::span<const std::uint8_t> bytes {result.stdout_bytes.data(), result.stdout_size};
    const auto frame = parse_dpdv_response(bytes);
    const auto progress = bytes.size() >= dpdv_frame_size ? parse_dpdv_frame(bytes.first(dpdv_frame_size)) : std::nullopt;
    std::cout << std::boolalpha << "{\"runner_outcome\":\"" << outcome_name(result.outcome)
              << "\",\"pid_raw\":" << result.pid << ",\"spawn_attempts\":" << result.spawn_attempts
              << ",\"reaped\":" << result.reaped << ",\"termination_sent\":" << result.termination_sent
              << ",\"system_error\":" << result.system_error << ",\"termination_error\":" << result.termination_error
              << ",\"parent_elapsed_ms\":" << result.elapsed.count()
              << ",\"stdout_bytes\":" << result.stdout_observed << ",\"stderr_bytes_omitted\":" << result.stderr_observed
              << ",\"selector_calls\":0,\"failure_trigger\":";
    if (result.failure_trigger) { std::cout << '"' << outcome_name(*result.failure_trigger) << '"'; }
    else { std::cout << "null"; }
    std::cout << ",\"wait_status_raw\":";
    if (result.wait_status) { std::cout << *result.wait_status; } else { std::cout << "null"; }
    std::cout << ",\"exit_code\":";
    if (result.wait_status && WIFEXITED(*result.wait_status)) { std::cout << WEXITSTATUS(*result.wait_status); }
    else { std::cout << "null"; }
    std::cout << ",\"signal_raw\":";
    if (result.wait_status && WIFSIGNALED(*result.wait_status)) { std::cout << WTERMSIG(*result.wait_status); }
    else { std::cout << "null"; }
    std::cout << ",\"open_attempt_intent_recorded\":" << (progress && progress->phase == DpdvPhase::OpenAttempted)
              << ",\"frame\":";
    if (frame) {
        std::cout << "{\"phase\":\"" << phase_name(frame->phase) << "\",\"flags\":" << static_cast<unsigned int>(frame->flags)
                  << ",\"precheck_reason\":" << static_cast<std::uint32_t>(frame->reason)
                  << ",\"precheck_return_raw\":" << std::bit_cast<std::int32_t>(frame->precheck_return)
                  << ",\"device_id_raw\":" << frame->device_id << ",\"service_id_raw\":" << frame->service_id
                  << ",\"transport_id_raw\":" << frame->transport_id
                  << ",\"open_attempted\":" << ((frame->flags & open_attempted_flag) != 0)
                  << ",\"open_succeeded\":" << ((frame->flags & open_succeeded_flag) != 0)
                  << ",\"connection_returned\":" << ((frame->flags & connection_flag) != 0)
                  << ",\"close_attempted\":" << ((frame->flags & close_attempted_flag) != 0)
                  << ",\"open_microseconds\":" << frame->open_microseconds
                  << ",\"close_microseconds\":" << frame->close_microseconds << ",\"open_return_raw\":";
        raw_result(frame->open_return, (frame->flags & open_result_flag) != 0);
        std::cout << ",\"close_return_raw\":";
        raw_result(frame->close_return, (frame->flags & close_result_flag) != 0);
        std::cout << '}';
    } else {
        std::cout << "null";
    }
    std::cout << "}\n";
    return 0;
}