#include "isolation/dpdv_protocol.hpp"

#include <CoreFoundation/CoreFoundation.h>
#include <IOKit/IOKitLib.h>
#include <mach/mach.h>

#include <algorithm>
#include <array>
#include <charconv>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <optional>
#include <string>
#include <string_view>
#include <unistd.h>

namespace {

using macmst::isolation::DpdvFrame;
using macmst::isolation::DpdvPhase;
using macmst::isolation::DpdvReason;

class IoReference {
public:
    IoReference() = default;
    explicit IoReference(io_object_t value) : value_(value) {}
    ~IoReference() { reset(); }
    IoReference(const IoReference&) = delete;
    IoReference& operator=(const IoReference&) = delete;
    io_object_t get() const { return value_; }
    io_object_t release() {
        const auto value = value_;
        value_ = IO_OBJECT_NULL;
        return value;
    }
    void reset(io_object_t value = IO_OBJECT_NULL) {
        if (value_ != IO_OBJECT_NULL) {
            IOObjectRelease(value_);
        }
        value_ = value;
    }
private:
    io_object_t value_ = IO_OBJECT_NULL;
};

template <typename Type>
class CfReference {
public:
    explicit CfReference(Type value = nullptr) : value_(value) {}
    ~CfReference() { if (value_ != nullptr) { CFRelease(value_); } }
    CfReference(const CfReference&) = delete;
    CfReference& operator=(const CfReference&) = delete;
    Type get() const { return value_; }
private:
    Type value_;
};

bool fail(DpdvFrame& frame, DpdvReason reason, kern_return_t result = KERN_SUCCESS) {
    frame.phase = DpdvPhase::PrecheckFailed;
    frame.reason = reason;
    frame.precheck_return = static_cast<std::uint32_t>(result);
    return false;
}

bool boolean_property(CFDictionaryRef properties, CFStringRef key, bool expected) {
    const auto value = CFDictionaryGetValue(properties, key);
    return value != nullptr && CFGetTypeID(value) == CFBooleanGetTypeID() &&
        (CFBooleanGetValue(static_cast<CFBooleanRef>(value)) != 0) == expected;
}

bool string_property(CFDictionaryRef properties, CFStringRef key, CFStringRef expected) {
    const auto value = CFDictionaryGetValue(properties, key);
    return value != nullptr && CFGetTypeID(value) == CFStringGetTypeID() && CFEqual(value, expected);
}

std::optional<std::int64_t> number_property(CFDictionaryRef properties, CFStringRef key) {
    const auto value = CFDictionaryGetValue(properties, key);
    std::int64_t number = 0;
    if (value == nullptr || CFGetTypeID(value) != CFNumberGetTypeID() ||
        CFNumberIsFloatType(static_cast<CFNumberRef>(value)) ||
        !CFNumberGetValue(static_cast<CFNumberRef>(value), kCFNumberSInt64Type, &number)) {
        return std::nullopt;
    }
    return number;
}

bool exact_class(io_object_t entry, CFStringRef expected) {
    CfReference<CFStringRef> class_name(IOObjectCopyClass(entry));
    return class_name.get() != nullptr && CFEqual(class_name.get(), expected);
}

bool identity(io_object_t entry, std::uint64_t& entry_id, std::string& path, DpdvFrame& frame) {
    auto result = IORegistryEntryGetRegistryEntryID(entry, &entry_id);
    if (result != KERN_SUCCESS) {
        return fail(frame, DpdvReason::Registry, result);
    }
    std::array<char, 512> buffer {};
    result = IORegistryEntryGetPath(entry, kIOServicePlane, buffer.data());
    if (result != KERN_SUCCESS) {
        return fail(frame, DpdvReason::Registry, result);
    }
    const auto end = std::find(buffer.begin(), buffer.end(), '\0');
    if (end == buffer.end() || entry_id == 0) {
        return fail(frame, DpdvReason::Topology);
    }
    path.assign(buffer.begin(), end);
    return true;
}

bool matching_iterator(const char* class_name, IoReference& iterator, DpdvFrame& frame) {
    auto matching = IOServiceMatching(class_name);
    if (matching == nullptr) {
        return fail(frame, DpdvReason::Internal);
    }
    io_iterator_t raw_iterator = IO_OBJECT_NULL;
    const auto result = IOServiceGetMatchingServices(kIOMainPortDefault, matching, &raw_iterator);
    iterator.reset(raw_iterator);
    return result == KERN_SUCCESS ? true : fail(frame, DpdvReason::Registry, result);
}

bool select_endpoint(const char* class_name, CFStringRef expected_class, CFStringRef support_key,
    IoReference& selected, std::uint64_t& selected_id, std::string& processor,
    DpdvReason count_reason, DpdvFrame& frame) {
    IoReference iterator;
    if (!matching_iterator(class_name, iterator, frame)) {
        return false;
    }
    unsigned int candidates = 0;
    bool exhausted = iterator.get() == IO_OBJECT_NULL;
    for (unsigned int index = 0; !exhausted && index < 256; ++index) {
        IoReference entry(IOIteratorNext(iterator.get()));
        if (entry.get() == IO_OBJECT_NULL) {
            exhausted = true;
            break;
        }
        CFMutableDictionaryRef raw_properties = nullptr;
        const auto result = IORegistryEntryCreateCFProperties(entry.get(), &raw_properties, kCFAllocatorDefault, 0);
        CfReference<CFMutableDictionaryRef> properties(raw_properties);
        if (result != KERN_SUCCESS || properties.get() == nullptr) {
            return fail(frame, DpdvReason::Registry, result);
        }
        const auto location = CFDictionaryGetValue(properties.get(), CFSTR("Location"));
        if (location == nullptr || CFGetTypeID(location) != CFStringGetTypeID()) {
            return fail(frame, DpdvReason::Property);
        }
        if (!CFEqual(location, CFSTR("External"))) {
            continue;
        }
        if (number_property(properties.get(), CFSTR("Unit")) != 0 ||
            !boolean_property(properties.get(), support_key, true)) {
            return fail(frame, DpdvReason::Property);
        }
        if (!exact_class(entry.get(), expected_class)) {
            return fail(frame, DpdvReason::ClassMismatch);
        }
        std::uint64_t entry_id = 0;
        std::string path;
        if (!identity(entry.get(), entry_id, path, frame)) {
            return false;
        }
        constexpr std::string_view component = "/RTBuddy(DCPEXT0)/";
        const auto position = path.find(component);
        if (position == std::string::npos || path.find("/dcpext0@") == std::string::npos) {
            return fail(frame, DpdvReason::Topology);
        }
        ++candidates;
        if (candidates == 1) {
            selected.reset(entry.release());
            selected_id = entry_id;
            processor = path.substr(0, position + component.size() - 1);
        }
    }
    if (!exhausted || (iterator.get() != IO_OBJECT_NULL && !IOIteratorIsValid(iterator.get())) || candidates != 1) {
        return fail(frame, count_reason);
    }
    return true;
}

bool select_transport(IoReference& selected, DpdvFrame& frame) {
    IoReference iterator;
    if (!matching_iterator("IOPortTransportStateDisplayPort", iterator, frame)) {
        return false;
    }
    unsigned int candidates = 0;
    bool exhausted = iterator.get() == IO_OBJECT_NULL;
    for (unsigned int index = 0; !exhausted && index < 256; ++index) {
        IoReference entry(IOIteratorNext(iterator.get()));
        if (entry.get() == IO_OBJECT_NULL) {
            exhausted = true;
            break;
        }
        CFMutableDictionaryRef raw_properties = nullptr;
        const auto result = IORegistryEntryCreateCFProperties(entry.get(), &raw_properties, kCFAllocatorDefault, 0);
        CfReference<CFMutableDictionaryRef> properties(raw_properties);
        if (result != KERN_SUCCESS || properties.get() == nullptr) {
            return fail(frame, DpdvReason::Registry, result);
        }
        if (boolean_property(properties.get(), CFSTR("Active"), false)) {
            continue;
        }
        if (!boolean_property(properties.get(), CFSTR("Active"), true) ||
            number_property(properties.get(), CFSTR("HPD_State")) != 2 ||
            number_property(properties.get(), CFSTR("LaneCount")) != 2 ||
            number_property(properties.get(), CFSTR("LinkRate")) != 4 ||
            number_property(properties.get(), CFSTR("SinkCount")) != 1 ||
            !string_property(properties.get(), CFSTR("LinkRateDescription"), CFSTR("8.1 Gbps (HBR3)")) ||
            !boolean_property(properties.get(), CFSTR("Tunneled"), false) ||
            !exact_class(entry.get(), CFSTR("IOPortTransportStateDisplayPort"))) {
            return fail(frame, DpdvReason::Topology);
        }
        std::string path;
        std::uint64_t entry_id = 0;
        if (!identity(entry.get(), entry_id, path, frame)) {
            return false;
        }
        if (path.find("/Port-USB-C@") == std::string::npos) {
            return fail(frame, DpdvReason::Topology);
        }
        ++candidates;
        if (candidates == 1) {
            selected.reset(entry.release());
            frame.transport_id = entry_id;
        }
    }
    if (!exhausted || (iterator.get() != IO_OBJECT_NULL && !IOIteratorIsValid(iterator.get())) || candidates != 1) {
        return fail(frame, DpdvReason::TransportCount);
    }
    return true;
}

bool emit(const DpdvFrame& frame) {
    const auto bytes = macmst::isolation::dpdv_response(frame);
    return write(STDOUT_FILENO, bytes.data(), bytes.size()) == static_cast<ssize_t>(bytes.size());
}

bool parse_id(const char* text, std::uint64_t& result) {
    const auto end = text + std::strlen(text);
    const auto parsed = std::from_chars(text, end, result);
    return parsed.ec == std::errc() && parsed.ptr == end && result != 0;
}

}

