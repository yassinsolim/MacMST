# M5P2: macOS Host-Side Source Creation And Multi-Stream Control

## Objective

Determine whether the exact macOS host stack can express more than one logical
source stream for one physical DPTX. This is a newly authorized host-only static
investigation above DCP firmware, not another packetizer or sideband search.
The final objective remains independent external displays through ordinary
USB-C/DisplayPort MST hubs without DisplayLink or special multi-DP Thunderbolt
hardware; static API presence alone cannot demonstrate that functionality.

Result: **RUNTIME_OBSERVER_STILL_REQUIRED**. Generic logical-display objects,
timing setters, host RPC forwarding and physical-port allocation are present.
No inspected path establishes two independent source contexts bound to one
physical DPTX. This is a scoped unresolved result, not a macOS or M5
architectural impossibility claim, and not a reason to rerun M3A.

`VERIFIED` below means an exact static byte, symbol, fixup, property or direct
value-flow observation. `STRONG` means the stated local interpretation follows
from those observations. `INFERRED` marks an integration hypothesis; `UNKNOWN`
marks an unclosed edge. None means hardware execution or safe callability.

Initial local hypothesis: a host DCPDP device/service proxy is created and
addressed by service/device identity, not necessarily by an independent source
index. The cheapest discriminating check is the current DCPDP/DCPAV factory
and message-encoder path: identify its inputs and where identity enters a
collection or command. An explicit source-index dimension tied to one physical
DPTX would disconfirm this hypothesis. Class names, collection length and
multiple physical links are insufficient.

## Frozen Baseline

M5P2 starts on clean, published `research/m5-observer-pipeline` at
`ec45795561620533450ac82399fd00e42cb857fd`, upstream equal, with the four exact
M5P1 commits verified above M5P0
`3f2240de0d33126c8f264dcfa0e04e3e61397391`. All 43 local/remote head/tag/peeled
identities matched. Main remains `7250caac7a9f627f381b91ab9dfeb86191344ed9`.
`research/m5-host-stream-control` branches directly from M5P1 without a merge.

The current OS metadata reports macOS 26.6.2 build 25G83. Target attribution
Mac17,2 / J704AP / T8142 is carried from the frozen exact-machine baseline,
not a new display or IORegistry observation. The 124 M5P1 synthetic tests and
all 31 fixture hashes pass; there are zero real-evidence gate passes.
`OFFLINE_OBSERVER_PIPELINE_READY` remains intact.

The consumed M2F marker and both historical receipts match their retained
hashes; the M2G DPCD-read attempt marker is absent. Preserve
`RETIRED_ON_DAILY_USE_M5`, `NOT_READY_FOR_DPCD_TEST`,
`STATIC_PACKETIZER_ANALYSIS_FROZEN` and
`NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED`.

No firmware payload, packetizer table, generator, payload-ID capacity or
sideband implementation is inspected. No private method, user-client call,
DCP/AUX/DPCD transaction, live debugger, display transition, binary patch,
kernel/security change or m1n1 operation is permitted. The sibling repository
is not accessed; its prior clean state is historical, not a fresh verification.
Keep the USB-C hub and both displays unplugged. No connection or new live
topology observation forms part of M5P2.

### Exact Host Inputs

The current, running-UUID-matched kernel collection is freshly re-read, not
merely assumed to match M3A. Its UUID is
`447D769E-1CB7-3086-A0B4-32226837B587`; IM4P container SHA-256 is
`b20d50fc8f445a5c578ac63bd974efeb6ae48a97116800301071891795fb26d9`;
decoded Mach-O SHA-256 is
`f516560c295e10d62c3d219237d23c5900664107b2115dad590eaa259516d05f`.
The reader accepts only a unique bounded `krnl` container and checks
`sysctl -n kern.uuid`. This metadata query is not display enumeration.
Container signature validation is not performed by this reader.

The current arm64e cache is under
`/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/`.
Its primary UUID bytes are `f2e86c536052388bba715a0c9b569413` and image-table
SHA-256 is `99bd7e60ec2d7ef76f7dbcf1cc1798d5669239b3de98196b9c89d78f267a5de6`.
All 13 component header identities are checked. Receipts hash each selected
image's header, function-start data, sections and captured function bodies;
**no full-cache-file digest or loaded-process identity is claimed**.

Metadata inventory covers 373 kernel fileset names and 3,649 cache image names.
Nineteen selected images (ten kernel, nine cached userspace) supply the host
receipts; 57 unique declared function bodies are retained. WindowServer and
one adjacent XPC executable are additional metadata-only controls. These are
not 57 source factories, and presence does not prove runtime use on this M5.

## Host Component Inventory

