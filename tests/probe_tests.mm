#import <Foundation/Foundation.h>

#include "platform/macos/registry.hpp"

extern "C" {
#include <IOKit/i2c/IOI2CInterface.h>
}
#include <cstddef>
#include <iostream>
#include <stdexcept>
#include <type_traits>

static_assert(sizeof(IOI2CRequest) == 124 && alignof(IOI2CRequest) == 4);
static_assert(kIOI2CDisplayPortNativeTransactionType == 4);
static_assert(offsetof(IOI2CRequest, sendTransactionType) == 0);
static_assert(offsetof(IOI2CRequest, replyTransactionType) == 4);
static_assert(offsetof(IOI2CRequest, sendAddress) == 8);
static_assert(offsetof(IOI2CRequest, replyAddress) == 12);
static_assert(offsetof(IOI2CRequest, sendSubAddress) == 16);
static_assert(offsetof(IOI2CRequest, replySubAddress) == 17);
static_assert(offsetof(IOI2CRequest, __reservedA) == 18);
static_assert(offsetof(IOI2CRequest, minReplyDelay) == 20);
static_assert(offsetof(IOI2CRequest, result) == 28);
static_assert(offsetof(IOI2CRequest, commFlags) == 32);
static_assert(offsetof(IOI2CRequest, __padA) == 36);
static_assert(offsetof(IOI2CRequest, sendBytes) == 40);
static_assert(offsetof(IOI2CRequest, __reservedB) == 44);
static_assert(offsetof(IOI2CRequest, __padB) == 52);
static_assert(offsetof(IOI2CRequest, replyBytes) == 56);
static_assert(offsetof(IOI2CRequest, completion) == 60);
static_assert(offsetof(IOI2CRequest, sendBuffer) == 68);
static_assert(offsetof(IOI2CRequest, replyBuffer) == 76);
static_assert(offsetof(IOI2CRequest, __reservedC) == 84);
static_assert(std::is_same_v<decltype(&IOFBGetI2CInterfaceCount), IOReturn (*)(io_service_t, IOItemCount*)>);
static_assert(std::is_same_v<decltype(&IOFBCopyI2CInterfaceForBus), IOReturn (*)(io_service_t, IOOptionBits, io_service_t*)>);
static_assert(std::is_same_v<decltype(&IOI2CInterfaceOpen), IOReturn (*)(io_service_t, IOOptionBits, IOI2CConnectRef*)>);
static_assert(std::is_same_v<decltype(&IOI2CSendRequest), IOReturn (*)(IOI2CConnectRef, IOOptionBits, IOI2CRequest*)>);
static_assert(std::is_same_v<decltype(&IOI2CInterfaceClose), IOReturn (*)(IOI2CConnectRef, IOOptionBits)>);

namespace {
NSDictionary* node(NSString* context, NSString* endpoint, NSString* location, id unit, NSNumber* identifier) {
    return @{@"path": [NSString stringWithFormat:@"IOService:/SoC/%@/RTBuddy(%@)/%@", context, context, endpoint],
             @"entry_id_raw": identifier, @"property_status_code_raw": @0,
             @"properties": @{@"Location": location, @"Unit": unit}};
}

NSDictionary* query(NSArray* entries) {
    return @{@"query_status_code_raw": @0, @"entries": entries};
}
}

