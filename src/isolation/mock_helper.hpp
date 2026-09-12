#pragma once

#include <array>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string_view>
#include <sys/types.h>

namespace macmst::isolation {

inline constexpr std::size_t mock_frame_size = 12;
inline constexpr std::array<std::uint8_t, 8> mock_header {'M', '2', 'C', 'M', 1, 1, 0, 0};
inline constexpr std::array<std::string_view, 13> mock_scenarios {
    "success", "failure", "crash", "sigterm", "sigkill", "hang", "malformed",
    "early-exit", "oversized", "cleanup-hang", "closed-pipes", "stderr-flood", "success-bad-exit"
};

inline std::array<std::uint8_t, mock_frame_size> mock_response(std::uint32_t status) {
    std::array<std::uint8_t, mock_frame_size> response {};
    for (std::size_t index = 0; index < mock_header.size(); ++index) {
        response[index] = mock_header[index];
    }
    for (std::size_t index = 0; index < 4; ++index) {
        response[8 + index] = static_cast<std::uint8_t>(status >> (index * 8));
    }
    return response;
}

inline std::optional<std::uint32_t> parse_mock_response(std::span<const std::uint8_t> bytes) {
    if (bytes.size() != mock_frame_size) {
        return std::nullopt;
    }
    for (std::size_t index = 0; index < mock_header.size(); ++index) {
        if (bytes[index] != mock_header[index]) {
            return std::nullopt;
        }
    }
    std::uint32_t status = 0;
    for (std::size_t index = 0; index < 4; ++index) {
        status |= static_cast<std::uint32_t>(bytes[8 + index]) << (index * 8);
    }
    return status;
}

enum class MockOutcome {
    Success,
    OperationFailure,
    InvalidInput,
    SpawnFailure,
    ProtocolFailure,
    OutputLimit,
    AbnormalExit,
    Timeout,
    ReapFailure,
    ReapTimeout,
    IoFailure
};

struct MockResult {
    MockOutcome outcome = MockOutcome::InvalidInput;
    std::optional<MockOutcome> failure_trigger;
    pid_t pid = 0;
    unsigned int spawn_attempts = 0;
    bool reaped = false;
    bool termination_sent = false;
    int system_error = 0;
    int termination_error = 0;
    std::optional<int> wait_status;
    std::optional<std::uint32_t> mock_ior_return;
    std::chrono::milliseconds elapsed {0};
    std::array<std::uint8_t, 64> stdout_bytes {};
    std::array<std::uint8_t, 1024> stderr_bytes {};
    std::size_t stdout_size = 0;
    std::size_t stderr_size = 0;
    std::size_t stdout_observed = 0;
    std::size_t stderr_observed = 0;
};

MockResult run_mock_helper(const char* executable, std::string_view scenario,
    std::chrono::milliseconds deadline, std::chrono::milliseconds reap_grace);

}