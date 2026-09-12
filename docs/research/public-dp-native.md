# Public DisplayPort-Native IOKit Investigation

**Public path result: PUBLIC_IOFRAMEBUFFER_PATH_UNAVAILABLE.** P1 observes no
published IOFramebuffer/I2C route for the active M5 external path. This is an
exposure result for the recorded hardware, OS and topology, not a statement that
M5 lacks native AUX or MST hardware. DPCD access remains **UNKNOWN**.

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
successful DPCD access. The result below is based on new M5 enumeration, not
inferred from the SDK. Neither the original RPC report nor its 13 gate states
was modified by this branch.

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
The CoreGraphics configuration-header SHA-256 is
`24fc3b20cb4815835a632990a43ed28256997acc2cf8d4600159f8e8a4d7e27c`.

The public enum assigns no-transaction = 0, simple = 1, DDC/CI reply = 2,
combined = 3, and `kIOI2CDisplayPortNativeTransactionType = 4`. The public
property key is `kIOI2CTransactionTypesKey`, whose exact string is
`IOI2CTransactionTypes`. It can be read from an interface using public
`IORegistryEntryCreateCFProperty`. Source inspection below confirms a bitmask:
the DP-native bit is **1 << 4 = 0x10**, whereas mask value 4 denotes DDC/CI reply.
`kIOI2CBusTypeKey` is `IOI2CBusType`, with I2C
bus type 1 and DisplayPort bus type 2. Bus type is distinct from transaction type.

The header is not self-contained: include CoreFoundation before it to declare
`CFTypeRef` used by `IOI2CCopyInterfaceForID`. The initial compile-only check
without that prerequisite failed; it did not involve any hardware operation.
For C++/Objective-C++, wrap this header include in `extern "C"`: the installed
header also lacks C++ linkage guards. A later strict link check exposed mangled
count/copy symbols until that guard was added. Compile-only layout checks alone
do not verify linkage. The probe uses the installed declarations, not redeclared
prototypes, with this narrow language-linkage guard.
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
establish a nonnull or IOFramebuffer-conforming result on M5. P1 invokes this
public function only for the selected active external display; its result is 0.
Private `CGSServiceForDisplayNumber`, CoreDisplay functions, and IOAV/IODP
constructors used by other projects are not public replacements used here.

## Pinned Implementation Evidence

These are current repository HEADs checked on 2026-09-12, not claims that their
source is the exact source of macOS 26.6.2. Eleven downloaded files are retained
under ignored `artifacts/sources/public-dp-native/`; every Git blob SHA-1 was
independently matched against GitHub. No downloaded code was built or executed.

