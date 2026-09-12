#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace macmst::displayport::dpcd {

inline constexpr std::uint32_t revision_address = 0x000;
inline constexpr std::uint32_t max_link_rate_address = 0x001;
inline constexpr std::uint32_t max_lane_count_address = 0x002;
inline constexpr std::uint32_t mst_capability_address = 0x021;
inline constexpr std::uint8_t mst_capability_mask = 0x01;
inline constexpr std::size_t receiver_block_size = 16;

struct ReceiverCapabilities {
    std::array<std::uint8_t, receiver_block_size> raw_receiver;
    std::optional<std::uint8_t> raw_mst_capability;
    std::uint8_t revision_major;
    std::uint8_t revision_minor;
    std::uint8_t max_link_rate_code;
    std::optional<std::uint32_t> legacy_max_link_rate_mbps_per_lane;
    std::uint8_t max_lane_count_raw;
    std::optional<std::uint8_t> max_lane_count;
    bool enhanced_framing;
    bool training_pattern_3;
    bool downstream_port_present;
    std::uint8_t downstream_port_count;
    bool extended_receiver_capabilities_present;
    std::optional<bool> mst_capable;
};

std::optional<ReceiverCapabilities> decode_receiver_capabilities(
    std::span<const std::uint8_t> bytes_at_address_zero,
    std::optional<std::uint8_t> byte_at_mst_capability_address = std::nullopt);

}