int main(int argc, char** argv) {
    DpdvFrame frame;
    std::array<std::uint64_t, 3> expected {};
    if (argc != 5 || (std::string_view(argv[1]) != "--no-open" && std::string_view(argv[1]) != "--open-once") ||
        !parse_id(argv[2], expected[0]) || !parse_id(argv[3], expected[1]) || !parse_id(argv[4], expected[2])) {
        return emit(frame) ? 0 : 3;
    }
    const bool no_open = std::string_view(argv[1]) == "--no-open";
    {
        IoReference device;
        IoReference service;
        IoReference transport;
        bool ready = false;
        try {
            std::string device_processor;
            std::string service_processor;
            ready = select_endpoint("DCPDPDeviceProxy", CFSTR("DCPDPDeviceProxy"), CFSTR("IODPDeviceUserInterfaceSupported"),
                device, frame.device_id, device_processor, DpdvReason::DeviceCount, frame) &&
                select_endpoint("DCPDPServiceProxy", CFSTR("DCPDPServiceProxy"), CFSTR("IODPServiceUserInterfaceSupported"),
                service, frame.service_id, service_processor, DpdvReason::ServiceCount, frame) && select_transport(transport, frame);
            if (ready && (device_processor != service_processor || frame.device_id != expected[0] ||
                frame.service_id != expected[1] || frame.transport_id != expected[2])) {
                ready = fail(frame, DpdvReason::Comparison);
            }
        } catch (...) {
            frame.phase = DpdvPhase::InternalError;
            frame.reason = DpdvReason::Internal;
        }
        if (ready) {
            frame.reason = DpdvReason::None;
            frame.precheck_return = 0;
            if (no_open) {
                frame.phase = DpdvPhase::DryRunReady;
            } else {
                frame.phase = DpdvPhase::OpenAttempted;
                frame.flags = macmst::isolation::open_attempted_flag;
                if (!emit(frame)) {
                    return 3;
                }
                using Clock = std::chrono::steady_clock;
                io_connect_t connection = IO_OBJECT_NULL;
                const auto started = Clock::now();
                const kern_return_t open_result = IOServiceOpen(device.get(), mach_task_self(), 0x44504456U, &connection);
                const auto opened = Clock::now();
                if (open_result == KERN_SUCCESS && connection != IO_OBJECT_NULL) {
                    const kern_return_t close_result = IOServiceClose(connection);
                    const auto closed = Clock::now();
                    frame.flags = 63;
                    frame.close_return = static_cast<std::uint32_t>(close_result);
                    frame.close_microseconds = static_cast<std::uint64_t>(
                        std::chrono::duration_cast<std::chrono::microseconds>(closed - opened).count());
                    frame.phase = close_result == KERN_SUCCESS ? DpdvPhase::CloseSucceeded : DpdvPhase::CloseFailed;
                } else if (open_result != KERN_SUCCESS) {
                    frame.flags = connection == IO_OBJECT_NULL ? 3 : 11;
                    frame.phase = DpdvPhase::OpenFailed;
                } else {
                    frame.flags = 7;
                    frame.phase = DpdvPhase::InternalError;
                    frame.reason = DpdvReason::NullConnection;
                }
                frame.open_return = static_cast<std::uint32_t>(open_result);
                frame.open_microseconds = static_cast<std::uint64_t>(
                    std::chrono::duration_cast<std::chrono::microseconds>(opened - started).count());
            }
        }
    }
    return emit(frame) ? 0 : 3;
}