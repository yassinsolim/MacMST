#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace macmst::isolation {

inline constexpr std::size_t dpdv_frame_size = 64;
inline constexpr std::uint8_t open_attempted_flag = 1;
inline constexpr std::uint8_t open_result_flag = 2;
inline constexpr std::uint8_t open_succeeded_flag = 4;
inline constexpr std::uint8_t connection_flag = 8;
inline constexpr std::uint8_t close_attempted_flag = 16;
inline constexpr std::uint8_t close_result_flag = 32;

enum class DpdvPhase : std::uint8_t {
    PrecheckFailed = 1, DryRunReady, OpenAttempted, OpenFailed,
    CloseSucceeded, CloseFailed, InternalError
};

enum class DpdvReason : std::uint32_t {
    None, Arguments, Registry, Property, ClassMismatch, DeviceCount,
    ServiceCount, TransportCount, Topology, Comparison, NullConnection, Internal
};

struct DpdvFrame {
    DpdvPhase phase = DpdvPhase::PrecheckFailed;
    std::uint8_t flags = 0;
    std::uint32_t precheck_return = 0;
    std::uint32_t open_return = 0;
    std::uint32_t close_return = 0;
    DpdvReason reason = DpdvReason::Arguments;
    std::uint64_t device_id = 0;
    std::uint64_t service_id = 0;
    std::uint64_t transport_id = 0;
    std::uint64_t open_microseconds = 0;
    std::uint64_t close_microseconds = 0;
};

inline std::array<std::uint8_t, dpdv_frame_size> dpdv_response(const DpdvFrame& frame) {
    std::array<std::uint8_t, dpdv_frame_size> bytes {'M', '2', 'F', 'O', 1,
        static_cast<std::uint8_t>(frame.phase), frame.flags, 0};
    const auto put = [&](std::size_t offset, std::uint64_t value, std::size_t width) {
        for (std::size_t index = 0; index < width; ++index) {
            bytes[offset + index] = static_cast<std::uint8_t>(value >> (index * 8));
        }
    };
    put(8, frame.precheck_return, 4);
    put(12, frame.open_return, 4);
    put(16, frame.close_return, 4);
    put(20, static_cast<std::uint32_t>(frame.reason), 4);
    put(24, frame.device_id, 8);
    put(32, frame.service_id, 8);
    put(40, frame.transport_id, 8);
    put(48, frame.open_microseconds, 8);
    put(56, frame.close_microseconds, 8);
    return bytes;
}

inline std::optional<DpdvFrame> parse_dpdv_frame(std::span<const std::uint8_t> bytes) {
    if (bytes.size() != dpdv_frame_size || bytes[0] != 'M' || bytes[1] != '2' || bytes[2] != 'F' ||
        bytes[3] != 'O' || bytes[4] != 1 || bytes[7] != 0 || bytes[5] < 1 || bytes[5] > 7 || bytes[6] > 63) {
        return std::nullopt;
    }
    const auto get = [&](std::size_t offset, std::size_t width) {
        std::uint64_t value = 0;
        for (std::size_t index = 0; index < width; ++index) {
            value |= static_cast<std::uint64_t>(bytes[offset + index]) << (index * 8);
        }
        return value;
    };
    DpdvFrame frame {static_cast<DpdvPhase>(bytes[5]), bytes[6],
        static_cast<std::uint32_t>(get(8, 4)), static_cast<std::uint32_t>(get(12, 4)),
        static_cast<std::uint32_t>(get(16, 4)), static_cast<DpdvReason>(get(20, 4)),
        get(24, 8), get(32, 8), get(40, 8), get(48, 8), get(56, 8)};
    if (static_cast<std::uint32_t>(frame.reason) > static_cast<std::uint32_t>(DpdvReason::Internal)) {
        return std::nullopt;
    }
    const bool no_operation = frame.flags == 0 && frame.open_return == 0 && frame.close_return == 0 &&
        frame.open_microseconds == 0 && frame.close_microseconds == 0;
    if (frame.phase == DpdvPhase::PrecheckFailed) {
        return no_operation && frame.reason != DpdvReason::None ? std::optional {frame} : std::nullopt;
    }
    if (frame.phase == DpdvPhase::InternalError) {
        const bool null_connection = frame.reason == DpdvReason::NullConnection && frame.flags == 7 &&
            frame.open_return == 0 && frame.close_return == 0 && frame.close_microseconds == 0;
        return (no_operation && frame.reason == DpdvReason::Internal) || null_connection ? std::optional {frame} : std::nullopt;
    }
    if (frame.reason != DpdvReason::None || frame.precheck_return != 0 ||
        frame.device_id == 0 || frame.service_id == 0 || frame.transport_id == 0) {
        return std::nullopt;
    }
    if (frame.phase == DpdvPhase::DryRunReady) {
        return no_operation ? std::optional {frame} : std::nullopt;
    }
    if (frame.phase == DpdvPhase::OpenAttempted) {
        return frame.flags == 1 && frame.open_return == 0 && frame.close_return == 0 &&
            frame.open_microseconds == 0 && frame.close_microseconds == 0 ? std::optional {frame} : std::nullopt;
    }
    if (frame.phase == DpdvPhase::OpenFailed) {
        return (frame.flags == 3 || frame.flags == 11) && frame.open_return != 0 && frame.close_return == 0 &&
            frame.close_microseconds == 0 ? std::optional {frame} : std::nullopt;
    }
    const bool closed = frame.flags == 63 && frame.open_return == 0;
    return closed && ((frame.phase == DpdvPhase::CloseSucceeded && frame.close_return == 0) ||
        (frame.phase == DpdvPhase::CloseFailed && frame.close_return != 0)) ? std::optional {frame} : std::nullopt;
}

inline std::optional<DpdvFrame> parse_dpdv_response(std::span<const std::uint8_t> bytes) {
    if (bytes.size() == dpdv_frame_size) {
        const auto frame = parse_dpdv_frame(bytes);
        return frame && (frame->phase == DpdvPhase::PrecheckFailed || frame->phase == DpdvPhase::DryRunReady ||
            (frame->phase == DpdvPhase::InternalError && frame->flags == 0)) ? frame : std::nullopt;
    }
    if (bytes.size() != dpdv_frame_size * 2) {
        return std::nullopt;
    }
    const auto started = parse_dpdv_frame(bytes.first(dpdv_frame_size));
    const auto finished = parse_dpdv_frame(bytes.subspan(dpdv_frame_size));
    if (!started || !finished || started->phase != DpdvPhase::OpenAttempted ||
        finished->phase == DpdvPhase::OpenAttempted || (finished->flags & open_attempted_flag) == 0 ||
        started->device_id != finished->device_id || started->service_id != finished->service_id ||
        started->transport_id != finished->transport_id) {
        return std::nullopt;
    }
    return finished;
}

inline bool valid_dpdv_prefix(std::span<const std::uint8_t> bytes) {
    if (bytes.size() > dpdv_frame_size * 2) {
        return false;
    }
    if (bytes.size() < dpdv_frame_size) {
        return true;
    }
    const auto first = parse_dpdv_frame(bytes.first(dpdv_frame_size));
    if (!first || (bytes.size() > dpdv_frame_size && first->phase != DpdvPhase::OpenAttempted)) {
        return false;
    }
    return bytes.size() < dpdv_frame_size * 2 || parse_dpdv_response(bytes).has_value();
}

}