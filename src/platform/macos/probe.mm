#import <Foundation/Foundation.h>

#include "probe/report.hpp"
#include "platform/macos/registry.hpp"

#include <CoreGraphics/CoreGraphics.h>
#include <IOKit/IOKitLib.h>
#include <dlfcn.h>
#include <sys/sysctl.h>
#include <sys/utsname.h>

#include <array>
#include <cerrno>
#include <cmath>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace macmst::macos {

NSDictionary* select_registry_properties(NSDictionary* properties) {
    NSArray* allowed = @[
        @"Location", @"Unit", @"role", @"BootComplete", @"DCPPowerState",
        @"IODPDeviceUserInterfaceSupported", @"IODPServiceUserInterfaceSupported",
        @"IODPControllerUserInterfaceSupported", @"IOAVDeviceUserInterfaceSupported",
        @"IOAVServiceUserInterfaceSupported", @"IOProviderClass", @"Active",
        @"HPD_State", @"HPD_StateDescription", @"Index", @"LaneCount", @"LinkRate",
        @"LinkRateDescription", @"MaxLaneCount", @"ParentBuiltInPortNumber",
        @"ParentBuiltInPortType", @"ParentBuiltInPortTypeDescription",
        @"ParentPortBuiltIn", @"ParentPortNumber", @"ParentPortType",
        @"ParentPortTypeDescription", @"Role", @"RoleDescription", @"SinkCount",
        @"TransportDescription", @"TransportType", @"TransportTypeDescription",
        @"Tunneled", @"idVendor", @"idProduct", @"bcdUSB", @"bDeviceClass",
        @"bDeviceSubClass", @"bDeviceProtocol", @"USB Product Name", @"USB Vendor Name",
        @"locationID", @"USBSpeed", @"PortNum", @"DisplayVendorID", @"DisplayProductID",
        @"IOI2CTransactionTypes", @"IOI2CBusType", @"IOI2CBusID"
    ];
    NSMutableDictionary* selected = [NSMutableDictionary dictionary];
    for (NSString* key in allowed) {
        id value = properties[key];
        if ([value isKindOfClass:[NSNumber class]] || [value isKindOfClass:[NSString class]]) {
            selected[key] = value;
        }
    }
    return selected;
}

