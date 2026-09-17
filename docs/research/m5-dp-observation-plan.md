# M5P5 External DisplayPort Observation Architecture and Acquisition Decision

Research/design only, 2026-09-17. No electrical capture,
hardware purchase, cable movement, or new Mac display query is authorized here.

## Objective

Enable multiple independent external displays from the base M5 MacBook Pro
through ordinary USB-C / DisplayPort MST hubs, without DisplayLink or requiring
separate Thunderbolt DP tunnels. Select the lowest observation layer that can
discriminate the next control-path question, not every eventual source question.

Local hypothesis: a complete passive upstream AUX capture can show branch
enumeration and payload-control progress (Q1-Q4/Q6); it cannot establish actual
simultaneous main-link video transmission (Q5). The discriminating public-source
check is whether payload-register programming and ACT-status polling are AUX
operations while generating ACT and payload packets is a separate driver action.

## M5P4 Baseline

[M5P4](m5-public-log-correlation.md) was audited and published unchanged on
`research/m5-public-log-correlation` at
`db517239b496168b05490a6c3d71af1f88329382`, with upstream equal, 0/0. Its three
linear commits, 477 scoped historical records, immutable review, capture hashes,
and 200 offline tests passed. All 45 previously published head/tag/peeled
identities were preserved; publication added only the M5P4 branch. No merge,
PR, tag update, live log cycle, or reconnect occurred.

[M5P3](m5-passive-runtime-topology.md) remains published at
`369b5e5f202640f906904d2dc91413bd1b0930f3`. Its connected snapshot reports a
non-tunneled USB-C transport with two lanes at HBR3 (8.1 Gbit/s per lane),
`SinkCount=1`, and one VG248 logical display record. M5P4 logs contain
`handleSinkCountChanged oldCount=0 newCount=2 add=1 remove=0`.
These differently scoped software counts are not assumed to be DPCD fields or
to identify two distinct monitors. Same-DPTX source ownership remains unresolved.

## Wire Questions

All result labels below describe possible future observations, not M5P5 captures.

| Question | Minimum evidence and interpretation | Layer |
| --- | --- | --- |
| Q1: Does the upstream link enter MST mode? | Preserve a successful receiver `DP_MSTM_CAP` read separately from a `DP_MSTM_CTRL` write with `DP_MST_EN` and its AUX ACK, or a successful state read. `WIRE_MST_MODE_ENABLED` means observed control state, not verified MST video. Capability and sideband traffic alone are insufficient. | AUX |
| Q2: Does the branch expose two downstream paths? | Complete `LINK_ADDRESS` reply bound to request/route/generation: branch GUID, port numbers, direction, peer type, message capability, DP/legacy plug status. Exclude input ports; distinguish logical/internal ports and converters from physical monitors. | AUX plus decoded sideband |
| Q3: Does the source query both paths? | Routed `REMOTE_DPCD_READ` / `REMOTE_I2C_READ` requests and replies with per-port addresses and lengths; reconstruct EDID offsets/segments and checksums. Equal EDIDs can still be two addressed paths. Missing reads may reflect caching, not absent monitors. | AUX plus decoded sideband |
| Q4: Does it allocate multiple payloads? | Correlate `ENUM_PATH_RESOURCES`, `ALLOCATE_PAYLOAD`, nonzero payload IDs and accepted PBN, local slot writes, payload-table update and ACT-handled status. Count concurrently retained allocations within one generation, not repeated requests or reused IDs. | AUX plus decoded sideband |
| Q5: Are multiple VCs actually transmitted? | Same physical main link, overlapping interval, decoded MTP/VC schedule and valid per-stream video/timing evidence. Two allocations do not prove this. Independent content/source ownership requires additional bindings. | Main link |
| Q6: Where does a one-allocation sequence stop? | Last completed control step and exact next request/reply/NAK, with capture boundaries, gaps and quiet interval preserved. This locates observed wire progress, not the internal macOS/DCP policy owner or a global hardware limit. | AUX plus decoded sideband |

## AUX / Sideband Observability

Implementation oracle: Linux revision
`238650ef6c7c7cca08e032527329424c9fbd70e5`, pinned from upstream HEAD on
2026-09-17. Public implementation evidence, not proprietary specification text
or a statement about M5 behavior:

