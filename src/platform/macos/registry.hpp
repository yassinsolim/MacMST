#pragma once

#import <Foundation/Foundation.h>

#include <cstdint>
#include <functional>

namespace macmst::macos {
NSDictionary* select_registry_properties(NSDictionary* properties);
NSDictionary* public_i2c_capabilities(id transaction_types);
NSDictionary* public_displayport_interfaces(NSArray* displays, NSDictionary* registry,
	bool observation_complete, const std::function<NSDictionary*(std::uint32_t)>& enumerate);
NSArray* external_dp_candidates(NSDictionary* registry, NSUInteger external_display_count,
							   bool observation_complete);
}