namespace {

class IoObject {
public:
    explicit IoObject(io_object_t value) : value_(value) {}
    ~IoObject() {
        if (value_ != IO_OBJECT_NULL) {
            IOObjectRelease(value_);
        }
    }
    IoObject(const IoObject&) = delete;
    IoObject& operator=(const IoObject&) = delete;
    io_object_t get() const { return value_; }

private:
    io_object_t value_;
};

void add_error(NSMutableArray* errors, NSString* operation, long long code) {
    [errors addObject:@{@"operation": operation, @"code_raw": @(code)}];
}

NSString* readable_string(const char* value) {
    NSString* decoded = [NSString stringWithUTF8String:value];
    return decoded == nil || decoded.length == 0 ? @"UNKNOWN" : decoded;
}

NSDictionary* related_entry_identity(io_registry_entry_t entry, bool redact_names,
                                    NSMutableArray* errors) {
    io_name_t name {};
    io_name_t class_name {};
    uint64_t identifier = 0;
    const auto name_status = IORegistryEntryGetName(entry, name);
    const auto class_status = IOObjectGetClass(entry, class_name);
    const auto id_status = IORegistryEntryGetRegistryEntryID(entry, &identifier);
    if (name_status != KERN_SUCCESS || class_status != KERN_SUCCESS || id_status != KERN_SUCCESS) {
        add_error(errors, @"IORegistry related-entry identity", kIOReturnError);
    }
    return @{@"name": redact_names ? @"[USB-related name omitted]" : readable_string(name),
             @"class": readable_string(class_name),
             @"entry_id_raw": id_status == KERN_SUCCESS ? @(identifier) : [NSNull null]};
}

NSDictionary* entry_relationships(io_registry_entry_t entry, bool redact_names,
                                 NSMutableArray* errors) {
    io_registry_entry_t parent_raw = IO_OBJECT_NULL;
    const auto parent_status = IORegistryEntryGetParentEntry(entry, kIOServicePlane, &parent_raw);
    IoObject parent(parent_raw);
    id parent_info = [NSNull null];
    if (parent_status == KERN_SUCCESS && parent.get() != IO_OBJECT_NULL) {
        parent_info = related_entry_identity(parent.get(), redact_names, errors);
    } else {
        add_error(errors, @"IORegistryEntryGetParentEntry", parent_status);
    }
    io_iterator_t children_raw = IO_OBJECT_NULL;
    const auto children_status = IORegistryEntryGetChildIterator(entry, kIOServicePlane, &children_raw);
    IoObject children_iterator(children_raw);
    NSMutableArray* children = [NSMutableArray array];
    if (children_status != KERN_SUCCESS) {
        add_error(errors, @"IORegistryEntryGetChildIterator", children_status);
    } else if (children_iterator.get() != IO_OBJECT_NULL) {
        for (io_registry_entry_t child_raw = IOIteratorNext(children_iterator.get()); child_raw != IO_OBJECT_NULL;
             child_raw = IOIteratorNext(children_iterator.get())) {
            IoObject child(child_raw);
            [children addObject:related_entry_identity(child.get(), redact_names, errors)];
        }
        if (!IOIteratorIsValid(children_iterator.get())) {
            add_error(errors, @"IORegistry child iterator invalidated", kIOReturnNotReady);
        }
    }
    return @{@"parent": parent_info, @"parent_status_code_raw": @(parent_status),
             @"children": children, @"children_status_code_raw": @(children_status)};
}

NSString* sysctl_string(const char* key, NSMutableArray* errors) {
    std::size_t size = 0;
    if (sysctlbyname(key, nullptr, &size, nullptr, 0) != 0) {
        add_error(errors, [NSString stringWithUTF8String:key], errno);
        return @"UNKNOWN";
    }
    if (size == 0 || size > 4096) {
        add_error(errors, [NSString stringWithUTF8String:key], EOVERFLOW);
        return @"UNKNOWN";
    }
    std::vector<char> buffer(size + 1, '\0');
    if (sysctlbyname(key, buffer.data(), &size, nullptr, 0) != 0) {
        add_error(errors, [NSString stringWithUTF8String:key], errno);
        return @"UNKNOWN";
    }
    NSString* value = [NSString stringWithUTF8String:buffer.data()];
    if (value == nil) {
        add_error(errors, [NSString stringWithUTF8String:key], EILSEQ);
        return @"UNKNOWN";
    }
    return value;
}

NSDictionary* collect_host(NSMutableArray* errors) {
    struct utsname information {};
    NSString* architecture = @"UNKNOWN";
    if (uname(&information) == 0) {
        architecture = [NSString stringWithUTF8String:information.machine];
    } else {
        add_error(errors, @"uname", errno);
    }
    return @{
        @"soc": sysctl_string("machdep.cpu.brand_string", errors),
        @"architecture": architecture,
        @"model": sysctl_string("hw.model", errors),
        @"macos_version": sysctl_string("kern.osproductversion", errors),
        @"macos_build": sysctl_string("kern.osversion", errors),
        @"source": @"sysctlbyname; uname"
    };
}

NSArray* collect_displays(NSMutableArray* errors, bool& available) {
    available = false;
    std::array<CGDirectDisplayID, 256> identifiers {};
    uint32_t count = 0;
    const auto status = CGGetOnlineDisplayList(static_cast<uint32_t>(identifiers.size()),
                                             identifiers.data(), &count);
    if (status != kCGErrorSuccess || count >= identifiers.size()) {
        add_error(errors, @"CGGetOnlineDisplayList", status == kCGErrorSuccess ? EOVERFLOW : status);
        return @[];
    }
    available = true;
    NSMutableArray* displays = [NSMutableArray array];
    for (uint32_t index = 0; index < count; ++index) {
        const auto identifier = identifiers[index];
        const auto mirror = CGDisplayMirrorsDisplay(identifier);
        NSMutableDictionary* display = [@{
            @"display_id_raw": @(identifier),
            @"vendor_id_raw": @(CGDisplayVendorNumber(identifier)),
            @"product_id_raw": @(CGDisplayModelNumber(identifier)),
            @"built_in": @(CGDisplayIsBuiltin(identifier) != 0),
            @"active": @(CGDisplayIsActive(identifier) != 0),
            @"main": @(CGDisplayIsMain(identifier) != 0),
            @"in_mirror_set": @(CGDisplayIsInMirrorSet(identifier) != 0),
            @"mirrors_display_id_raw": mirror == kCGNullDirectDisplay ? [NSNull null] : @(mirror),
            @"source": @"CGGetOnlineDisplayList; CGDisplay queries"
        } mutableCopy];
        CGDisplayModeRef mode = CGDisplayCopyDisplayMode(identifier);
        if (mode != nullptr) {
            display[@"mode_width"] = @(CGDisplayModeGetWidth(mode));
            display[@"mode_height"] = @(CGDisplayModeGetHeight(mode));
            display[@"pixel_width"] = @(CGDisplayModeGetPixelWidth(mode));
            display[@"pixel_height"] = @(CGDisplayModeGetPixelHeight(mode));
            const double rate = CGDisplayModeGetRefreshRate(mode);
            display[@"refresh_hz"] = std::isfinite(rate) && rate > 0 ? @(rate) : [NSNull null];
            CGDisplayModeRelease(mode);
        } else {
            add_error(errors, @"CGDisplayCopyDisplayMode", identifier);
        }
        [displays addObject:display];
    }
    return displays;
}

NSDictionary* collect_registry(NSMutableArray* errors) {
    NSArray* classes = @[@"AppleDCPExpert", @"DCPAVControllerProxy", @"DCPAVDeviceProxy", @"DCPAVServiceProxy",
                         @"DCPDPControllerProxy", @"DCPDPDeviceProxy", @"DCPDPServiceProxy",
                         @"AppleDCPDPTXRemotePortProxy", @"AppleDCPDPTXRemotePortUFP",
                         @"IOMobileFramebufferShim", @"IOFramebuffer", @"IOI2CInterface",
                         @"IOPortTransportStateDisplayPort", @"IOUSBHostDevice", @"IOAVService"];
    NSMutableDictionary* inventory = [NSMutableDictionary dictionary];
    for (NSString* requested_class in classes) {
        io_iterator_t iterator_raw = IO_OBJECT_NULL;
        CFMutableDictionaryRef matching = IOServiceMatching(requested_class.UTF8String);
        const kern_return_t status = matching == nullptr ? kIOReturnNoMemory :
            IOServiceGetMatchingServices(kIOMainPortDefault, matching, &iterator_raw);
        IoObject iterator(iterator_raw);
        NSMutableArray* entries = [NSMutableArray array];
        inventory[requested_class] = @{@"query_status_code_raw": @(status), @"entries": entries};
        if (status != KERN_SUCCESS) {
            add_error(errors, [@"IOServiceGetMatchingServices:" stringByAppendingString:requested_class], status);
            continue;
        }
        for (io_registry_entry_t entry_raw = IOIteratorNext(iterator.get()); entry_raw != IO_OBJECT_NULL;
             entry_raw = IOIteratorNext(iterator.get())) {
            IoObject entry(entry_raw);
            uint64_t entry_id = 0;
            io_name_t name {};
            io_name_t actual_class {};
            io_string_t path {};
            const auto id_status = IORegistryEntryGetRegistryEntryID(entry.get(), &entry_id);
            const auto name_status = IORegistryEntryGetName(entry.get(), name);
            const auto class_status = IOObjectGetClass(entry.get(), actual_class);
            const auto path_status = IORegistryEntryGetPath(entry.get(), kIOServicePlane, path);
            const bool usb = [requested_class isEqualToString:@"IOUSBHostDevice"];
            CFMutableDictionaryRef properties_raw = nullptr;
            const auto property_status = IORegistryEntryCreateCFProperties(entry.get(), &properties_raw,
                                                                           kCFAllocatorDefault, 0);
            NSDictionary* properties = CFBridgingRelease(properties_raw);
            if (property_status != KERN_SUCCESS) {
                add_error(errors, [@"IORegistryEntryCreateCFProperties:" stringByAppendingString:requested_class], property_status);
            }
            if (id_status != KERN_SUCCESS || name_status != KERN_SUCCESS ||
                class_status != KERN_SUCCESS || path_status != KERN_SUCCESS) {
                add_error(errors, @"IORegistryEntry identity/path read", kIOReturnError);
            }
            [entries addObject:@{
                @"entry_id_raw": id_status == KERN_SUCCESS ? @(entry_id) : [NSNull null],
                @"name": usb ? @"[USB registry name omitted]" :
                         readable_string(name),
                @"class": readable_string(actual_class),
                @"path": usb ? @"[USB registry path omitted]" :
                         readable_string(path),
                @"property_status_code_raw": @(property_status),
                @"properties": select_registry_properties(properties),
                @"relationships": entry_relationships(entry.get(), usb, errors)
            }];
        }
        if (iterator.get() != IO_OBJECT_NULL && !IOIteratorIsValid(iterator.get())) {
            add_error(errors, [@"IOIterator invalidated:" stringByAppendingString:requested_class], kIOReturnNotReady);
        }
    }
    return inventory;
}

NSDictionary* inspect_symbols() {
    NSMutableDictionary* symbols = [NSMutableDictionary dictionary];
    for (NSString* symbol in @[@"IOAVServiceCreateWithService", @"IOAVServiceReadI2C",
                               @"IOAVServiceWriteI2C", @"IOAVServiceCopyEDID",
                               @"IOAVServiceCopyProperties", @"IOAVServiceGetLinkData",
                               @"IODPDeviceCreate", @"IODPDeviceCreateWithLocation",
                               @"IODPDeviceCreateWithService", @"IODPDeviceReadDPCD",
                               @"IODPDeviceWriteDPCD", @"IODPDeviceGetTypeID",
                               @"IODPDeviceGetAVDevice", @"IODPDeviceGetController",
                               @"IODPServiceCreate", @"IODPServiceCreateWithLocation",
                               @"IODPServiceCreateWithService", @"IODPServiceGetDevice",
                               @"IODPControllerCreateWithService"]) {
        symbols[symbol] = dlsym(RTLD_DEFAULT, symbol.UTF8String) != nullptr ?
                         @"PRESENT_NOT_INVOKED" : @"NOT_FOUND";
    }
    return symbols;
}

std::string text_value(id value) {
    if (value == nil || value == [NSNull null]) {
        return "UNKNOWN";
    }
    return std::string([[value description] UTF8String]);
}

std::string query_count(NSDictionary* registry, NSString* class_name) {
    NSDictionary* query = registry[class_name];
    if (query == nil || [query[@"query_status_code_raw"] longLongValue] != KERN_SUCCESS) {
        return "UNKNOWN";
    }
    NSArray* entries = query[@"entries"];
    return std::to_string(entries.count);
}

NSArray* successful_entries(NSDictionary* registry, NSString* class_name) {
    NSDictionary* query = registry[class_name];
    id status = query[@"query_status_code_raw"];
    if (![status isKindOfClass:[NSNumber class]] || [status longLongValue] != KERN_SUCCESS ||
        ![query[@"entries"] isKindOfClass:[NSArray class]]) {
        return @[];
    }
    return query[@"entries"];
}

NSString* processor_context(NSDictionary* entry) {
    id path = entry[@"path"];
    id unit = entry[@"properties"][@"Unit"];
    id status = entry[@"property_status_code_raw"];
    if (![entry[@"properties"][@"Location"] isEqual:@"External"] ||
        ![path isKindOfClass:[NSString class]] || ![path hasPrefix:@"IOService:/"] ||
        ![unit isKindOfClass:[NSNumber class]] || [unit longLongValue] < 0 ||
        [unit doubleValue] != static_cast<double>([unit unsignedIntValue]) ||
        CFGetTypeID((__bridge CFTypeRef)unit) == CFBooleanGetTypeID() ||
        ![status isKindOfClass:[NSNumber class]] || [status longLongValue] != KERN_SUCCESS) {
        return nil;
    }
    const NSRange start = [path rangeOfString:@"/RTBuddy("];
    if (start.location == NSNotFound) {
        return nil;
    }
    const NSRange end = [path rangeOfString:@")/" options:0
                         range:NSMakeRange(start.location, [path length] - start.location)];
    return end.location == NSNotFound ? nil : [path substringToIndex:end.location + 1];
}

NSArray* matching_context(NSArray* entries, NSString* context, NSNumber* unit) {
    NSMutableArray* matches = [NSMutableArray array];
    for (NSDictionary* entry in entries) {
        if ([processor_context(entry) isEqualToString:context] &&
            [entry[@"properties"][@"Unit"] isEqualToNumber:unit]) {
            [matches addObject:entry];
        }
    }
    return matches;
}

std::string render_text(NSDictionary* report) {
    NSDictionary* host = report[@"host"];
    NSDictionary* registry = report[@"registry"];
    std::ostringstream output;
    output << "# MacMST Probe\n\nHost\n"
           << "  SoC: " << text_value(host[@"soc"]) << '\n'
           << "  Architecture: " << text_value(host[@"architecture"]) << '\n'
           << "  Model: " << text_value(host[@"model"]) << '\n'
           << "  macOS: " << text_value(host[@"macos_version"])
            << " (" << text_value(host[@"macos_build"]) << ")\n\nDisplay Controllers\n"
            << "  AppleDCPExpert registry instances: " << query_count(registry, @"AppleDCPExpert") << '\n';
        for (NSDictionary* entry in registry[@"AppleDCPExpert"][@"entries"]) {
         output << "    " << text_value(entry[@"path"]) << '\n';
        }
        output << "\nConnection\n  Active USB-C to DCP route: see inferred candidates below\n"
            << "  USB4/Thunderbolt involvement: UNKNOWN\n";
        for (NSDictionary* entry in registry[@"IOPortTransportStateDisplayPort"][@"entries"]) {
         NSDictionary* properties = entry[@"properties"];
         output << "  Published port: " << text_value(properties[@"ParentPortTypeDescription"])
             << " #" << text_value(properties[@"ParentPortNumber"])
             << "; active=" << text_value(properties[@"Active"])
             << "; tunneled=" << text_value(properties[@"Tunneled"]) << '\n'
             << "    LaneCount=" << text_value(properties[@"LaneCount"])
             << "; LinkRate(raw)=" << text_value(properties[@"LinkRate"])
             << "; description=" << text_value(properties[@"LinkRateDescription"])
             << "; SinkCount(raw)=" << text_value(properties[@"SinkCount"]) << '\n';
        }
        output << "\nDock\n  Manufacturer/product: UNKNOWN (not identified)\n"
            << "  VID/PID: UNKNOWN (no verified dock association)\n"
            << "  USB speed: UNKNOWN\n  MST capability: UNKNOWN\n"
            << "  USB device candidates: " << query_count(registry, @"IOUSBHostDevice") << '\n';
        for (NSDictionary* entry in registry[@"IOUSBHostDevice"][@"entries"]) {
         NSDictionary* properties = entry[@"properties"];
         output << "    " << text_value(properties[@"USB Vendor Name"]) << ' '
             << text_value(properties[@"USB Product Name"])
             << "; VID(raw)=" << text_value(properties[@"idVendor"])
             << "; PID(raw)=" << text_value(properties[@"idProduct"])
             << "; USBSpeed(raw)=" << text_value(properties[@"USBSpeed"]) << '\n';
        }
        output << "\nmacOS Displays\n";
    std::size_t internal = 0;
    std::size_t external = 0;
    for (NSDictionary* display in report[@"displays"]) {
        const bool built_in = [display[@"built_in"] boolValue];
        built_in ? ++internal : ++external;
        output << "  " << (built_in ? "Internal" : "External") << " logical display "
               << text_value(display[@"display_id_raw"]) << ": "
               << text_value(display[@"pixel_width"]) << 'x' << text_value(display[@"pixel_height"])
               << " pixels; in mirror set=" << text_value(display[@"in_mirror_set"]) << '\n';
    }
        const bool display_enumeration_ok = [report[@"display_enumeration_ok"] boolValue];
        output << "  Internal logical displays: " << (display_enumeration_ok ? std::to_string(internal) : "UNKNOWN") << '\n'
            << "  External logical displays: " << (display_enumeration_ok ? std::to_string(external) : "UNKNOWN") << '\n'
            << "  Physical downstream displays observed: UNKNOWN\n\nApple Display Services\n";
        for (NSString* class_name in @[@"DCPAVServiceProxy", @"AppleDCPDPTXRemotePortProxy",
                                       @"DCPDPControllerProxy", @"DCPDPDeviceProxy", @"DCPDPServiceProxy",
                        @"AppleDCPDPTXRemotePortUFP", @"IOFramebuffer",
                        @"IOI2CInterface", @"IOAVService"]) {
         output << "  " << text_value(class_name) << " registry instances: " << query_count(registry, class_name) << '\n';
        }
         output << "\nExternal DisplayPort Candidates\n";
         NSArray* candidates = report[@"external_dp_candidates"];
         output << "  Count: " << candidates.count << '\n';
         for (NSDictionary* candidate in candidates) {
             output << "  Processor: " << text_value(candidate[@"processor_path"]) << '\n'
                 << "    Device: " << text_value(candidate[@"device_path"]) << '\n'
                 << "    Service: " << text_value(candidate[@"service_path"]) << '\n'
                 << "    Location: External; Unit: " << text_value(candidate[@"unit_raw"]) << '\n'
                 << "    Pairing: " << text_value(candidate[@"pairing"]) << '\n'
                 << "    Activity: " << text_value(candidate[@"activity_assessment"]) << '\n'
                 << "    Dock association: requires controlled capture comparison\n";
         }
         output << "\nPrivate API Availability\n";
         for (NSString* symbol in @[@"IODPDeviceCreate", @"IODPDeviceCreateWithService",
                        @"IODPDeviceReadDPCD", @"IODPDeviceWriteDPCD"]) {
             output << "  " << text_value(symbol) << ": " << text_value(report[@"symbol_visibility"][symbol]) << '\n';
         }
         output << "\nDPCD Transport\n  Read capability: UNVERIFIED\n  Private object acquired: no\n\n"
             << "  IOAVServiceReadI2C symbol: " << text_value(report[@"symbol_visibility"][@"IOAVServiceReadI2C"])
                << " (not a transport test)\n  IODPDeviceReadDPCD symbol: "
                << text_value(report[@"symbol_visibility"][@"IODPDeviceReadDPCD"])
                << " (ABI and service binding unverified)\n\nCapabilities\n  I2C-over-AUX: UNKNOWN (not tested)\n"
           << "  Native AUX: UNKNOWN (no transport implemented)\n"
           << "  DPCD access: UNKNOWN\n  MST branch visible: UNKNOWN\n\n"
           << "Research Status\n  Native MST source support: UNKNOWN\n";
    NSArray* errors = report[@"errors"];
    output << "  Observation errors: " << errors.count << '\n';
    for (NSDictionary* error in errors) {
        output << "    " << text_value(error[@"operation"]) << ": " << text_value(error[@"code_raw"]) << '\n';
    }
    return output.str();
}

}

