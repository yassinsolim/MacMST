# M3A: Apple M5 MST Source Feasibility

## Scope And Retirement

The question is whether the current M5 display stack contains source-side
DisplayPort MST machinery, not whether the attached hub advertises MST.
Selector 0 is **RETIRED_ON_DAILY_USE_M5**. Its investigation is not reopened,
wrapped, improved or executed. **NOT_READY_FOR_DPCD_TEST** remains in force.
The consumed M2F marker stays intact and the DPCD read-attempt marker stays absent.

This milestone permits static analysis and public read-only observation only.
No DPDV open, IOConnect method, IODP API, IOI2C/AUX/DPCD/sideband transaction,
mode change, link training, payload allocation or display reconfiguration is run.
No firmware or security setting is changed. Multiple controllers, displays or
Thunderbolt tunnels alone do not establish MST on one physical DisplayPort link.

## Integration And Retirement Tag

The starting research/w06-wake-or-strand branch was clean at
`b18ffd118f405ee7f91ce630a140086818ff4649`, equal to upstream. Both M2I commits,
six changed UTF-8 blobs and five documentation paths were audited. Main was
`1a014d8d3c3cd35ed5381160b809cf4803d79d69`. Historical refs, the consumed M2F
marker and both M2F result receipts matched; the read marker was absent.

M2I was merged --no-ff as `a882c1dc75501c03347050f1cdb91c38df2af39d`, message
`merge: retire unresolved selector-0 DPCD transport`. Parents are
`1a014d8d3c3cd35ed5381160b809cf4803d79d69` and
`b18ffd118f405ee7f91ce630a140086818ff4649`; the merge tree equals M2I. Main was
pushed, followed by annotated tag `selector0-retired-v0.6`, object
`55b7f703fe11b396e6b159d76fcc84cc31ec6b6d`, peeling to the merge. Its message is
`MacMST selector-0 transport retired on daily-use M5 after unresolved W06 wake and callback-quiescence proof.`
Both remote identities were verified before creating
research/m5-mst-source-feasibility from that tagged merge. Historical branches
and tags remain unchanged.

The host identity check at 2026-09-14T01:49:57Z reported macOS 26.6.2 (25G83),
kernel UUID `447D769E-1CB7-3086-A0B4-32226837B587`, unchanged from the M5 baseline.
The observed UTC time, rather than the earlier prompt date, timestamps this work.

## Evidence Rubric: Defined Before Apple Search

Strong evidence requires a DisplayPort-attributed implementation or control
surface, with an exact owning image, function and data-flow context. Candidates:

- Explicit MST terms that resolve to DP-specific behavior, not an unrelated acronym.
- Code using MST-specific register/window clusters as DP addresses, not offsets.
- Sideband header/CRC/opcode processing connected to MST message transport.
- Branch GUID plus route-address/port topology tied to a DP source link.
- PBN, VCPI/payload IDs, slot tables and payload-update/ACT state transitions.
- Multiple independent timing/stream encoders mapped to payload IDs on one link.

Literal hits and constant hits are discovery leads, not conclusions. A name can
establish a named control concept without proving its body, firmware execution or
M5 packetizer. A negative bounded search is not a silicon-absence theorem.

Weak evidence includes generic stream/payload/bandwidth terminology, DSC slices,
framebuffer/display-pipe allocation, multiple DP ports/controllers and independent
Thunderbolt DP tunnels. These are explicit negative controls. ACT must be a DP
payload activation sequence, not a substring of action/active; PBN/RAD must be
protocol fields, not arbitrary symbols or small integers.

Confidence labels are VERIFIED_ON_CURRENT_M5_STACK (observed current component
identity or public fact), STRONG_STATIC_EVIDENCE, WEAK_STATIC_EVIDENCE,
NEGATIVE_SEARCH_RESULT and UNKNOWN. Static presence in a current image is not
proof its MST code is used by the selected M5 endpoint. Implementation evidence
requires both MST protocol/control machinery and one-link stream-to-payload
packetization. Host controls alone leave the packetizer unresolved; opaque or
incomplete firmware can prevent a meaningful complete-stack classification.

## Pinned Linux Protocol Oracle

Current torvalds/linux HEAD was pinned before Apple scanning as
`704340f1cd0dcef829eb62f5b48ae95a2ce17bdf`. Retained files under ignored
artifacts/sources/m3a/linux are drm_dp.h, drm_dp_mst_helper.h,
drm_dp_mst_topology.c, drm_dp_helper.c and i915/display/intel_dp_mst.c.
They are source evidence only, not compiled or executed. Existing v6.12
`adc218676eef25575469234709c2d87185ca223a` remains the historical comparison.

