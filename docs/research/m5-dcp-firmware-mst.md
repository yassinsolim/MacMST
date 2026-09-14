# M3B: Identified M5 DCP Firmware And MST

## Scope And Integration

This milestone follows [M3A](m5-mst-source-feasibility.md). It examines public
Apple firmware offline, not the attached sink or an executable transport.
Selector 0 remains **RETIRED_ON_DAILY_USE_M5** and the global gate remains
**NOT_READY_FOR_DPCD_TEST**. No private display operation, DPDV open, selector,
DPCD/AUX/I2C/MST transaction, restore/update, firmware load, security change or
physical disconnect is performed.

The starting M3A branch and upstream were exactly
`19cc4e33799a3dff5a0393687b75b22a2bb036b1`, with a clean tree. Its three linear
commits, eight text paths and ten changed blobs were audited. Main was
`a882c1dc75501c03347050f1cdb91c38df2af39d`; the retirement tag, historical refs,
consumed M2F marker and both historical M2F receipts matched. The read-attempt
marker was absent.

The authorized --no-ff merge is
`24f2d1c3065ec0d7f80b5a53077f3e169f79368f`, message
`merge: record M5 host-side MST feasibility investigation`. Its parents are the
old main and exact M3A HEAD, and its tree equals the audited M3A tree. Main was
pushed and verified. Annotated `m5-mst-host-scan-v0.7`, object
`393a501da735dbeb6134ccb4a0da3f5d9d0b584a`, peels to that merge. Its message is
`Verified M5 host-side MST source scan; packetizer feasibility remains unresolved at the DCP firmware boundary.`
The tag was pushed and verified before creating research/m5-dcp-firmware-mst.
All remaining work stays on that branch. The earlier retirement tag remains
object `55b7f703fe11b396e6b159d76fcc84cc31ec6b6d`, pointing to the old main.

The observed investigation start was 2026-09-14T02:51:08Z. Actual UTC is retained
instead of the earlier date in the prompt. No model/editor configuration changed.

## Target Firmware

