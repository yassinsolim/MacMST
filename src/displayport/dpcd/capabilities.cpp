#include "displayport/dpcd/capabilities.hpp"

#include <algorithm>

namespace macmst::displayport::dpcd {
namespace {

std::optional<std::uint32_t> legacy_rate_mbps(std::uint8_t code) {
    switch (code) {
    case 0x06: return 1620;
    case 0x0a: return 2700;
    case 0x14: return 5400;
    case 0x1e: return 8100;
    default: return std::nullopt;
    }
}

}

RevisionPlausibility classify_revision_byte(std::uint8_t raw_revision) {
    if (raw_revision >= 0x10 && raw_revision <= 0x14) {
        return RevisionPlausibility::PlausibleKnown;
    }
    if (raw_revision == 0x00 || raw_revision == 0xff) {
        return RevisionPlausibility::Implausible;
    }
    return RevisionPlausibility::Unrecognized;
}

std::optional<ReceiverCapabilities> decode_receiver_capabilities(
    std::span<const std::uint8_t> bytes_at_address_zero,
    std::optional<std::uint8_t> byte_at_mst_capability_address) {
    if (bytes_at_address_zero.size() < receiver_block_size) {
        return std::nullopt;
    }
    ReceiverCapabilities decoded {};
    std::copy_n(bytes_at_address_zero.begin(), receiver_block_size, decoded.raw_receiver.begin());
    decoded.raw_mst_capability = byte_at_mst_capability_address;
    decoded.revision_major = static_cast<std::uint8_t>(decoded.raw_receiver[0] >> 4);
    decoded.revision_minor = static_cast<std::uint8_t>(decoded.raw_receiver[0] & 0x0f);
    decoded.max_link_rate_code = decoded.raw_receiver[1];
    decoded.legacy_max_link_rate_mbps_per_lane = legacy_rate_mbps(decoded.max_link_rate_code);
    decoded.max_lane_count_raw = static_cast<std::uint8_t>(decoded.raw_receiver[2] & 0x1f);
    if (decoded.max_lane_count_raw == 1 || decoded.max_lane_count_raw == 2 || decoded.max_lane_count_raw == 4) {
        decoded.max_lane_count = decoded.max_lane_count_raw;
    }
    decoded.enhanced_framing = (decoded.raw_receiver[2] & 0x80) != 0;
    decoded.training_pattern_3 = (decoded.raw_receiver[2] & 0x40) != 0;
    decoded.downstream_port_present = (decoded.raw_receiver[5] & 0x01) != 0;
    decoded.downstream_port_count = static_cast<std::uint8_t>(decoded.raw_receiver[7] & 0x0f);
    decoded.extended_receiver_capabilities_present = (decoded.raw_receiver[14] & 0x80) != 0;
    if (byte_at_mst_capability_address.has_value()) {
        decoded.mst_capable = (*byte_at_mst_capability_address & mst_capability_mask) != 0;
    }
    return decoded;
}

}