Initial selection is based on the frozen [M3A host inventory](m5-mst-source-feasibility.md#current-m5-display-stack-and-search-coverage),
not a repeat of its MST-signature scan. The first controlling surfaces are
DCPDPFamilyProxy/DCPAVFamilyProxy for host object creation and message encoding,
and AppleDisplayCrossbar/AppleDCPDPTXProxy for physical output association.
Higher-level CoreDisplay/SkyLight paths are followed only where they identify
display, timing, mirror or binding semantics. Every new claim must be bound to
the current image UUID, raw bytes and a reproducible symbol/xref or call edge.

| Binary/component | Role | Why relevant | Priority |
| --- | --- | --- | --- |
| CoreDisplay | Generic display records, configuration and pipe/service lookup | Caller-supplied display object -> allocation/map; mirror records | P1, logical creation |
| SkyLight | WindowServer-side display configuration | Mirror/independent-output configuration entries | P1, logical policy |
| IOMobileFramebuffer private framework | Per-handle display/mode operations and virtual backend registration | Concrete setters and callback boundary | P1, host API |
| AppleMobileDispH17G-DCP | `IOMobileFramebufferShim`, `UnifiedPipeline2` | Peer framebuffer fan-out and concrete RPC override | P1, timing/host RPC |
| IOMobileGraphicsFamily-DCP | AP stubs, `DCPLink`, `AppleDCPLinkService` | A411/A413 construction and existing service forwarding | P1, timing/host RPC |
| DCPDPFamilyProxy | DP controller/device/service proxies | Endpoint-backed identity and lifecycle, not assumed source objects | P1, device identity |
| DCPAVFamilyProxy | AV proxy base, timing and mode IPC | Role byte, timing body, endpoint destination | P1, command production |
| IOAVFamily | AV service, link roles and interfaces | Explicit role formatter and virtual-mode interfaces | P1, role semantics |
| IODisplayPortFamily | Port/switch state and virtual DP device | Port-address collection versus emulated device capability storage | P1, ownership distinction |
| AppleDisplayCrossbar | Physical/logical port allocation | T8142-specific availability and count checks | P1, physical binding |
| AppleDCPDPTXProxy | Remote DPTX-port forwarding | One packed port-attributes request, associated UFP reference | P1, physical routing |
| AppleDCP | Host DCP platform/controller support | Adjacent controller owner; no qualified source factory identified | P2 |
| WindowServer executable | SkyLight-linked process entry | Links to SkyLight and libSystem; process not attached or queried | P2, orchestration |
| CoreGraphics | Public display API front | Current image and configuration entrypoint metadata only | P2, forwarding |
| IOKit userspace | Registry/service API imports | Exact cached import resolves to registry-entry-ID getter | P2, identity |
| DisplayServices / DisplayTransportServices | Adjacent display services and transport objects | Inventoried; no binding-owning body qualified | P2, candidate adjacency |
| QuartzCore | Composition/virtual-display adjacent framework | Inventoried only; a composition surface is not a DP source | P3 |
| EXDisplayPipe | Small adjacent pipe-control interface | Power/indicator/log setter names, not a source factory | P3 |
| CoreDisplayXPCService | Nearby application XPC service | Static identity/dependencies only; no service contacted | P3 |
| DriverKit/UserServer candidates | Possible alternative host boundary | Selected proxy personalities use kernel AFK services; no DriverKit source-creation contract qualified | P3, unresolved alternative |
| Thunderbolt DP adapter families | Separate-link/tunnel architectural control | Present in host name inventory; historical role only, no new tunnel-body analysis | P3, not same-link evidence |

Ranked ownership questions: logical creation first in CoreDisplay/SkyLight;
timing first in the framebuffer shim/AP and DCPAV video interface; physical
selection first in Crossbar/remote-port proxies; DCP object creation first in
the endpoint/proxy matching path; source identity only after those distinct
namespaces can be bound. No blanket graphics-library or protocol-signature
function scan was performed.

### Image UUIDs

Kernel identifiers below omit their already-recorded `com.apple.driver.` or
`com.apple.iokit.` prefix. Cached paths are recorded in each receipt.

| Image | Current Mach-O UUID |
| --- | --- |
| DCPDPFamilyProxy | `7732A096-166C-312F-8AEB-BF0DED28C5C3` |
| DCPAVFamilyProxy | `9CA0BBA6-98A5-3CAB-8D7A-9EB2D79C9D08` |
| IODisplayPortFamily | `21AA8D3B-3EE1-3812-9D20-BB3B5A0B79DB` |
| IOAVFamily | `6E4B9D42-04A2-393A-B1F5-F121B8D00954` |
| AppleDCPDPTXProxy | `B88B6C2C-8CF9-317B-94CE-D9DF5809ABB0` |
| AppleDCP | `4E81DEE6-C09C-35F7-AFEC-50A982E1EEFC` |
| AppleMobileDispH17G-DCP | `6D81BA37-15A7-38E5-9984-8C9F3ADEEDE5` |
| IOMobileGraphicsFamily-DCP | `98ECE2F0-AB94-39FA-A02D-76AD313A3161` |
| AppleDisplayCrossbar | `5A00089D-B7A4-3280-BE13-5D1118134A02` |
| IOGraphicsFamily | `047DBAFA-C0DA-370B-81C4-22189161397E` |
| CoreDisplay | `D8E7E31A-7D3E-3742-A3EE-469C6237FAF4` |
| CoreGraphics | `38C8FBEC-DE88-33FE-B742-A192F22CC754` |
| SkyLight | `0C8F41C6-6D93-3DB3-B522-CA8CFF5C3B33` |
| IOMobileFramebuffer | `2BC48182-F354-3AB0-8F18-0C60CAAFE398` |
| IOKit | `12372585-DF92-33EF-B632-714FAA13260A` |
| DisplayServices | `0AE066F1-6087-3373-9CD4-8AED1AE7ECD4` |
| DisplayTransportServices | `2B145BB7-EE69-3D5C-A85C-61B45C0A9A71` |
| EXDisplayPipe | `3CF5134F-F923-3BDD-8F2D-D1F5C1B046B0` |
| QuartzCore | `98CB7012-30E5-3BDD-8C84-CDBDA9DB3017` |
| WindowServer, arm64e slice | `9D734FC6-31E5-3954-AB14-48B0512AD7E7` |
| CoreDisplayXPCService, arm64e slice | `3CE92CF3-0658-394D-B03A-1CB82BFFC51D` |

WindowServer's complete universal file SHA-256 is
`69034a0706940371291761d62eb0734f8b6b78409f6e7887710116eb38d5c152`.
CoreDisplayXPCService's is
`764b73a71b86b1f7ea613c8efd2db6390771bff26de77af7d3fea33067ac65bb`.
The XPC bundle reports version 291.4, SDK build 25G74 and platform version
26.6.1; those are build metadata inside the current 25G83 installation, not
an alternative running OS identification. Only libSystem is a declared direct
dependency of that executable; no inference excludes dynamic dependencies.

The standalone files are
`/System/Library/PrivateFrameworks/SkyLight.framework/Versions/A/Resources/WindowServer`
and
`/System/Library/Frameworks/CoreDisplay.framework/Versions/A/XPCServices/CoreDisplayXPCService.xpc/Contents/MacOS/CoreDisplayXPCService`.
Their metadata was read with `xcrun dwarfdump --uuid`, `shasum -a 256` and
`xcrun otool -L` using those exact paths. The XPC bundle's adjacent
`Contents/Info.plist` was parsed with `plutil -p`; no executable was launched.

## Host Display Object Model

`VERIFIED` static identity path: `DCPAVProxy::start(IOService*)` at
`0xfffffe000a019478` stores the matched endpoint in `self+184`, reads the
provider property `EPICUnit`, and stores its 32-bit value at `self+236`
(`0xfffffe000a0197c8`). `getUnit()` at `0xfffffe000a00a4bc` reads that scalar.
The corresponding bundle personalities match `AFKEndpointInterface` by
`EPICName`: `dcpdp-controller-epic`, `dcpdp-device-epic`,
`dcpdp-service-epic`, `dcpav-video-interface-epic` and `dcpdptx-port-epic`.
Those are service identities, not demonstrated independent scanout sources.
The endpoint pointer, unit and location remain separate fields; one proxy
does not by itself prove one physical transmitter or one logical source.

`DCPDPDeviceProxy::start(IOService*)` at `0xfffffe000a022338` retrieves
device-matching data and publishes identity/OUI properties.
`getDeviceMatchingData(...)` at `0xfffffe000a02280c` is a message-based getter
for device IDs and OUIs, not a source-construction contract. Matching an
advertised endpoint creates a host IOService proxy; no command in this path
has yet been established to allocate another firmware source for an existing
physical DPTX.

Receipts: [proxy inventory](../../artifacts/probes/m5p2/proxy-inventory.json),
[proxy functions](../../artifacts/probes/m5p2/proxy-functions.json).
All addresses are unslid host Mach-O virtual addresses, not firmware addresses.

The proxy starts receive a provider, not an established `(physical DPTX,
logical source index)` pair. Host construction per advertised service is
`STRONG`; construction per independently timed source is `UNKNOWN`. The
current bundle has explicit `display-crossbar,t8142` and `atc-dpxbar,t8142`
matches, but matching metadata is not a fresh active-object observation.
No host definition is qualified in these paths for the requested names known
from the frozen firmware baseline: `DCPDPVirtualDevice`,
`AppleDCPDPTXController` or `AppleDCPDPTXNub`. This is not a claim that no such
host name exists anywhere.

CoreDisplay's `CoreDisplay_CreateDisplayForCGXDisplayDevice` at `0x182f85008`
looks up a map keyed by the supplied `CGXDisplayDevice*`, allocates a 1,152-byte
record on the absent-key path, and stores the supplied pointer at record
`+104`. Its named hash-table specialization holds
`unique_ptr<CoreDisplay::Display>`. This is a new host wrapper for an existing
display identity, not proof of creation of a new hardware scanout source.
Full map removal/destruction and underlying source ownership remain unclosed.

## DCPDPVirtualDevice

Keep three concepts separate: the frozen firmware class name
`DCPDPVirtualDevice`, host IOAV/DisplayPort virtual-device or virtual-EDID mode,
and CoreDisplay/IOMobileFramebuffer virtual-display interfaces. No equivalence
between those concepts follows from their names. Host virtual-device mode is
qualified using its own callers and data flow; no new firmware body is
opened to infer the missing relationship.

**VIRTUAL_DEVICE_ROLE_UNRESOLVED**, specifically for the requested
`DCPDPVirtualDevice` source role. The following host controls do not resolve it:

| Host object/control | Concrete evidence | Role and limit |
| --- | --- | --- |
| `IODPVirtualDevice::device(unsigned int,unsigned char,bool,bool,bool,IOAVDSCVersion,bool)`, `0xfffffe000a7f514c`, 868 bytes | Allocates a 1,400-byte host object, calls its initializer and repeatedly calls its local `_writeDPCD` with capability addresses/values | STRONG emulated DP-device/capability model; no physical-owner parameter or independent-source binding established |
| `IODPVirtualDevice::init`, `0xfffffe000a7d4cfc`; `_readDPCD`, `0xfffffe000a7d4df0`; `_writeDPCD`, `0xfffffe000a7d4af0` | Storage reference at `+1368`; address formatted into a local key and looked up/updated through that storage | Device register/capability emulation, not a source-context collection; no live DPCD read/write executed |
| `IODPVirtualDevice::free`, `0xfffffe000a7d4d58` | Releases non-null references at `+1368` and `+1384`, clears them, delegates to base cleanup | Host-owned state lifetime; current M5 instantiation and full provider association UNKNOWN |
| `DCPAVControllerProxy::setVirtualDeviceMode(bool)`, `0xfffffe000a00b72c`, 148 bytes | Existing controller proxy sends an eight-byte zero-extended boolean argument at message `+80` | Mode toggle; no count, returned source object or same-owner coexistence contract |
| `DCPAVServiceProxy::setVirtualEDIDMode(bool,OSData*)`, `0xfffffe000a00f4d4`, 500 bytes | Mode byte at `+64`, length masked to 16 bits at `+80`, data at `+96`; not a large-input rejection check | EDID emulation/control, not an independently timed source allocation |
| `CGXVirtualDisplayCreate`, `0x182f7721c`, and `Destroy`, `0x182f7774c` | Invoke registered callbacks; null/failure paths retained | Higher-level virtual display lifetime, hardware backend unresolved |
| `IOMobileFramebufferInstallVirtualDisplay(s)`, `0x18f283600` / `0x18f283654` | Copy a callback table and contexts into globals; plural variant checks count <=12 | Backend registration, not proof of twelve hardware streams or a DPTX association |

The local host factory's 1,400-byte object is not identified with a frozen
firmware object by similar name or size. Multiple emulated devices, virtual
displays or EPIC services would still require a separate ownership/timing
contract before counting as independent source contexts. No such contract or
coexistence-versus-replacement rule was recovered for the requested object.

## Source Cardinality Parameters

The following are `VERIFIED` host parameter flows with `UNKNOWN` same-DPTX
source-count implications:

| Parameter | Exact host use | What it does not establish |
| --- | --- | --- |
| `EPICUnit` | Provider property -> proxy `+236` -> `getUnit()` | Not an independently allocated source index |
| `IOAVLinkSource` | Low byte of argument `w2` serialized by link/timing methods | Enum name alone does not establish more than one independent source |
| `set_display_device(unsigned)` | One 32-bit argument in the existing framebuffer RPC | Not a source-construction request |
| `set_digital_out_mode(unsigned,unsigned)` | Two 32-bit arguments in the existing framebuffer RPC | Mode/device selection is not simultaneous multi-source allocation |
| `IODPTXPortAttributes` | One packed 64-bit value serialized by remote-port `connectTo` | Port address and routing attributes are not a stream/payload binding |

`IOAVLinkSourceString` at `0xfffffe000a5ad2f0` accepts values 0..4 for formatting.
Five chain-verified slots at `0xfffffe00083cdf18` through
`0xfffffe00083cdf38` resolve respectively to **Upstream, Intermediate,
Downstream, All, VFTG**. `All` alone prevents interpreting this list as five
independent hardware contexts. The formatter's bounds are not a source limit
or a validation contract for every API using the enum. `VFTG` is preserved as
the raw name; its role is not expanded speculatively.

`IOMobileFramebufferShim::set_display_device(unsigned)` at
`0xfffffe0009785fc4` first calls the AP implementation for itself. Conditional
paths call it on a scalar peer at `self+10760` and on eight-byte-stride entries
at `self+10768`, with byte count `self+10800`. This is concrete host peer-object
coordination, but neither the collection membership nor its flags proves that
the peers use the same physical DPTX. The same input value is forwarded to each;
this is not a distinct-source-ID allocator.

## Host-to-DCP RPC Construction

These layouts describe host message buffers before sending, with byte offsets
relative to their base. They are not captured transactions, decoded firmware
handlers, callable contracts or safety approvals.

| Producer | Serialized input | Boundary |
| --- | --- | --- |
| `DCPAVServiceProxy::startLink(IOAVLinkData*,IOAVLinkSource,unsigned)` at `0xfffffe000a010420` | 272 bytes from data pointer at `+64`; role byte at `+336`; unsigned argument at `+352` | Direct call to `DCPAVProxy::__sendMessage` |
| `DCPAVVideoInterfaceProxy::startLink(IOAVVideoLinkData*,IOAVLinkSource)` at `0xfffffe000a012e6c` | Optional 256-byte data copy at `+64`; role byte at `+320` | Direct call to the same sender |
| `DCPAVVideoInterfaceProxy::setTimingElement(unsigned long long,IOAVLinkSource)` at `0xfffffe000a0136f4` | Role byte at `+64`; 64-bit timing value at `+80` | Direct call to the same sender; no allocation returned |
| `AppleDCPDPTXRemotePortProxy::connectTo(IODPTXPortAttributes)` at `0xfffffe00090f4bd8` | Input bits 0..7 -> `+64`, 8..15 -> `+65`, 16..31 -> `+66`, 32..63 -> `+68` | One packed routing value, not two source bindings |
| `IOMobileFramebufferAP::set_display_device(unsigned)` at `0xfffffe000a98e7e0` | Four-byte input, four-byte output; immediate tag `0x41343131` (`A411` in big-endian character notation) | Host virtual sender slot `+2992`; firmware dispatch intentionally not inspected |
| `IOMobileFramebufferAP::set_digital_out_mode(unsigned,unsigned)` at `0xfffffe000a98e8b4` | Eight-byte input, four-byte output; tag `0x41343133` (`A413`) | Same host sender slot; not a new source factory |

Raw message constants, exact sender closure and unknown semantics remain
separately qualified in the final receipt inventory. The two AP tags are
numeric instruction constants; their little-endian register serialization is
`31313441` / `33313441`. No request is sent.

Receipts: [routing functions](../../artifacts/probes/m5p2/routing-functions.json),
[framebuffer functions](../../artifacts/probes/m5p2/framebuffer-functions.json).

The input blobs remain opaque beyond the proved copies/stores. A source ID
could exist in an unqualified field or another path; lack of an explicit
argument here is not an absence theorem.

`VERIFIED` DCPAV sending boundary: `__sendMessage` at `0xfffffe000a008e20`
computes total length as the u32 at `+8` plus 64. Its two blocks at
`0xfffffe000a009054` / `0xfffffe000a0090a4` use command value `0xc0` and the
existing endpoint reference at proxy `+184`, directly or through
`performCommandGated`. The unit is not thereby proved to be a source ID.

| Host producer | Raw eight bytes copied to message `+4` | u32 at `+4`; u32 length at `+8` | Destination personality |
| --- | --- | --- | --- |
| AV service `startLink` | `1600000040010000` at `0xfffffe0007825818` | `0x16`; 320 bytes | `dcpav-service-epic` |
| Video `startLink` | `0e00000020010000` at `0xfffffe00078258a8` | `0x0e`; 288 bytes | `dcpav-video-interface-epic` |
| Video `setTimingElement` | `1900000030000000` at `0xfffffe0007825900` | `0x19`; 48 bytes | `dcpav-video-interface-epic` |
| Remote-port `connectTo` | `0b00000020000000` at `0xfffffe00073f4a50` | `0x0b`; 32 bytes | `dcpdptx-port-epic` |
| Remote-port `validateConnection` | `0c00000030000000` at `0xfffffe00073f4a58` | `0x0c`; 48 bytes | `dcpdptx-port-epic` |

These method-local operation values are not globally unique opcodes. Each
producer also writes constant `0x69706378` at `+12` (raw `78637069`);
no extra semantic interpretation of that marker is needed.

`VERIFIED` framebuffer sending boundary, with a necessary base/override
distinction: the AP vtable slot at `0xfffffe00084e3b90` resolves to base
`IOMobileFramebufferAP::rpc` at `0xfffffe000a98c1d0`, which returns
`0xe00002c7`. That stub is **not** an architectural blocker. The shim's
corresponding chain-verified slot at `0xfffffe000814c500` resolves to
`UnifiedPipeline2::rpc` at `0xfffffe000977d00c`. It loads `self+9856`, and if
non-null forwards unchanged arguments to `DCPLink::rpc` at
`0xfffffe000a998a04`, setting its last boolean to false. `DCPLink` waits for
its service, uses service reference `+40`, and calls
`AppleDCPLinkService::rpc` at `0xfffffe000a992e4c`; the false-flag path wraps
the call with an existing callback. The service packages tag, input/output
pointers and lengths into `rpc_args_t` for the host `rpc_caller`.

Thus a real host command-production path is structurally present. The
receiver's firmware dispatch, mapping of that link object to a physical DPTX,
and any hidden source allocation are **UNKNOWN and not inspected**. Wait and
callback presence does not prove cancellation, safe termination or permission
to invoke the path. The retired selector transport is not revisited.

## Generic Multi-Display Path

CoreDisplay's existing-display wrapper map, SkyLight's per-display configuration
entries and the shim's peer-object fan-out demonstrate host support for
multiple logical records/targets. This is useful generic architecture evidence,
not yet an independently timed per-DPTX source model.

An important rejected lead is `FindDisplayPipeForService(unsigned)` at
`0x182f4d9bc` (1,336 bytes). Its local map keys are 32-bit service handles;
32-byte nodes store the key at `+16` and a 64-bit value at `+24`. Its call at
`0x182f4dab4` reaches authenticated stub `0x18302b2c8`; slot
`0x1ee4e8ae8` is chain-verified to `_IORegistryEntryGetRegistryEntryID` at
`0x184861fc8` in the current IOKit image. The result is a service/registry-ID
lookup, not demonstrated source creation or a physical DPTX identity, despite
the helper's name. CoreDisplay calls it at `0x182f85278`.

Two separate framebuffer objects or distinct Thunderbolt DP tunnels can
represent separate physical outputs. The current host tunnel-family name
inventory and historical separate-link role are controls only. They do not
show two sources sharing a transmitter. Construction before physical
assignment, independent timing ownership, and the point at which a logical
source is bound to one physical DPTX remain unclosed.

## Mirror / Clone Path

**MIRROR_SOURCE_MODEL_UNRESOLVED**.

`SLSConfigureDisplayMirrorOfDisplay` at `0x186eace48` validates configuration
capacity and canonical display IDs, rejects self-mirroring, and appends a
28-byte configuration record: display ID at `+0`, operation 3 at `+4`,
enable/nonzero-target state at `+8`, mirror target ID at `+12`.
`SLSConfigureDisplayIndependentOutput` at `0x186ebbeb0` similarly appends
operation 9 with the supplied value at `+8`. These are pending host
configuration records, not DCP source-construction messages.

`CGXLMirrorDisplays` at `0x182feda3c` (224 bytes) keeps both monitor pointers,
sets one mirror-parent ID from the other monitor's ID, traverses linked
`CGXMonitor` records to redirect matching parent IDs, updates flags at `+288`,
and calls `CorrectMirrors`. This establishes retained **monitor records**, not
retained independent source/timing-generator objects. No captured body binds
these records to simultaneous streams or proves the eventual source count.

The historical owner-reported duplicated hub image is not a current observation
and is not identified with this software mirror path. Single-source scanout,
multiple sources sharing content/timing, and downstream duplication remain
undistinguished for that topology. No display configuration was applied.

## Logical Display to DPTX Graph

The graph deliberately contains gaps. `VERIFIED` edges are static linkage,
call/value-flow or chained-pointer edges, not claims that the path executed.

| Edge | Confidence | Exact support / unresolved part |
| --- | --- | --- |
| WindowServer -> SkyLight | VERIFIED | Standalone executable declares the SkyLight dependency |
| SkyLight configuration -> current CoreDisplay display factory | UNKNOWN | Both implementations present; active dispatch between the selected paths not closed |
| `CGXDisplayDevice*` -> CoreDisplay `Display` wrapper | STRONG | Absent-key allocation and stored input pointer in `0x182f85008`; not a hardware-source factory |
| Display wrapper -> service/registry identity | VERIFIED | Call `0x182f85278`, helper and authenticated IOKit binding above |
| Logical display/mode object -> selected framebuffer handle/callback | UNKNOWN | Actual source/physical ownership and backend selection not established |
| Userspace framebuffer setters -> selected backend | VERIFIED | Existing-handle callbacks `+2728` / `+2736`; null-handle/callback rejection |
| Selected backend -> current shim/AP setter | UNKNOWN | No concrete userspace callback initialization/user-client selector closure recovered |
| Shim setter -> AP message producer | VERIFIED | Direct `set_display_device` calls; digital-mode gated block at `0xfffffe000978a494` |
| Shim RPC slot -> `UnifiedPipeline2` -> `DCPLink` -> `AppleDCPLinkService` | VERIFIED | Two kernel fixup slots, `self+9856`, direct forwarding and service `+40`; conditional on initialized objects |
| DCPAV device/service -> existing AFK endpoint | VERIFIED | Provider matching, pointer `+184`, command `0xc0` host blocks |
| Crossbar port allocation -> concrete remote-port proxy instance | INFERRED | Compatible host port abstractions and matching personalities; runtime instance/virtual call association not closed |
| Remote-port connection -> DCPAV message sender | VERIFIED | `0xfffffe00090f4ed4` directly targets `0xfffffe000a008e20`; one packed port-attributes value |
| Either host RPC service -> one physical DPTX -> independent logical sources | UNKNOWN | No same-owner identity/lifetime/timing contract; firmware boundary stays frozen |

These last unknowns must not be replaced by matching endpoint numbers, unit
numbers, registry IDs, port indices or class names across namespaces.

## Collection Cardinality

| Actual host owner / collection | Key, storage and operations | Qualified cardinality / physical relationship |
| --- | --- | --- |
| CoreDisplay display-wrapper map | Key `CGXDisplayDevice*`; `unique_ptr<Display>` values; find-before-allocation and insertion path in `0x182f85008`; full removal path not qualified | Multiple display records supported; source-owner relationship UNKNOWN |
| `FindDisplayPipeForService` cache | u32 service key, u64 registry ID, 32-byte nodes; insert/grow/rehash and cached lookup in `0x182f4d9bc` | Identity cache, not a collection of sources or timing engines |
| `CGSConfigData` | Count at `+8`, array pointer at `+16`, 28-byte entries; capacity check and append in mirror/independent-output functions | Per-display configuration commands; application/removal lifetime outside inspected bodies |
| `CGXMonitor` linked records | Next pointer `+0`, identity `+8`, mirror parent `+12`; mirror loop updates existing records | Monitor records remain distinct; source cardinality UNKNOWN |
| `DCPAVProxy` | Scalar endpoint `+184`, unit `+236`; initialized in start; free body at `0xfffffe000a009734` retained | One selected endpoint/unit per proxy, not a global source maximum; full service removal/coexistence contract UNKNOWN |
| Framebuffer shim peers | Scalar `+10760`; pointer entries at `+10768`, stride 8, count byte `+10800`; setter fan-out | Existing peer framebuffers, not proved same-DPTX sources; storage extent/active membership not inferred from field spacing |
| `IODPSwitchAllocationState` | Owner reference `+16`, raw array `+24`, count `+32`, four-byte records keyed by packed port address; `withCapacity` at `0xfffffe000a7e3778` | Port-address routing state, not a source/payload table or a resolved physical DPTX identity |
| Same switch state, mutation | `connect(port,peer)` at `0xfffffe000a7e528c` bounds-checks an address-derived index, overwrites one connection word; null peer clears local/peer state | One selected connection record per indexed address in this abstraction; not a one-stream silicon limit |
| Same switch state, lookup/iteration/free | `getConnectionState(address)` at `0xfffffe000a7b0f90`; `iterateConnectionStates` at `0xfffffe000a7b00d8` filters valid/type bits and stops on callback result; `free` at `0xfffffe000a7b5094` releases backing owner | Capacity and active port membership are distinct; multiple sources within one port are not represented by this proved key |
| Host `IODPVirtualDevice` | Local keyed capability storage `+1368`; initializer, read/write helpers and free | Emulated device state, not a source collection |
| IOMobileFramebuffer virtual registration | One callback table plus context array and count <=12 | Software backend registration; not twelve DPTX sources |

No collection above is qualified as independent source contexts grouped by one
physical DPTX. No complete all-alias/all-subclass cardinality proof is claimed.

## Same-DPTX Binding

**HOST_STREAM_CONTROL_PATH_UNRESOLVED**.

The decisive requirement is not merely two host objects, but two independently
identifiable logical sources that can coexist under the **same** physical
transmitter, with distinct timing/scanout state or an explicit source-space
contract. The inspected host constructors, dictionaries, role enum, setters
and connection records do not establish that relationship. The opaque copied
link data, unclosed backend callback selection and service-to-physical-owner
mapping prevent either a positive same-link result or a global negative.

This preserves the frozen opacity: **runtime source-controller membership of
one physical T8142 DPTX register owner**. The new host route did not resolve it;
it did not reopen the firmware investigation to force an answer. A future
qualified host contract could resolve it without new packetizer disassembly.

## Policy / Feature Guards

| Owner/function | Exact condition and branches | Evidence quality | Would changing it suffice? |
| --- | --- | --- | --- |
| T8142 Crossbar `handleStart`, `0xfffffe0009188fb8` | Provider `supports-aux-only` low bit -> `self+368`; present `appledptx-no-aux-only` boot argument replaces it with `(value == 0)` | VERIFIED raw property strings at `0xfffffe000740c061` / `0xfffffe000740c073` and stores | No: controls AUX-only route eligibility, not an MST source allocator; no boot argument changed |
| T8142 `isUFPAvailable`, `0xfffffe000916ca40`, and selection, `0xfffffe000916c820` | A candidate-port virtual predicate plus `+368` bit can reject/permit fallback; delegated availability checks remain; fallback returns one candidate pointer | VERIFIED local conditions; predicate/active port interpretation only partially closed | At most a prerequisite for that route; no same-link source sufficiency |
| Crossbar `reachedDispCountLimit`, `0xfffffe0009183714` | Threshold `self+364 == 0` returns false; otherwise a callback counts candidates and comparison `count >= threshold` returns true | VERIFIED comparison; current runtime threshold and complete count membership UNKNOWN | No: generic allocation limit, not a proved MST policy prohibition; changing it would not create timing/source ownership |
| Switch `connect` / `getConnectionState` | Derived port index >= `self+32`, or null storage, rejects; valid index updates/looks up a four-byte record | VERIFIED | Necessary storage/address validity only; not an MST feature gate |
| SkyLight mirror config, `0x186eace48` | Valid capacity and canonical display IDs required; equal source/target IDs rejected | VERIFIED | Generic configuration correctness, not same-DPTX multi-stream policy |
| IOMobileFramebuffer virtual registration, `0x18f283654` | Context count >12 returns `0xe00002c2`; otherwise copies registration state | VERIFIED | Software backend bound, not a hardware display limit |
| AP base RPC, `0xfffffe000a98c1d0` | Unconditional `0xe00002c7`; overridden in shim by chain-verified `UnifiedPipeline2::rpc` | VERIFIED rejected blocker hypothesis | Patching base stub is neither indicated nor sufficient |

No `supportsMST`, branch/tunnel/SoC check or mirror fallback in the inspected
controlling bodies is qualified as the gate that prohibits an otherwise proved
same-DPTX multi-source mechanism. This is not an exhaustive absence claim.
No macOS binary, feature flag, boot argument or security policy was patched.

## Mechanism vs Policy

Mechanism: **HOST_MECHANISM_UNRESOLVED**, scoped to more than one independent
source under one physical DPTX. Generic host display creation/configuration and
message-production mechanisms are positively present; do not restate this as
"macOS has no multi-display machinery."

Policy: **MST_POLICY_GATE_UNRESOLVED**. The concrete guards above govern
configuration validity, physical allocation and AUX-only eligibility. None is
shown to be the last policy obstacle in front of a complete same-link mechanism.
Neither uncertainty nor a base-class unsupported return is a new architectural
blocker, and no policy-patch research route is justified by this evidence.

## Static API Candidates

All entries are **STATIC_API_CANDIDATE**, never `SAFE_TO_CALL`. They are concrete
controls considered during discovery, not a recommendation to invoke them.

| Candidate / image / ABI | Creation or binding inputs | Validation, lifetime and effects | Qualification gap |
| --- | --- | --- | --- |
| DCPAV video `setTimingElement`, `0xfffffe000a0136f4`; C++ `this`, u64 timing, `IOAVLinkSource` | Existing proxy plus one timing value and role | Message construction/send/result; proxy is already initialized; expected timing state change | No independent source or physical-owner argument proved; cancellation/authorization/safety unqualified |
| DCPAV controller `setVirtualDeviceMode`, `0xfffffe000a00b72c`; C++ `this`, bool | Existing controller, one boolean | Sends mode change; no returned object/count; cleanup/firmware side effects unresolved | No coexistence or source-construction contract |
| Framebuffer AP `set_display_device` / `set_digital_out_mode`, `0xfffffe000a98e7e0` / `0xfffffe000a98e8b4`; u32 / two u32 | Existing framebuffer/link; A411/A413 payloads | Concrete host override path; DCPLink waits for existing service; peer calls can fan out; source creation not established | Userspace setters are callbacks, actual user-client selector and runtime physical binding UNKNOWN; no selectors invoked |
| Remote-port `connectTo`, `0xfffffe00090f4bd8`; C++ `this`, packed `IODPTXPortAttributes` | Existing proxy, one packed port route | `validateConnection` is a separate 0x0c request; connect is 0x0b and may alter routing | No logical-source/timing/payload binding tuple; call/rollback/termination safety UNKNOWN |

The host `IODPVirtualDevice` factory and CoreDisplay virtual registration are
nonqualifying emulation/backend leads, not alternative hardware-source APIs.
No concrete candidate currently satisfies the same-owner creation/binding bar
for designing a host-control hardware experiment. Selector 0 stays retired;
no helper, including a historical no-open mode, was run.

## Observer Schema Impact

**OFFLINE_OBSERVER_PIPELINE_READY** remains. Frozen schema v1, the entire
M5P1 consumer/evaluator, golden fixtures and human-only handoff are unchanged.
No version bump, invented source-ID field or fixture relabeling is needed.

Existing `raw_payload`, `decoded_fields`, provenance annotations and unknown
extension preservation can retain externally captured host bytes and later
reviewed decoding. The raw EPIC unit, IORegistry ID, link-role value, physical
port address, request tag and object lifetime must remain separate concepts.
They must not be normalized into `source_context` merely because they differ.
These static receipts are not live observer records or real A-E gate passes.
The 31-fixture manifest remains
`52d9a04fabc5d192c494e098720399f4cb144da0fe70c1e8422856a723bb8b8a`;
all positive pipeline gate examples remain synthetic, with zero real passes.

## Strategic Outcome

**RUNTIME_OBSERVER_STILL_REQUIRED** is the single selected outcome.

M5P2 adds useful host evidence: actual service matching and scalar identity,
role semantics, local virtual-device emulation, explicit RPC layouts and
override resolution, monitor-level mirror state, and physical connection
collections. It neither proves a same-link multi-source mechanism nor an
architectural prohibition. The initial hypothesis is supported within the
selected proxy path: provider/service identity is established, independent
source identity is not. Other paths and opaque fields remain open.

The next qualifying evidence must tie independent source/timing identities
and overlapping lifetimes to **one** physical DPTX, through an independently
validated observer or a new explicit host ownership contract. The prior
observer-platform limitations are not solved here. No target experiment,
purchase promotion, macOS policy patch, firmware restart or sibling platform
work follows automatically. A future milestone requires its own authorization.

### Reproduction And Evidence Limits

The independent [host receipt tool](../../tools/host_stream_control.py) reuses
only the file-reader/boundary helpers from the existing kernel/cache tools.
It never calls the old MST scanner entry point, loads a protocol oracle,
collects display state or accepts a firmware input. Each JSON receipt retains
exact arguments, current OS metadata, reader hashes, section hashes, declared
function ranges, full raw instruction bytes, direct calls/callers and selected
literal xrefs. Pointer receipts require actual kernel/cache chain membership.
The checked bounds are 16 selected images, 48 functions (32 KiB each), 128
pointer slots and 32 explicit data ranges (256 bytes each) per invocation.
Output must be a new file under the M5P2 artifact root.

All 22 receipts are local-only, under
[artifacts/probes/m5p2](../../artifacts/probes/m5p2); original Apple binaries
are not vendored. Key whole-receipt SHA-256 values are:

| Receipt | SHA-256 |
| --- | --- |
| [host-metadata.json](../../artifacts/probes/m5p2/host-metadata.json) | `0ddd8c48b4796c08af7655e8d75a31f9fa2a89ad512b95a4501bd4d2b4a6239a` |
| [proxy-functions.json](../../artifacts/probes/m5p2/proxy-functions.json) | `8df8a458158f920728cbcda4e700f01ca30c3b153a7f1dcbfc867daf3ff4f95e` |
| [virtual-functions.json](../../artifacts/probes/m5p2/virtual-functions.json) | `950ab1a71ffcdc8622b9cf5e7dddeeaeb1aba5fbc73556d1fb8f65da05a441ea` |
| [routing-functions.json](../../artifacts/probes/m5p2/routing-functions.json) | `093f6d82124fdf06cf61af86423a99df5be6473edf8e07d257fd0855deffb114` |
| [connection-state.json](../../artifacts/probes/m5p2/connection-state.json) | `4822643a3296c54a91cb985c935676b91736eaa188e8f9bdfb8deea11d8c9233` |
| [rpc-constants.json](../../artifacts/probes/m5p2/rpc-constants.json) | `3eec4c465e5b8277995cac86a1672711074d42a92ad01034efdf5efc7e19ae08` |
| [role-and-binding-pointers.json](../../artifacts/probes/m5p2/role-and-binding-pointers.json) | `6d4e7837c903868a485167cf064bf731a0d63a2e3caedf9b9dcaa5eebc34baa5` |
| [framebuffer-functions.json](../../artifacts/probes/m5p2/framebuffer-functions.json) | `9809038cf6107f06024b0c1b18da4012472033cea95acc336cbbe0e69db2dab2` |
| [shim-rpc-override.json](../../artifacts/probes/m5p2/shim-rpc-override.json) | `edc959aa6bb130f5b244950037edfbe9c811417a54a6fcd6f58b8821a4fb3213` |
| [dcp-link-rpc.json](../../artifacts/probes/m5p2/dcp-link-rpc.json) | `0b834fdb81919ce39658725f867d66d509f16322b72871843152ad3a2db29bb8` |
| [userspace-functions.json](../../artifacts/probes/m5p2/userspace-functions.json) | `4b7c0c01e3d5e1bfabe50d91fa86ea8ee3ecdca7da2b4b0f9f00d6fcf0403b3d` |
| [service-id-binding.json](../../artifacts/probes/m5p2/service-id-binding.json) | `8e6f1162fc2b1edcde5d0817972a9414dbf85ae7d634947111aaa1a09b6312a0` |

Reproduce a decisive host slice without invoking any inspected function:

```sh
python3 tools/host_stream_control.py --inventory \
	--kernel-image com.apple.driver.DCPDPFamilyProxy \
	--kernel-image com.apple.driver.DCPAVFamilyProxy \
	--kernel-image com.apple.iokit.IOAVFamily \
	--symbols 'DCPDP|DCPAVProxy|IOAVLinkSourceString' --strings 'EPICUnit' \
	--function 0xfffffe000a019478 --function 0xfffffe000a00a4bc \
	--function 0xfffffe000a0136f4 --function 0xfffffe000a5ad2f0 \
	--pointer 0xfffffe00083cdf18 --pointer 0xfffffe00083cdf20 \
	--pointer 0xfffffe00083cdf28 --pointer 0xfffffe00083cdf30 \
	--pointer 0xfffffe00083cdf38 \
	--data 0xfffffe0007825900:8 \
	--output artifacts/probes/m5p2/reproduce-proxy-role.json
```

Every other exact selection is preserved in its receipt's `arguments` object.
Re-running requires a new output name and the same 26.6.2/25G83 host inputs;
compare image/body/data hashes, not timestamps or whole newly generated JSON.
Raw whole-function retention is not full decompilation or an exhaustive caller
closure. Literal xrefs cover adjacent ADRP/ADD only; dynamic callbacks and
unselected-image callers remain open. The 6,952-byte digital-mode function is
retained, but only its stated local/gated paths are interpreted. One instruction
at `0x182f4d9f8` in the identity-cache helper remains `UNDECODED`; no claim
depends on guessing it or declaring complete control-flow coverage.

### Verification

The strict 16-action MacMST build passes under AppleClang 21.0.0.21000101.
Offline CTest is 2/2: 124 unchanged observer tests and 12 new synthetic host
receipt tests. An explicit allowlist of 24 existing synthetic kernel/cache/
callgraph parser tests also passes; no firmware test method or live collector
is executed. Python byte compilation and changed-file editor checks pass.
No produced native executable is run.

```sh
python3 -X dev -W error -m unittest discover -s tests -p test_host_stream_control.py
python3 -X dev -W error -m unittest discover -s tests -p 'test_dcp_trace*.py'
python3 -m py_compile tools/host_stream_control.py tests/test_host_stream_control.py
cmake -S . -B build-m5p2-offline -G Ninja -DCMAKE_BUILD_TYPE=Debug \
	-DMACMST_ENABLE_HARDWARE_TESTS=OFF -DMACMST_ENABLE_DPDV_OPEN_EXPERIMENT=OFF
cmake --build build-m5p2-offline
ctest --test-dir build-m5p2-offline -L offline --output-on-failure
```

A metadata serialization check initially rejected binary plist data. The
reader now preserves typed raw hex, serializes before opening its destination,
and has a regression test; the same focused check and acquisition then passed.
The failed new partial receipt was removed, not treated as evidence. No
historical capture was removed or overwritten.

## Safety / Hardware State

**USB_C_HUB_CONNECTION_NOT_REQUIRED**. Keep the hub and both monitors unplugged.
M5P2 used only current host file/metadata reads, offline parsing and disassembly,
synthetic tests and compilation. Git publication is restricted to the research
branch below. There was no IORegistry display capture, live display-framework/user-client
call, private selector, AUX/DPCD transaction, DCP request, mirror/mode transition,
debugger attachment, boot/DFU operation, macOS patch or security change.
No m1n1 sibling access or delegated platform work occurred.

Preserve **RETIRED_ON_DAILY_USE_M5**, **NOT_READY_FOR_DPCD_TEST**,
**STATIC_PACKETIZER_ANALYSIS_FROZEN** and
**NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED**. The consumed
M2F marker and both retained receipts remain unchanged; the M2G DPCD-read
attempt marker remains absent. All historical M3A-M4Q/resume reports and the
entire current M5P1 self-enable/schema/handoff content are preserved.

Platform readiness remains **M5_OBSERVER_CODE_NOT_READY_FOR_TARGET_TEST**;
purchase remains **SACRIFICIAL_M5_STILL_PREMATURE**. Nothing in compilation,
static host API presence or synthetic evaluation demonstrates working MST on
real hardware. The publication target is only `research/m5-host-stream-control`
from the exact M5P1 baseline: no merge, PR, old branch update or tag change.