[Device metadata](https://api.ipsw.me/v4/device/Mac17%2C2?type=ipsw) and the
[exact-build record](https://api.ipsw.me/v4/ipsw/Mac17%2C2/25G83) agree:

| Field | Public Metadata |
| --- | --- |
| ProductType / device | Mac17,2 / MacBook Pro (14-inch, M5) |
| BoardConfig / platform | J704AP / t8142 |
| CPID / BDID | 33090 / 34, or 0x8142 / 0x22 |
| Version / build | macOS 26.6.2 / 25G83 |
| Signed | true in IPSW.me metadata; not an independent TSS authorization test |
| Filename | UniversalMac_26.6.2_25G83_Restore.ipsw |
| Published whole size | 19,772,231,540 bytes |
| Published whole SHA-256 | `885503b7f4b06609e9a512f2befd40f59730640a3f1233e3892d60affdd51c95` |
| Published whole SHA-1 | `4833c12d9d8d330d47216edbcaaf8cb4b926c99a` |
| Published whole MD5 | `7df89dc33e7c7414c69b7292b32fe64e` |

The exact [Apple CDN source](https://updates.cdn-apple.com/2026SummerFCS/fullrestores/140-75212/A2A24B94-1FC1-45A3-93F7-C51B02AF1F4D/UniversalMac_26.6.2_25G83_Restore.ipsw)
is independently tied to the target by its extracted BuildManifest, not by its
filename alone. Published whole-archive hashes were not locally verified because
the entire IPSW was never downloaded. No restore service or TSS request was sent.

Blacktop ipsw was not installed (`command -v ipsw` found no executable), so the
fallback uses Python's ZIP/ZIP64 parser over a bounded HTTP Range stream. It
refuses non-206 replies before reading their bodies, verifies exact Content-Range,
archive size and validators, and imposes per-request/member/total bounds.

Only four archive members were retrieved: BuildManifest, J704AP DeviceTree,
J704AP normal DCP firmware, and the same-build M4 normal DCP comparison. No DMG,
Restore/Info plist, restore DCP variant or entire IPSW was needed.

| Extraction | Range Requests | Apple Body Bytes Read |
| --- | ---: | ---: |
| BuildManifest only | 13 | 1,514,598 |
| J704AP DeviceTree and DCP | 16 | 4,437,738 |
| J604AP M4 DCP comparison only | 11 | 4,208,165 |
| Total | 40 | 10,160,501 |

The two retained metadata responses total 7,187 body bytes. Range accounting
includes repeated ZIP directory/header reads; it measures response bodies read,
not TLS/HTTP overhead or independent webpage-tool traffic. Receipts retain UTC,
URL, status, headers, exact range, body size and body hash for each archive read.

The retained metadata retrieval ran at 2026-09-14T02:55:46.190596Z through
02:55:46.515718Z. The first Apple request was at 02:55:46.516063Z, requesting
bytes 19772231518-19772231539 and returning HTTP 206. Apple reported
Last-Modified=Thu, 13 Aug 2026 22:11:09 GMT and ETag
`"897267912aaabf161b13a62c1bfbe48f-2358"`; that ETag is a validator, not a
claimed whole-file digest. BuildManifest itself is 26,535,137 bytes after ZIP
inflation, with 1,357,245 compressed member bytes.

## Exact BuildIdentity

BuildManifest SHA-256:
`e8ff2cdd3e8ab3a668132bf9453948b70f1863b849a6185914f54a9ec25356d3`.
ProductBuildVersion=25G83, ProductVersion=26.6.2 and SupportedProductTypes includes
Mac17,2. Selection is the unique identity at zero-based index **156**:

| Field | Selected Value |
| --- | --- |
| Ap,ProductType / Ap,Target / Ap,TargetType | Mac17,2 / J704AP / j704 |
| ApChipID / ApBoardID / ApSecurityDomain | 0x8142 / 0x22 / 0x01 |
| Info.DeviceClass | j704ap |
| Info.Variant / RestoreBehavior | macOS Customer / Erase |
| Info.BuildNumber / BuildTrain | 25G83 / CheerG |
| Info.VariantContents.DCP / Firmware | macOSProduction / macOSProduction |
| UniqueBuildID, raw 20 bytes | 853423c4f405886fc9b636db727220b051db45da |

Erase is an offline identity-selection field, never an operation performed.
J704AP also has index 44 Customer Erase Install (IPSW) and index 100 Customer
Upgrade Install (IPSW). These are retained, not silently treated as the same
identity. Product, target, board ID, chip ID, build and production variant are
checked together; a CPID substring alone is insufficient. Duplicate matches fail
closed. All three J704AP variants reference the normal t8142 DCP path.

The selected identity's deterministic sorted binary-plist serialization SHA-256
is `94cc166baa7845901ff25b14b509dd6391745b2bf1bebd218b97fc14fb093e72`.
This is a local identity-record digest, not an Apple-signed identity identifier.

## DCP Firmware Mapping

Path result: **M5_DCP_FIRMWARE_PATH_RESOLVED**.

The selected normal component is **Ap,DCP2**, path
**Firmware/dcp/t8142dcp.im4p**, Trusted=true, Info.Img4PayloadType=dcp2.
Info.IsFirmwarePayload is absent, not false. Its exact manifest Digest is:

`250388ecfc4901d9fc8efa556bd88ffc58826053916dcc66252e031374bf4b4814d94747951f0eb3bc6b9038815c6012`

The path was discovered in the selected Apple BuildIdentity. It was not inferred
from T8142. This inspected build really does contain that path, despite the
reasonable warning that a universal inventory need not name firmware after the
host SoC.

| Related Selected Component | Path | Type Override | Trusted / IsFirmwarePayload |
| --- | --- | --- | --- |
| Ap,DCP2 | Firmware/dcp/t8142dcp.im4p | dcp2 | true / absent |
| Ap,RestoreDCP2 | Firmware/dcp/t8142dcp_restore.im4p | rdc2 | true / absent |
| DeviceTree | Firmware/all_flash/DeviceTree.j704ap.im4p | absent | true / true |
| RestoreDeviceTree | Firmware/all_flash/DeviceTree.j704ap.im4p | rdtr | true / absent |

Restore-DCP Digest:
`34ca4e026922eea2661799ee658179fc2f6ca62e8023e310f9ddd40e0e961cf458ee47edbb4a684942cd57d41516e8cc`.
DeviceTree Digest:
`343e5ff5d3642e5780703439749ac9e5ca9bca4c9e0ff882485ea304d85e84351020711592822aaaa8eb4470f3aeb927`.
RestoreDeviceTree Digest:
`43714ba0751e7f2bc1c2cbecc115b7f11c19952f54a4d0ccdc9240aee1d064d6cc5587029691e7e499c90951ec4b0a0b`.

The other J704AP variants also include a DCP key with raw-type digest and display
vendor calibration. The selected identity's full display-component dictionary,
all variant dictionaries, raw flags and digests remain in the ignored mapping
receipt. Normal versus restore/type-personalized digests must not be conflated.

## DeviceTree Cross-Check

J704AP DeviceTree IM4P is 62,729 bytes, SHA-256
`13f4dce18ca0936616c71eb9ccbb18ad791bcc01d06d287405d5cd0b4dc2c962`.
It decodes without keys to 458,380 bytes, SHA-256
`79cc631c24ced43e166c56d717083350ee4baff7b055c200c481c4d9bf4cfba5`.
The bounded parser reads 569 nodes and retains relevant raw property bytes and
decoded strings with original offsets.

Root compatible is J704AP, Mac17,2, AppleARM; target-type is J704. The arm-io
compatible is arm-io,t8142. Display nodes include disp0,t8142, dispext0,t8142 and
dispext1,t8142; dcp/dcpext0/dcpext1 use iop,ascwrap-v6 with rtbuddy-v2 nubs.
The DPTX AUX nodes use dptx-aux,t8142 with a dptx-core,t8103 compatibility string.
Some PHY nodes retain t8132 compatibility as a fallback. These are cross-checks
of the board/controller family, not MST capability or unchanged-hardware proof.

The tree agrees with the manifest-selected T8142 board family. It does not
independently identify the firmware filename or prove how many streams a link
can packetize. No tree property or boot argument was modified.

## Cross-Generation Mapping

All rows come from unique macOS Customer / Erase identities in this same 25G83
BuildManifest, not separate filenames guessed from chip names.

| Host | Board / CPID / BDID | Identity Index | Normal DCP File |
| --- | --- | ---: | --- |
| M5 Mac17,2 | J704AP / 0x8142 / 0x22 | 156 | t8142dcp.im4p |
| M4 Mac16,1 | J604AP / 0x8132 / 0x22 | 146 | t8132dcp.im4p |
| M5 Pro Mac17,9 | J714sAP / 0x6050 / 0x08 | 159 | t605xdcp.im4p |
| M4 Pro Mac16,8 | J614sAP / 0x6040 / 0x04 | 149 | t604xdcp.im4p |

Their Ap,DCP2 digests differ. M5 does not reference the selected M4 t8132 file;
the represented M5 Pro identity does not reference t604x. Only base M5 and base
M4 payloads were downloaded for byte comparison. This mapping does not by itself
prove changed DCP silicon or any other unexamined board's firmware association.

The represented M5 Pro Ap,DCP2 digest is
`14255e45eae7be1c14746fce60da5f988adbbd8c823f777821ce177dbaafc06ab4d81430b9220360eb24d5831852cf6c`;
the M4 Pro digest is
`0538209b5c2818d117ff888a0625814cf389c6000e115a82dc9bedca2d26fcb825eaa37cf570fbfc20f6baf0eb723962`.
No Pro-family image was downloaded or scanned.

## Image4 Identity

| Item | Identified M5 DCP |
| --- | --- |
| IM4P size / raw type / description | 4,223,041 bytes / dcpf / 1 |
| Raw IM4P SHA-256 | `3f1424dbd80664128041bff2585e09bcf7fed9a75ac38e6c5a273f0b6494f219` |
| Raw IM4P SHA-384 | `8e7ccf0f2cc7b48a2bee1d930f1d063220459b3da2aa0ddcc713dc81f7a92f955e49bcad5c88b91a33639a4b819f8372` |
| Payload offset / compressed payload bytes | 25 / 4,223,005 |
| Compression | LZFSE, mode integer 1, declared output 16,023,552 bytes |
| Keybag / encryption observation | No keybag field; successfully decompressed using public libcompression without keys |
| Decoded bundle SHA-256 | `9c4d1b86ecbc897109235fabf6dbf0d83330e1e0f2f76ccd135484e708fefb7c` |

The selected Ap,DCP2 digest matches SHA-384 after changing only the four-byte
IM4P type at offset 13 from dcpf to the manifest's explicit dcp2 in memory.
Original bytes are unchanged. Raw dcpf SHA-384 matches the DCP component in the
other J704AP identities. DeviceTree's normal digest matches the raw IM4P; its
restore digest matches the explicit rdtr type override. These checks establish
manifest/component integrity, not independent Apple signature or TSS validation.

No key search, device key extraction, firmware execution, decryption bypass or
security-setting change was needed or performed. Raw containers and decoded
payloads remain under ignored artifacts/sources/m3b and are not published.

## Firmware Layout And Coverage

The decoded M5 image is a **BUND type-4 RTKit bundle**, not a standalone Mach-O.
Its 11 declared range entries include ktxt/kdat, rtxt/rdat, utxt, dsro, nold and
ubdl. The nold metadata at bundle offset 0xf00000 is a 115,108-byte Apple
DeviceTree with 708 nodes, SHA-256
`609a255e040ef2185c23f49197c3c0e32636a12de32b7510e6289b8ff185c887`.
The runtime header at 0xefc608 is explicitly referenced by the dcp_legacy
compartment metadata for DISP_INT, DISP_EXT0 and DISP_EXT1. This association is
stronger than merely choosing the largest embedded image.

The application Mach-O is ARM64, raw CPU type 0x0100000c, subtype 0x80000002,
filetype 5, UUID **18E26403-396D-3512-AF59-17E24808703A**. Its main text VM base
is 0x04000000. Bundle strings identify RTKit-3255.160.4.release and
AppleDCP-1041.120.7~2715-t8142dcp.RELEASE. These are static version strings, not
an attestation of the currently running DCP's bytes.

| Mapped Section | VM Address | Bytes | Bundle Offset | SHA-256 |
| --- | --- | ---: | --- | --- |
| __TEXT,__text | 0x4000000 | 3,346,996 | 0x27000 | `7c103615ab877aed6fd816942db04e222f2ee6bf8d131db7c59f08f839294bf2` |
| __TEXT,__cstring | 0x474d248 | 238,471 | 0x774248 | `d4b7c2505f537915420b565473cfc7dfdb95e41185ba473dad9bb632879a6564` |
| __TEXT,__lcxx_override | 0x47875d0 | 112 | 0x7ae5d0 | `8f427a1727ce8dd0c7861b996aee2fa5c5279a1666982dd9f7e507bc7283fb10` |
| __TEXT,__chain_starts | 0x474d200 | 72 | 0x774200 | `d703ed2c278fb2ffc05d1ecc05a08275ee28f046d80ed7c48aee46bd34ff8188` |
| __OS_LOG,__string | 0x4d69000 | 150,088 | 0xf20000 | `3123b4ba25a9f5b486d8c99c1ebbe0c7e749b6459483dd0d92b75abda28b8d30` |

All 25 nonempty file-backed application sections are mapped and hashed. Other
declared sections are empty or zero-fill, not missing executable sections.
Section relocations are zero in the inspected application headers. There is no
LC_DYLD_CHAINED_FIXUPS command; __chain_starts declares format 7, VM-offset mode
2 and eight chain starts. Walking them validates 27,054 pointer entries.
Nineteen selected slots are retained with raw bytes, chain index/hop count,
target and chain-metadata hash. Pointer identity alone does not prove a dynamic
receiver or reachability.

There is **no LC_FUNCTION_STARTS**. LC_SYMTAB declares 101,198 records, but its
original file offsets are not a recovered symbol table in this split bundle;
the public DCP reconstruction tool discards those fields. No symbol names or
complete declared function boundaries are claimed from that table. PAC entries
and direct BL targets partition the executable sections into **10,020 inferred
code regions**, not 10,020 proved functions. Regions are at most 64 KiB;
detailed disassembly is limited to 32 KiB. Boundaries can include neighboring
leaves or omit indirect-only entries.

The frozen [M3A oracle](mst-source-signatures.json) is byte-unchanged, SHA-256
`ba7b651e9bf9d73043abc9176f6f74f464e702772dc7c7a99a63c8e43a3e3073`.
The final pass records **348 candidate regions**, **707 string hits**, **766
direct string references** and **three constant-table candidates**. Strings,
sections, VM addresses, hashes, code-region references and candidate assessments
are retained. Missing function attribution is explicit. Forty-five selected
regions have full raw instruction receipts; positive claims below rely on local
structural evidence, not exhaustive decompilation of every candidate.

The external instances of dcp_legacy are covered. Other compartments such as
dcp_trusted, the RTKit kernel and roottask are not silently included in an
absence claim. This scope supports the positive MST-control finding, not a
hardware absence theorem or complete packetizer ownership proof.

## Firmware String Findings

| Exact Firmware String | Address / Context | Qualification |
| --- | --- | --- |
| DCPDPTXMSTManager | 0x4763f32; chain reference 0x48fd470 | Class name corroborated by the constructor-selected manager vtable |
| DCPDPTXMSTPort | 0x4763d47; chain reference 0x48fd410 | Port construction and routed topology fields corroborate the name |
| dp2-no-mst | 0x476317b; reference 0x41612f0 | Disabling setting, not an unconditional unsupported-MST assertion |
| failed to update MSTM_CTRL ret=0x%x | 0x4763186 | Actual 0x111 control operation |
| failed to setup MST link ret=0x%x | 0x47631e0; reference 0x415fd9c | MST setup branch, not evidence it ran on this machine |
| Primary MST port PBN:%d | 0x4763233; reference 0x415f794 | Reads port field +230 following path-resource enumeration |
| allocate payload failed 0x%08x (ignored) | 0x4763c90; reference 0x41609cc | Conditional manager allocation operation, not multi-stream runtime success |
| updatePayloadTable / invalid slot %d - %d | 0x47525df / 0x47525f2 | DPTX table programming with a 64-slot bound in region 0x4063c48 |

OS_LOG adds DCPDP2XService.cpp, DCPDPDevice.cpp and
AppleDCPDPTXController.cpp context. Code references to VM addresses 0x4d8822a,
0x4d893e9 and 0x4d881ce match the PBN, allocate-payload and enum-path-resource
messages at bundle offsets 0xf3f22a, 0xf403e9 and 0xf3f1ce. This cross-checks the
ubdl-to-OS_LOG mapping. A lossy reconstructed file offset points at zero-filled
data and would have missed the diagnostics.

DP 2.0 single-stream sideband is a crucial alternative. The pinned header's
DP_MSTM_CAP includes DP_SINGLE_STREAM_SIDEBAND_MSG at bit 1. Region 0x4161220
tests capability mask 0x03 and initially writes 0x06 to MSTM_CTRL: upstream
requests/source role, without MST_EN. Region 0x415f004 separately writes
`0x06 | mode` at call 0x415f154 and stores mode at service +2304 after success.
Neither the codec nor a disabling option establishes multiple timing streams.
No unconditional "MST unsupported" conclusion follows from this search.

Generic AFK payloads, DisplayID tiled topology, DSC metadata, Thunderbolt bandwidth
and overlay planes are not packetizer evidence. The three table candidates also
do not qualify: two contain video-mode width/height patterns; the apparent four
sideband windows at 0x471b5c4 lie inside a long sequence descending by 0x200,
not a recovered register table. The positive result rests on code behavior.

## DPCD Firmware Address Census

Every operation below is **static evidence only**, never a MacMST transaction.
Receiver slots +1344/+1352 and service slots +3328/+3336 have read/write argument
roles corroborated by buffers, returned values and ordinary-DP diagnostics.
These are analyst roles, not recovered symbol names. Raw argument 500 remains
an opaque value here; retired selector timing/lifetime analysis is not reopened.

| Address / Range | Qualified Firmware Use | Region / Exact Callsite | Meaning |
| --- | --- | --- | --- |
| 0x100 | One-byte write from rate control | 0x4126f1c / 0x4126f8c | LINK_BW_SET positive control |
| 0x101 | One-byte read/write | 0x4127198 / 0x4127380, 0x41273c8 | LANE_COUNT_SET positive control |
| 0x102 | One-byte write | 0x4126504 / 0x412656c | TRAINING_PATTERN_SET positive control |
| 0x202-0x204 | Three-byte read and status diagnostic | 0x4125f18 / 0x4125f74 | Lane/alignment status positive control |
| 0x160 | One-byte read | 0x4123e7c | DSC_ENABLE positive control |
| 0x600 | Power-control access | 0x412db34 | DP_SET_POWER positive control |
| 0x021 | One-byte read; tests bits 0/1 | 0x4161220 / 0x4161370 | MST/single-stream-sideband capability |
| 0x111 | Writes 0x06, zero, and 0x06 OR mode | 0x4161220 / 0x4161444, 0x41614a8; 0x415f004 / 0x415f154 | MSTM_CTRL role/mode control |
| 0x030-0x03f | Conditional 16-byte GUID write or routed equivalent | 0x4166858 / 0x4166988 | GUID handling after LINK_ADDRESS |
| 0x1c0-0x1c2 | Three-byte ID/start/count write | 0x4128fbc / 0x412907c | Branch payload assignment |
| 0x1c0-0x1c2 | Writes bytes 0, 0, 63 then polls update | 0x41291c8 / 0x412921c | Payload-table reset |
| 0x2c0 | Reads status with caller mask 1/2; writes bit 0 | 0x41290f8 / 0x4129150, 0x41291b0 | TABLE_UPDATED / ACT_HANDLED |
| 0x1000 | Writes constructed routed header/body/CRC | 0x4165ce4 / 0x4165fdc | DOWN_REQ sideband transport |
| 0x1400 and continuation | Reads chunks and parses header/body | 0x41640f8 / 0x4164174 and subsequent read | DOWN_REP sideband transport |
| 0x2003 | Reads/tests and acknowledges bit 4 | 0x4165ce4 / 0x4165f1c, 0x4165f70 | ESI DOWN_REP_MSG_RDY in sideband context |

Upstream windows 0x1200/0x1600 are not promoted from constant hits. Ordinary DP
and MST-specific sequences demonstrate meaningful local coverage. Raw census
counts still include unrelated values; numerical equality alone is not access.

## Sideband Codec

Classification: **DCP_MST_SIDEBAND_CODEC_FOUND**.

The constructor at 0x4161398 selects vtable address point 0x47a3150. Declared
chains bind slot +376 at 0x47a32c8 to receive region 0x41640f8. The sender at
0x4165ce4 builds LCT/LCR, RAD, broadcast/path bits, six-bit body length,
SOMT/EOMT and sequence, calculates CRCs, acknowledges ESI bit 4 and writes
DOWN_REQ. The receiver reads DOWN_REP, checks header CRC/sequence and reassembles
body fragments with bounds checks. This is structural codec evidence.

Header CRC at 0x416449c uses feedback 0x13, top bit 0x10 and four zero bits.
The actual leaf ends at 0x4164520; the inferred 144-byte region also includes
the following eight-byte return-zero leaf. The exact 136-byte CRC body SHA-256 is
`712658c0b8df67416676df2a4678df55e5d32ccd817797f05573fb272fdb2894`.
Body CRC at 0x4164410 is 140 bytes, feedback 0xd5 and eight zero bits, SHA-256
`1a18c82bf7e006bd5291d2d84326fd93c945ef2a34983efaacf0130ba24482e5`.
Both connect directly to the identified packet path and match the frozen oracle.
No firmware function was emulated or executed.

## Topology Model

Classification: **DCP_MST_TOPOLOGY_MODEL_FOUND**.

Region 0x4166858 sends LINK_ADDRESS=0x01, handles the 16-byte GUID at reply +1,
port count at +17, peer/input/output flags and variable port records. It creates
port objects through 0x4161f28, adds them to a collection and recursively invokes
topology discovery for branch peers. Port construction stores manager/parent at
+184/+192, RAD at +204, route counters at +212 and port number at +224, extending
the route by nibble with a checked length. This is more than branch OUI metadata.

Region 0x41666b4 builds ENUM_PATH_RESOURCES=0x10 and decodes big-endian full and
available PBN into port fields +230/+232. Region 0x416626c builds
REMOTE_DPCD_READ=0x20 with routed port, 20-bit address and count; 0x4165c0c builds
REMOTE_DPCD_WRITE=0x21. Region 0x4166388 builds REMOTE_I2C_READ=0x22 transaction
descriptors and checks reply length/count. These use the same parent route and
sideband codec, not the retired host selector.

## Payload And ACT

Classification: **DCP_MST_PAYLOAD_ALLOCATOR_SEARCH_INCONCLUSIVE**.

Payload-allocation **primitives** are positively identified. Manager slot +320
reaches 0x416525c, multiplying link-derived state at manager +112 by an input
requirement, rounding a fixed-point product and forwarding PBN to gated slot
+264. That slot is 0x4166524: it serializes ALLOCATE_PAYLOAD=0x11, port nibble,
payload ID and big-endian PBN into a five-byte request. Clear-table opcode 0x14
is built at 0x41667e4. Complete multi-stream reservation policy is not recovered.

Region 0x4128fbc writes branch ID/start/count, polls 0x2c0 mask 1, invokes a
source-side virtual operation, then polls mask 2. The status helper's local loop
has ten iterations but returns zero after exhaustion; it is not a validated
ACT-success or transport-safety guarantee. Source ACT emission and all dynamic
receiver/caller bindings are not fully qualified. No selector gate is promoted.

DPTX region 0x4063c48 checks start+count <=64, clears sixteen 32-bit slot words
and writes seven-bit fields through register-interface helpers. Its local slot
population uses literal payload ID **1**. Helpers 0x405e9e0/0x405ecdc forward to
virtual register methods; they are not independently proved MMIO leaf stores.
Offsets such as 0x2428 are internal source-register arguments, not DPCD addresses
or public APIs.

The full bandwidth-to-PBN-to-slot policy for multiple simultaneous independent
streams, distinct VCPI/ID ownership and source ACT completion remains unproved.
A serializer and one-ID table routine do not establish a complete multi-stream
allocator. The inconclusive classification preserves, rather than dismisses,
the positive allocation and ACT-control primitives.

## One-Link Packetizer

Classification: **DCP_MST_PACKETIZER_SEARCH_INCONCLUSIVE**.

Source payload-slot control exists, but no qualified path accepts multiple
independently timed logical streams on one DPTX instance and maps each to a
distinct payload ID. The inspected slot routine writes ID 1; it does not prove
a multi-ID scheduler. Other timing/video functions and indexed configuration
fields are insufficient alone. Some rely on compiler-outlined helpers whose
full data flow is not reconstructed automatically.

DISP_INT/DISP_EXT0/DISP_EXT1 are independent outputs sharing application bytes,
not multiple streams on one link. Overlays, DSC slices, independent Thunderbolt
DP tunnels and tunnel-bandwidth allocation remain negative controls. A sideband
manager may support single-stream sideband or one allocated payload without
establishing the desired multi-display MST behavior.

The remaining boundary is **ownership and capacity of the one-DPTX source
stream-to-payload packetizer, including multiple independent timing streams and
distinct payload IDs**. It is no longer an unavailable DCP image or missing host
DPCD transport. No new generic scan or hardware experiment is scheduled.

## Cross-Generation Differential

The M4 comparison is LZFSE IM4P decoded to standalone ARM64 Mach-O, UUID
**81BAF476-679D-3CC0-8C6A-E6B6FA659D5E**, text VM base 0. Its Ap,DCP2 digest is
`15f7707b88858d0ea60ba96e4a58bb89388a19d461e4a89b0f9ec3d34ba244f46005fb949ed4cc3e21166412f542fa8f`.
Raw IM4P SHA-256:
`c487d63174c3c606b2394532c46e0f165e2ef07f515fbb954c1eabb67ff963b8`.
Decoded size 11,862,016 bytes, SHA-256:
`c0ebc96cab2ef315ed968c39ce6134f6d90503e84b0f6bc214c3ed3c91949abc`.
Version strings are AppleDCP-1041.120.7~2715-t8132dcp.RELEASE and
RTKit-3255.160.4.release. The symbol table is empty and function-start command
absent; the same inferred-region policy is used.

M4 coverage is 26 sections, 10,433 inferred regions, 349 candidate regions,
709 string hits and 766 direct references. Whole payloads and compared
text/const/cstring/log section hashes differ. Selected MST class, MSTM, PBN,
allocation, dp2-no-mst and updatePayloadTable strings are shared, with no
M5-only or M4-only hit in that diagnostic set.

The exact CRC leaves are byte-identical: M5 header CRC 0x416449c matches M4
0x15aa44 for 136 bytes; M5 body CRC 0x4164410 matches M4 0x15a9b8 for 140 bytes.
This is narrow shared-code evidence, not proof all DPTX code is unchanged.
Layouts, relocations and untraced functions prevent a complete semantic delta
claim. No M4 capability or new-to-M5 MST support is inferred.

| Frozen Constant Group | M5 Candidate Regions | M4 Candidate Regions |
| --- | ---: | ---: |
| dp_training_control | 18 | 21 |
| mst_control_and_irq | 4 | 3 |
| mst_payload_opcodes | 25 | 23 |
| mst_payload_registers | 1 | 1 |
| mst_remote_opcodes | 3 | 2 |
| mst_sideband_crc | 13 | 12 |
| mst_sideband_windows | 4 | 4 |

These are unqualified co-occurrence counts across different inferred regions,
not counts of MST functions or evidence of newly added protocol features.

The supplementary [25G82-to-25G83 public diff](https://github.com/blacktop/ipsw-diffs/blob/4c1e7fcbf5d0865984f00560cd2086c9aba4e261/26_6_2_25G82_vs_26_6_2_25G83/README.md)
names the exact builds but provides no DCP/MST code finding that independently
settles this question. Its omission is not negative firmware evidence. The
manifest-bound extracted bytes are primary to this result.

## Asahi Context

M3A's pinned generation limits remain: populated M1-M3 display tables and their
historical "No MST!" wording do not determine M5 behavior; established M4 display
documentation is incomplete/TBD. Lack of Linux M5 MST support is not evidence
against the control implementation now found in Apple firmware. No new Asahi
hardware capability claim is made. The pinned m1n1 ADT format is parser evidence
only, never executed against the running machine.

## Combined Evidence Map

| MST Requirement | Preserved M3A Host Evidence | Identified M5 Firmware Evidence | Final Confidence |
| --- | --- | --- | --- |
| MST capability/control | No qualified host sequence | 0x021 read and 0x111 role/mode writes | VERIFIED_IN_IDENTIFIED_M5_DCP_FIRMWARE; STRONG_FIRMWARE_STATIC_EVIDENCE |
| Sideband transport | No qualified host codec | Routed codec, CRC4/CRC8, DOWN_REQ/DOWN_REP and ESI | VERIFIED_IN_IDENTIFIED_M5_DCP_FIRMWARE; STRONG_FIRMWARE_STATIC_EVIDENCE |
| LINK_ADDRESS/topology | Identity/branch boolean only | GUID, variable ports, parent/RAD and recursive enumeration | VERIFIED_IN_IDENTIFIED_M5_DCP_FIRMWARE; STRONG_FIRMWARE_STATIC_EVIDENCE |
| Remote DPCD/I2C | No routed host operation qualified | 0x20/0x21 DPCD and 0x22 I2C request/reply structures | VERIFIED_IN_IDENTIFIED_M5_DCP_FIRMWARE; STRONG_FIRMWARE_STATIC_EVIDENCE |
| PBN | No qualified host flow | Path PBN fields and fixed-point allocation argument | STRONG_FIRMWARE_STATIC_EVIDENCE for primitive; UNKNOWN for full policy |
| VCPI/payload allocation | No host allocator qualified | ALLOCATE_PAYLOAD and branch/source tables; inspected source uses ID 1 | STRONG_FIRMWARE_STATIC_EVIDENCE for primitives; UNKNOWN for multi-ID allocator |
| ACT | No host sequence qualified | Branch update, source operation, ACT_HANDLED polling | STRONG_FIRMWARE_STATIC_EVIDENCE for flow; UNKNOWN for complete source activation |
| One-link packetizer | Opaque firmware boundary | Slot control, no proved independent multi-stream binding | UNKNOWN |

VERIFIED_IN_IDENTIFIED_M5_DCP_FIRMWARE means BuildManifest-backed bytes for
J704AP/25G83, not execution on the daily-use M5 or an accessible macOS control
surface. String-only context is WEAK_FIRMWARE_STATIC_EVIDENCE until qualified.
No M5-only MST strings is a NEGATIVE_FIRMWARE_SEARCH_RESULT within the specified
comparison, not a hardware impossibility claim.

## Feasibility Result And Consequence

**M5_DCP_FIRMWARE_MST_CONTROL_EVIDENCE_FOUND_PACKETIZER_UNRESOLVED**.

The exact J704AP firmware is identified, obtained and decoded, and contains
real MST protocol, topology and payload-control machinery. M3A's negative host
result remains correct in its host scope; it does not imply the entire source
stack lacks that control. The stronger implementation result still requires
multiple independently timed streams on one physical link, not just the codec,
one-ID table or static logs.

The next milestone should focus **only on one-DPTX packetizer ownership/capacity
and multi-stream timing-to-payload binding**. Do not return to selector 0,
generic DPCD access, a wrapper or a hardware experiment. Native MST was not
exercised and no execution authorization is requested.

- Selector status: **RETIRED_ON_DAILY_USE_M5**.
- DPCD gate: **NOT_READY_FOR_DPCD_TEST**.
- Historical M2F marker remains consumed; the DPCD-read marker remains absent.

## Provenance And Reproduction

The two new tools are narrowly scoped:
[ipsw_dcp.py](../../tools/ipsw_dcp.py) acquires the fixed device/build manifest
and exact selected members; [dcp_firmware.py](../../tools/dcp_firmware.py) parses
the identified Image4, ADT, nold BUND/standalone runtime inputs and reuses the
frozen [M3A scanner](../../tools/scan_mst.py). Existing native code, transport
code, public collector, binary readers and the protocol oracle are unchanged.

| Tool / Test | SHA-256 |
| --- | --- |
| tools/ipsw_dcp.py | `0d35871e8701427db8d9691004284bb3ce00c6b1e7d8977affcd75f085f6b4e9` |
| tools/dcp_firmware.py | `796a67157d8516e11a507ab684ab4acac2de71e11392710cf5e8323bc969927e` |
| tests/test_iodp_static.py | `4a2271f218410b8859856d8152c98afbb4e6af637fb82e5a98e143716b2a34dd` |

Receipts below are relative to ignored artifacts/sources/m3b. Earlier captures
remain immutable; final receipts bind all six scanner/reader dependencies and
the oracle hash, plus explicit detail addresses and pointer-slot selections.

| Receipt | SHA-256 |
| --- | --- |
| 25G83-manifest-20260914/extraction.json | `ac30894ad38dd0cb231f43097a5ec0cd6612ecefab5eae14edc358813ef6eef5` |
| 25G83-components-20260914/extraction.json | `a6eff7644aa9c9c2e9c83a48394a180613394ca9c8f74e87b115e7564d79c5ba` |
| 25G83-m4-components-20260914/extraction.json | `70aa469a53e0927f2969758c375e0bfd8e2fcdcc034b1bf6a480dfce976f3a31` |
| 25G83-m5-verified-20260914/decoded.json | `584080efc96e05072d1b0b0172834a0f561216d07833e6eb3219831be0f5d9a3` |
| 25G83-m4-replay-20260914/decoded.json | `bbe02b343a1cec727efe70af60e3928b5f7979bb9aa627549a79f54322682a2d` |

Retained device metadata SHA-256 is
`78d0fb5450159e584021bfa8176b8607cecf06b89b1d2e03ad506d86880b763c`;
exact-build metadata SHA-256 is
`5c8e36e6ccb18fb3d217c42a2670404d53323e942c2079e214781dbd7bb5956c`.

| Public Format / Comparison Source | Revision And SHA-256 |
| --- | --- |
| [Blacktop BUND structs](https://github.com/blacktop/ipsw/blob/10c88230b8c2b90145a2dc6895551d0eda6eb692/pkg/bundle/bundle.go) | 10c88230b8c2b90145a2dc6895551d0eda6eb692; `be5f7184b9006fa7e19a11216715008c010a433af19c8b6c652a35f430940522` |
| [Blacktop runtime mapping](https://github.com/blacktop/ipsw/blob/10c88230b8c2b90145a2dc6895551d0eda6eb692/pkg/bundle/runtime.go) | Same pin; `e61bc1c63884b67a5baab97e5ab31d6447885c7a6b38b93a5c36dc663918f741` |
| [m1n1 Apple DeviceTree format](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/adt.py) | b4654b32941d51afdb77579d63e7cb1aa6c03ecc; `b1d0c1af0ea83f73b9e6003efb9b42a4892cb35be8efb9c7566d3512c1846a3f` |
| [Apple chained pointers](https://github.com/apple-oss-distributions/dyld/blob/fd8d0c4d52320ebf64db34f3cb280310d905c5ae/include/mach-o/fixup-chains.h) | fd8d0c4d52320ebf64db34f3cb280310d905c5ae; `90bd2b316ada7fc5fe47c2872ea679f0c6cc6d249ed5965dbbdc5bea5afdd21a` |
| Public 25G82-to-25G83 diff summary | 4c1e7fcbf5d0865984f00560cd2086c9aba4e261; `4150470002ccad91ae219bd2f8bff31101ac35ea95740abe88e571e7d7a5c932` |

The initial guessed Blacktop IM4P source path returned 404; it is not evidence
of missing firmware. The first BUND adapter expected the generic urst/ASN.1
variant and rejected the real nold/ADT variant. The observed variant was then
implemented with synthetic tests; unused generic support was removed. The first
post-text shortcut pointed OS_LOG at zeros, so it was excluded until declared
ubdl and three exact code references resolved its mapping. The initial M4 pass
decoded but did not scan standalone Mach-O; a tested input adapter completed
the comparison. None of these incomplete passes is negative MST evidence.

Fresh reproduction uses new output directories and public/offline operations:

```sh
python3 -m unittest discover -s tests -p 'test_iodp_static.py' -k m3b
python3 tools/ipsw_dcp.py --output artifacts/sources/m3b/local-manifest
python3 tools/ipsw_dcp.py --manifest-directory artifacts/sources/m3b/local-manifest --output artifacts/sources/m3b/local-components
python3 tools/dcp_firmware.py --components artifacts/sources/m3b/local-components --output artifacts/sources/m3b/local-scan --scan
python3 tools/ipsw_dcp.py --manifest-directory artifacts/sources/m3b/local-manifest --comparison-m4 --output artifacts/sources/m3b/local-m4
python3 tools/dcp_firmware.py --components artifacts/sources/m3b/local-m4 --output artifacts/sources/m3b/local-m4-scan --scan
```

The metadata gate requires the exact build to remain listed as signed. A future
metadata/download failure must be reported, not bypassed by substituting another
build. The tools refuse existing output directories. To replay detailed bodies,
use --detail-address and --pointer-slot selections stored in the final receipt;
addresses are only valid for the recorded image identity. A fresh clone lacks
the ignored historical files. No reproduction command loads or invokes firmware.

## Validation

| Check | Result / Scope |
| --- | --- |
| `cmake --build build` | PASS, existing strict-warning native targets up to date |
| `ctest --test-dir build -L unit --output-on-failure` | 9/9 PASS, 5.80 seconds; unit and userspace containment only |
| `cmake --build build-sanitized` | PASS, existing ASan/UBSan targets up to date |
| `ctest --test-dir build-sanitized -L unit --output-on-failure` | 9/9 PASS, 7.98 seconds; no hardware label selected |
| `python3 -m unittest discover -s tests -p 'test_iodp_static.py'` | 83/83 PASS, including eleven M3B methods |
| Focused `-k m3b` tests | 11/11 PASS after the final parser narrowing |
| Final offline replay | M5/M4 firmware scan sections, candidates and diagnostics identical to retained prior valid passes |
| Detailed evidence | 45 full inferred-region receipts and 19 selected declared pointer bindings reproduce; raw bytes, sizes, addresses and SHA-256 verified |
| Build association | Exact production identity and type-adjusted SHA-384 component digests verified; J704AP tree agrees; M4 remains separately labeled |
| Frozen inputs | M3A report, oracle, existing readers, collector, native sources and native binaries unchanged |

The consumed M2F marker SHA-256 remains
`2f3da1f224c0602dc46f812d3f6eb2c1560fe7a82c1a89f93eedb725b2726efc`.
Historical successful/stopped receipt hashes remain
`86ee9fdd87eb631e7552b0087471a149c183667c2162e838866ce993e1dd3d04` and
`79387346acdaebed1efb2284a531de8f2cf5aad1d64915a3f5f527040ebae840`.
M2G-DPCD-READ-ATTEMPTED remains absent. The existing helper/parent were not run,
including no-open mode; contract tests use synthetic frames and mock processes.

M3B's evidence is public-download and static/offline only. No new live display
capture was needed. Compilation, test success and static control evidence do not
demonstrate native MST on the daily-use M5. No firmware was executed, flashed,
restored, personalized on the device or uploaded. No system configuration changed.

## Git Publication

The milestone remains on research/m5-dcp-firmware-mst, based on the integrated
host-scan tag at `24f2d1c3065ec0d7f80b5a53077f3e169f79368f`.

- `34237386881d5ef30140a1bc5d13d3c72adb19ed`: exact J704AP firmware mapping,
	public metadata, range accounting and Image4/DeviceTree association report.
- `4e7191bab77b85f57033719a7fb946a65a89331a`: bounded extraction/firmware tools
	and eleven synthetic regression methods. Committed bytes match final receipts.
- The containing findings commit completes the firmware classification,
	validation, combined map and current indexes/ledger E181-E193/S57-S61.

Publication contains eight text paths: two static tools, one existing test file
and five research/index documents. Firmware, raw captures, decoded payloads,
downloaded sources and build outputs stay ignored. No native/transport source,
build setting, frozen oracle, prior M3A report or historical selector report is
changed. All E001-E180/S01-S56 ledger rows remain byte-for-byte intact.

Before publication, all 26 protected local/remote branch, tag and peeled-tag
identities matched, and the M3B remote branch did not exist. Main and
m5-mst-host-scan-v0.7 remain at the integrated M3A state. The push is explicitly
branch-only and non-force:

```sh
git -c push.followTags=false push -u origin refs/heads/research/m5-dcp-firmware-mst:refs/heads/research/m5-dcp-firmware-mst
```

M3B is not merged, no PR is created and no additional tag is part of this
publication. Git publication does not authorize a private display operation.