NSArray* external_dp_candidates(NSDictionary* registry, NSUInteger external_display_count,
                               bool observation_complete) {
    NSArray* devices = successful_entries(registry, @"DCPDPDeviceProxy");
    NSArray* services = successful_entries(registry, @"DCPDPServiceProxy");
    NSArray* av_services = successful_entries(registry, @"DCPAVServiceProxy");
    NSMutableArray* active_ports = [NSMutableArray array];
    for (NSDictionary* port in successful_entries(registry, @"IOPortTransportStateDisplayPort")) {
        NSDictionary* properties = port[@"properties"];
        if ([properties[@"Active"] isEqual:@YES] &&
            ([properties[@"ParentPortTypeDescription"] isEqual:@"USB-C"] ||
             [properties[@"ParentPortTypeDescription"] isEqual:@"HDMI"]) &&
            [port[@"property_status_code_raw"] isEqual:@0]) {
            [active_ports addObject:port];
        }
    }
    NSMutableArray* candidates = [NSMutableArray array];
    for (NSDictionary* device in devices) {
        NSString* context = processor_context(device);
        if (context == nil) {
            continue;
        }
        NSNumber* unit = device[@"properties"][@"Unit"];
        NSArray* peers = matching_context(devices, context, unit);
        NSArray* matching_services = matching_context(services, context, unit);
        NSArray* matching_av = matching_context(av_services, context, unit);
        const bool unique = peers.count == 1 && matching_services.count == 1;
        NSString* pairing = unique ? @"INFERRED_SHARED_PROCESSOR_AND_UNIT" :
                            matching_services.count == 0 ? @"MISSING_SERVICE" : @"AMBIGUOUS";
        [candidates addObject:[@{
            @"processor_path": context, @"location": @"External", @"unit_raw": unit,
            @"device_entry_id_raw": device[@"entry_id_raw"], @"device_path": device[@"path"],
            @"device_interface_supported_raw": device[@"properties"][@"IODPDeviceUserInterfaceSupported"] == nil ?
                                               [NSNull null] : device[@"properties"][@"IODPDeviceUserInterfaceSupported"],
            @"matching_service_count": @(matching_services.count),
            @"service_entry_id_raw": unique ? matching_services[0][@"entry_id_raw"] : [NSNull null],
            @"service_path": unique ? matching_services[0][@"path"] : [NSNull null],
            @"av_service_path": matching_av.count == 1 ? matching_av[0][@"path"] : [NSNull null],
            @"pairing": pairing, @"evidence_class": @"INFERRED",
            @"activity_assessment": @"UNVERIFIED", @"private_object_acquired": @NO,
            @"safe_to_invoke_private_api": @NO,
            @"dock_association": @"REQUIRES_CONTROLLED_CAPTURE_COMPARISON",
            @"active_transport_paths": [active_ports valueForKey:@"path"]
        } mutableCopy]];
    }
    if (observation_complete && candidates.count == 1 && external_display_count == 1 && active_ports.count == 1) {
        NSMutableDictionary* candidate = candidates[0];
        if ([candidate[@"pairing"] isEqual:@"INFERRED_SHARED_PROCESSOR_AND_UNIT"]) {
            candidate[@"activity_assessment"] = @"INFERRED_SINGLE_ACTIVE_EXTERNAL_CONTEXT";
        }
    }
    return candidates;
}

