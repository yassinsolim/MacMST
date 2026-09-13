#include "displayport/dpcd/capabilities.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <span>
#include <string_view>

namespace {
unsigned failures = 0;
unsigned checks = 0;

void expect(bool condition, std::string_view description) {
    ++checks;
    if (!condition) {
        ++failures;
        std::cerr << "FAIL: " << description << '\n';
    }
}
}

int main() {
    namespace dpcd = macmst::displayport::dpcd;
    expect(dpcd::revision_address == 0x000, "revision byte is fixed at DPCD address zero");
    for (unsigned int value = 0; value <= 0xff; ++value) {
        const auto raw = static_cast<std::uint8_t>(value);
        const auto expected = value >= 0x10 && value <= 0x14 ? dpcd::RevisionPlausibility::PlausibleKnown :
            value == 0x00 || value == 0xff ? dpcd::RevisionPlausibility::Implausible :
            dpcd::RevisionPlausibility::Unrecognized;
        expect(dpcd::classify_revision_byte(raw) == expected, "classify all raw revisions without rejecting unknown encodings");
    }
    constexpr std::uint8_t sentinel = 0xff;
    constexpr std::size_t requested_length = 1;
    std::array<std::uint8_t, 129> supplied_reply {};
    supplied_reply[128] = 0x14;
    for (const std::size_t received_length : std::array<std::size_t, 6> {0, 8, 112, 116, 128, 129}) {
        std::array<std::uint8_t, 129> host_message {};
        std::array<std::uint8_t, 3> guarded_output {0xa5, sentinel, 0x5a};
        const std::size_t outer_output_size = requested_length;
        std::copy_n(supplied_reply.begin(), received_length, host_message.begin());
        std::copy_n(host_message.begin() + 128, requested_length, guarded_output.begin() + 1);
        const auto expected = received_length == host_message.size() ? dpcd::RevisionPlausibility::PlausibleKnown :
            dpcd::RevisionPlausibility::Implausible;
        expect(guarded_output.front() == 0xa5 && guarded_output.back() == 0x5a, "synthetic one-byte copy preserves caller canaries");
        expect(outer_output_size == 1 && host_message[112] == 0, "synthetic host path can retain success and requested output size");
        expect(guarded_output[1] != sentinel, "changed sentinel alone cannot prove a complete firmware reply");
        expect(dpcd::classify_revision_byte(guarded_output[1]) == expected, "synthetic short prefix leaves zero payload despite bounded copy");
    }
    expect(dpcd::classify_revision_byte(0x15) == dpcd::RevisionPlausibility::Unrecognized &&
           dpcd::classify_revision_byte(0x20) == dpcd::RevisionPlausibility::Unrecognized,
           "unrecognized future revision remains evidence to review, not declared invalid transport");
    std::array<std::uint8_t, dpcd::receiver_block_size> bytes {};
    bytes[0] = 0x14;
    bytes[1] = 0x1e;
    bytes[2] = 0xc4;
    bytes[5] = 0x01;
    bytes[7] = 0xf2;
    bytes[14] = 0x80;
    const auto original = bytes;

    for (std::size_t length = 0; length < bytes.size(); ++length) {
        expect(!dpcd::decode_receiver_capabilities(std::span(bytes).first(length)), "reject truncated base block");
    }
    const auto decoded = dpcd::decode_receiver_capabilities(bytes, 0x01);
    expect(decoded.has_value(), "accept complete base block");
    if (!decoded) {
        return 1;
    }
    expect(decoded->raw_receiver == original && bytes == original, "preserve all base bytes without modifying input");
    expect(decoded->revision_major == 1 && decoded->revision_minor == 4, "decode DPCD revision nibbles");
    expect(decoded->max_link_rate_code == 0x1e && decoded->legacy_max_link_rate_mbps_per_lane == 8100, "HBR3 raw and Mbps per lane");
    expect(decoded->max_lane_count == 4 && decoded->enhanced_framing && decoded->training_pattern_3, "lane count and flags independent");
    expect(decoded->downstream_port_present && decoded->downstream_port_count == 2, "downstream fields masked");
    expect(decoded->extended_receiver_capabilities_present, "extended receiver capability flag");
    expect(decoded->raw_mst_capability == 1 && decoded->mst_capable == true, "receiver MST-capable bit");
    expect(!dpcd::decode_receiver_capabilities(bytes)->mst_capable.has_value(), "unread MST byte is unknown, not false");
    expect(dpcd::decode_receiver_capabilities(bytes, 0x02)->mst_capable == false, "single-stream sideband bit is not MST bit");
    expect(dpcd::decode_receiver_capabilities(bytes, 0x80)->raw_mst_capability == 0x80, "preserve reserved MST capability bits");
    expect(dpcd::decode_receiver_capabilities(bytes, 0xff)->mst_capable == true, "mask MST bit without rejecting other flags");
    expect(dpcd::mst_capability_address == 0x21 && dpcd::mst_capability_mask == 1, "MST register address and bit");

    const std::array<std::uint8_t, 4> rates {0x06, 0x0a, 0x14, 0x1e};
    const std::array<std::uint32_t, 4> mbps {1620, 2700, 5400, 8100};
    for (std::size_t index = 0; index < rates.size(); ++index) {
        bytes[1] = rates[index];
        expect(dpcd::decode_receiver_capabilities(bytes)->legacy_max_link_rate_mbps_per_lane == mbps[index], "known legacy link rates");
    }
    for (const std::uint8_t rate : std::array<std::uint8_t, 4>{0, 1, 4, 255}) {
        bytes[1] = rate;
        const auto result = dpcd::decode_receiver_capabilities(bytes);
        expect(result->max_link_rate_code == rate && !result->legacy_max_link_rate_mbps_per_lane,
               "rate-table, UHBR-context, or unknown code is not invented legacy bandwidth");
    }
    for (const std::uint8_t lanes : std::array<std::uint8_t, 3>{1, 2, 4}) {
        bytes[2] = lanes;
        expect(dpcd::decode_receiver_capabilities(bytes)->max_lane_count == lanes, "valid lane counts");
    }
    bytes[2] = 0xff;
    const auto invalid_lanes = dpcd::decode_receiver_capabilities(bytes);
    expect(invalid_lanes->max_lane_count_raw == 31 && !invalid_lanes->max_lane_count, "reserved lane count stays raw and unknown");
    bytes.fill(0);
    const auto zero = dpcd::decode_receiver_capabilities(bytes, 0);
    expect(zero && !zero->max_lane_count && !zero->legacy_max_link_rate_mbps_per_lane && zero->mst_capable == false,
           "all-zero bytes are decoded without pretending a usable receiver");
    std::cout << checks << " checks; " << failures << " failures (synthetic bytes only)\n";
    return failures == 0 ? 0 : 1;
}