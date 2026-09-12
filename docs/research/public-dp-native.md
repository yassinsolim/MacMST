# Public DisplayPort-Native IOKit Investigation

## Scope And Integration

This investigation is enumeration-only on `research/public-dp-native`, based on
merge commit `2ffc77d9d532502495fca5d88291d42eed61e45b`. The completed RPC-safety
branch was integrated with a normal two-parent merge and pushed to main. Its
branch remains at `0c4d742933d82afe6379f33698bc50d81bd08a90`; the baseline tag
still targets `2512e2f34ec5fc2b2f03102ecfb44951dad3c517`.

The private path remains **NOT_READY_FOR_DPCD_TEST** with all existing gate
states unchanged. This branch must not open an I2C interface, send an IOI2C
request, create a private DP object, invoke a private selector, or change display
or security state. Header declarations and advertised capabilities are not
successful DPCD access. A final public-path classification requires new M5
enumeration evidence; it is not inferred from the SDK.

## Installed SDK Contract

`PRIMARY_SOURCE`: Xcode 26.6 (17F113), macOS SDK **26.5**, Apple Clang
21.0.0 (clang-2100.1.1.101), inspected 2026-09-12. The selected SDK and exact
header are:

```text
/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk
System/Library/Frameworks/IOKit.framework/Headers/i2c/IOI2CInterface.h
```

The exact IOI2C header SHA-256 is
`f64c1c9dbe27059a67893e2160f4663efcd6ea6bda7208063f1ede6fc9f71eb6`.

The public enum assigns no-transaction = 0, simple = 1, DDC/CI reply = 2,
combined = 3, and `kIOI2CDisplayPortNativeTransactionType = 4`. The public
property key is `kIOI2CTransactionTypesKey`, whose exact string is
`IOI2CTransactionTypes`. It can be read from an interface using public
`IORegistryEntryCreateCFProperty`; the advertisement's encoding must be checked
against source before decoding. `kIOI2CBusTypeKey` is `IOI2CBusType`, with I2C
bus type 1 and DisplayPort bus type 2. Bus type is distinct from transaction type.

The header is not self-contained: include CoreFoundation before it to declare
`CFTypeRef` used by `IOI2CCopyInterfaceForID`. The initial compile-only check
without that prerequisite failed; it did not involve any hardware operation.
The current installed declarations, not guessed function pointers, are:

```c
#include <CoreFoundation/CoreFoundation.h>
#include <IOKit/i2c/IOI2CInterface.h>

IOReturn IOFBGetI2CInterfaceCount(io_service_t framebuffer, IOItemCount *count);
IOReturn IOFBCopyI2CInterfaceForBus(io_service_t framebuffer, IOOptionBits bus,
                                  io_service_t *interface);
IOReturn IOI2CInterfaceOpen(io_service_t interface, IOOptionBits options,
                           IOI2CConnectRef *connect);
IOReturn IOI2CSendRequest(IOI2CConnectRef connect, IOOptionBits options,
                         IOI2CRequest *request);
IOReturn IOI2CInterfaceClose(IOI2CConnectRef connect, IOOptionBits options);
```

Only the first two are permitted in this investigation, and only on a proved
external framebuffer target. A copied bus interface is caller-owned and released
with `IOObjectRelease`, without opening it. The SDK explicitly requires an
IOFramebuffer instance for the count call; it does not authorize substituting
an arbitrary DCP registry object.

### Arm64 Request Layout

The installed `IOI2CRequest` uses `#pragma pack(push, 4)` and the `__LP64__`
branch. The header-derived layout below is checked with compile-only arm64
`sizeof`, `alignof` and `offsetof` assertions: **124 bytes**, alignment **4**.
No request object is submitted by that validation.

| Offset | Size | Field |
| --- | --- | --- |
| 0 | 4 | sendTransactionType |
| 4 | 4 | replyTransactionType |
| 8 | 4 | sendAddress |
| 12 | 4 | replyAddress |
| 16 | 1 | sendSubAddress |
| 17 | 1 | replySubAddress |
| 18 | 2 | __reservedA |
| 20 | 8 | minReplyDelay |
| 28 | 4 | result |
| 32 | 4 | commFlags |
| 36 | 4 | __padA |
| 40 | 4 | sendBytes |
| 44 | 8 | __reservedB |
| 52 | 4 | __padB |
| 56 | 4 | replyBytes |
| 60 | 8 | completion |
| 68 | 8 | sendBuffer |
| 76 | 8 | replyBuffer |
| 84 | 40 | __reservedC |

The header distinguishes `IOI2CSendRequest`'s submission IOReturn from the
transaction's `request.result`. Null completion denotes synchronous operation;
`sendBytes` and `replyBytes` are documented as updated on completion. These are
generic API declarations, not yet a verified native-DP address/buffer encoding
or a bounded transaction contract. Native request design is conditional on an
actual interface advertising type 4; it must not be guessed from DDC examples.

### CoreGraphics Declaration

The same SDK's `CoreGraphics.framework/Headers/CGDisplayConfiguration.h`
declares the following at line 372, without an architecture exclusion:

```c
CG_EXTERN io_service_t CGDisplayIOServicePort(CGDirectDisplayID display)
    API_DEPRECATED("No longer supported", macos(10.2,10.9));
```

This is a public deprecated API, not a private replacement. The installed
CoreGraphics headers expose no alternate CGDisplay-to-IOService declaration in
the inspected service/registry search. Availability of a declaration does not
establish a nonnull or IOFramebuffer-conforming result on M5. No mapping call
has yet been made in this investigation.

## Validation Strategy

Reuse the existing CMake/CTest unit and separate hardware labels. Deterministic
tests will cover capability decoding, external-only selection, ambiguous and
missing services, raw error preservation, and privacy filtering. The hardware
probe may enumerate registry objects and public bus capabilities only. Strict
warnings and the existing ASan/UBSan configuration remain required. No request
transmission, opening, private call or DPCD success can be claimed by these tests.