| Source | Exact Revision / Relevant Implementation | Finding And Limit |
| --- | --- | --- |
| Apple IOKitUser, S25 | `323ead896d04424f87184d8f6ff0cce811aab106`; [IOGraphicsLib.c](https://github.com/apple-oss-distributions/IOKitUser/blob/323ead896d04424f87184d8f6ff0cce811aab106/graphics.subproj/IOGraphicsLib.c), IOFBGetI2CInterfaceCount / IOFBCopyI2CInterfaceForBus / IOI2CCopyInterfaceForID | PRIMARY_SOURCE: count reads IOFBI2CInterfaceIDs and returns success with zero if absent; copy masks the bus index to eight bits and finds an IOI2CInterface by ID. These routines do not open an interface. Success alone does not prove a usable target. |
| Apple IOGraphics, S25 | `76285384ff0ce63965a21b8023bf6d7e447fcc19`; [IONDRVFramebuffer.cpp](https://github.com/apple-oss-distributions/IOGraphics/blob/76285384ff0ce63965a21b8023bf6d7e447fcc19/IONDRVSupport/IONDRVFramebuffer.cpp), csSupportedTypes and kIOI2CTransactionTypesKey | PRIMARY_SOURCE: publishes the supported-types bitmask and tests bits using 1 << transaction type. This is the legacy provider implementation, not an M5 driver attestation. |
| Lunar, S26 | `8a21ffe302a00890d9f5d5101536cdd2a4631be8`; [DDC.c](https://github.com/alin23/Lunar/blob/8a21ffe302a00890d9f5d5101536cdd2a4631be8/Lunar/DDC/DDC.c), [DDC.swift](https://github.com/alin23/Lunar/blob/8a21ffe302a00890d9f5d5101536cdd2a4631be8/Lunar/DDC/DDC.swift) | PRIMARY_SOURCE for project behavior: arm64 read/write branches use DCP/AV services; other branches use I2CController/framebuffer. The C debug path checks and logs type-4 support, but selecting it as the DDC request type is commented out. Its broad capability scan is not proof of support on a particular M5 display. |
| MonitorControl, S27 | `f16d90f29cefbd9fff47e26fc8f99fe7a5280deb`; [IntelDDC.swift](https://github.com/MonitorControl/MonitorControl/blob/f16d90f29cefbd9fff47e26fc8f99fe7a5280deb/MonitorControl/Support/IntelDDC.swift), [Arm64DDC.swift](https://github.com/MonitorControl/MonitorControl/blob/f16d90f29cefbd9fff47e26fc8f99fe7a5280deb/MonitorControl/Support/Arm64DDC.swift), [OtherDisplay.swift](https://github.com/MonitorControl/MonitorControl/blob/f16d90f29cefbd9fff47e26fc8f99fe7a5280deb/MonitorControl/Model/OtherDisplay.swift) | PRIMARY_SOURCE for project behavior: OtherDisplay constructs IntelDDC only when not arm64. IntelDDC selects DDC/CI reply or simple modes; Arm64DDC uses private IOAVService I2C. No native type-4 selection appears in these inspected paths. |
| ddc-macos-rs, S28 | `de44fd8671e95dac351d2c81737dc0527e4fe31e`; [monitor.rs](https://github.com/haimgel/ddc-macos-rs/blob/de44fd8671e95dac351d2c81737dc0527e4fe31e/src/monitor.rs), [intel.rs](https://github.com/haimgel/ddc-macos-rs/blob/de44fd8671e95dac351d2c81737dc0527e4fe31e/src/intel.rs), [arm.rs](https://github.com/haimgel/ddc-macos-rs/blob/de44fd8671e95dac351d2c81737dc0527e4fe31e/src/arm.rs) | PRIMARY_SOURCE for project behavior: enumeration tries framebuffer discovery first, then an AV-service fallback; not an unconditional compile-time exclusion of IOFramebuffer on arm64. The inspected Intel path selects DDC/CI reply or simple modes; the arm path uses private IOAVService I2C. |
| AllRez, S29 | `433f3513225199f44e0e6bc90294b2be8df6b9a8`; [displayport.cpp](https://github.com/joevt/AllRez/blob/433f3513225199f44e0e6bc90294b2be8df6b9a8/AllRez/displayport.cpp), dp_dpcd_read / dp_dpcd_write | PRIMARY_SOURCE for a real type-4 code example: helpers populate native transaction types and pass requests to UniversalI2CSendRequest. This compatibility wrapper uses its own historical request type; neither it nor its write path was invoked or copied. It is not proof of a working M5 public interface. |

Project code is primary evidence of what that project does. A third-party
observation or comment about missing Apple Silicon framebuffers is not Apple
documentation or an M5 measurement. Whether Apple **intentionally** removed all
legacy framebuffer exposure on every Apple Silicon configuration remains
UNKNOWN; the public CG deprecation predates Apple Silicon. DDC-only failures in
these projects do not independently disprove other IOI2C modes.

## M5 Capture P1

P1 is `artifacts/probes/20260912T104606Z/`, captured with the new public probe:
**40 read-only commands, zero failures, 27 hashed artifacts**. Its eight recorded
source hashes match probe commit `c4e65edfd933aa0ca580fb2b998885eac1d4b01f`.

| Identity | Value |
| --- | --- |
| Host | Apple M5 / Mac17,2 / arm64 / macOS 26.6.2 (25G83). |
| Probe SHA-256 | `7aba2b482d60083e8aabb98ffb340b44d7b068f5f9ca7ef41e46e3b7145d49d3` |
| macmst-probe.json SHA-256 | `33c0cba345a60c2ec82d30408c06defd1d00834a6f27eebfff8ec0a9abb1999d` |
| manifest.json SHA-256 | `9b7c481b3a2d91b7d9e6028a604e3520ce0c814a5bff564aa8a14f5cddc3fc2d` |
| Active external logical display | ID raw 3, built-in false, active true, 1920x1080 at 60 Hz; vendor raw 1129, product raw 9381. |
| Existing External DCP target | DCPEXT0 / Unit 0; DP device/service IDs raw 4294970467 / 4294970463, observations only. |
| Published transport | USB-C port 4; HPD raw 2 / High; two lanes; LinkRate raw 4 / 8.1 Gbps HBR3; SinkCount 1; Tunneled false. |

`VERIFIED_ON_M5`: host/displays and the selected DCPDP, DCPAV, DP-transport and
USB records match G5 exactly; USB count remains six. The prior owner-correlated
ZMUIPNG 14-in-1/right-side socket topology is the context, not a new physical
correlation experiment. No cable cycle, mode change or display-state operation
was performed. Capture IDs and service IDs must never be reused as handles.

### External Service Mapping

`VERIFIED_ON_M5`: `CGDisplayIOServicePort(3)` returned **0 / IO_OBJECT_NULL**.
The function returns a service port, not an IOReturn; zero is not a fabricated
successful IOReturn. The display was still active and external at the end of
the observation.

| Requested Mapping Detail | P1 Observation |
| --- | --- |
| Public CoreGraphics service | null |
| Service class | Not available: no returned service. |
| Provider / parent | Not available: no returned service. |
| Properties of returned service | None; no arbitrary registry service substituted. |
| IOFramebuffer target | ABSENT |
| Stop reason | NO_MAPPED_SERVICE |

### I2C Enumeration And Capabilities

Because there is no returned framebuffer target, **IOFBGetI2CInterfaceCount was
not called**. Passing null, an Embedded target, an IOMobileFramebufferShim or a
DCP proxy merely to obtain success would violate the target contract. Therefore
Stage 4 is blocked before invocation, not a zero-bus result from that API:

| Field | Exact P1 Value |
| --- | --- |
| i2c_enumeration | NOT_CALLED_NO_FRAMEBUFFER |
| count_attempted | false |
| count_status_code_raw / count_status_hex | null / null: no IOReturn was returned. |
| bus_count_raw / interpreted bus_count | null / null: no count output was produced. |
| IOFBCopyI2CInterfaceForBus calls | 0; Stage 5's positive-count prerequisite was unmet. |
| Buses observed through the selected CG route | Empty list, not a fabricated count result. |
| DP-native advertisement | UNKNOWN; there is no interface mask to decode. |
| Interface opens / requests | 0 / 0 |
| DPCD access / native AUX / MST source support | UNKNOWN / UNKNOWN / UNKNOWN |

### Alternate Public Exposure

The native public IORegistry inventory and independent `ioreg` class queries
agree. Every native matching query below returned IOReturn **0 / 0x00000000**;
every corresponding ioreg command exited 0. These are **registry query** results,
not the absent IOFB count-call result.

| Requested Class | Published Instances |
| --- | --- |
| IOFramebuffer | 0 |
| IOI2CInterface | 0 |
| IOFramebufferI2CInterface | 0 |
| IODisplay / IODisplayConnect / IODisplayPort | 0 each |
| AppleCLCD / AppleCLCD2 | 0 each |
| IOMobileFramebuffer / IOMobileFramebufferShim | 3 each, the same three shim objects. |
| DCPDPDeviceProxy / DCPDPServiceProxy | 2 each: Embedded and External; not public framebuffer substitutes. |

The three shim paths have the common prefix
`IOService:/AppleARMPE/arm-io@10F00000/AppleSoCIO/` and these suffixes:

```text
dispext0@F4000000/IOMobileFramebufferShim
disp0@74000000/IOMobileFramebufferShim
dispext1@98000000/IOMobileFramebufferShim
```

All have actual class IOMobileFramebufferShim and published IOProviderClass
AppleARMIODevice. Their immediate parents are AppleARMIODevice objects named
dispext0, disp0 and dispext1 respectively. These registry relationships do not
turn them into a CG-provided IOFramebuffer. DCP/DCPEXT/DP provider chains remain
visible in the saved tree and existing candidate report, but no public I2C
interface was found elsewhere. No shim/proxy was passed to an IOFB API.

### Assessment

The required publicly exposed route is absent in this snapshot, including the
alternate class search. This constrains **all modes that require this public
IOFramebuffer/I2C route**, not only DDC/CI, because there is no exposed interface
on which to select any mode. It is not a firmware rejection of transaction 4,
a silicon capability result, or proof about all future macOS/topology versions.

The derived classification is **PUBLIC_IOFRAMEBUFFER_PATH_UNAVAILABLE**. A
published interface with a real 0x10 advertisement would disconfirm this result
for a new snapshot; the constant in a header cannot do so. The existing private
path remains NOT_READY_FOR_DPCD_TEST, without downgrading any FAIL or UNKNOWN.

## Probe Behavior

The public diagnostic reports selection, CG service metadata when available,
framebuffer conformance, count/copy IOReturns in signed raw and unsigned hex form,
raw capability masks and per-mode advertisement. Missing/malformed masks remain
UNKNOWN; unknown bits are retained. Bus type 2 is not a substitute for the native
transaction bit. Successful zero counts, skipped calls and returned errors are
different states. Count/copy capability failures remain in structured output.

Only one active non-built-in display may reach the enumeration callback. The
probe checks it again before and after public mapping/enumeration, rejects a
non-framebuffer target, bounds bus indices to the public eight-bit range, and
checks copied-interface conformance. A separately retained CG service reference
and copied bus references are released without opening them. The one deprecated
CG call has a local deprecation-warning guard; strict warnings remain enabled
elsewhere. No public or private request function is linked by the executable.

The metadata is allowlisted; serials, EDID and unrelated blobs are not persisted.
Snapshots are sequential, not atomic. The positive count/copy branch is covered
by synthetic classification cases but **was not exercised on this M5 hardware**,
because no qualifying framebuffer existed. No successful transaction is claimed.

## Next Investigation

Stage 10's condition was not met: type 4 was not observed as advertised by any
interface. **No future public DPCD request contract is approved or implemented.**
The AllRez example is a lead, not a substitute for a current provider contract.
A future public experiment would first need an actual external interface and
advertisement, then provider-specific native encoding, completion/error and
bounded-lifetime evidence, followed by separate approval. No request is sent now.

After this public investigation is closed, the remaining private-path options
are separate future work, not changes made on this branch:

1. Further static proof of full replies, firmware semantics and bounded recovery.
2. An isolated child-process watchdog design, without assuming process isolation
    cancels outstanding kernel/DCP work or makes the call safe.
3. Process-death and user-client teardown/quiescence proof before relying on any
    watchdog or termination mechanism; no live fault injection is authorized here.
4. Another Apple display interface, first classified as public or private with
    its own exact ABI, target, authorization and side-effect evidence.

## Validation Strategy

Reuse the existing CMake/CTest unit and separate hardware labels. Deterministic
tests will cover capability decoding, external-only selection, ambiguous and
missing services, raw error preservation, and privacy filtering. The hardware
probe may enumerate registry objects and public bus capabilities only. Strict
warnings and the existing ASan/UBSan configuration remain required. No request
transmission, opening, private call or DPCD success can be claimed by these tests.

## Validation Results

| Command / Check | Result |
| --- | --- |
| `cmake --build build` | PASS, strict native build. |
| `ctest --test-dir build -L unit --output-on-failure` | PASS, 7/7 entries; 42 synthetic DPCD checks and 37 static-parser methods retained. |
| `ctest --test-dir build -L hardware --output-on-failure` | PASS, 1/1 public-only probe entry. No IOFB call without a valid target. |
| `cmake --build build-sanitized` | PASS, existing ASan/UBSan configuration. |
| `ctest --test-dir build-sanitized -L unit --output-on-failure` | PASS, 7/7 entries; added native fault cases also passed the focused sanitized probe_privacy run. |
| `python3 tools/capture_baseline.py --probe build/macmst` | PASS, P1: 40 commands, zero failures, no opens or requests. |
| Executable import audit in cli_contract | PASS: public mapping/count/copy present; IOI2CSendRequest, interface open/close and private transport imports absent. |
| Capture/source provenance | PASS: 27 P1 artifact hashes, 8 core/capture sources, probe binary and 11 upstream files with independent blob-ID matches. |

The native unit target checks the installed SDK layout/signatures and synthetic
external-only selection, no built-in fallback, ambiguity, missing/failed registry
queries, absent/invalid masks, unknown bits, zero/error/over-limit counts, copied
interface errors/conformance/indexing, and display changes. The seven Python
capture privacy methods preserve public scalar capabilities without serial/EDID
data. Positive advertisement is never promoted to DPCD success.

Reproduce on the recorded source and hardware with the commands above; captures
receive a fresh UTC name. The raw P1 data and upstream sources stay ignored.
No DPCD/MST transaction, firmware/security change, private API invocation, or
display reconfiguration was performed. Compilation and tests are not hardware
transport evidence.