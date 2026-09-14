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