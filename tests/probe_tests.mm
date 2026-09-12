#import <Foundation/Foundation.h>

#include "platform/macos/registry.hpp"

#include <iostream>

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
        std::cout << "PASS: synthetic external pairing, ambiguity, mismatched contexts, incomplete observations\n";
    }
    return 0;
}