Initial exact constants from current
[drm_dp.h](https://github.com/torvalds/linux/blob/704340f1cd0dcef829eb62f5b48ae95a2ce17bdf/include/drm/display/drm_dp.h):

| Concept | Register / Value | Discriminator |
| --- | --- | --- |
| MST capability | DP_MSTM_CAP=0x021, DP_MST_CAP=bit 0 | Receiver capability, not source packetizer evidence by itself |
| Branch GUID | DP_GUID=0x030 | Needs GUID-sized/routing/topology context |
| MST control | DP_MSTM_CTRL=0x111; MST_EN=bit 0, UP_REQ_EN=bit 1, UPSTREAM_IS_SRC=bit 2 | Source enabling/sideband role, stronger when connected to topology |
| Payload allocation | DP_PAYLOAD_ALLOCATE_SET=0x1c0, START_TIME_SLOT=0x1c1, TIME_SLOT_COUNT=0x1c2 | Adjacent ID/start/count operations, not one isolated integer |
| Payload/ACT status | DP_PAYLOAD_TABLE_UPDATE_STATUS=0x2c0; TABLE_UPDATED=bit 0, ACT_HANDLED=bit 1 | Requires update/activation/poll ordering |
| Sideband windows | DOWN_REQ=0x1000, UP_REP=0x1200, DOWN_REP=0x1400, UP_REQ=0x1600 | Cluster plus DP access/header/CRC behavior |
| Topology requests | LINK_ADDRESS=0x01, CONNECTION_STATUS_NOTIFY=0x02, ENUM_PATH_RESOURCES=0x10 | Small opcodes need packet-format context |
| Payload requests | ALLOCATE_PAYLOAD=0x11, QUERY_PAYLOAD=0x12, RESOURCE_STATUS_NOTIFY=0x13, CLEAR_PAYLOAD_ID_TABLE=0x14 | Cluster and PBN/payload association |
| Remote operations | REMOTE_DPCD_READ/WRITE=0x20/0x21, REMOTE_I2C_READ/WRITE=0x22/0x23 | Sideband routing required; generic local DPCD is not remote MST access |
| Negative controls | DP_DSC_SUPPORT=0x060; DP_SINK_COUNT=0x200 | DSC or sink count alone does not establish MST |

The local falsifiable hypothesis is that a scoped function-level scan can
distinguish MST-specific control/codec/payload evidence from generic display and
IPC terms using these combinations and their source-backed state transitions.
The cheap discriminating checks are a positive signature fixture and unrelated
small-integer/string controls, followed by inspection of candidate argument flow.
An unqualified single constant or broad string hit must fail that evidence test.

## Canonical Signature Set

The machine-readable oracle is
[mst-source-signatures.json](mst-source-signatures.json): 29 register addresses,
12 message opcodes, seven multi-constant groups and three literal-pattern families.
All numeric registers/opcodes/masks were checked against the pinned header. Names
include mangled/CamelCase variants; PMstop and link-address linker callbacks are
deliberate false-positive cases, not reasons to assume exact Linux spelling.

| Signature | Source-Backed Shape / Transition | False-Positive Rule |
| --- | --- | --- |
| Sideband header | Wire size 3+floor(LCT/2); LCT/LCR nibbles, RAD storage 8 bytes; broadcast/path bits 7/6, length mask 0x3f, SOMT/EOMT bits 7/6, sequence bit 4 | These are wire/storage sizes, not an assumed Apple sizeof(struct) |
| Header/body integrity | Header CRC feedback 0x13/top bit 0x10, four bits; body feedback 0xd5/top bit 0x100, eight bits | The Linux function named drm_dp_msg_data_crc4 actually returns an eight-bit body remainder; a polynomial alone is insufficient |
| Reassembly | 48-byte chunk and 256-byte reassembly storage, SOMT/EOMT/sequence transitions, request-ID mask 0x7f | Generic IPC fragmentation is not MST unless tied to its header/opcodes/windows |
| Topology | 16-byte GUID, RAD nibble route/LCT, parent port and port list, input/output and downstream state, path PBN, remote EDID context | Branch ID/OUI or a single branch boolean is not this hierarchy |
| Remote DPCD/I2C | Port nibble plus 20-bit DPCD address/count; routed I2C transaction list, device/count/data | Generic local DPCD or local I2C primitives do not establish remote sideband access |
| Payload | VCPI mask 0x7f, big-endian 16-bit PBN, starting slot/count, SDP stream-sink nibbles | Encryption stream IDs and DSC slices are not virtual-channel payload assignment |
| PBN/slots | PBN unit 54/64 Mbytes/s; current mode formula includes 64/54 and DRM MST/SSC overhead; 8b/10b uses 63 slots starting at 1, 128b/132b uses 64 starting at 0 | Link rate times lane count or generic memory bandwidth is not PBN without stream/slot context |
| Payload activation | Three-byte ID/start/count write at 0x1c0; table-updated status at 0x2c0; source ACT emission/sent status; branch ACT-handled bit | A branch table write is not proof the source packetizer can multiplex streams |
| Source stream binding | i915 stream encoders share a primary physical DP port, allocate per-stream payload state, program source transcoder payload allocation, emit ACT and complete the branch assignment | Two physical links/tunnels or multiple display pipes alone do not meet this test |

The oracle's source files and hashes are pinned at revision
704340f1cd0dcef829eb62f5b48ae95a2ce17bdf, not floating HEAD:

| Linux File | SHA-256 |
| --- | --- |
| include/drm/display/drm_dp.h | `7f7958ee96e2dcd2329ef53422b1801eb2ba0a2f47febdc42cfb808a45754c5f` |
| include/drm/display/drm_dp_mst_helper.h | `d0f4dda7b717db766c494e0ec63d72c65291a09c12ede6ec759659c67821f44c` |
| drivers/gpu/drm/display/drm_dp_mst_topology.c | `9d09eca1a83d53fc2a45c8313e10513b88bef0dbd7a805fa359c859e16831139` |
| drivers/gpu/drm/display/drm_dp_helper.c | `e9f9869b034230c39766a1237ad7b96b3d88e8f3e8c5b315189a2a855ce7d155` |
| drivers/gpu/drm/i915/display/intel_dp_mst.c | `54d868be670bd6c6342d7f875991d28553c5d559792cd84f45f2a3b2cbae2446` |

The v6.12 comparison header SHA-256 remains
`70ea7e2c08c2155450f998d30d53e147070443168f616f06584b671e2b37dfd2`.
Linux implementations and retry/activation routines are protocol evidence only;
none was compiled, imported as an Apple transport, or executed.

## Current M5 Display Stack And Search Coverage

Metadata inventory contained 373 kernel fileset images and 3649 cached userspace
images. The scan selected 13 kernel and 11 userspace images, not all graphics code.
The public DisplayPort transport-state class supplied the reason to include
IOAccessoryManager; SkyLight/CoreBrightness close the adjacent display-policy
scope. Audio AVB, unrelated GPU/media and iOSSupport compatibility images were
not treated as the M5 external DisplayPort implementation.

Kernel source K is the running-UUID-matched collection, container SHA-256
`b20d50fc8f445a5c578ac63bd974efeb6ae48a97116800301071891795fb26d9`, decoded SHA-256
`f516560c295e10d62c3d219237d23c5900664107b2115dad590eaa259516d05f`. The scan's
per-image UUID, header, exact selected sections, section hashes and function-start
hash bind every candidate. Fileset presence does not establish execution of every
class variant on M5; classes for older chips in a shared image remain distinct.

| K Bundle | Binary UUID | Evidence-Supported Responsibility / Scope |
| --- | --- | --- |
| com.apple.driver.DCPDPFamilyProxy | 7732A096-166C-312F-8AEB-BF0DED28C5C3 | Current DCPDPDeviceProxy/ServiceProxy objects and branch device identity; generic DP RPC surface, not MST proof |
| com.apple.driver.DCPAVFamilyProxy | 9CA0BBA6-98A5-3CAB-8D7A-9EB2D79C9D08 | DCPAVServiceProxy/VideoInterfaceProxy link and timing messages |
| com.apple.iokit.IODisplayPortFamily | 21AA8D3B-3EE1-3812-9D20-BB3B5A0B79DB | IODPDevice capabilities/link/DSC controls, port/service objects and stream SDP/MSA construction |
| com.apple.iokit.IOAVFamily | 6E4B9D42-04A2-393A-B1F5-F121B8D00954 | AV timing, EDID/CEA and audio/video metadata; negative controls |
| com.apple.driver.AppleDCPDPTXProxy | B88B6C2C-8CF9-317B-94CE-D9DF5809ABB0 | Current remote-port proxies; DCP message link-rate forwarding |
| com.apple.driver.AppleDCP | 4E81DEE6-C09C-35F7-AFEC-50A982E1EEFC | DCP controller host image; no qualified MST implementation hit |
| com.apple.driver.AppleMobileDispH17G-DCP | 6D81BA37-15A7-38E5-9984-8C9F3ADEEDE5 | Public IOMobileFramebufferShim class owner, superclass UnifiedPipeline2; multiple instances are not one-link MST |
| com.apple.iokit.IOMobileGraphicsFamily-DCP | 98ECE2F0-AB94-39FA-A02D-76AD313A3161 | Adjacent display pipeline host image; no qualified MST hit |
| com.apple.driver.AppleDisplayCrossbar | 5A00089D-B7A4-3280-BE13-5D1118134A02 | Physical/logical DP port routing and display allocation, not a proved VCPI allocator |
| com.apple.driver.AppleThunderboltDPAdapterFamily | 089C0EDD-F9E2-32E2-B3AD-F5040D3801F3 | DP adapter/link-bandwidth negative control |
| com.apple.driver.AppleThunderboltDPInAdapter | EE032191-DE12-3C38-A7C5-FC2EFE2B4D4B | Thunderbolt DP input adapter, distinct from an MST stream encoder |
| com.apple.driver.AppleThunderboltDPOutAdapter | 522E0AB5-C86E-381B-9659-2E9E081AA726 | DP tunnel construction negative control |
| com.apple.iokit.IOAccessoryManager | 000C7572-462F-3393-8B18-4E4201512BC7 | Public IOPortTransportStateDisplayPort owner; tunneled transport-state collection |

Userspace source U is the current arm64e dyld cache. Image-table/component UUIDs
and header hashes are retained; each image has an exact scanned-section digest,
not a claimed full-cache-file hash. The selected cached Mach-O UUID is checked
against the cache image table before scanning. Dylib/class presence is not a
claim every candidate is called by the active M5 display.

| U Image | Binary UUID | Scope |
| --- | --- | --- |
| CoreDisplay | D8E7E31A-7D3E-3742-A3EE-469C6237FAF4 | Display configuration/timing and virtual framebuffer controls |
| CoreGraphics | 38C8FBEC-DE88-33FE-B742-A192F22CC754 | Display-facing framework with graphics/image-format false-positive controls |
| IOKit | 12372585-DF92-33EF-B632-714FAA13260A | Public/private display symbols and shared AV formatting; no private call invoked |
| IOMobileFramebuffer | 2BC48182-F354-3AB0-8F18-0C60CAAFE398 | Userspace framebuffer/display metadata |
| DisplayServices | 0AE066F1-6087-3373-9CD4-8AED1AE7ECD4 | Adjacent display services |
| DisplayTransportServices | 2B145BB7-EE69-3D5C-A85C-61B45C0A9A71 | DTSDPDeviceDPCDInfo value object, including branch boolean/OUI/device ID |
| EXDisplayPipe | 3CF5134F-F923-3BDD-8F2D-D1F5C1B046B0 | Small adjacent display-pipe interface |
| libdpfu.dylib | B9E57F34-C7CA-3BBD-806C-4A8D0C67CB21 | Display firmware-update comparison only; never executed |
| libPS190Updater.dylib | 890D3A6A-FE7B-3D04-BA1F-B6EAE4D0071C | Branch identity/update comparison only; never executed |
| SkyLight | 0C8F41C6-6D93-3DB3-B522-CA8CFF5C3B33 | Display configuration/stream orchestration and debug/event negative controls |
| CoreBrightness | 1F873909-B3B8-3D55-9673-9AFA86BB085B | Adjacent display-policy control; color/sensor-format negative control |

Final scan totals: **62,740 declared functions** (17,752 kernel, 44,988 userspace),
**203 candidate functions**, **eight data-table candidates**, zero skipped
oversized functions and zero image parsing errors. The scan covers selected
__text, __cstring, __objc_methname/__objc_classname where present, __os_log and
__const sections. Its candidate receipts retain image UUID/digest, enclosing
declared function/hash, matched signature, raw immediate sites and initial
unqualified assessment. Literal/data addresses lacking a function are explicitly
data, not fabricated function starts.

Coverage is bounded: selected move-wide, compare and logical immediates; adjacent
ADRP+ADD literal references; aligned 32-bit payload/window table clusters within
64 bytes. Dynamic or indirectly loaded addresses, jump tables, split calculations,
some string encodings and firmware code can escape these signatures. Every
negative below is scoped to this search, not an exhaustive semantic decompilation.

## Qualified Literal And Symbol Findings

No DP-attributed MST/VCPI/PBN/sideband/ACT implementation name was established in
the selected host images. All stronger-looking name hits were disqualified:

| Hit / Location | Assessment |
| --- | --- |
| IOService::PMstop, imported at raw address 0 in kernel symbol tables | Power-management stop, substring Mst; undefined import, not an MST function at address zero |
| IOKit __OSKextLinkAddressCallback at 0x1848d83e8 and its data symbol | Kext linker load-address callback, not MST LINK_ADDRESS |
| BranchDeviceID / BranchIEEEOUI in DCPDP and IODP; BranchDeviceOUI in transport state | Device identity metadata. No associated GUID/RAD hierarchy, routed port list or PBN model was established |
| IODPPortService::setBranchID at 0xfffffe000a7d1d20 | Publishes branch string/OUI identity via a gated setter; not discovery of a branch graph |
| DTSDPDeviceDPCDInfo::isBranch at 0x2411c6e84; initWithInfo at 0x2411c692c | A boolean/value-object field alongside OUI/device/version information, not an MST topology manager |
| Crossbar DPTX_INACTIVE_ACK / DPRX_INACTIVE_ACK log strings | Physical port inactivity handshake, not DP payload ACT handling |
| AppleThunderboltDPOutAdapterCM "branching path in state evaluation" | Control-flow diagnostic, unrelated to a DP branch device |
| Public BLMStandbyEnable property / generic radio and active-region symbols | Backlight standby or unrelated fields, not MST or ACT |

The source-compatible branch identity functions are weak DP evidence, not MST
control-surface evidence sufficient for the stronger feasibility classification.
No caller of a qualified sideband codec exists to enumerate because no such
codec was established; direct caller receipts for selected controls are retained
with an explicit same-image/direct-only limit.

## Constant And Table Findings

Multi-constant matches were tested against their argument/field roles, not counted
as MST implementations. Important examples:

- IODPVideoLinkVideoStreamConfigurationSDP at 0xfffffe000a7ad324 and userspace
	0x1848ff280 construct video stream metadata. Values 0x10-0x14 and 0x20-0x23
	overlap request opcodes but are not a routed request-ID switch. The source
	header also defines SDP VSC/CEA type 0x21: a byte equal to MST_CAP's address is
	not automatically an access to that address.
- IODPDevice::cacheCapabilities at 0xfffffe000a7db3e8 compares receiver revisions;
	IODPVirtualDevice::device at 0xfffffe000a7f514c sets up a virtual receiver with
	DSC/video fields. Neither supplies PBN/VCPI/ACT semantics.
- IOAV audio format/CEA processing and timing validation contain opcode-like or
	0x1c0/0x2c0 values. Their recorded owners and selected bodies concern audio/video
	modes, not payload-table allocation.
- CoreDisplay IOPReturnToString at 0x182fbd324 uses error-code cases; CoreGraphics
	file loading at 0x1876f633c uses file/memory parameters. These are controls for
	register-sized constants outside DP access.
- SkyLight's debug payload and display-stream descriptions are compositor/debug
	serialization, not a proved physical DP stream-to-VCPI mapping. Other matches
	belong to PDF/glyph/image formats, tablet events, TIFF/Metal or brightness data.

In WSCreateDebugPayloadForStream at 0x186e6f320, values 449 and 448 feed
WSDebugGetExternalKey at calls 0x186e6f40c and 0x186e6f49c, respectively; both
resolve to 0x1870842f4. They are debug-key indices, not DPCD-address arguments.
The 548-byte body SHA-256 is
`0784c56e20f0847d2c52e4dcb90696b7fcbdfe4ca313907d470b51eff8df3c34`.
WSAddDisplayStreamsInfoToExternalDebuggingDictionary at 0x186e56440 calls the same
key helper and typed dictionary setters; its 2252-byte body SHA-256 is
`3fe325906044fe99fdbfbcc2ec05c07882eb35b42a0a7dc75877244d4e47adf8`.
These selected-body assessments do not claim every one of the 203 candidate
functions was exhaustively semantically disproved.

All eight data-table matches were attributed to non-MST tables:

| Candidate Address / Image | Owning Table / Direct Reference Where Recovered | Assessment |
| --- | --- | --- |
| 0xfffffe000798257c / IOAVFamily | HDMI audio clock-regeneration s_acr_table; direct reference in IOAVHDMIAudioClockRegenerationDataForLink at 0xfffffe000a5acc04 | Clock values, not sideband windows |
| 0xfffffe000798e78c / IOAVFamily | IOAVVideoTimingGetITSource::sITResolutions | Pixel widths/heights and format codes |
| 0xfffffe000798f028 / IOAVFamily | IOAVService::enumerateBasicTimingElements::modes | Display mode dimensions |
| 0x18302ec4c / CoreDisplay | gVFBModeList; references include CGXConstructVirtualFramebuffer at 0x182f73f38 | Virtual framebuffer resolutions |
| 0x1e674dab0 / CoreGraphics | _AGL table; reference from component_to_unichars at 0x1873858b4 | Glyph/Unicode mapping, not payload IDs |
| 0x184930144 / IOKit | Same HDMI audio clock-regeneration table; consumer at 0x1848fd3a8 | Audio clock values |
| 0x18493c354 / IOKit | Same sITResolutions table | Pixel dimensions |
| 0x1871cd590 / SkyLight | WS::Displays::AspectRatio::target_pixel_widths, consumer at 0x186f7085c | Pixel widths 4096/4608/5120, not DPCD windows |

Data-symbol attribution uses the containing section, neighboring symbol extent,
raw word pattern and direct references when present. A zero exact ADRP+ADD
reference count is not proof of no indirect consumer. No data-table hit is
qualified as an MST register table.

## DPCD Address-Use Census

This table is static operation evidence, not a record of transactions executed by
MacMST. Generic dynamic-address proxies remain GENERIC_DPCD_PRIMITIVE; their
availability alone neither supplies MST control nor proves no constant addresses.

Declared fixup chains bind IODPDevice vtable address point
0xfffffe000845a558, slot+3112 at 0xfffffe000845b180 (raw c8dc790366341180) to
readDPCD at 0xfffffe000a7a1cc8, and slot+3120 at 0xfffffe000845b188
(raw 60dd7903bc611180) to writeDPCD at 0xfffffe000a7a1d60. Page SHA-256 is
`693f6b9f7efc940a6714c4276c638d25a4c078a7eb615cf8190bcd159c144793`.
IODP13Service slot+4384 at 0xfffffe0008464b08 (raw 88e67b0324af1180) resolves
to IODPService::writeDPCD at 0xfffffe000a7c2688, page SHA-256
`465b73f7f10a55517711b7c4ab37eba15c67a53ad9ddba4cde853f4ffb40c629`.
These are census-callsite bindings, not reopening selector safety or authorization.

| Address / Range | Static Operation / Caller | Meaning / Evidence |
| --- | --- | --- |
| 0x000-0x00f | Read 16 bytes, cacheCapabilities, call 0xfffffe000a7db550 | Base receiver capability block; constant address w1 and size w3 feed the read slot |
| 0x2200-0x220f | Conditional read 16 bytes, same caller, 0xfffffe000a7db5a0 | Extended receiver capability block |
| 0xf0000-0xf0009 | Read 10 bytes, same caller, 0xfffffe000a7db478 | LTTPR capability structure, not MST branch routing |
| 0x060-0x06f | Read 16 bytes, getDSCCapabilitiesDPCD, 0xfffffe000a7dc43c | DSC receiver capabilities |
| 0x090 | Read one byte, cacheCapabilities, 0xfffffe000a7db90c | FEC capability |
| 0x02e / 0x116 | Reads, cacheCapabilities, 0xfffffe000a7dbd00 / 0xfffffe000a7dbd40 | Receiver ALPM capability/configuration |
| 0x2210 | Read one byte, cacheCapabilities, 0xfffffe000a7dbda4 | DPRX feature enumeration |
| 0x100 | Write one byte, setLinkRate, 0xfffffe000a7a0d60 | Link bandwidth setting |
| 0x101 | Read/write, setLaneCount, 0xfffffe000a7dd884 / 0xfffffe000a7dd8c8 | Lane-count control |
| 0x102 / 0x103 | Writes, clearTrainingPattern / commonSetTrainingPatternAndDriveSettings, 0xfffffe000a7a1718 / 0xfffffe000a7de384 | Link-training pattern and drive settings |
| 0x107 | Write, setDownspread, 0xfffffe000a7a161c | Link downspread control |
| 0x160 | Read/write, getDSCEnabled/setDSCEnabled, 0xfffffe000a7a1208 / 0xfffffe000a7a12f4 | DSC enable, not MST mode |
| 0x2003 | Write one byte, IODP13Service::acknowledgeIRQ, 0xfffffe000a7c462c | Shared ESI IRQ vector; this register alone does not prove the MST-ready bits or sideband flow are implemented |
| 0x470-0x472 | Read three bytes, cacheCapabilities, 0xfffffe000a7db9ac | Address use established; register semantics UNKNOWN in the pinned-header comparison |
| 0x328 | Read one byte, cacheCapabilities, 0xfffffe000a7dbbe0 | Address use established; register semantics UNKNOWN |
| 0x35f | Write, setLaneCount, 0xfffffe000a7dd854 | Address use established; register semantics UNKNOWN |
| 0x310 | Write, commonSetTrainingPatternAndDriveSettings, 0xfffffe000a7de3d0 | Address use established; register semantics UNKNOWN |
| 0x021 | No qualified MST-capability address use in the inspected candidates | Stream-format and event-type value 33 are false positives; no claim of all dynamic-address coverage |
| 0x111 | No qualified MST-enable use found | Negative selected-host search, not a firmware or hardware absence claim |
| 0x1c0-0x1c2 / 0x2c0 | No qualified payload allocation/ACT register flow found | Matching values occur in unrelated format/timing data or virtual call offsets |
| 0x1000 / 0x1200 / 0x1400 / 0x1600 | No qualified sideband-window operation found | For example 0x1200 at 0xfffffe000a7ee260 is a vtable offset, and several 0x1000 values are size limits/resolutions |

Additional unclassified address uses are preserved in the full function receipts,
without assigning unverified meanings or treating them as MST. The positive
base/link/DSC controls show that this search can find genuine
DP address uses; the absent MST sequences remain a bounded negative, not proof
that an opaque firmware implementation cannot use them.

## Sideband, Topology And Payload Results

- Sideband codec: **NO_APPLE_MST_SIDEBAND_CODEC_FOUND**, in the inspected host
	images and signature coverage. No candidate connects the source-derived
	header/CRC/opcode structure to DP sideband windows. Firmware is not covered.
- Topology model: **NO_APPLE_MST_TOPOLOGY_MODEL_FOUND**, in the inspected host
	images. Branch identity/boolean metadata lacks a demonstrated GUID/RAD/ports/
	PBN hierarchy and remote access behavior. Thunderbolt topology is not counted.
- Payload allocator: **NO_MST_PAYLOAD_ALLOCATOR_FOUND**, in the inspected host
	images. No function or table is qualified as per-stream PBN/VCPI/slots/ACT
	assignment. Generic bandwidth, DSC and IPC payloads remain negative controls.
- One-link packetizer: **PACKETIZER_SEARCH_INCONCLUSIVE**. Single-stream MSA/SDP
	formatting and multiple display/port objects do not establish independent
	streams mapped to multiple payload IDs on one physical DP link. The physical
	packetization implementation remains beyond the recovered host control surface.

These are evidence classifications with the stated host scope. No actual MST
topology, allocation, sideband exchange or packetized multi-stream link was tested.

## Thunderbolt Negative Control

The current host contains separate Thunderbolt DP input/output adapter classes,
createDPTunnels at 0xfffffe0009ca5b84 and per-link rate/lane bandwidth calculation
at 0xfffffe0009c64944. IOPortTunnelingTransportState has add/remove transport
operations; IODPPortService::isTunneled at 0xfffffe000a7d2924 reads a separate
published-state flag. The pinned Asahi routing document explicitly describes
USB4 tunneling with up to two controllers per USB-C port.

This is a different model from one DP link allocating multiple VC payloads. The
plural name createDPTunnels is not itself proof of two display streams: a tunnel
implementation also has protocol paths such as AUX/video, and each DP adapter's
link is separate from an MST stream. No observation of two active tunneled
displays was made here. The current hub's active DP state is Tunneled=false.
Multiple DCPEXT remote-port objects or source display pipes are therefore not
counted as a one-link MST packetizer.

## Public M5 Observation

A public CoreGraphics health check found two active displays, one external with
1920x1080 pixels. The existing collector then produced
artifacts/probes/20260914T021304Z: **40 public read-only commands, zero failures**.
The report SHA-256 is
`810a87937918b330650e89272a349823d1759492d2a692a160d85f6736b06016`, manifest
`5bfb1e562e7e5ede34b854378f4124589715572e4661f7107bd863e9a1846ac9`.

Observed External Unit 0 DCPDP device/service paths remain under DCPEXT0. The
active USB-C DP transport reports HPD=2, two lanes, raw LinkRate=4/HBR3,
SinkCount=1, Tunneled=false and one 1920x1080@60 logical external display.
Physical mirroring remains the owner's report, not an inference from the logical
display count or its in_mirror_set flag. No private object or I2C interface was
opened. The existing public framebuffer path remains unavailable, not reopened.

A separate public class/property-name capture reuses only RegistryReader's
matching/identity/property methods, not its retired userServer workflow. It
recorded two DCPDPDeviceProxy, two DCPDPServiceProxy, four DPTX remote-port,
two DisplayPort transport-state and three framebuffer-shim objects. All 62
recorded IOKit status calls returned zero. It retains property names even when
values are not allowlisted, avoiding a false absence conclusion from filtering.

No stream-count, payload-ID, VCPI, PBN, branch-GUID or RAD topology property name
was identified in that bounded class set. BranchDeviceID/OUI and Tunneled are
present; framebuffer BLMStandbyEnable is a substring false positive. This is weak
negative registry evidence only. Neither missing property names nor SinkCount=1
establishes the source hardware's capabilities or every hidden firmware state.

## DCP Firmware Boundary

| Observed Interface / Message | Classification | What It Does Not Establish |
| --- | --- | --- |
| Retained generic DP register primitives | GENERIC_DPCD_PRIMITIVE | Not routed MST remote DPCD or a usable/approved transport; selector retirement unchanged |
| IODP MSA/VSC SDP formatting and link/DSC controls | GENERIC_STREAM_CONTROL | No demonstrated stream-to-VCPI/slot mapping |
| DCPAVServiceProxy::startLink at 0xfffffe000a010420 | FIRMWARE_OPAQUE | Copies 272 bytes of link data plus source/options into a message; no recovered MST topology/payload interpretation |
| DCPAVVideoInterfaceProxy::startLink at 0xfffffe000a012e6c | FIRMWARE_OPAQUE | Copies 256 bytes of video-link data and a source byte; source packetizer behavior not recovered |
| DCPAVVideoInterfaceProxy::setTimingElement at 0xfffffe000a0136f4 | GENERIC_STREAM_CONTROL / FIRMWARE_OPAQUE | Serializes a timing identifier/source and sends it; no evidence of multiple timing streams on one physical DP link |
| AppleDCPDPTXRemotePortProxy::handleSetLinkRate at 0xfffffe00090f1b30 | GENERIC_STREAM_CONTROL | Forwards a message field to a port operation, not MST payload activation |
| PMstop, linker, timing/audio/glyph/debug candidates | UNRELATED | No HOST_EXPLICIT_MST candidate qualified |

No usable M5-attributed local DCP firmware image was found in the inspected
/usr/standalone/firmware root, its FUD child, the current MacSoftwareUpdate asset
root (catalog files only), or four bounded Preboot firmware patterns. Accessory
firmware directories/updaters are not assumed to be DCP firmware. This is a
scoped availability result, not proof no firmware image exists elsewhere. No
firmware was loaded, changed, decrypted, extracted from privileged memory or run.

The single controlling opacity boundary is **the M5 DCP firmware's DP link/stream
implementation behind the high-level link/timing RPCs, including source
stream-to-payload packetization**. Host code could omit explicit sideband/PBN
machinery if firmware implements it. The current evidence neither establishes
that hidden implementation nor excludes it.

## Asahi Comparison By Generation

Current remote HEADs were pinned/rechecked and match the retained revisions:
AsahiLinux/linux `77cb8f24c2381a8abb7272d7bbdec548d6426a8a`, m1n1
`b4654b32941d51afdb77579d63e7cb1aa6c03ecc`, docs
`715664a269937fe83293f46bbbeaae6094cb504e`.

- The current [display-controller document](https://github.com/AsahiLinux/docs/blob/715664a269937fe83293f46bbbeaae6094cb504e/docs/hw/soc/display-controllers.md)
	still says "No MST!" alongside DP 1.4/DSC and USB4 tunneling. Its populated
	controller tables cover M1-M3; M4 entries are TBD. That broad introductory
	wording is not a demonstrated M5 hardware result.
- The pinned M3 feature page marks main-display support WIP; the M4 page marks
	it TBA. The pinned documentation tree/overview has no M5 feature-support page.
	Missing documentation is not proof no M5 work exists elsewhere.
- The selected Linux dcp/connector/iomfb/DPTX/DPAV files contain generic link,
	mode and EPIC control, with explicit t6020/t8112 and generic dcp/dcpext match
	entries in dcp.c. No MST branch/PBN/VCPI source implementation or M5-specific
	display support was identified in this bounded file set. Generic matches are
	not proof all later chips work.
- The two retained m1n1 DCP service files expose service wrappers; DCPDPDevice is
	a service-name declaration, not a recovered MST implementation. No M4/M5 MST
	protocol or one-link packetizer claim was established from them.

The documentation feature-support root and an initially assumed m1n1 source
path returned 404. Actual feature pages were resolved from the pinned tree;
only successfully retained files contribute source evidence. No Asahi code was
executed. Generation-scoped comparison cannot substitute for current M5 firmware.

## MST Source Evidence Map

| MST Requirement | Apple M5 Stack Evidence | Location | Confidence |
| --- | --- | --- | --- |
| MST capability control | No qualified 0x021/0x111 access/enable sequence; generic DP capability controls do exist | IODisplayPortFamily census and final host scans | NEGATIVE_SEARCH_RESULT for inspected host MST control |
| Sideband transport/codec | No qualified window/header/CRC/opcode flow; table/format matches disqualified | Kernel and userspace candidate receipts | NEGATIVE_SEARCH_RESULT; firmware UNKNOWN |
| LINK_ADDRESS / topology | Branch identity/boolean metadata only; no GUID/RAD/port hierarchy established | DCPDP branch properties, IODPPortService, DTSDPDeviceDPCDInfo | WEAK_STATIC_EVIDENCE for identity, not MST topology |
| Remote DPCD / I2C | Generic local primitives/metadata, no qualified routed sideband operations | Retained primitive classification and host signature scan | NEGATIVE_SEARCH_RESULT for MST remote operations |
| PBN calculation | No mode-to-PBN plus link-slot allocation flow found | Function/table candidates and bandwidth negative controls | NEGATIVE_SEARCH_RESULT |
| VCPI / payload allocation | No qualified stream/ID/start/count table machinery | 0x1c0-0x1c2/0x2c0 candidate assessment | NEGATIVE_SEARCH_RESULT |
| ACT activation | No source payload activation plus ACT-sent/handled sequence established | Crossbar inactivity and display/debug controls disqualified | NEGATIVE_SEARCH_RESULT |
| One-link multi-stream packetizer | Generic stream formatting and opaque DCP link/timing RPCs; no physical one-link stream-to-payload binding established | DCPAV video/link firmware boundary | UNKNOWN |

Public M5 identities/topology are VERIFIED_ON_CURRENT_M5_STACK. Confirmed ordinary
DP address controls are STRONG_STATIC_EVIDENCE for their stated non-MST roles,
not for source MST. None of the eight MST requirements is promoted by multiple
display controllers, generic strings or a sink capability alone.

## Feasibility And Project Consequence

Primary result: **M5_MST_SOURCE_FEASIBILITY_UNRESOLVED**.

The targeted host search found no qualified MST source implementation, but the
opaque M5 DCP link/stream firmware prevents turning that host-side negative into
a complete source-stack conclusion. No M5 hardware absence claim follows. No
MST-specific control surface was established that would justify the stronger
control-found classification, and no one-link packetizer proof was recovered.

The next decision is whether a **read-only, M5-attributed firmware/control
specification for the link/stream-to-payload boundary** can become available.
Without that evidence, this milestone does not justify risky transport work.
Do not return to selector 0, wrap it in a new helper, or execute link/MST controls.
No next hardware experiment is authorized or scheduled.

- Selector-0 status: **RETIRED_ON_DAILY_USE_M5**.
- DPCD gate: **NOT_READY_FOR_DPCD_TEST**.
- Existing one-byte and in-flight termination gates remain unchanged.

## Tooling, Provenance And Reproduction

[../../tools/scan_mst.py](../../tools/scan_mst.py) reuses the existing kernel
container/fixup/function-start readers, dyld cache reader and LLVM disassembler.
It adds candidate-only constant/literal/table scanning, exact image selection,
bounded detail receipts and optional healthy-baseline public property names. It
does not call the retired inspection/coordinator entrypoints or invoke inspected
code. Importing the existing reader classes is not executing their workflows.

Limits are explicit: 64 KiB scanned function bound, 32 KiB detail body bound,
64 MiB section bound, at most 64 detail addresses, 4 KiB symbol-name reads, and
64-byte aligned-table co-occurrence windows. The final replay reports zero
unassigned text-prefix bytes, skipped functions or image errors. This establishes
byte-range coverage under the supported signatures, not semantic completeness.
Raw body bytes, caller/callee sites, image UUIDs and section hashes are retained
in ignored receipts; no Apple binary or upstream source is published in Git.

Final source identities:

| Local Tool / Oracle | SHA-256 |
| --- | --- |
| tools/scan_mst.py | `7ed7aa1025203c66ba1659987d027545311bc3a6fc292e477f2a7e29da4b0f47` |
| tests/test_iodp_static.py | `61ee57154836100e5f352276525654242c4cc994064f8b3052db8af8b2d7b4cb` |
| docs/research/mst-source-signatures.json | `ba7b651e9bf9d73043abc9176f6f74f464e702772dc7c7a99a63c8e43a3e3073` |

The cache image table is derived from dyld revision
fd8d0c4d52320ebf64db34f3cb280310d905c5ae, retained dyld_cache_format.h SHA-256
`dd6f7d9ffc5cb318988c16dbecf958d04b0c65cd9ee1892a838e374f76fd182c`.
The current image-table hash is
`99bd7e60ec2d7ef76f7dbcf1cc1798d5669239b3de98196b9c89d78f267a5de6`, with 13
cache components whose UUIDs/header hashes are checked. Scanned-section digests
are deliberately not mislabeled full dyld-cache file hashes.

| Retained Receipt | SHA-256 |
| --- | --- |
| m3a-inventory-20260914/mst-inventory.json | `16a22bb2ef0c493ed2c5e469a1925075bf129d9f07334ac6639e0fb023835c0e` |
| m3a-scan-20260914/kernel-verified.json | `cf44d9ec286d3d7f52edd1cf1fcc1334bd088b3b6f47e3a3bb1b8a1ddd910ca1` |
| m3a-scan-20260914/userspace-verified.json | `0de9539be9ba682ae353e43d126094b235fab554b18dad9b5144f4e3077c9749` |
| m3a-scan-20260914/firmware-boundary-controls.json | `d9ff383366beb110990cde498a994b356163d1e26855e5a2f1dacc22065666e4` |
| m3a-scan-20260914/public-property-names.json | `dfcd800b6f3a7831ae4c58d910fef9c52c7887ca2ba24e9cc94c1e73bee9c90d` |

The verified kernel/userspace receipts were replayed with the final tool. Image
section hashes, all candidates/census/table matches and all 29 selected detail
bodies exactly match the previous final scans. The three DCP firmware-boundary
detail bodies add a separate receipt; its earlier tool hash is historical, not
silently replaced. The public names receipt likewise predates the final static
coverage guard and remains an immutable public observation.

Asahi source hashes, with repository/revision scope specified above:

| Retained Asahi File | SHA-256 |
| --- | --- |
| docs: display-controllers.md | `b0b08009a585efa9fe62570af66fb48cdb7a94246dfb481b95c97445580b9ca7` |
| docs: feature-support/m3.md | `b2e4b1e426c67bdedd8c743d9d8c7cce7f7bbb0530f7a2c12a474639666da753` |
| docs: feature-support/m4.md | `f1f06c04144136e239b265e30a7b92d973c68fc4d3e41ac215ea015ba4e9d5f5` |
| docs: feature-support/overview.md | `0f217fa291492a6037402e17697a9bfb8f9aa6eb2700f89f58c5fa11a90aa6cb` |
| Linux: apple/dcp.c | `3ce8fe948765e3e157cddff9e2f60d584517869f87c79766406fc2f225f87e6f` |
| Linux: apple/dcp.h | `fb90336889a7646033b9fcddccc4dcbc2a3c015b89a394f0702acd2b21458ef8` |
| Linux: apple/connector.c | `bbc24737128162405fa06a6a4344b48997bb2aa409cd6f7cef5eade88b479359` |
| Linux: apple/dptxep.c | `1c2fd002b44b9141728107f9cd99c74df4851e58fe0008f78fb0c6362893176a` |
| Linux: apple/iomfb.c | `9b0e7d0952f87f9c1b3c6483f00071ecc7480d58e9570382c2323b8dcd0da12e` |
| Linux: apple/epic/dpavservep.c | `4befdad91d6ad90035f84c5ed78688c97210a1c8a8f0d8c85ffadab7cc747291` |
| m1n1: fw/dcp/dcpav.py | `a9f408a5d6b55889e77dd84ab63e40a1d6a2f418ea4bdd49fe5972b6884c3555` |
| m1n1: fw/dcp/dcpep.py | `de2466ecc571dbd09e1481948332f4c4f1a848197aac989c95c24430778a0d07` |

The initial cache adapter rejected a valid iOSSupport path and then tried to read
the whole 406 MB shared symbol string pool. Both local parser limitations were
fixed and regression-tested: normalized absolute paths and bounded individual
symbol-name reads. The initial zero-image/error receipt is preserved, not cited
as negative evidence. CamelCase signature tests also exposed and fixed a missing
RemoteDPCD spelling. No parser issue was bypassed by disabling bounds or invoking
private interfaces.

Reproduce a small, non-executing signature/control scan with fresh output paths:

```sh
python3 -m unittest discover -s tests -p 'test_iodp_static.py' -k mst
python3 tools/scan_mst.py --inventory --output artifacts/probes/m3a-local/inventory.json
python3 tools/scan_mst.py --kernel-image com.apple.iokit.IODisplayPortFamily --output artifacts/probes/m3a-local/dp.json
python3 tools/scan_mst.py --userspace-image /System/Library/Frameworks/CoreDisplay.framework/Versions/A/CoreDisplay --output artifacts/probes/m3a-local/coredisplay.json
```

For the full recorded scope, pass one --kernel-image or --userspace-image per
image in the inventory tables, with --detail-address only for declared function
starts in the retained receipts. The tool refuses an existing output path and
a kernel UUID mismatch. A fresh clone lacks the ignored receipts/upstream files;
that is unavailable historical evidence, not permission for a private experiment.
The optional --public-baseline accepts only a retained healthy public capture
and does not enable any transport. No source hash, compilation result or static
negative is evidence of native MST functionality on hardware.

## Validation

| Check / Command | Result And Limit |
| --- | --- |
| `cmake --build build` | PASS; strict-warning targets already up to date, no native-source change |
| `ctest --test-dir build -L unit --output-on-failure` | 9/9 PASS; 5.65 s total; includes userspace containment mocks, not a private display experiment |
| `cmake --build build-sanitized` | PASS; existing ASan/UBSan targets already up to date |
| `ctest --test-dir build-sanitized -L unit --output-on-failure` | 9/9 PASS; 7.53 s total; no hardware label selected |
| `python3 -m unittest discover -s tests -p 'test_iodp_static.py'` | 72/72 PASS, including twelve M3A methods; synthetic parsing/signature/coverage checks |
| Same command with `-k mst` | 12/12 PASS after the final function-coverage and bounded table-window guard |
| Final same-scope scanner replay | 24 images, 62,740 functions; all 203 function/eight table candidates and 29 detail bodies identical to retained prior scans; zero image errors, skipped functions or unassigned text-prefix bytes |
| Detailed-body provenance | All 32 detailed bodies (22 kernel, seven userspace, three firmware-boundary controls) match complete raw instruction bytes, addresses, lengths, hashes and image UUIDs |
| Oracle/source provenance | Five current Linux files and historical header hashes match; all 29 registers, 12 opcodes and eight masks match pinned definitions; retained Asahi/dyld/tool hashes verified |
| Public evidence provenance | 27 artifact hashes, 13 capture-source hashes, probe hash, 40 successful commands and 62 zero-status IOKit calls verified offline |
| Static-only safety audit | Existing non-executing binary/import audit passes; new scanner imports only reader/disassembler methods, no private API or coordinator entrypoint invoked |
| Documentation and editor checks | Local links/anchors/fences, exact classifications/eight-row map, whitespace and editor diagnostics pass; historical E001-E167/S01-S51 rows preserved |

The optional open-only targets already enabled in the two local builds remain
unexecuted in M3A. Contract tests use synthetic frames, mock children and an
unrelated temporary consumed marker; they do not authorize or run a private
helper mode. No native production/isolation source, CMake setting, reused static
reader, public collector or system configuration changed.

Immutable safety/binary checks:

| Item | Unchanged SHA-256 / State |
| --- | --- |
| M2F-ATTEMPTED | `2f3da1f224c0602dc46f812d3f6eb2c1560fe7a82c1a89f93eedb725b2726efc`; consumed |
| Historical successful M2F result | `86ee9fdd87eb631e7552b0087471a149c183667c2162e838866ce993e1dd3d04` |
| Historical stopped M2F result | `79387346acdaebed1efb2284a531de8f2cf5aad1d64915a3f5f527040ebae840` |
| M2G-DPCD-READ-ATTEMPTED | Absent; never created or reset |
| build/macmst | `450832c50446d3a430cbed2bcab7c285cddf5f6b370b2339df2cd0a33aefd89a` |
| build/macmst_dpdv_open_helper | `d94b0a450e89daa697675d816e231994e37456ec61928fc72261ec500f153830`; not executed |
| build/macmst_dpdv_open_check | `f94db7e91ef670ce6c59ce73929016d2d36a5adb44fb9714f188932771b55e8b`; not executed |

The earlier M2F runtime attestation belongs only to its historical binary and
one open/immediate-close observation. It is not transferred to the unexecuted
rebuilt helper/parent. M3A performed **zero private display operations** and no
DPCD/MST transaction. What was observed on real M5 hardware is only the public
display/registry state described above; native MST remains untested.

## Git Publication

M3A is isolated on research/m5-mst-source-feasibility, based on the integrated
retirement commit `a882c1dc75501c03347050f1cdb91c38df2af39d`.

- `58682b6b74d71ae1634f538e004f2bcb805b7372`: pre-search rubric and pinned MST
	source signatures, committed before the Apple implementation search.
- `6c4e466bddf5281cfa57d6120f99ed83579b3996`: finalized scanner, twelve focused
	test methods and literal-pattern corrections; committed bytes match the
	verified kernel/userspace receipts.
- The containing findings commit finalizes this report, the two README indexes,
	open questions and evidence ledger E168-E180/S52-S56.

The complete milestone changes eight text paths: one scanner, one existing test
file, the signature JSON and five documentation files. No production/isolation
code, build configuration, historical selector report, credential/editor setting,
Apple binary, firmware, raw capture or downloaded upstream source is included.
Historical E001-E167/S01-S51 ledger rows remain byte-for-byte intact.

The publication command is deliberately branch-only and non-force:

```sh
git -c push.followTags=false push -u origin refs/heads/research/m5-mst-source-feasibility:refs/heads/research/m5-mst-source-feasibility
```

Before publication, all 23 protected local/remote branch, tag and peeled-tag
identities matched, and the M3A remote branch did not exist. Main remains the
retirement merge, with selector0-retired-v0.6 object
`55b7f703fe11b396e6b159d76fcc84cc31ec6b6d` unchanged. M3A is not merged and no
pull request or additional tag is part of this milestone. Publication is not
authorization for any private interface or hardware experiment.