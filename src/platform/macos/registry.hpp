#pragma once

#import <Foundation/Foundation.h>

namespace macmst::macos {
NSDictionary* select_registry_properties(NSDictionary* properties);
NSArray* external_dp_candidates(NSDictionary* registry, NSUInteger external_display_count,
							   bool observation_complete);
}