int main() {
    @autoreleasepool {
        NSDictionary* input = @{
            @"LinkRate": @30, @"Active": @NO, @"idVendor": @4660, @"idProduct": @22136,
            @"USB Serial Number": @"PRIVATE", @"IOPlatformUUID": @"PRIVATE",
            @"IODisplayEDID": [@"PRIVATE" dataUsingEncoding:NSUTF8StringEncoding],
            @"EventLog": @{@"secret": @"PRIVATE"}, @"UnknownProperty": @"PRIVATE",
            @"Location": @"External", @"LaneCount": @[@4]
        };
        NSDictionary* selected = macmst::macos::select_registry_properties(input);
        NSDictionary* expected = @{@"LinkRate": @30, @"Active": @NO, @"idVendor": @4660,
                                   @"idProduct": @22136, @"Location": @"External"};
        if (![selected isEqualToDictionary:expected]) {
            std::cerr << "Registry allowlist or raw-value preservation failed\n";
            return 1;
        }
        if (macmst::macos::select_registry_properties(nil).count != 0) {
            std::cerr << "Unavailable registry properties must not create observations\n";
            return 1;
        }
        NSError* error = nil;
        NSData* json = [NSJSONSerialization dataWithJSONObject:selected options:0 error:&error];
        if (json == nil || error != nil) {
            std::cerr << "Selected registry values must serialize to JSON\n";
            return 1;
        }
        for (NSNumber* mask in @[@0, @4, @16, @31, @(0x8000000000000010ULL)]) {
            NSDictionary* capabilities = macmst::macos::public_i2c_capabilities(mask);
            const bool native = ([mask unsignedLongLongValue] & 0x10ULL) != 0;
            if (![capabilities[@"transaction_types_raw"] isEqual:mask] ||
                ![capabilities[@"displayport_native"] isEqual:@(native)] ||
                ![capabilities[@"dp_native"] isEqual:native ? @"ADVERTISED" : @"NOT_ADVERTISED"]) {
                std::cerr << "Transaction capability masks must preserve raw bits and use bit 4, not value 4\n";
                return 1;
            }
        }
        NSDictionary* ddc_only = macmst::macos::public_i2c_capabilities(@4);
        NSDictionary* all_types = macmst::macos::public_i2c_capabilities(@31);
        if (![ddc_only[@"ddc_ci_reply"] isEqual:@YES] || ![ddc_only[@"displayport_native"] isEqual:@NO] ||
            ![all_types[@"simple"] isEqual:@YES] || ![all_types[@"combined"] isEqual:@YES] ||
            ![macmst::macos::public_i2c_capabilities(@(0x8000000000000010ULL))[@"unknown_transaction_bits_hex"]
               isEqual:@"0x8000000000000000"]) {
            std::cerr << "Known and unknown transaction bits must be decoded independently\n";
            return 1;
        }
        for (id malformed in @[@YES, @(-1), @16.0, @16.5, @"16", @[], @{}, [NSNull null]]) {
            NSDictionary* capabilities = macmst::macos::public_i2c_capabilities(malformed);
            if (![capabilities[@"property_state"] isEqual:@"INVALID"] ||
                ![capabilities[@"dp_native"] isEqual:@"UNKNOWN"] ||
                capabilities[@"transaction_types_raw"] != [NSNull null]) {
                std::cerr << "Invalid capability properties must not become a supported or unsupported mask\n";
                return 1;
            }
        }
        if (![macmst::macos::public_i2c_capabilities(nil)[@"property_state"] isEqual:@"ABSENT"]) {
            std::cerr << "A missing capability property must remain absent\n";
            return 1;
        }
        NSDictionary* external_display = @{@"display_id_raw": @27, @"built_in": @NO, @"active": @YES};
        NSDictionary* internal_display = @{@"display_id_raw": @1, @"built_in": @YES, @"active": @YES};
        NSDictionary* inactive_display = @{@"display_id_raw": @28, @"built_in": @NO, @"active": @NO};
        NSDictionary* public_registry = @{@"IOFramebuffer": query(@[]), @"IOI2CInterface": query(@[])};
        NSMutableDictionary* public_observation = [@{
            @"target_still_active_external": @YES, @"mapping_completed": @YES,
            @"framebuffer_conforms": @NO, @"count_attempted": @NO,
            @"count_status_code_raw": [NSNull null], @"bus_count_raw": [NSNull null], @"buses": @[]
        } mutableCopy];
        NSUInteger enumeration_calls = 0;
        const auto enumerate = [&](std::uint32_t identifier) -> NSDictionary* {
            if (identifier != 27) {
                throw std::runtime_error("Only the selected external display may be enumerated");
            }
            ++enumeration_calls;
            return public_observation;
        };
        const auto public_report = [&]() {
            return macmst::macos::public_displayport_interfaces(@[internal_display, external_display],
                                                                public_registry, true, enumerate);
        };
        if (![public_report()[@"result"] isEqual:@"PUBLIC_IOFRAMEBUFFER_PATH_UNAVAILABLE"] || enumeration_calls != 1) {
            std::cerr << "Complete empty public inventory and a missing mapped framebuffer must be explicit\n";
            return 1;
        }
        for (NSArray* displays in @[@[internal_display], @[inactive_display], @[external_display, external_display],
                                    @[@{@"display_id_raw": @(-1), @"built_in": @NO, @"active": @YES}]]) {
            NSDictionary* result = macmst::macos::public_displayport_interfaces(displays, public_registry, true, enumerate);
            if (![result[@"result"] isEqual:@"PUBLIC_PATH_UNRESOLVED"] || enumeration_calls != 1) {
                std::cerr << "No built-in, inactive, ambiguous or invalid-display fallback is allowed\n";
                return 1;
            }
        }
        macmst::macos::public_displayport_interfaces(@[external_display], public_registry, false, enumerate);
        if (enumeration_calls != 1) {
            std::cerr << "Incomplete snapshots must not enumerate a display\n";
            return 1;
        }
        NSDictionary* alternate_registry = @{@"IOFramebuffer": query(@[]), @"IOI2CInterface": query(@[@{}])};
        if (![macmst::macos::public_displayport_interfaces(@[external_display], alternate_registry, true, enumerate)[@"result"]
               isEqual:@"PUBLIC_PATH_UNRESOLVED"]) {
            std::cerr << "An unmapped alternate public interface must not be declared absent\n";
            return 1;
        }
        NSDictionary* failed_registry = @{@"IOFramebuffer": query(@[]), @"IOI2CInterface": @{
            @"query_status_code_raw": @(static_cast<IOReturn>(kIOReturnNotReady)), @"entries": @[]}};
        if (![macmst::macos::public_displayport_interfaces(@[external_display], failed_registry, true, enumerate)[@"result"]
               isEqual:@"PUBLIC_PATH_UNRESOLVED"]) {
            std::cerr << "Failed registry queries must not establish absence\n";
            return 1;
        }
        public_observation[@"framebuffer_conforms"] = @YES;
        public_observation[@"count_attempted"] = @YES;
        public_observation[@"count_status_code_raw"] = @0;
        public_observation[@"bus_count_raw"] = @0;
        if (![public_report()[@"i2c_enumeration"] isEqual:@"NO_BUSES"]) {
            std::cerr << "Successful zero count must not be confused with a skipped or failed call\n";
            return 1;
        }
        public_observation[@"bus_count_raw"] = @1;
        for (id mask in @[@4, @16, [NSNull null]]) {
            public_observation[@"buses"] = @[@{@"index_raw": @0, @"copy_status_code_raw": @0,
                @"interface_conforms": @YES, @"capabilities": macmst::macos::public_i2c_capabilities(mask)}];
            NSString* expected_result = [mask isEqual:@4] ? @"PUBLIC_INTERFACE_PRESENT_NO_DP_NATIVE" :
                [mask isEqual:@16] ? @"PUBLIC_DP_NATIVE_CANDIDATE" : @"PUBLIC_PATH_UNRESOLVED";
            NSDictionary* result = public_report();
            if (![result[@"result"] isEqual:expected_result] || ![result[@"dpcd_access"] isEqual:@"UNKNOWN"] ||
                ![result[@"request_attempted"] isEqual:@NO] || ![result[@"interface_open_attempted"] isEqual:@NO]) {
                std::cerr << "Advertisement classification must never become a transaction or DPCD success\n";
                return 1;
            }
        }
                public_observation[@"count_status_code_raw"] = @(static_cast<IOReturn>(kIOReturnNotReady));
        if (![public_report()[@"result"] isEqual:@"PUBLIC_PATH_UNRESOLVED"] ||
                        ![public_report()[@"enumeration"][@"count_status_code_raw"] isEqual:@(static_cast<IOReturn>(kIOReturnNotReady))]) {
            std::cerr << "Enumeration errors must preserve raw IOReturn without consuming the output count\n";
            return 1;
        }
                public_observation[@"count_status_code_raw"] = @(static_cast<IOReturn>(kIOReturnUnsupported));
                if (![public_report()[@"i2c_enumeration"] isEqual:@"UNSUPPORTED"] ||
                        ![public_report()[@"result"] isEqual:@"PUBLIC_IOFRAMEBUFFER_PATH_UNAVAILABLE"]) {
                        std::cerr << "The signed IOReturn unsupported value must retain its capability meaning\n";
                        return 1;
                }
        public_observation[@"count_status_code_raw"] = @0;
                for (NSDictionary* bus in @[
                        @{@"index_raw": @0, @"copy_status_code_raw": @(static_cast<IOReturn>(kIOReturnNoDevice)),
                            @"interface_conforms": @YES, @"capabilities": macmst::macos::public_i2c_capabilities(@16)},
                        @{@"index_raw": @0, @"copy_status_code_raw": @0, @"interface_conforms": @NO,
                            @"capabilities": macmst::macos::public_i2c_capabilities(@16)},
                        @{@"index_raw": @1, @"copy_status_code_raw": @0, @"interface_conforms": @YES,
                            @"capabilities": macmst::macos::public_i2c_capabilities(@16)}]) {
                        public_observation[@"buses"] = @[bus];
                        if (![public_report()[@"result"] isEqual:@"PUBLIC_PATH_UNRESOLVED"]) {
                                std::cerr << "Failed, nonconforming or misindexed interfaces cannot advertise a candidate\n";
                                return 1;
                        }
                }
                public_observation[@"buses"] = @[];
                if (![public_report()[@"result"] isEqual:@"PUBLIC_PATH_UNRESOLVED"]) {
                        std::cerr << "Incomplete bus enumeration must not claim all capabilities are known\n";
                        return 1;
                }
        public_observation[@"bus_count_raw"] = @257;
        if (![public_report()[@"result"] isEqual:@"PUBLIC_PATH_UNRESOLVED"]) {
            std::cerr << "Bus indices must not alias through the public eight-bit index mask\n";
            return 1;
        }
        public_observation[@"target_still_active_external"] = @NO;
        if (![public_report()[@"selection_status"] isEqual:@"DISPLAY_CHANGED_DURING_ENUMERATION"]) {
            std::cerr << "A changed display invalidates the capability classification\n";
            return 1;
        }
        NSDictionary* device = node(@"DCPEXT0", @"device", @"External", @0, @100);
        NSDictionary* service = node(@"DCPEXT0", @"service", @"External", @0, @101);
        NSDictionary* embedded = node(@"DCP", @"device", @"Embedded", @0, @1);
        NSDictionary* port = @{@"path": @"IOService:/HPM/Port-USB-C@4/DisplayPort", @"property_status_code_raw": @0,
                                @"properties": @{@"Active": @YES, @"ParentPortTypeDescription": @"USB-C"}};
        NSMutableDictionary* registry = [@{
            @"DCPDPDeviceProxy": query(@[embedded, device]),
            @"DCPDPServiceProxy": query(@[service]),
            @"DCPAVServiceProxy": query(@[]),
            @"IOPortTransportStateDisplayPort": query(@[port])
        } mutableCopy];
        NSArray* candidates = macmst::macos::external_dp_candidates(registry, 1, true);
        if (candidates.count != 1 || ![candidates[0][@"service_entry_id_raw"] isEqual:@101] ||
            ![candidates[0][@"activity_assessment"] isEqual:@"INFERRED_SINGLE_ACTIVE_EXTERNAL_CONTEXT"] ||
            ![candidates[0][@"safe_to_invoke_private_api"] isEqual:@NO]) {
            std::cerr << "Unique external context must remain an inference, never API authorization\n";
            return 1;
        }
        if (![macmst::macos::external_dp_candidates(registry, 1, false)[0][@"activity_assessment"] isEqual:@"UNVERIFIED"] ||
            ![macmst::macos::external_dp_candidates(registry, 2, true)[0][@"activity_assessment"] isEqual:@"UNVERIFIED"]) {
            std::cerr << "Partial or multiple-display snapshots must not infer a unique active context\n";
            return 1;
        }
        registry[@"DCPDPServiceProxy"] = query(@[service, service]);
        candidates = macmst::macos::external_dp_candidates(registry, 1, true);
        if (![candidates[0][@"pairing"] isEqual:@"AMBIGUOUS"] || candidates[0][@"service_path"] != [NSNull null]) {
            std::cerr << "Duplicate services must remain ambiguous\n";
            return 1;
        }
        for (NSDictionary* mismatch in @[node(@"DCPEXT1", @"service", @"External", @0, @102),
                                         node(@"DCPEXT0", @"service", @"External", @1, @103),
                                         node(@"DCPEXT0", @"service", @"Embedded", @0, @104)]) {
            registry[@"DCPDPServiceProxy"] = query(@[mismatch]);
            if (![macmst::macos::external_dp_candidates(registry, 1, true)[0][@"pairing"] isEqual:@"MISSING_SERVICE"]) {
                std::cerr << "Do not pair across processors, units, or Embedded location\n";
                return 1;
            }
        }
        registry[@"DCPDPDeviceProxy"] = query(@[device, device]);
        registry[@"DCPDPServiceProxy"] = query(@[service]);
        for (NSDictionary* candidate in macmst::macos::external_dp_candidates(registry, 1, true)) {
            if (![candidate[@"pairing"] isEqual:@"AMBIGUOUS"]) {
                std::cerr << "Duplicate devices must not choose one service implicitly\n";
                return 1;
            }
        }
        NSMutableDictionary* malformed_path = [device mutableCopy];
        malformed_path[@"path"] = @"IOService:/missing-processor/device";
        registry[@"DCPDPDeviceProxy"] = query(@[malformed_path,
            node(@"DCPEXT0", @"device", @"External", @YES, @106),
            node(@"DCPEXT0", @"device", @"External", @(-1), @107)]);
        if (macmst::macos::external_dp_candidates(registry, 1, true).count != 0) {
            std::cerr << "Invalid processor paths and noninteger Unit identities must not pair\n";
            return 1;
        }
        registry[@"DCPDPDeviceProxy"] = query(@[embedded, node(@"DCPEXT0", @"device", @"External", @"0", @105)]);
        if (macmst::macos::external_dp_candidates(registry, 0, true).count != 0) {
            std::cerr << "Embedded devices and malformed Unit values must not become candidates\n";
            return 1;
        }
        std::cout << "PASS: registry privacy, scalar types, raw values, unavailable properties, JSON\n";
        std::cout << "PASS: public IOI2C masks, unknown bits, invalid properties and installed SDK ABI\n";
        std::cout << "PASS: synthetic external pairing, ambiguity, mismatched contexts, incomplete observations\n";
    }
    return 0;
}