ProbeOutput collect_probe() {
    @autoreleasepool {
        NSMutableArray* errors = [NSMutableArray array];
        NSISO8601DateFormatter* formatter = [[NSISO8601DateFormatter alloc] init];
        NSString* started = [formatter stringFromDate:[NSDate date]];
        NSDictionary* host = collect_host(errors);
        bool display_enumeration_ok = false;
        NSArray* displays = collect_displays(errors, display_enumeration_ok);
        NSDictionary* registry = collect_registry(errors);
        NSUInteger external_display_count = 0;
        for (NSDictionary* display in displays) {
            if (![display[@"built_in"] boolValue]) {
                ++external_display_count;
            }
        }
        NSArray* candidates = external_dp_candidates(registry, external_display_count,
                                                     display_enumeration_ok && errors.count == 0);
        NSDictionary* report = @{
            @"schema_version": @1,
            @"started_utc": started,
            @"completed_utc": [formatter stringFromDate:[NSDate date]],
            @"host": host,
            @"displays": displays,
            @"display_enumeration_ok": @(display_enumeration_ok),
            @"registry": registry,
            @"external_dp_candidates": candidates,
            @"dpcd_transport": @{@"read_capability": @"UNVERIFIED", @"private_object_acquired": @NO},
            @"registry_source": @"IOServiceGetMatchingServices; IORegistryEntryCreateCFProperties; allowlisted properties only",
            @"symbol_visibility": inspect_symbols(),
            @"symbol_visibility_source": @"dlsym(RTLD_DEFAULT); no private function invoked; addresses omitted",
            @"dock_identification": @"UNKNOWN",
            @"active_usb_c_display_path": @"UNKNOWN",
            @"usb4_thunderbolt_involvement": @"UNKNOWN",
            @"physical_downstream_displays": [NSNull null],
            @"capabilities": @{@"i2c_over_aux": @"UNKNOWN", @"native_aux": @"UNKNOWN",
                               @"dpcd_access": @"UNKNOWN", @"mst_branch_visible": @"UNKNOWN",
                               @"native_mst_source_support": @"UNKNOWN"},
            @"privacy": @"No serial numbers, UUIDs, EDID, or credentials collected.",
            @"snapshot_atomic": @NO,
            @"errors": errors
        };
        NSError* serialization_error = nil;
        NSData* json = [NSJSONSerialization dataWithJSONObject:report
                       options:NSJSONWritingPrettyPrinted | NSJSONWritingSortedKeys
                       error:&serialization_error];
        if (json == nil) {
            throw std::runtime_error("JSON serialization failed");
        }
        return {render_text(report),
                std::string(static_cast<const char*>(json.bytes), json.length) + "\n",
                errors.count == 0};
    }
}

}