- [drm_dp.h](https://github.com/torvalds/linux/blob/238650ef6c7c7cca08e032527329424c9fbd70e5/include/drm/display/drm_dp.h)
  defines AUX opcodes, DPCD fields, MST request IDs and reply types.
- [drm_dp_mst_helper.h](https://github.com/torvalds/linux/blob/238650ef6c7c7cca08e032527329424c9fbd70e5/include/drm/display/drm_dp_mst_helper.h)
  defines route, port, payload and reply structures.
- [drm_dp_mst_topology.c](https://github.com/torvalds/linux/blob/238650ef6c7c7cca08e032527329424c9fbd70e5/drivers/gpu/drm/display/drm_dp_mst_topology.c)
  encodes/reassembles sideband transactions. `drm_dp_add_payload_part1()`
  programs DPRX DPCD, then explicitly leaves ACT/payload-packet generation to
  the driver. `drm_dp_check_act_status()` polls receiver-reported ACT handling.
- [drm_dp_helper.c](https://github.com/torvalds/linux/blob/238650ef6c7c7cca08e032527329424c9fbd70e5/drivers/gpu/drm/display/drm_dp_helper.c),
  `drm_dp_dpcd_write_payload()` (line 954), writes the update-status field,
  then payload ID/start/count at `0x1c0`, then reads update status.
  `drm_dp_dpcd_poll_act_handled()` (line 1024) reads receiver status, not
  transmitted packets. This focused check supports the local hypothesis.

The six unmodified source downloads are retained locally under
[artifacts/probes/m5p5/sources](../../artifacts/probes/m5p5/sources).
SHA-256 is over exact downloaded bytes; no Linux code was compiled or executed.

| File at the pinned revision | SHA-256 |
| --- | --- |
| `include/drm/display/drm_dp.h` | `7f7958ee96e2dcd2329ef53422b1801eb2ba0a2f47febdc42cfb808a45754c5f` |
| `include/drm/display/drm_dp_mst_helper.h` | `d0f4dda7b717db766c494e0ec63d72c65291a09c12ede6ec759659c67821f44c` |
| `drivers/gpu/drm/display/drm_dp_mst_topology.c` | `9d09eca1a83d53fc2a45c8313e10513b88bef0dbd7a805fa359c859e16831139` |
| `drivers/gpu/drm/display/drm_dp_helper.c` | `e9f9869b034230c39766a1237ad7b96b3d88e8f3e8c5b315189a2a855ce7d155` |
| `include/linux/usb/typec_dp.h` | `601bc7daf26aee18d4efce18e18af659c9b5937ca59b16f4026e7cde04ba2c50` |
| `drivers/usb/typec/altmodes/displayport.c` | `bd64b70bf2e4c2200821c3c3a21b88c2a9c5212c494ed943bd60c6079d5067b0` |

### DPCD and AUX Oracle

Addresses below are generic native-DPCD addresses, not observed values from
this Mac or hub and not instructions to issue reads/writes.

| Region | Public definitions and evidence use |
| --- | --- |
| `0x000-0x00e`, `0x080-0x08f`; extended receiver caps `0x2200` | Receiver revision, rate/lanes/coding, downstream-port descriptors and format-conversion capabilities. Revision and descriptor layout must be decoded, not assumed. |
| `0x021`, `0x030-0x03f` | `DP_MSTM_CAP`: bit 0 MST capability, bit 1 single-stream sideband capability; `DP_GUID` is 16 raw bytes. Capability is not enablement. |
| `0x100-0x108`, `0x111` | Link rate/lane count/training/coding and `DP_MSTM_CTRL`: bits 0/1/2 are `DP_MST_EN`, `DP_UP_REQ_EN`, `DP_UPSTREAM_IS_SRC`. Native HBR3 rate code is `0x1e`, not M5P3's software `LinkRate=4`. |
| `0x1c0-0x1c2` | Payload ID, start slot, slot count. Zero-count deallocation and reset semantics must not become an additional stream. |
| `0x200-0x205`; ESI `0x2002-0x200f` | Sink count, service IRQ, lane and sink status; `DP_GET_SINK_COUNT` combines bit 7 with bits 5:0, excluding bit 6 CP-ready. Preserve the whole byte. `DOWN_REP_MSG_RDY` / `UP_REQ_MSG_RDY` are bits 4/5 of the service IRQ byte. |
| `0x2c0`, `0x2c1-0x2ff` | Payload-table updated bit 0, ACT-handled bit 1; slot-ID table. Slot numbering must follow the negotiated coding: this HBR3 question uses 8b/10b, with usable slots 1-63, not UHBR's 0-63 convention. |
| `0x1000`, `0x1200`, `0x1400`, `0x1600` | Respectively DOWN_REQ, UP_REP, DOWN_REP, UP_REQ sideband buffers. An AUX fragment/ACK is not an entire sideband request/reply. |
| `0x500-0x50b`, `0x060-0x06f`, `0x090`, `0x120`, `0x160` | Branch OUI/ID/revisions and DSC/FEC capabilities/control for topology comparability. Read only if present in the future recorded traffic. |

Native AUX WRITE/READ opcodes are `0x8`/`0x9`; I2C WRITE/READ are `0x0`/`0x1`,
write-status update `0x2`, MOT flag `0x4`. Native replies occupy bits 1:0;
I2C replies bits 3:2. ACK/NACK/DEFER must retain layer and raw bits. Native
payloads are at most 16 bytes per transaction. EDID I2C address `0x50`, segment
address `0x30` and offset-setting writes are I2C-space values, not DPCD
`DP_GUID` or an MST request ID with a coincidentally equal number.

### Sideband Oracle

The owning implementation symbols are `drm_dp_encode_sideband_req()`,
`drm_dp_sideband_parse_reply()`, `drm_dp_sideband_parse_req()` and their
message-specific parsers in the pinned topology file. An ACK reply has a
clear high bit in the reply's first byte; a NAK has it set. Preserve request
type, NAK GUID/reason/data and raw body. An AUX ACK of a request-buffer write
does not mean the branch accepted that request.

| Message | Request ID | Fields to retain and decision use |
| --- | --- | --- |
| `LINK_ADDRESS` | `0x01` | Request route and full reply: branch GUID, port count, port number, input flag, peer type, MCS, DDPS, legacy presence, DPCD revision, peer GUID, simultaneous-stream and stream-sink counts. Port descriptors, not an aggregate count, answer Q2. |
| `CONNECTION_STATUS_NOTIFY` | `0x02` | Upstream notification with branch GUID, port, legacy/DP plug flags, MCS, direction and peer type; source's reply and IRQ handling. Update topology epochs rather than appending duplicate sinks. |
| `ENUM_PATH_RESOURCES` | `0x10` | Port request; reply port, FEC-capable flag, full and available PBN. Resource advertisement is not allocation. |
| `ALLOCATE_PAYLOAD` | `0x11` | Port, number of SDP streams, 7-bit VC payload ID, 16-bit PBN and stream-sink array; ACK port, VCPI and accepted PBN. Keep destination/RAD and generation; nonzero accepted allocation is control evidence. |
| `QUERY_PAYLOAD` | `0x12` | Port and VCPI request; reply port and allocated PBN. The reply does not echo VCPI, so bind to its complete request. |
| `CLEAR_PAYLOAD_ID_TABLE` | `0x14` | Observe broadcast/path context and reply; invalidates earlier allocation state. Included because resets determine whether payload IDs overlap. |
| `REMOTE_DPCD_READ` | `0x20` | Port, 20-bit remote address, requested byte count; ACK port/count/data. A request alone proves attempted access, not a successful read. |
| `REMOTE_DPCD_WRITE` | `0x21` | Port/address/count/raw data and reply; preserve failure details. Observe source-issued writes only, never synthesize them. |
| `REMOTE_I2C_READ` | `0x22` | Port, preceding I2C transactions with device IDs/data/stop-delay fields, read device/count; ACK port/count/data. Reconstruct each EDID block with explicit request context. |
| `REMOTE_I2C_WRITE` | `0x23` | Port, I2C device ID, count/data and reply. Distinguish normal EDID offset/segment operations from native-DPCD writes and from a complete EDID read. |
| `POWER_UP_PHY` | `0x24` | Port and reply. A power-up request/ACK is not stream creation. |
| `POWER_DOWN_PHY` | `0x25` | Port and reply, with lifecycle effects retained; not a requested MacMST operation. |

Peer types are `0` none, `1` source-or-SST-branch, `2` MST branch, `3` SST sink,
`4` legacy converter. `drm_dp_mst_is_virtual_dpcd()` explicitly allows multiple
protocol branches inside one physical hub. Therefore GUID/port multiplicity
does not automatically count separate physical boxes, monitors or M5 sources.

`AUX_CAPTURE_CAN_RESOLVE_NEXT_GATE` is conditional on naturally occurring,
complete Q1-Q4 traffic at the upstream observation point. This is a layer
sufficiency decision, not capture readiness or a promise that the connected
idle hub will repeat its discovery traffic. No stimulus is authorized in M5P5.

Native AUX ACK/NACK/DEFER and sideband ACK/NAK are separate layers. Preserve
both. Reassemble raw fragments using buffer/address, LCT/LCR/RAD, sequence,
SOMT/EOMT, length and header/body CRC before interpreting a reply. Sideband
sequence numbers are not globally unique. `DP_SINGLE_STREAM_SIDEBAND_MSG`
in `DP_MSTM_CAP` is a further reason not to infer MST video from sideband use.

The header CRC is four bits; the body/chunk CRC is eight bits, notwithstanding
the Linux helper name `drm_dp_msg_data_crc4()`. This report defines no substitute
wire decoder. A future decoder must validate raw bytes against the oracle and
mark CRC-invalid, partial or ambiguous reassembly unusable for positive claims.
The oracle is implementation evidence, not a guarantee that every debug decode
path is a canonical protocol validator.

An ACT-handled status read reports what the receiver says; it is not an AUX
copy of an ACT packet. Its association with the current table requires observed
reset/update boundaries and no relevant loss. A stale set bit is insufficient.

## Main-Link Observability

AUX cannot inspect MTP contents, show actual VC scheduling, verify two MSAs,
establish independent pixel streams, or validate packetizer correctness. Q5
becomes the next gate after two current accepted allocations and a qualified
ACT-handled sequence, or if the specific question is actual link packetization.
Full main-link decoding is not a minimum requirement for Q1-Q4/Q6.

## USB-C Alt Mode Topology

`UPSTREAM_USB_C_DP_PATH_MUST_BE_OBSERVED` for the current-hub question. The
Mac-to-branch link is between the M5 USB-C port and the ZMUIPNG 14-in-1 hub.
An observer only on a hub-to-monitor output cannot be assumed to see upstream
branch management; a downstream SST or HDMI conversion output is not that link.
This follows the supplied physical topology and the protocol distinction:
remote MST requests are carried on the source-to-branch AUX link. A downstream
output may expose a local sink's AUX/EDID or HDMI DDC, not the original branch's
upstream request buffers. The exact physical connector types on both current
hub outputs were not independently recorded; no new visual inspection or query
was requested. The M5P4 `AppleDCPDP2HDMI` label is not a cable inventory.

```text
M5 USB-C port
  -> USB-C DP Alt Mode upstream segment  <-- required observation point
  -> ZMUIPNG 14-in-1 branch / conversion functions
       -> display output -> ASUS VG248 A
       -> display output -> ASUS VG248 B
```

Public technical basis:
[VESA DisplayPort over USB-C](https://www.displayport.org/displayport-over-usb-c/)
describes native DisplayPort over an Alternate Mode with USB/power coexistence,
not USB-rendered graphics. The public
[TI HD3SS460 datasheet, SLLSEM7D, January 2017](https://www.ti.com/lit/ds/symlink/hd3ss460.pdf),
sections 8.3 and 9.2, shows reversible SBU/AUX routing and two-video/two-USB
versus four-video lane configurations. It is a generic routing example, rated
for older DP/USB rates, not a proposed HBR3 observer or an M5 circuit diagram.
No pin assignments or construction procedure are reproduced here.

Pinned Linux
[typec_dp.h](https://github.com/torvalds/linux/blob/238650ef6c7c7cca08e032527329424c9fbd70e5/include/linux/usb/typec_dp.h)
defines the DP SVID `0xff01`, mode/status/configure VDOs, pin assignments and
HPD/IRQ flags. Its
[Alt Mode driver](https://github.com/torvalds/linux/blob/238650ef6c7c7cca08e032527329424c9fbd70e5/drivers/usb/typec/altmodes/displayport.c)
handles status/configure and Attention notifications. These are USB-C/PD
control definitions, not an Apple implementation model.

| Requirement | Why an observer must preserve it |
| --- | --- |
| Orientation and connector/cable identity | Reversal affects high-speed mapping and AUX polarity/routing; determine orientation without forcing a different role. The existing captive-versus-detachable hub cable and suitable fixture genders remain a mechanical qualification gate. |
| CC, Vconn and PD | Preserve attachment, power/data roles, cable identity and any power contract. CC/PD-only decoding is not AUX capture; AUX runs as differential signaling on SBU. No power contract was recorded in M5P3. Do not apply historical VESA-page 100 W marketing as a current cable rating. |
| DP Alt Mode | Preserve discovery, entry, status/configure and exit, supported assignments, and all source/partner decisions. An instrument must not impersonate either partner to make a trace easier. |
| SBU/AUX | Receive both directions with documented differential/common-mode limits, loading, polarity handling and raw reply visibility; do not terminate it as a new sink. |
| Main-link mapping and USB3 | Keep two-lane HBR3 and any USB3 coexistence for a current-hub comparison. A four-lane-only fixture or adapter changes available bandwidth. Actual USB3 activity/negotiation is unknown until separately observed. |
| HPD | Native DP has a discrete HPD path; USB-C conveys DP HPD state/IRQ through PD Alt Mode status/Attention. Decode/observe this without synthesizing transitions. A DPA-400's HPD input is not automatically proof of all CC events on USB-C. |
| Signal integrity and grounding | Added connectors, cables, capacitance, bias, power-off leakage and common ground can disturb even an electrically nonparticipating observer. Require documented HBR3 transparency for the exact assembly, not merely an AUX decoder license. |

An HDMI analyzer only on a hub output is insufficient for Q1-Q4. A native-DP
analyzer can be sufficient on a genuine upstream native-DP lab segment, or with
a manufacturer-qualified USB-C observation fixture, but not via an arbitrary
USB-C/DP gender adapter, breakout or active converter. No such item is inserted.

## Native-DP Lab Equivalence

`NATIVE_DP_MST_LAB_TOPOLOGY_VALID` for the broad ordinary-MST **M5 source**
question, conditionally on the requirements below. This is scientific design
equivalence, not a claim that a particular adapter/hub has been tested or that
the original ZMUIPNG behavior must reproduce.

```text
M5 USB-C -> native-DP Alt Mode adapter -> native DP segment -> DP MST branch
                                          observation         -> monitor A
                                          point               -> monitor B
```

Native DisplayPort carried by Alt Mode is still sourced by the M5, not by a USB
graphics engine. A DP MST hub on that segment tests multiple VCs on one M5
physical outgoing link. It does not substitute separate Thunderbolt tunnels.
The inserted adapter must expose that native signal, not DisplayLink, another
USB graphics device, HDMI conversion, or an extra MST/tunneling branch.
"Alt Mode adapter" does not mean every component is electrically passive: a
PD controller/mux or redriver may be present. Its behavior needs documentation.

It is not guaranteed to select the same internal DCP/controller instance,
source-binding policy or physical route merely because the same Mac/port is
used. M5P2-M5P4 did not establish that private binding. A positive native-DP
result answers capability for the tested setup; a negative result neither
proves M5 impossibility nor explains the original hub. Resolving that hub's
count discrepancy still requires its upstream segment.

| Controlled variable | Requirement / confounder |
| --- | --- |
| Mac/OS/port and display state | Same base M5/OS build and recorded source port for a later comparison; no assumption that "dispext" names prove internal ownership. Record lid/power/display modes; do not change them now. |
| Adapter function | Native DP Alt Mode signal path, HBR3 and MST/AUX pass-through, no EDID synthesis, display engine, MST aggregation or protocol conversion. Preserve short HPD IRQs. The pinned Linux `drm_dp_mst_wait_tx_reply()` documents that a real Type-C/DP adapter can filter short HPD pulses; adapter choice is not neutral. |
| Lane count and USB3 | The baseline has two DP lanes. A native DP adapter may use four and remove USB3 sharing; label that as a distinct capacity experiment unless two-lane behavior can be matched through a documented, separately approved method. Do not force lane settings now. |
| Link rate/coding, DSC/FEC | Preserve or explicitly stratify HBR3, 8b/10b, DSC/FEC capability and enable state. DP 1.4 on a box does not prove those states. No forced DSC or mode setting. |
| Branch chipset/firmware | Record branch GUID/OUI/revision and chipset if established. A different branch changes topology, interoperability and advertised resources. It is a contrast, not evidence of the ZMUIPNG implementation. |
| Downstream transport | Native DP monitors remove possible HDMI conversion. Keeping the same VG248 panels, mode and downstream conversion where feasible reduces confounding; output connector types remain to be documented separately. |
| Cables/PD/HPD/repeaters | Preserve native AUX and unmodified EDIDs, document PD/mux/retimer behavior, cable lengths/ratings and exact insertion assembly. HBR3 pass-through is required even for AUX-only capture. |

No consumer adapter or hub is selected: the requirements are established, but
no low-cost product has been qualified against them. A sacrificial adapter/hub
can be replaceable laboratory equipment, not electrical protection for the Mac.
Native DP is a fallback contrast for future approved work, not a reason to
disturb the currently connected hub or delay qualifying direct USB-C AUX access.

## Analyzer Market

Checked 2026-09-17. `Documented` below means manufacturer documentation, not
MacMST hardware verification. `Unqualified` means the surveyed documents do
not close that capability, not that it is impossible. Capture of an instrument's
own source/sink transactions is distinct from observing two real devices.
Current catalogue presence does not prove stock, a support contract or a price.

| Exact product / option | USB-C Alt Mode inline | Native DP inline | AUX decode | MST sideband decode | HBR3 main-link capture | MST VC/MTP decode | Passive observation | Current support status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Unigraf DPA-400 2.1; DP Y-cable `546126`, optional USB-C Y-cable `546127` | Documented optional cable; exact hub fit/PD limits unqualified | Documented bypass Y-cable | Documented raw/parsed DPCD, I2C/EDID | Explicitly documented | No; main lanes bypass measurement unit | No | Manual says AUX communication is not participated in; exact assembly still needs qualification | Current quote/demo product; manual v13, SW 2.1, 2023-09-06; Windows 10/8/7 listed |
| Ellisys Type-C Tracker Standard DP `CTR1-A-STD-DP`; Pro `CTR1-A-PRO` | Documented two test receptacles, SBU AUX and PD, orientation detection | Not documented as native-DP instrument | Documented AUX/SBU capture and field/raw views | Full MST reassembly/CRC/Q1-Q4 export coverage unqualified | No; gigabit pairs pass through | No | Documented nonintrusive capture with passive high-speed pass-through; exact HBR3 assembly acceptance still required | Current ordering/technical pages; free lifetime software updates claimed; DP edition or Pro required |
| Teledyne LeCroy quantumdata M42de HBR3 `00-00264`, or UHBR `00-00263`, passive probe option `95-00222` | Documented T.A.P.4 mode on Alt Mode links | Documented T.A.P.4 mode | Documented AUX Channel Analyzer | Documented MST negotiations; sample raw/reassembly completeness still required | Documented, 1/2/4 lanes up to 8.1 Gbit/s and UHBR on licensed system | Datasheet explicitly describes VC demux and MTP view | Explicit passive-monitor mode distinct from source/sink emulation | Current catalogue; datasheet `0125` (2025); capture/source option `95-00226` must be confirmed for intended feature set |
| Unigraf UCD-500 Gen3 with DP 2.1 Link Analyzer `MT6690` | USB-C test ports documented; inline passive assembly unqualified | Native DP test ports documented; inline passive assembly unqualified | Documented AUX logs/reference operation | MST up to four streams and MST CTS documented; passive sideband export unqualified | Link analysis documented, including DP 1.4a operation | Stream waveform/symbol/timing views documented; exact passive MTP export unqualified | Product says Link Analyzer (Monitor); surveyed Console manual describes reference modes, not enough to qualify a true passive tap | Current product and Console 3.10 manual rev 1, 2026-08-05 |
| Total Phase USB Power Delivery Analyzer | Historical PD instrument, not qualified AUX observation | No native-DP route documented | Not qualified for SBU AUX | Not documented | Not documented | Not documented | PD observation is not a DP AUX tap | Manufacturer EOL: unavailable for purchase; existing-customer support, no new software updates |
| Infineon CY4500-EPR EZ-PD Protocol Analyzer | Current PD instrument; DP AUX observation unqualified | No native-DP route documented | Not established; CC/PD is the advertised family purpose | Not established | Not established | Not established | Passive CC analysis does not imply SBU capture | Current active/preferred listing; predecessor CY4500 is EOL. Not selected for Q1-Q4 |

### Primary Product Sources

- **Unigraf DPA-400:**
  [current product and optional cable](https://www.unigraf.fi/product/dpa-400-displayport-aux-channel-monitor/),
  [January 2023 data sheet](https://www.unigraf.fi/app/uploads/2020/02/DPA-400-Data-Sheet-01-2023.pdf),
  [manual v13](https://www.unigraf.fi/app/uploads/2023/04/DP-2.1-AUX-Channel-Monitor-User-Manual.pdf),
  pp. 7-9 (nonparticipation/cables), 18-22 (buffering/direction/records),
  28-31 (binary/HTML export and limits).
- **Ellisys Type-C Tracker:**
  [technical data](https://www.ellisys.com/products/ctr1/technical.php),
  [edition/order codes](https://www.ellisys.com/products/ctr1/purchase.php),
  [brochure](https://www.ellisys.com/products/download/ctr1_brochure.pdf).
  Std HDMI/TB/TCPC editions are not substituted for Std DP. USB Explorer 350's
  USB3/PD claim alone is not this product's AUX capability.
- **Teledyne LeCroy M42de:**
  [current product](https://www.teledynelecroy.com/protocolanalyzer/quantumdata-m42de.aspx),
  [data sheet, Receiver/Capture Analyzer and Ordering Information](https://www.teledynelecroy.com/files/pdf/quantumdata-m42de-datasheet.pdf),
  [passive-monitoring white paper, pp. 1-3](https://www.teledynelecroy.com/files/whitepapers/using_displayport_passive_monitoring_wp.pdf).
  These explicitly distinguish the nonintrusive tap from a reference sink.
  The 2025 ordering table labels some MST CTS work "in development" while
  newer product text is broader; do not equate CTS availability with a
  verified capture license or assume the newest software feature set.
- **Unigraf UCD-500 Gen3:**
  [current product](https://www.unigraf.fi/product/displayport-2-video-generator-analyzer-ucd-500/),
  [Console 3.10 manual rev 1](https://www.unigraf.fi/app/uploads/2023/04/UCD-500-Console-User-Manual-v3_10-1.pdf),
  pp. 7-10, 106-110 and options. Powerful generator/CTS features are not
  grounds to authorize active emulation or claim passive interoperability.
- **PD-only screening:**
  [Total Phase EOL notice](https://www.totalphase.com/products/usb-power-delivery-analyzer/),
  [Infineon CY4500 EOL and CC-only description](https://www.infineon.com/cms/en/product/evaluation-boards/cy4500/),
  [current CY4500-EPR](https://www.infineon.com/evaluation-board/CY4500-EPR).
  Total Phase's recommendation of the older CY4500 is not current availability
  evidence; the manufacturer's replacement chain matters.

Keysight was screened but no exact currently supported AUX/MST observer was
qualified: its queried DisplayPort product/category pages returned HTTP 403,
including the
[DisplayPort software path](https://www.keysight.com/us/en/products/oscilloscopes/oscilloscope-software/displayport.html).
No guessed model or reseller assertion is entered as a supported capability.
An oscilloscope compliance application, analog eye test, or USB4 analyzer name
alone does not meet the wire requirements. This is a research-access limit,
not a conclusion that Keysight has no suitable equipment. Search-engine
responses were challenge pages or irrelevant; no capability claim relies on
them. Browser fallback was unavailable because Google Chrome is not installed.

### Documentation Receipts

Unmodified PDFs are retained locally, not republished as project source.
The filename/date is not treated as proof of current instrument firmware.

| Downloaded file | SHA-256 |
| --- | --- |
| `DPA-400-Data-Sheet-01-2023.pdf` | `1e387336077159e1bac20e5125bbf6857bad1aeacc2f0fb38156939862dd285e` |
| `DP-2.1-AUX-Channel-Monitor-User-Manual.pdf` | `37287d0b9aae563141c47a0149f6275e1da3a3903f28a4a939108ed505ac5ad3` |
| `quantumdata-m42de-datasheet.pdf` | `ee4a7e1e4a817389074a327843bb83c7cd0b95837d315230ec06726120e598bc` |
| `using_displayport_passive_monitoring_wp.pdf` | `a3a0d07e34d5d58f86ce562a888da50e53edb2918ac54d075129ff75bfa023db` |
| `UCD-500-Console-User-Manual-v3_10-1.pdf` | `7aab0dd9a0f35e0889952d28e9e5b673a3a5f77e530ac6e4daeb917022933e58` |
| `ctr1_brochure.pdf` | `e585063da65ce6ed2da326d8f491e87889628060fea645d9080e0ad9dcef6530` |
| `hd3ss460.pdf` | `ac2a6dc2c5d69ec20fd4403331cc1c05ea66523ffa92b0a2810acf742a729c46` |

### Candidate Acceptance Gaps

DPA-400 is the most explicit AUX/MST-only fit on paper. It uses binary files
readable by its GUI and portable HTML reports, not a promised JSON/CSV API.
Manual appendix A specifies a 14 MB buffer, 32 microsecond timestamp resolution
and AUX transactions as fast as 0.5 ms per request/reply. These are not a
guarantee of gap-free capture for every source burst. Obtain representative
raw exports, overflow/drop behavior and maximum sustained/burst qualification
before using an absent second request/allocation as evidence. The manual's
connection-independent direction mode infers source/reply from payload, so
record that as a heuristic unless independently verified. The original
DPA-400 direct main-link path was limited to 2.7 Gbit/s; current bypass cables
must be used/qualified for HBR3. A used base unit plus a decoder upgrade is not
automatically the right physical assembly.

The optional USB-C `546127` cable is documented, but its gender compatibility
with this hub's exact upstream cable, PD/Vconn current/voltage limits, all
orientations, two-lane/USB3 pass-through, AUX loading and power-off behavior
remain unverified. Do not solve connector mismatch with an improvised coupler.
Ellisys has two USB-C receptacles and a documented supplied analysis cable,
making it a useful alternative if current-hub insertion fits better. Its
typical high-speed pass-through claim (up to 20 Gbit/s on most systems) is not
a guarantee for this assembly. Native AUX data/export completeness, full MST
reassembly, filtering defaults and overload behavior remain acceptance gates.

Neither vendor's ESD statement establishes daily-use-Mac safety. A real sample
trace must demonstrate Q1-Q4 fields, fragmented replies, negative/retry cases,
direction provenance, export byte coverage, and measurable capture boundaries.
No sample export from either instrument was obtained in M5P5.

## Low-Cost AUX Options

`NO_PRACTICAL_LOW_COST_AUX_PATH_IDENTIFIED` in this bounded survey. Dedicated
AUX instruments exist, but an affordable, complete, electrically qualified
package has not been priced or secured. This is not a claim that a low-cost
receiver cannot be developed or borrowed. No DIY wiring procedure is provided.

| Path | Electrical / integrity and direction | Decode, reproduction and cost decision |
| --- | --- | --- |
| DPA-400 or Ellisys Std DP temporary access | Purpose-built AUX monitoring and manufacturer cable; exact loading, orientations and burst/loss behavior still gated above | Least additional hardware-development burden. Prices are quote-only in the surveyed pages, so neither is called inexpensive. Borrow/lab/demo qualification precedes purchase. |
| PD-only USB-C analyzer | CC/PD is a different signal from SBU/AUX; preserving USB data lanes is not measuring AUX | Current CY4500-EPR page displayed USD 428.34 per unit and 78 in stock when checked, but that volatile listing does not establish AUX capability. An inexpensive wrong-layer instrument cannot answer Q1-Q4. No order placed. |
| Existing lab oscilloscope and qualified high-impedance differential probe | Potentially sees low-bandwidth AUX without decoding HBR3. Must satisfy AUX differential/common-mode range, receive-only loading, edge bandwidth, polarity, isolation/ground and long capture duty cycle; scope sample rate alone is insufficient | Needs bidirectional AUX framing, request/reply, CRC/sideband software and a certified observation fixture. Can be economical only when already available and qualified, not a demonstrated ready-made low-cost route. |
| FPGA or dev board | A compatible AUX analog front end, receive-only behavior, protection, buffering and a controlled-impedance observation assembly are still necessary; FPGA I/O voltage labels do not establish compatibility | Existing native-DP transmitter/receiver IP is often an active endpoint, not a sniffer. Separate hardware development and bench validation would be needed; neither is designed or authorized here. |
| Generic single-ended logic analyzer | Digital threshold/rate does not make differential AUX directly compatible; grounding, common-mode limits, bias/loading and bidirectional turnaround matter | Manchester-like decoding alone does not supply safe electrical reception or MST reassembly. No direct pin probing, breakout or cable wiring is proposed. |
| Generic switch/evaluation board such as TI HD3SS460 | A routing component, not a nonparticipating analyzer; its documented DP 1.2a/5.4 Gbit/s use is not HBR3 qualification | The low component/evaluation-board cost is not the cost of a safe capture system. Not selected. |

As a bounded open-source check, the public recursive trees for
[Glasgow](https://api.github.com/repos/GlasgowEmbedded/glasgow/git/trees/d5c7dbf2441e4ee0e2cb603dd53b5f8a3c02175e?recursive=1)
(tree ID `d5c7dbf2441e4ee0e2cb603dd53b5f8a3c02175e`) and
[libsigrokdecode](https://api.github.com/repos/sigrokproject/libsigrokdecode/git/trees/71f451443029322d57376214c330b518efd84f88?recursive=1)
(tree ID `71f451443029322d57376214c330b518efd84f88`) contained no path matching
`displayport|dp_aux|aux.*dp|manchester` in the returned listing. This is a
filename-level lead check, not a code audit or proof no open-source AUX sniffer
exists. No project was cloned, executed, modified or used as hardware support.
Web discovery limitations above further bound the low-cost conclusion.

## Minimum Analyzer Requirements

`MACMST_ANALYZER_MINIMUM_REQUIREMENTS`:

1. Real-source-to-real-branch, bidirectional upstream AUX observation with a
   documented nonparticipating path. Native DP, or a qualified USB-C fixture
   preserving CC/PD/Vconn/orientation/SBU/HPD and USB3 coexistence as applicable.
2. Transparency to the recorded DP 1.4/HBR3 two-lane, 8b/10b link, with known
   cables and electrical limits. Support lower rates if the source negotiates
   them, retaining the actual rate. **No main-link decoding requirement.**
3. Native AUX and I2C-over-AUX request/reply bytes, opcodes, addresses, lengths,
   ACK/NACK/DEFER, timestamps, raw ordering, retry/error visibility. Declare
   resolution and maximum burst/sustained rate; no false precision.
4. Complete MST buffers/header/body bytes sufficient to reassemble/decode all
   listed Q1-Q4 messages, routed DPCD/EDID, PBN/VCPI and payload-table/ACT status.
   Vendor MST decode is convenient; a verified offline decoder over complete
   raw exports can satisfy the same requirement. No source-generated queries.
5. Full acquisition boundaries and loss/overflow/truncation/filtering receipts,
   original exports plus hashes and documented format/version, preserved raw
   bytes and exact decoder/cable/software provenance. No silent filters.
6. A representative offline export passes the proposed schema's negative cases
   and can distinguish two present ports and overlapping allocations before
   any physical Mac experiment is approved. Unknown vendor export fields are
   not filled from expectation.

Minimum means W1/W2 qualification, not that all candidate equipment has passed.
Neither nanosecond timing, video-frame capture, HDCP decryption, compliance
stimulus generation nor UHBR20 support is required for the next control gate.

## Ideal Analyzer Requirements

`MACMST_ANALYZER_IDEAL_REQUIREMENTS`: all minimum requirements plus synchronized
native HPD or USB-C CC/PD/Alt Mode and voltage context, full HBR3 1/2/4-lane
main-link capture, MTP/VC schedule and ACT-packet decode, per-VC MSA/VB-ID/SDP
timing, DSC/PPS/FEC visibility where used, and overlap/loss receipts in one clock
domain. Support both native DP and USB-C on documented true-passive assemblies.
Provide long pretrigger capture and open/exportable raw symbols/bytes with
validated import. The ability to separate streams does not require their
timings to differ; same timings or pictures do not prove one stream.

Independent-content experiments would need later approved, nonprotected test
content and explicit bindings. No HDCP bypass, authentication injection, or
content-protection changes are part of this requirement. M42de's documented
passive/VC mode is a future W3/W4 candidate, not a minimum-spec purchase.

## Wire Evidence Schema

`macmst.dp_wire`, proposed schema version `1`, is independent of the frozen
[DCP observer schema](dcp-observer-schema-v1.md). This is a design contract, not
a shipped live collector, commercial-format parser, or validated vendor import.
No existing M5P1 schema, fixtures, evaluator or real-evidence gate is changed.

### Capture Envelope

| Field group | Required semantics |
| --- | --- |
| `schema`, `schema_version`, `evidence_kind`, `capture_id` | Explicit `synthetic` or `hardware`; never inferred from a filename or scenario. A mixed-origin capture is invalid. |
| `generation_id`, `link_id`, `observation_point` | Capture-local identity for one physical upstream segment; topology diagram, source/branch direction, adapter/cable and connector orientation. USB-C versus native DP is explicit. A log registry ID is not a wire link ID. |
| `started_utc`, `ended_utc`, `clock` | Original clock ticks, unit, resolution, drift/uncertainty, epoch/wrap and any independently established wall-clock alignment. No fabricated nanosecond precision or causation from close timestamps. |
| `equipment`, `topology`, `environment` | Model, hardware/firmware revision, licenses, decoder mode, probe/cable part numbers, negotiated lane/rate/coding, PD state, hub/monitor identities, Mac/OS build and operator approval receipt. Unknown fields stay unknown. |
| `raw_artifacts`, `decoder_provenance` | Original binary/export SHA-256, byte length, source filename, format/version, software version and normalization revision; retain original unmodified locally. Archive reports with privacy review, not unrestricted EDID/HDCP identifiers. |
| `coverage`, `loss`, `intervention_log` | Armed-before-event status, initial known/unknown state, observed reset/hotplug boundaries, stop reason, dropped records/overrun/truncation/decode failures and all physical/software interventions. An undocumented buffer behavior is unknown loss, not zero loss. |

### Event Records

| Field group | Required semantics |
| --- | --- |
| `event_id`, `generation_id`, `link_id`, `record_index` | Unique within capture; retain vendor ordering even when timestamps tie. Raw fragment and decoded message records are different event kinds. |
| `timestamp_ticks`, `duration_ticks`, `direction`, `direction_basis` | Direction is source-to-branch, branch-to-source or unknown. Basis identifies verified connectors, vendor heuristic or undecoded; uncertain direction cannot establish macOS-issued requests. |
| `kind`, `raw_bytes_hex`, `raw_reference` | AUX request/reply, HPD/PD event, sideband message, or main-link record; byte offset/length or export record reference binds every decoded assertion to hashed raw evidence. Unknown vendor extensions are preserved. |
| `aux` | Native versus I2C-over-AUX, raw/decoded opcode, address space/address, MOT, requested/transferred length, separate native and I2C replies, data bytes and retry/DEFER status. Unknown is not ACK. |
| `sideband` | Raw header/body, LCT/LCR/RAD, broadcast/path, SOMT/EOMT, sequence, length, CRC results, buffer addresses, message/reply types and all contributing AUX event IDs. Do not duplicate an AUX fragment into two completed messages. |
| `topology` | Raw branch GUID/peer GUID, branch path, port, direction, peer type and DDPS/legacy/MCS flags; logical/physical interpretation with provenance. Missing GUIDs are not invented. |
| `payload` | Raw and decoded VCPI, requested/accepted PBN (protocol units), slot start/count, table/update epoch, table bytes and ACT status. Keep attempts, success, removal and unknown state separate. |
| `remote_access` | Routed port, remote DPCD or I2C address, EDID segment/offset, byte ranges and checksums. Whole-EDID claims require all declared blocks or an explicit base-block-only qualification. |
| `correlation`, `quality` | Request/reply and fragment references, matching basis, unresolved candidates, loss/truncation/CRC/length/direction status, raw coverage. Missing information is explicit `null` plus reason, not an inferred zero or false. |
| `main_link` | Optional later phase: physical lanes/coding, MTP and VC fields, schedule epochs, per-VC MSA/timing/raw packet references and overlap interval. Absent for AUX-only evidence. |

### Import and Evaluation Boundary

Future adapter flow: immutable vendor export -> format-specific reader -> raw
AUX records -> generic sideband reassembly -> generation-scoped topology and
allocation state -> Q1-Q6 findings. An adapter must disclose whether it has
original electrical samples, raw AUX bytes, or only a vendor-decoded report.
An HTML label without its underlying bytes cannot silently become raw evidence.
Vendor formats are not assumed to match this schema or to be publicly specified.

Mandatory offline fixtures before accepting an eventual importer: request-only,
NACK/DEFER and retry; split/reordered/missing sideband chunks; CRC and length
failure; duplicate/zero GUID; sequence reuse; same EDID on two routes; cached
EDID; zero-PBN removal; reused payload ID after reset; overlapping versus
sequential allocations; stale ACT bit; direction ambiguity; clock wrap/ties;
buffer loss; late capture start; synthetic/hardware mixing. All must fail closed
for claims they cannot support. No fixture is a hardware result.

Wire payload IDs are not DCP source identities. Even future hardware Q4/Q5
success does not automatically pass M5P1 ownership gates A-E. A separately
justified bridge must bind physical link, generation, source/stream identities
and independent behavior; preserving the current schema avoids laundering
wire control evidence into that stronger contract.

## Decisive Trace Scenarios

These are prospective hypotheses; none has been captured in M5P5. All require
verified upstream direction, successful matched replies, known capture limits
and an explicit observation interval. Negative claims need complete coverage
from a known lifecycle boundary, not an idle capture started after setup.

| Scenario | Decisive trace within that scope | Interpretation and disconfirming observation |
| --- | --- | --- |
| A | MST enable accepted; two present output paths; successful complete EDID reads on both; exactly one accepted nonzero concurrent VCPI after control settles, no hidden second allocation in a loss interval. | Second-path enumeration succeeds but control does not reach a second retained allocation in the interval. Host/DCP policy or source binding is a hypothesis, not a located cause. A second concurrent accepted allocation disproves the one-payload premise; a NAK/resource failure supplies a competing explanation. |
| B | Two distinct current VCPI allocations to intended paths, accepted nonzero PBN, corresponding local slots/table updates and a newly qualified ACT-handled report. No intervening removal/reset or missing messages. | Control progresses beyond the single public logical display. Prioritize Q5 main-link capture; receiver status does not itself prove two packetized videos. Sequential IDs, failed ACKs, stale ACT or deallocation disprove this scenario. |
| C | Qualified lifecycle capture observes capability and control state, but no accepted `DP_MST_EN` enable; ideally explicit disabled-state reads/writes, plus coverage of discovery through stable link. | MST was not observed enabled in this generation. Investigate why machinery was not used; do not infer permanent impossibility. A later accepted enable falsifies the bounded disabled interpretation; a late/gapped trace is inconclusive. |
| D | Complete routed topology reports only one present eligible output path upstream, after accounting for input/internal ports and descendant branches. | The branch's presented topology may explain the one-path control behavior. A native-DP branch is a future contrast, not proof the original hub is defective. A second present path in the same complete topology disproves the premise. |
| E | Two present eligible output paths, but requests address only one during a complete new enumeration interval with caching/previous state explicitly bounded. | Focus on where enumeration ceased or was skipped; caching or policy remains a hypothesis. A successful second-path query falsifies the premise; a missing initialization interval prevents the negative claim. |

An explicit NAK or timeout is a recorded wire outcome, not proof of an Apple
policy restriction. If only one payload is allocated, Q6 returns the last
successful stage, first failed/absent next step and coverage limitations. It
cannot name the responsible private method or demonstrate an architectural cap.

## Sink-Count Discrepancy

Neither software count has an established wire-register binding. Candidate
comparisons are native `DP_SINK_COUNT` / ESI reads and routed `LINK_ADDRESS`
port/presence records at known times. Comparing numbers alone cannot identify
the semantic owner, physical panels or the internal source count.

| Retained observation | Closest future wire comparison | What remains unproved |
| --- | --- | --- |
| M5P4 service log, record 17 at `2026-09-16 11:26:45.140180 UTC`: `oldCount=0 newCount=2 add=1 remove=0` | Source-observed `0x200` / `0x2002` values; complete branch output-port and DDPS/legacy state; routed EDIDs, notifications and conversion topology | The log field may be an aggregate/service-specific count, transformed count or a different-time observation. Neither `newCount=2` nor `add=1` supplies two route identities. No typed log-to-register binding exists. |
| M5P3 connected public transport snapshot, roughly `11:27:47-48 UTC`: `SinkCount=1` | The same register addresses at the same upstream segment and generation; distinct immediate-receiver, eligible-output-path and logical-entity cardinalities maintained separately | The software property might represent a different scope, cached state or later sample. It is not established to be the DPCD sink-count byte or simply the number of immediate physical receivers. |
| One public VG248 logical record; both downstream panels owner-reported mirrored | Whether two output paths are advertised, whether both are queried, and how many payloads are retained | A public logical display is not necessarily one wire payload, one physical panel or one M5 source. Mirroring can occur before or after the branch without those counts deciding where. |

Testable explanations include different service/transport counting scopes,
different sampling times, hub-internal conversion or clone presentation, and
cached/aggregated software state. These alternatives do not call either count
wrong. A complete future LINK_ADDRESS/RAD/EDID topology can replace the ambiguous
count inference with actual branch-presented paths. If normal macOS traffic
never enumerates the branch, passive AUX cannot invent that missing reply.

Even a new wire capture cannot retroactively bind the September 16 fields to
registers. Exact software-field semantics need separate, explicit correlation
evidence. Any synchronized public-software observation proposed for a future
experiment requires its own scope/approval; M5P3/M5P4 captures are not rerun or
rewritten. The immediate gain is resolving what the branch exposed and what
the source requested, not guessing the internal name of a counter.

## Capture Phase Ladder

| Phase | Scope and entry gate | Exit evidence / escalation |
| --- | --- | --- |
| W0 | This no-hardware plan, source research, vendor/access qualification. | Requirements and a separately reviewable physical experiment, not a capture. |
| W1 | After explicit approval of equipment and exact topology: listen to upstream AUX only, with qualified nonparticipating hardware, source/reply direction, raw export and coverage receipts. | Native DPCD capability/control and raw sideband transport. If bytes are sufficient, no new hardware is needed for W2. |
| W2 | Decode W1 offline with the pinned oracle; vendor decoder is optional if complete raw bytes are usable. | Q1-Q4/Q6 and A-E scoped outcomes. Incomplete discovery, lost bytes or absent natural traffic is inconclusive, not automatic W3 justification. Any required stimulus needs separate approval. |
| W3 | Q5 becomes the gate, especially after scenario B; qualified native DP HBR3 source-to-branch tap. | Actual overlapping MTP/VC/video timing evidence. Two VCs still do not alone bind private M5 source ownership or independent content. |
| W4 | Need current USB-C-hub-specific data-path evidence that the controlled native-DP contrast cannot supply. | Qualified USB-C full-link trace, with PD/Alt Mode and all loading/interposition effects recorded. |

W1/W2 are observation and interpretation tiers, not necessarily two instrument
purchases. A DPA-400-like instrument can provide both. Neither W3 nor W4 is
required merely to inspect payload allocation. Do not progress between physical
phases automatically, even if documentation describes an available capability.

## Safety Model

Distinguish `TRUE_PASSIVE_TAP` from `INLINE_PROTOCOL_INTERPOSER`. The latter
may terminate or regenerate a link, negotiate PD, drive HPD, or answer AUX
even when its UI says observer. None is qualified for this Mac by marketing
language alone. No injected AUX, EDID/HPD/PD changes, forced MST, automatic
mode changes, or unqualified repeater operation is authorized.

`TRUE_PASSIVE_TAP` here means the observed protocol path is not terminated,
answered, trained, regenerated or changed by the instrument. It does not mean
zero capacitance, no added connector loss, or that measurement electronics
cannot need power. A specified high-impedance receive-only probe is a candidate,
not automatically a validated tap. Document impedance/capacitance, common-mode
limits, connector/cable loss, grounding, power-off behavior and worst-case
failure modes before daily-use-Mac consideration.

Future authorization must identify exact equipment, firmware/software/licenses,
cable part numbers and topology, how transmit/generator/emulation functions are
disabled, passive-mode defaults on reset, safe controller-host isolation and
raw-export acceptance. Use a separate lab controller for instrument software;
no administrator driver installation on this M5 is approved. A sacrificial
adapter does not electrically isolate or protect the Mac by itself.

An insertion necessarily interrupts or perturbs the current physical setup;
this report does not authorize insertion, hotplug, sleep/wake, training stimulus,
probe contact, breakout use, cable opening, or EDID/display-mode changes.
Unexpected retraining, instability, PD behavior or evidence of injected traffic
is an abort condition for a future approved run, not a reason to improvise.
Do not submit AUX/DPCD requests, private selectors or synthetic wire traffic on
the daily-use M5. No firmware, NVRAM, boot or security settings may be modified.

## Equipment Decision

`AUX_ANALYZER_ACQUISITION_WARRANTED`, meaning **qualify temporary AUX access**,
not buy, connect or run equipment. Specific first route: Unigraf DPA-400 2.1
with the appropriate official Y-cable through a manufacturer demonstration or
an engineering/test-house owner. It explicitly targets source/branch AUX and
MST sideband. Ellisys `CTR1-A-STD-DP` is the USB-C alternative if cable fit,
timing or PD context favors it, conditional on a raw-export/reassembly sample.
Do not select either instrument for Mac connection until its acceptance gaps
are closed. No inventory, loan term, instrument operator or physical booking
has yet been secured.

Native DP is scientifically useful but does not have to precede AUX-access
qualification because documented USB-C observation paths exist. Full-link
equipment is not warranted for Q1-Q4; escalate only when Q5 or a genuinely
data-path-specific question becomes decisive. This keeps the original hub's
unresolved presentation in scope without treating M5 safety as a license to
stop pursuing the final source/compatibility goal.

### Access Routes

| Route | Source-backed availability and practical qualification |
| --- | --- |
| Manufacturer demonstration, then possible loan | [Unigraf explicitly offers online demos](https://www.unigraf.fi/book-a-demo/) and the DPA-400 page links one. Use a future demo/sample to verify Q1-Q4 export and passive setup first. A remote GUI demo is not a hardware loan or an M5 result. Loan/evaluation-unit terms are not publicly established; no form submitted. |
| Engineering/validation lab or test house | [VESA's current ATC directory](https://vesa.org/displayport-developer/compliance/) lists Allion and Granite River Labs across regions; [Allion advertises issue-analysis/debug services](https://www.allion.com/issue_analysis_debugging_consulting_service/). These are credible service leads, not proof of local DPA-400 stock, observer-only capture permission or affordable access. Ask for a receive-only interoperability session and export deliverables, not an automatic active CTS run. |
| University or colleague borrowing | An existing EE/display validation lab may already own suitable equipment, reducing acquisition cost. No university inventory was verified. [UNH-IOL's current testing catalogue](https://www.iol.unh.edu/services/testing) is a networking/testing lead, but did not establish DisplayPort availability; do not claim it has a suitable analyzer. No nearby lab is selected because the user's region/access eligibility is unknown. |
| Rental | [Electro Rent offers rental programs](https://www.electrorent.com/us/services/rent-test-equipment). Specific DPA-400/CTR1/M42de stock, option licenses, cables, host software, rental duration, insurance and export access remain unconfirmed. A rental company's existence is not a confirmed rental route for these models. |
| Used market | [Certified pre-owned channels](https://www.electrorent.com/us/services/buy-used-test-equipment) exist, but no suitable lot was qualified. Require exact cable, firmware, transferable licenses and return/calibration terms. [LeCroy lists M41d and the 980 system as discontinued](https://www.teledynelecroy.com/protocolanalyzer/discontinued-products); a cheap chassis/HDMI module is not a qualified DP passive analyzer. |
| New purchase | DPA-400 and M42de are quote-based; Ellisys provides edition-specific inquiries without a public price in the surveyed page. No complete landed-cost quote, delivery or uniquely inexpensive fit was established. Buying a full-link generator/CTS suite is disproportionate to an AUX-control gate without access alternatives being tried. |

Best practical route: **manufacturer sample/demo qualification followed by
borrowed or staffed lab access** to the qualified AUX-only assembly; consider
rental if a complete package is actually available. Availability, price and
geographic convenience remain questions, not facts. This report neither contacts
vendors nor spends funds. Access qualification can remain W0 with the current
hub untouched.

### Questions for a Future Provider

Ask for proof of the exact current-hub connector fit and manufacturer cable
rating; nonparticipating AUX/HPD/PD behavior including start/reset/power-off;
two-lane HBR3/USB3 preservation; max burst/sustained capture rate and overload
indication; raw export for multi-fragment LINK_ADDRESS, remote EDID/DPCD and
payload/ACT status; source/reply direction basis; original-format viewer/license
portability; and separately priced temporary access. These are draft acceptance
questions, not correspondence sent on the user's behalf.

## Purchase Gate

`PURCHASE_NOT_YET_JUSTIFIED`.

The protocol requirements are known, but no one device/assembly has passed the
electrical, cable-fit, loss and export gates. Borrow/demo/rental/lab access has
not been ruled impractical, the total cost is unknown, and no decisive physical
experiment has yet been separately authorized. Therefore the user's purchase
conditions are not met. No purchase, rental booking, lab reservation, vendor
contact or expenditure occurred. No sacrificial Mac purchase is implied.

## Current Hardware State

`KEEP_CURRENT_HUB_CONNECTED`. Leave the ZMUIPNG hub and both ASUS VG248
monitors connected with the existing mirrored behavior and settings unchanged.
No new hardware observation has occurred in M5P5.

`RETIRED_ON_DAILY_USE_M5`, `NOT_READY_FOR_DPCD_TEST`, and
`OFFLINE_OBSERVER_PIPELINE_READY` are preserved. The T8142 packetizer-analysis
freeze, m1n1 policy boundary, and immutable safety markers remain in force.

`STATIC_PACKETIZER_ANALYSIS_FROZEN` and
`NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED` remain unchanged.
No sibling m1n1 access, private API call, native probe execution, electrical
capture, new log query or public topology query occurred in M5P5. There are
zero new real wire traces and zero new hardware-evidence gate passes.

### Verification

On 2026-09-17, the existing hardware-disabled build and all four offline CTests
passed: 124 observer, 12 host-receipt, 33 topology and 31 public-log tests,
200 existing tests total. No native display executable or firmware test ran.

```sh
cmake --build build-m5p4-offline
ctest --test-dir build-m5p4-offline -L offline --output-on-failure
```

Focused document checks validated the exact 19 required sections, unique result
classifications, local links, all 13 downloaded-file SHA-256 receipts, the
12 sideband opcodes against the pinned header, and the five prospective A-E
rows. The preserved M5P3 capture validator passes both states; differential,
M5P4 historical/review hashes and 477 records match the completed baseline.
All prior tracked files were unchanged at the first M5P5 report commit, and
the 46 published identities after M5P4 publication remained unchanged.
The consumed M2F marker and two receipts match their recorded hashes;
`M2G-DPCD-READ-ATTEMPTED` remains absent.

No new importer, protocol parser, electrical receiver or machine-executed wire
schema validator was implemented. The schema, scenario rules and acceptance
fixtures are designs for a later offline implementation with real vendor
exports. Compilation and existing synthetic tests establish preservation, not
instrument safety, current wire behavior, M5 MST functionality or readiness for
a hardware experiment. Manufacturer and access gaps above remain unverified.