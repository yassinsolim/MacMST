# M5P7 Self-Built Low-Cost DisplayPort AUX Observer

2026-09-18. Offline engineering and public-source research only. No equipment
purchased, assembled, inserted or probed; no signal capture or outreach.

## Objective

Advance a MacMST-owned passive observer toward multiple independent displays
from the base M5 through ordinary DP MST, without DisplayLink or separate
Thunderbolt tunnels. Track B (our engineering) is primary and continues
independently of Track A (optional commercial/lab access).

This milestone implements the bounded offline AUX/MST/W1 pipeline and derives
a capture architecture. It does **not** establish a safe finished electrical
front end, a working M5 capture or native MST functionality. Missing critical
electrical data is an engineering task, not a requirement to wait for replies.

## M5P6 Baseline

[M5P6](m5-aux-access.md) was audited and published unchanged on
`research/m5-aux-access` at `e909e471cbf5982749de2c67655197d091438a27`, upstream
0/0. Its two linear commits, clean tree, unchanged four-draft UNSENT contact
package, 19 source receipts, 477 M5P4 records, M5P3/M5P4 capture/review hashes,
200 prior offline tests and safety markers passed. All 47 previously published
head/tag/peeled identities were preserved; publication added only M5P6.

M5P5 remains published at `54d30598f013b617282375d5295a6b37269fb5b9`.
The new branch starts from the exact M5P6 HEAD. No message was sent in the
prior workflow or this milestone; no email system or physical setup was queried
to establish that. The earlier evidence remains immutable regardless of
ordinary hub use between milestones.

M5P6's equipment uncertainties remain historically valid. Its mandatory outreach
and keep-connected workflow do **not** control M5P7: outreach is optional and
current physical state is neither known nor required.

## W1 Evidence Requirements

These are M5P7's nine gates, intentionally distinct from M5P6's eight labels.
All are control-plane questions; none requires video/pixel decoding.

| Gate | Required observation | Important limit |
| --- | --- | --- |
| W1.1 | `DP_MSTM_CAP` read and reply at `0x021` | Capability is not enablement. |
| W1.2 | Accepted `MSTM_CTRL`/`DP_MST_EN` write or state read at `0x111` | Control state, not actual MST video. |
| W1.3 | Complete AUX-carried MST sideband request/reply traffic | Sideband can exist in single-stream mode too. |
| W1.4 | LINK_ADDRESS GUID, ports, direction, peer types and presence flags; notifications | Internal/logical ports and converters are not automatically separate panels. |
| W1.5 | Routed REMOTE_DPCD_READ/WRITE and REMOTE_I2C_READ/WRITE, including EDID paths | Attempted access, accepted data and complete EDID contents are distinct. |
| W1.6 | ENUM_PATH_RESOURCES requests/replies | Resource advertisement is not an allocation. |
| W1.7 | ALLOCATE/QUERY/CLEAR transactions, VCPI/PBN and separate local slot writes | Count overlapping retained IDs, not requests/retries or lifetime ID reuse. |
| W1.8 | Payload-table update and receiver ACT-handled status | AUX does not contain the actual main-link ACT packet. |
| W1.9 | Wire sink-count/ESI bytes, topology and notifications compared with historical count domains | A new lifecycle cannot retroactively bind `newCount=2` and `SinkCount=1` to one register. |

No object count, GUI display name, timing coincidence or payload ID is promoted
to a private M5 source identity. Unknowns remain explicit.

## AUX Electrical Layer

`PUBLICLY_VERIFIED_ELECTRICAL_FACT` means the stated **public source actually
documents the fact in its stated context**, not that MacMST measured the M5 or
obtained a current normative VESA electrical specification.
`IMPLEMENTATION_ASSUMPTION` labels proposed budgets, extrapolations and missing
electrical qualifications. Endpoint ratings are not observer-loading allowances.

Primary sources:

- **E1:** TI [SN65DSI86 SLLSEH2C, revised October 2020](https://www.ti.com/lit/ds/symlink/sn65dsi86.pdf),
  electrical table pp. 11-14 and section 8.4.5.2 AUX Channel.
- **E2:** TI [SLLA343, October 2013](https://www.ti.com/lit/an/slla343/slla343.pdf),
  sections 2.3.2-2.3.3, pp. 7-8. This is an endpoint implementation guide.
- **E3:** TI [SN75DP130 SLLSE57E, revised March 2015](https://www.ti.com/lit/ds/symlink/sn75dp130.pdf),
  recommended AUX conditions, AUX electricals and typical AUX monitoring
  configurations. It is a redriver/monitoring example, not our approved tap.
- **E4:** Public [DisplayPort connector definition](https://github.com/mithro/displayport-hardware-hacking/blob/85b100b10359d53b6bceda0a3f529a6826747f70/libraries/display_port.lib),
  `DISPLAY_PORT`, and the associated open schematic. A layout must still be
  checked against the exact connector manufacturer's drawing/view orientation.

| Electrical statement | Classification | Evidence and scope |
| --- | --- | --- |
| Ordinary AUX is differential, AC-coupled, half-duplex and bidirectional, with source request then sink reply | PUBLICLY_VERIFIED_ELECTRICAL_FACT | E1 section 8.4.5.2 explicitly describes a doubly terminated channel. A single voltage trace does not uniquely identify the transmitting endpoint. |
| Manchester-II, nominal 1 Mbit/s before encoding, nominal half-bit interval 0.5 us | PUBLICLY_VERIFIED_ELECTRICAL_FACT | E1/E2. E1's Manchester interval range is 0.4-0.6 us; E3's input-rate range is 0.8-1.2 Mbit/s. These device specifications are reported separately, not fused into a universal standard. |
| Fast AUX is a separate mode | PUBLICLY_VERIFIED_ELECTRICAL_FACT | E2 excludes FAUX; E3 lists 720 Mbit/s FAUX separately. HBR3 on the main link does not imply 720 Mbit/s AUX. This observer design supports ordinary AUX only. |
| E1 AUX TX differential peak-to-peak 0.18-1.38 V, RX 0.18-1.36 V | PUBLICLY_VERIFIED_ELECTRICAL_FACT | E1 table defines peak-to-peak as twice the absolute pin difference. Do not mistake these values for each pin's voltage to ground or a universal M5 amplitude. |
| E1 AUX DC common mode 0-1.2 V; turnaround common-mode limit 0.3 V | PUBLICLY_VERIFIED_ELECTRICAL_FACT | E1 endpoint pin table, not arbitrary cable-side DC conditions. |
| E3 AUX differential input amplitude 300-1400 mV peak-to-peak; source common mode 0-2000 mV before AC coupling | PUBLICLY_VERIFIED_ELECTRICAL_FACT | E3 explicitly scopes the measurement location. Cable-side bias and powered-off protection must be considered independently. |
| E3 DC AUX+ condition -0.5 to 0.4 V and AUX- 2 to 3.6 V in its DP monitoring configuration | PUBLICLY_VERIFIED_ELECTRICAL_FACT | E3 recommended input conditions. This is a direct counterexample to assuming both wires are ground-centred GPIO-compatible signals. |
| Endpoint AUX termination 100 ohm and doubly terminated topology | PUBLICLY_VERIFIED_ELECTRICAL_FACT | E1. Do not add a third 100-ohm receiver termination across an existing link. Source output impedance and receiver termination are not the same as a high-Z observer input. |
| AUX coupling capacitance 75-200 nF and endpoint detection-bias resistors | PUBLICLY_VERIFIED_ELECTRICAL_FACT | E1/E2; E2 illustrates optional 100-kohm source-detection bias for that bridge. These belong to endpoint design, not components to add to the observed pair. |
| 100-ohm differential routing with 50-ohm single-ended routing guidance | PUBLICLY_VERIFIED_ELECTRICAL_FACT | E2 gives +/-20% and +/-15% respectively for its AUX PCB routing. This is a characteristic-impedance/routing guide, not a shunt measurement load specification. |
| Idle/turnaround may be differential near-zero with existing endpoint bias, rather than a valid binary logic level | IMPLEMENTATION_ASSUMPTION | Consistent with E1 turnaround and AC-coupled operation; exact idle envelope, hysteresis and both-transmitter transitions need bench verification. A comparator stuck high/low can conceal idle. |
| Request/reply timing: E1 uses a 400-us reply timer and 100-us retry spacing | PUBLICLY_VERIFIED_ELECTRICAL_FACT | E1 section 8.4.5.2.1 implementation behavior. Not proof of all endpoints' legal timing or an M5 timeout. |
| MacMST packet-pairing window is at most 1 ms between packet starts | IMPLEMENTATION_ASSUMPTION | Conservative offline association bound, not a protocol limit. Longer/ambiguous pairs become incomplete instead of being silently paired. |
| Native AUX data is at most 16 bytes per transaction; request has command/address/length and reply carries status | PUBLICLY_VERIFIED_ELECTRICAL_FACT | Public Linux `drm_dp.h`, E1 AUX registers, and inspected decoders; framed packets and reassembled MST messages have different sizes. |
| Native DP connector AUX_CH_P = pin 15, AUX_CH_N = pin 17, shield/ground pin 16; HPD 18, return 19, DP_PWR 20 | PUBLICLY_VERIFIED_ELECTRICAL_FACT | E4 symbol pin labels. These are identification data, not instructions to open a cable or attach a probe. Exact plug/receptacle viewing direction must be verified before any layout. |
| HPD is a separate native-DP signal; MST readiness can cause IRQ-related AUX reads | PUBLICLY_VERIFIED_ELECTRICAL_FACT | E1/E2 and pinned Linux service-IRQ/sideband-buffer definitions. USB-C HPD uses Alt Mode/PD context as established in M5P5; native DP removes that complication at the tap. |
| Exact M5/hub source impedance, cable bias, transients, ground offset and permissible observer R/C are known | IMPLEMENTATION_ASSUMPTION | They are **not established**. No public source inspected specifies a universal third-observer loading budget for this exact assembly. This blocks a final schematic/parts selection. |

The differing source contexts matter. A part advertised as LVDS, rail-to-rail
or 400 Mbit/s is not thereby suitable for cable-side AUX. The practical design
must tolerate normal signal and bias, power sequencing and faults while
remaining nonparticipating. No current M5 pin voltage is inferred here.

## Native-DP Tap Topology

`NATIVE_DP_AUX_TAP_PREFERRED`.

```text
Future, separately approved laboratory topology only:
M5 -> native USB-C DP Alt Mode adapter -> native DP segment -> MST branch
                                          |                    -> sink A
                                     receive-only tap          -> sink B
```

Native DP gives identified AUX/HPD contacts without SBU orientation switching,
CC/PD policy or a USB-C multifunction cable fixture at the observation point.
It materially simplifies measurement, repeatable orientation and fault review.
It does not eliminate controlled-impedance layout, short-stub/loading concerns,
power-pin isolation or preservation of all HBR3 main lanes. An arbitrary
breakout or protoboard is not an HBR3-transparent assembly.

M5P5's equivalence is for a controlled **ordinary-MST source** experiment. A
different adapter/branch may negotiate four DP lanes instead of the recorded
two-lane/USB3 sharing and may remove downstream HDMI conversion. Record those
differences; do not claim reproduction of the ZMUIPNG software counters or the
same private DCP route. No topology is assembled or changed in M5P7.

## Passive Front End

Layer 1 is only acquisition. Layer 2 is offline decoding. No software or FPGA
output has an intentional conductive drive path to AUX or HPD.

```text
AUX+ source <-------------------------------> branch AUX+
                         |
                  qualified high-Z input
                         |
                 differential acquisition -> raw samples -> offline decoder
                         |
                  qualified high-Z input
                         |
AUX- source <-------------------------------> branch AUX-
```

This is a functional architecture, **not a build-ready circuit**. It neither
replaces terminations/bias nor inserts an active protocol repeater. Hardware
must prevent GPIO output-enable mistakes from reaching the pair. A receive-only
symbol in HDL alone cannot establish protection from ESD diodes, input faults,
ground offsets or powered-off backfeeding.

| Front-end candidate | Public facts and comparison | Decision |
| --- | --- | --- |
| Proper low-capacitance differential active probe and scope | Existing specified probe can retain analogue differential waveform and reveal idle/amplitude. Require published R/C, common-mode/differential range, noise and power-off behavior for the exact probe and connection. | Best B1/B2 reference if already available; no random probe or hardware inventory is assumed. No exact available probe qualified. |
| TI TLV3502 comparator pair | [SBOS321E](https://www.ti.com/lit/ds/symlink/tlv3502.pdf): 4.5 ns nominal delay, very small powered input bias, typical common-mode input impedance 10^13 ohm || 2 pF, differential 10^13 ohm || 4 pF. Inputs have supply-rail clamps; the datasheet's 10 mA current limit is an absolute-protection condition, not acceptable AUX loading. | Bandwidth plausible; direct cable attachment rejected. Power-off clamps, protection R/C, thresholds, hysteresis and idle-window sensing remain unqualified. |
| AD830 difference amplifier | [Manufacturer](https://www.analog.com/en/products/ad830.html) specifies 85 MHz unity-gain bandwidth, +/-2 V differential and wide common mode under its stated supplies. | Candidate analogue stage only. Exact supply-dependent input loading, offset/noise and fault/power-off behavior need complete modelling; not approved by bandwidth alone. |
| INA821 instrumentation amplifier | [Manufacturer](https://www.ti.com/product/INA821): 4.7 MHz bandwidth at minimum gain, with gain-dependent performance. | Less margin than the proposed 10 MHz decoding target; high CMRR at low frequency does not guarantee AUX edge/turnaround fidelity. Not selected. |
| SN65LVDS2 dedicated receiver | [Manufacturer](https://www.ti.com/product/SN65LVDS2) identifies a receiver-only LVDS part with LVTTL output. | Speed alone does not close thresholds/common mode, cable-side DC bias, input termination/loading or power-off safety. No assumed AUX compatibility and no added LVDS termination. |
| Front end feeding FPGA/logic analyzer | Downstream digital capture need not know AUX electrical levels if the receiver is correctly qualified. | Preferred digital architecture, contingent on the front end. GPIO only sees isolated/conditioned logic, never the raw pair. |

Provisional high-Z targets such as at least 1 Mohm and a few pF or less are
`IMPLEMENTATION_ASSUMPTION`, not a permissible VESA load budget. For scale,
100 ohm in parallel with 1 Mohm changes DC resistance by about 0.01%, but a
4 pF shunt has only about 4 kohm reactance at 10 MHz. Stub/protection/layout
capacitance matters even when DC leakage is tiny.

There is a real protection-versus-bandwidth tradeoff: a 1 Mohm series resistor
with 4 pF yields a 4 us time constant, far too slow for 0.4-0.6 us half-bits.
Reducing resistance protects timing but can let a powered-off clamp load the
bus. These calculations are assumptions for design exploration, not a safe
resistor prescription. Solve this with a reviewed high-Z/power-off-safe topology
and simulation, not speculative connection or software promises.

## Capture Requirements

All following budgets are `IMPLEMENTATION_ASSUMPTION` derived from the public
ordinary-AUX timing envelope; they are not hardware measurements.

- Design for half-bit features as short as 0.4 us, about 2.5 million possible
  transitions/s on one sliced waveform. Retain request and reply clocks
  independently; no shared synchronous clock is available from the bus.
- Proposed edge-rise budget of at most 0.1 us implies approximately 3.5 MHz
  analogue bandwidth using BW x rise-time ~= 0.35. Use at least 10 MHz usable
  small-signal bandwidth as a design target for margin. This is for decoding,
  **not** electrical compliance or characterizing actual fast edge shape.
- Minimum supported sampled input is 10 MS/s (100 ns); 20 MS/s is desirable
  and 40 MS/s (25 ns) is the robust digital target. Those give 4, 8 and 16
  samples per shortest half-bit respectively. Prove threshold/noise/jitter
  margin at B1/B2; sample count alone is not enough.
- Plan for 180 seconds including idle/attach/settling, with pre-attach recording
  and explicit generation boundaries. This is an experiment bound, not a claim
  about how long macOS setup takes. Do not discard idle intervals without time
  and overflow bookkeeping.

| Representation | Rate / storage calculation | Consequence |
| --- | --- | --- |
| One binary channel, packed, 20 MS/s | 2.5 MB/s; 450 MB/180 s | Already exceeds USB full-speed's raw 1.5 MB/s signalling ceiling before overhead. |
| Two binary/window-state channels, packed, 40 MS/s | 10 MB/s; 1.8 GB/180 s | A practical target for continuous USB high-speed FIFO or Ethernet storage. |
| Analogue differential, 20 MS/s, 16-bit storage | 40 MB/s; 7.2 GB/180 s | Scope streaming/export must be explicitly capable; deep screenshot memory is insufficient. |
| Absolute 64-bit time per edge, 2.5 Medges/s | At least 20 MB/s before flags | Edge capture is not automatically smaller than packed samples. Two threshold crossings may increase event rate. |
| Run/edge deltas with bounded coding | Good for long idle periods; worst-case rate still bounded by transitions, not average desktop activity | Preserve every transition/time delta and escape/wrap records; never rely on typical compression to avoid loss. |
| 64 KiB FIFO at 10 MB/s | About 6.55 ms host-stall coverage | Too little for an unbounded host pause. |
| 1 MiB FIFO at 10 MB/s | About 104.86 ms stall coverage | Proposed minimum robust buffer, plus sustained drain rate above production rate; not an infinite guarantee. |

Use a 64-bit sample counter: 32 bits at 40 MHz wraps in 107.3741824 seconds,
shorter than the planned interval. Require block sequence numbers, sample
counts, sticky overrun flag, dropped-count/time bounds and final stop receipt.
Reserve an independent loss register/path so a full FIFO cannot also erase
the fact it overflowed. The observer cannot backpressure AUX; it must report
loss and invalidate affected conclusions. Throughput/FIFO calculations were
checked with exact Python rational/integer arithmetic.

## Oscilloscope Path

`OSCILLOSCOPE_CAPTURE_ONLY_FOR_SHORT_TRANSACTIONS` for the currently qualified
low-cost/unspecified-memory route, not a claim that all scopes are incapable.

A specified differential probe -> scope -> raw waveform export -> offline
decoder is the fastest reference for B1/B2 and isolated transactions if suitable
equipment already exists. At 20 MS/s, 1 Mpoint is 50 ms, 10 Mpoints 0.5 s,
100 Mpoints 5 s. Full 180-second capture requires 3.6 Gsamples per analogue
channel, or proved gap-free streaming. A random low-end scope is not qualified.

Two single-ended channels plus subtraction is only acceptable after checking
each probe's input R/C, channel skew, common-mode range, ground/reference and
combined loading. Ground clips must not create a new short/reference path.
Math subtraction does not remove common-mode overload or probe capacitance.
A proper differential probe is the preferred reference, not an arbitrary
high-voltage attenuator whose noise floor hides small AUX swings.

Triggers may use differential activity or a qualified receive-only HPD
observation. Segmenting on every request can extend useful memory, but any
dead time or missed reply makes an attach-sequence negative inconclusive.
Require vendor raw binary or documented waveform CSV with sample interval,
scale/offset, trigger alignment, segment timestamps and loss/dead-time metadata.
No commercial waveform importer is invented in this milestone; neutral sliced
digital input is the implemented physical-decoding boundary.

## Logic Analyzer Path

Classification: **conditionally feasible after front-end and streaming
qualification**, not ready for bus connection.

**Do not connect raw AUX directly to ordinary logic-analyzer GPIO.**

Use an electrically qualified high-Z differential receiver, ideally preserving
positive/negative/idle information, followed by asynchronous digital sampling.
Minimum 10 MS/s, target 20-40 MS/s, known threshold and propagation-delay
variation, no silent compression/filtering and explicit overflow are required.
Fixed delay can be accounted for; asymmetric delay, hysteresis and slow threshold
crossing distort Manchester duty cycle and must be measured. A single comparator
does not physically identify direction; a trusted role annotation or later
validated grammar/context analysis is still needed.

[Saleae Logic 8](https://www.saleae.com/products/saleae-logic-8) currently lists
100 MS/s digital and continuous PC streaming, CAD 710.00 when checked. This is
a candidate acquisition engine, not proof of AUX electrical safety, exact
continuous-channel throughput or lowest cost. Cheap FX2 clones/sample-rate
claims are not enough: test clock error, sample conservation, host stalls and
overrun marking with synthetic input before treating missing traffic as absent.

## FPGA Path

Preferred hardware **class** for further engineering: a receive-only 40 MHz
sampler, two conditioned digital inputs, 64-bit tick counter, at least 1 MiB
effective FIFO and a transport with demonstrated sustained throughput above
10 MB/s for packed samples (target 20 MB/s headroom). No specific complete
board/front-end combination is yet qualified or selected for purchase.

```text
qualified analogue front end -> input synchronizers / 40 MHz sampler
 -> raw sample packer or lossless run encoder -> timestamped FIFO
 -> sequenced USB/Ethernet blocks + independent sticky loss metadata
 -> host raw files -> offline AUX -> MST -> W1
```

At 40 MHz, synchronizer/quantization uncertainty is on the order of sample
ticks, not zero; record fixed pipeline latency and test metastability-related
edge placement. Simulate full/noisy-rate input, counter wrap and host stalls.
No transmitter, AUX output-enable, HPD driver, DPCD bank, training engine or
main-link decoder belongs in the gateware or connector pin assignment.

| Category | Evidence / bottleneck | Evaluation |
| --- | --- | --- |
| Artix-7 Arty A7-100T | [Digilent](https://digilent.com/shop/arty-a7-artix-7-fpga-development-board/) documents 256 MB DDR3L and 10/100 Ethernet; USB is UART/JTAG, not automatically a bulk sample FIFO. Current page lists USD 314.00; 35T is retired. | Ample logic/memory for a buffered experiment; 100 Mbit Ethernet is tight for a 10 MB/s target with overhead/headroom. Reducing to 20 MS/s or faster transport needs explicit design/validation. Not lowest-cost approved rig. |
| ECP5 / Gowin boards | Logic families can implement the modest sampler; family popularity or MHz does not specify board memory, USB transport or input safety. | No complete low-cost board with all required margins qualified. A USB programming bridge is not assumed to expose a fast FIFO. |
| Glasgow Interface Explorer | [Current analyzer2 documentation](https://glasgow-embedded.org/en/applets/interface/analyzer2.html) defines packed digital blocks, Overflow/Complete markers and streaming; current introduction says analyzer2 needs revD, whose availability is pre-launch. | Reuse its open capture/block design or a future adapter when applicable. Its GPIO/slow analogue inputs are not an AUX front end; no stock or revC applet support assumed. |

An FPGA FIFO plus USB high-speed interface or gigabit Ethernet is plausible,
but nominal 480 Mbit/s/1 Gbit/s is not achieved throughput. No board was built,
gateware flashed or acquisition daemon started.

## MCU Path

`MCU_AUX_CAPTURE_UNRESOLVED` for a complete dependable attach observer.

- [RP2040 Pico](https://www.raspberrypi.com/products/raspberry-pi-pico/) has
  133 MHz cores, PIO, 264 kB SRAM and USB 1.1; [Pico 2](https://www.raspberrypi.com/products/raspberry-pi-pico-2/)
  has 150 MHz, 520 kB and USB 1.1. PIO can plausibly sample short bursts, but
  the 12 Mbit/s raw bus ceiling is below even one packed 20 MS/s channel.
  264 kB is about 0.106 s at 2.5 MB/s before firmware buffers. Do not assume
  idle compression or real-time protocol decoding always saves the capture.
- [Teensy 4.1](https://www.pjrc.com/store/teensy41.html) documents 600 MHz,
  1 MB RAM, FlexIO, DMA and 480 Mbit/s USB. Those are promising resources, not
  proof of sustained asynchronous input + DMA + host transfer with bounded
  stalls. Its ordinary GPIOs are 3.3 V and not raw AUX inputs. No firmware path
  or worst-case timing margin was implemented/verified here.
- STM32 timer/DMA and ESP32 capture concepts are not retained as selected
  solutions without an exact peripheral clock/input/DMA/transport budget.
  CPU frequency and interrupt rates are not capture guarantees.

No MCU is chosen by price alone. A future deterministic timer/FlexIO/PIO
simulation and throughput benchmark can resolve this in Track B; vendor/lab
replies are not required.

## Existing Open-Source Work

The current survey used public repository search for DisplayPort AUX, MST
decoder, Manchester, sideband and FPGA PHY concepts, plus actual source reads.
Earlier M5P5 filename-only negatives are not an exhaustive result. No external
project was executed against hardware or modified.

| Repository / exact revision | Licence/language and inspected source | Actual relevance / reuse decision |
| --- | --- | --- |
| [ngscopeclient/scopehal](https://github.com/ngscopeclient/scopehal/tree/e812615f5d1ce9498952fd1f6847f8bda151d5a3) | BSD-3-Clause header, C++; `scopeprotocols/DPAuxChannelDecoder.cpp`, `Refresh`, Manchester/framing and register decode | Real analogue/digital offline AUX decoder. Uses role alternation (`packetIsRequest`) and heuristic I2C ACK display; these cannot supply MacMST loss/direction proof. Useful independent framing/reference tool, no full MST sideband assembler found in this file. |
| [cnbright/DPAUXAnalyzerV2LLA](https://github.com/cnbright/DPAUXAnalyzerV2LLA/tree/998924660bb793d7815efc470bf72b75e5cd35f8) | C++ Saleae LLA and `DisplayPortAUXSimulationDataGenerator.cpp`; no clear repository-wide licence identified | Actual Manchester/start/stop code; synthetic generator confirms high-four/low-four half-cell delimiters and MSB-first Manchester polarity. Depends on already safe logic-level input and Saleae SDK. Not copied as an undocumented dependency. |
| [cnbright/DPAUXAnalyzerHLA](https://github.com/cnbright/DPAUXAnalyzerHLA/tree/484a8d4329826662d7145f5741f46f7dde3bc9e7) | MIT, Python; `HighLevelAnalyzer.py`, `_parse_request`, `_parse_reply`, `_process_packet` | AUX request/reply assembly over LLA events, not electrical capture or MST topology decoding. README admits a dangling final request may not flush at EOF. Reference for raw fields; Saleae callback/role assumptions do not match our bounded independent contract. |
| [briansune/sigrok-pulseview-displayport-aux](https://github.com/briansune/sigrok-pulseview-displayport-aux/tree/55b700c987c253ef906e25c092401d457039544e) | `pd.py` explicitly GPL-2.0-or-later, Python sigrok | Real AUX Manchester/command annotations with configurable precharge/preamble; no MST sideband reassembly in inspected file and no safe electrical front end. Reusable optional external annotation tool with licence compliance, not bundled here. |
| [mithro/displayport-hardware-hacking](https://github.com/mithro/displayport-hardware-hacking/tree/85b100b10359d53b6bceda0a3f529a6826747f70) | CC-BY-SA-4.0 per README; KiCad schematic/library | Actual connector/layout/intercept work. README and schematic deliberately allow AUX/HPD driving and add endpoint-style networks. **Not** a safe receive-only tap as-is; no jumper/wiring instructions adopted. |
| [hamsternz/FPGA_DisplayPort](https://github.com/hamsternz/FPGA_DisplayPort/tree/8b9cba275af11566e219f393b6493753ecec87ae) | MIT, VHDL; `src/aux_channel.vhd`, active AUX/training states | Genuine TX/RX source implementation, not passive observer. Potential bench-oracle concepts only; do not load active transmitter logic into the observer. |
| [parport0/displayport_aux_checkpoint](https://github.com/parport0/displayport_aux_checkpoint/tree/6ea8aa194b1854aacd3c627abc7a80f0ec9b1391) | CC0-1.0 LICENSE inspected, KiCad/RP2040 board | README and tree establish a board, not a qualified passive receiver, firmware decoder or demonstrated loss-free MST capture. No capture firmware found in the inspected tree; not selected. |
| [Glasgow](https://github.com/GlasgowEmbedded/glasgow/tree/ead3a00e37f6f68203bdd98134831ffb9bc73b0b) | Python/Amaranth; analyzer2 `__init__.py` and `protocol.md`; [project licence](https://glasgow-embedded.org/en/license.html) offers 0BSD or Apache-2.0 for source, docs and designs | Actual sampler, sticky-overflow circuit breaker, memory flow-control and host API inspected. COBS-framed 32-bit sample words have overflow trailers; the last marked word is explicitly unreliable. Useful existing Layer 1 design to reuse, not an applet executed or an AUX-safe electrical input. Dependencies retain their own licence terms. |
| [Linux DRM oracle](https://github.com/torvalds/linux/tree/238650ef6c7c7cca08e032527329424c9fbd70e5) | Public C protocol definitions and MST helpers, file-specific permissive notices | Reused as the exact opcode/field/CRC/fragmentation oracle; not executed. GPU AUX-access tools found by search are active bus clients, not passive observers. |

MacMST implements the missing conservative, hardware-independent adapter and
evidence layer rather than vendoring a scope application or guessing an
unlicensed file's reuse permission. No third-party implementation was copied
into the new modules. Existing public decoding and capture tools remain usable
as independent comparisons/optional acquisition backends. Any future copied
code or hardware derivative must retain its actual licence and attribution.

## AUX Decoder

[tools/dp_aux_decode.py](../../tools/dp_aux_decode.py) accepts neutral framed
raw bytes, `digital_samples` or `ideal_symbols`. It parses native and
I2C-over-AUX commands, 20-bit addresses, MOT, length, request data, separate
native/I2C reply status and returned data. Raw reply status occupies the high
nibble of its first wire byte; Linux's abstract status flags are not inserted
directly as a complete wire byte.

The waveform path recovers half-cell timing from short runs, locates a run of
at least eight zero symbols plus the high-four/low-four delimiter, decodes
MSB-first Manchester pairs and retains framing/timing errors. It requires
10 MS/s or faster digital sampling; ideal symbols are explicitly synthetic.
Clock range/jitter cases are tested, not all legal/noisy electrical waveforms.
This is a bounded initial decoder, not a compliance-certified PHY.

Packet `kind`, `direction` and `direction_basis` may be supplied by a qualified
export/fixture or synthetic source. Unknown is retained; the tool does **not**
alternate directions, infer source identity from amplitude, or silently turn
grammar guesses into known physical direction. With unannotated single-channel
waveforms, direction remains unknown and positive W1 attribution is blocked.
A later ambiguity-preserving grammar/context resolver is independent work,
not a claim that an extra transmitting sensor is required.

Events include schema/capture/sequence/timestamp, direction/confidence/basis,
command/address, request/reply raw bytes/status, malformed/truncated/loss flags
and decoder version. Original records/extensions are retained. Bounds: 16 MiB
JSON input, 100,000 normalized records, 2,000,000 samples per waveform record.
Large continuous waveform files need a later streamed import backend; they
must not be silently truncated to these limits.

## MST Decoder

[tools/dp_mst_decode.py](../../tools/dp_mst_decode.py) uses the pinned Linux
oracle from M5P5. It reconstructs accepted native AUX accesses to DOWN_REQ
`0x1000`, UP_REP `0x1200`, DOWN_REP `0x1400` and UP_REQ `0x1600`, preserving
the contributing AUX sequence numbers. Failed/unknown transactions interrupt
reassembly rather than disappearing.

Manifest-only loss intervals are normalized into explicit loss events before
AUX pairing and MST reconstruction. A gap cannot be bypassed by presenting
otherwise complete-looking packets on either side. Unknown capture quality
stays unknown rather than becoming an invented known drop.

It preserves raw header/body/chunks, LCT/LCR/RAD, broadcast/path, SOMT/EOMT,
sequence, request/reply type, GUID/port/peer, VCPI/PBN and CRC/error/loss state.
Header CRC is 4-bit polynomial 0x13; body CRC is 8-bit polynomial 0xD5 despite
Linux's historical `drm_dp_msg_data_crc4` name. Fixed CRC-8 check vector
`123456789 -> 0xbc` supplements round-trip tests. Chunk size is bounded by the
48-byte buffer and reassembled body by 256 bytes.

Implemented: LINK_ADDRESS, CONNECTION_STATUS_NOTIFY, ENUM_PATH_RESOURCES,
ALLOCATE_PAYLOAD, QUERY_PAYLOAD, CLEAR_PAYLOAD_ID_TABLE, REMOTE_DPCD_READ/WRITE,
REMOTE_I2C_READ/WRITE and POWER_UP/DOWN_PHY. Unknown opcodes remain raw and
cannot establish completeness. NAKs remain distinct from AUX ACKs. Partial,
CRC-bad and orphan-sequence messages remain visible; a later valid retransmission
does not erase the earlier error.

Slot count is null in an ALLOCATE_PAYLOAD body because it is not there; native
`0x1c0-0x1c2` slot writes are evaluated separately. Remote I2C's packed
control byte is retained raw: the pinned Linux encode/debug-decode paths have
different stop-bit shifts, so the tool does not pretend that discrepancy is
an independently resolved protocol rule.

## State Reconstruction

AUX requests pair only with a subsequent qualified reply in the bounded
association window, with known declared direction and expected read length.
Gaps, extra requests, malformed packets and unknown roles interrupt pairing.
No missing request, ACK or EDID is fabricated.

MST exchanges match channel, route, sequence, path and request ID, with
port/VCPI/returned-length consistency checks. Allocation state distinguishes
requests, accepted PBN, zero-PBN removal and clear/reset; repeated IDs are not
automatically additional channels. Timeline output carries raw-event references,
acceptance/completeness and errors. Earlier valid observations remain visible
when later capture loss invalidates exclusivity.

Loss interrupts retained allocation state as well as packet pairing; IDs on
opposite sides of a gap do not establish concurrency. Non-root clear scope
remains unresolved and blocks an exclusive count. Slot qualification currently
requires a complete three-byte write and observed 8b/10b channel coding at
`0x108`; unsupported/unknown coding is not silently treated as 63-slot DP.
Unmatched local payload IDs also block exclusivity. Resource replies, correlated
QUERY replies and accepted clears are exposed separately from attempts.
QUERY replies also reconcile retained PBN/ID state; contradictory observations
are preserved and block an exclusive count rather than being ignored.

The current implementation reports each observed LINK_ADDRESS topology rather
than manufacturing a global physical-panel graph. EDID paths mean successful
transport of a decoded request to I2C address 0x50, not validated full EDID
contents or necessarily a successful remote response. Root/descendant/logical
interpretations remain explicit in the raw port descriptors.

## W1 Evaluator

[tools/dp_wire_analyze.py](../../tools/dp_wire_analyze.py) returns W1.1-W1.9
separately, each with `COMPLETE_FOR_INTERVAL` or `CAPTURE_INCOMPLETE`.
Completeness requires declared pre-attach arming, filters disabled, no known or
unknown loss, a nonempty bounded interval and qualified transactions/messages.
These declarations require future acquisition/bench receipts; software cannot
self-prove that a physical recorder missed nothing.

MST enable returns exactly `MST_ENABLE_ESTABLISHED`,
`MST_ENABLE_NOT_OBSERVED_IN_COMPLETE_CAPTURE`, or `MST_ENABLE_UNRESOLVED`.
It is observed control state, not main-link functionality. Allocation outputs
preserve observed IDs/PBN/slots and a maximum observed concurrent-ID count;
an **exclusive** count or `only_one_payload_established` additionally requires
a complete interval and explicitly known initially empty table.

ACT completion requires a qualified current slot update, an observed low
ACT-handled state then updated+handled status in that epoch. A stale bit does
not qualify; incomplete capture returns unknown. `actual_act_packet_observed`
and `real_source_ownership_established` remain false. Hardware authorization is
always false, including for input labeled hardware. Known synthetic direction
provenance cannot be relabeled hardware.

## Synthetic Scenarios

[tools/dp_wire_synthetic.py](../../tools/dp_wire_synthetic.py) deterministically
generates raw AUX request/reply records that carry real wire-format sideband
fragments and CRCs, not predeclared W1 conclusions. No electrical generation
or hardware transport exists in this tool.

| Scenario | Synthetic input | Checked outcome |
| --- | --- | --- |
| A | Enable, two peers, two EDID requests, one accepted payload | Two observed paths and one exclusive control allocation only in complete interval |
| B | Two peers/two allocations, slot programming and low-to-high ACT status | IDs 1/2 and completion; no video/source-ownership proof |
| C | Capability read, disabled control, no enable | Negative enable result only with complete interval |
| D | One branch peer | One reported peer, not a global source limit |
| E | Two peers, requests only to one EDID path | One observed probed path; caching/policy cause not inferred |
| F | Gap during allocation interval | CAPTURE_INCOMPLETE; no one-payload/exclusive-count conclusion |
| G | CRC-bad message then valid retransmission | Valid later topology retained; earlier error still makes interval incomplete |
| H | Direction ambiguous throughout | Direction unknown, MST enable unresolved, no source attribution |

The new suite contains **94 tests** covering required packet types,
framing/timing, raw preservation, duplicate/nonfinite JSON, CRC, sequence/loss,
retransmission, A-H, CLI/bundle overwrite refusal and completeness rules.
All 200 prior tests plus this suite
pass (five offline CTests). No synthetic positive is an M5 observation.

## Capture Format

```text
capture/
  manifest.json
  raw/capture.json
  aux-events.jsonl
  mst-events.jsonl
  analysis.json
  hashes.json
```

Schema 1 input declares `capture_id`, `capture_generation`, `physical_link_id`,
`evidence_kind`, `interval`, `coverage`, optional `loss_intervals`, `acquisition`
and `records`. Acquisition metadata includes hardware, firmware, sample rate,
clock source, front-end revision, timestamp resolution and input configuration.
Record timestamps are integer nanoseconds; raw source clock/scale must remain
in acquisition/extension fields. Binary sample/edge files can be additional
future raw assets, not replaced by decoded output.

The bundle writer archives the exact input bytes before analysis output,
records SHA-256 and decoder-source hashes, includes a caller-supplied decoder
commit (null if not supplied), and refuses an existing destination or symlinked
destination path. Raw files are never overwritten. Native vendor formats and
bulk waveform streaming are future adapters, not invented formats here.

Reproduction uses **synthetic files only** in a new output directory:

```sh
python3 tools/dp_wire_synthetic.py A --output artifacts/probes/m5p7/demo-A.json
python3 tools/dp_aux_decode.py artifacts/probes/m5p7/demo-A.json
python3 tools/dp_mst_decode.py artifacts/probes/m5p7/demo-A.json
python3 tools/dp_wire_analyze.py artifacts/probes/m5p7/demo-A.json --bundle artifacts/probes/m5p7/demo-A
python3 tools/dp_wire_analyze.py artifacts/probes/m5p7/demo-A.json --timeline
python3 -X dev -W error -m unittest discover -s tests -p test_dp_wire.py -v
cmake --build build-m5p4-offline
ctest --test-dir build-m5p4-offline -L offline --output-on-failure
```

No captured hardware sample has been imported. Do not use the file names or
synthetic capture generation as a hardware reproduction receipt.

## Safety Model

The final circuit is **not** declared `OBSERVER_SAFE_FOR_BENCH_VALIDATION` yet.
That classification requires a defensible specific front end, not just a
generic high-impedance box in a diagram. B0 software is safe to run offline;
electrical B1/B2 requires further design review and separate bench scope.

Required receipts before electrical use:

- Input resistance, differential/common-mode capacitance and frequency response
  including connectors, traces, protection and probe tips, measured powered/on/off.
- Verified signal/common-mode/transient range, clamp currents and component
  absolute-versus-operating limits; ESD strategy without excessive bus loading.
- No intentional AUX/HPD drive path, and hardware-enforced protection against
  GPIO misconfiguration and credible input/rail faults. No reliance solely on
  firmware input mode, an FPGA tristate or an unpowered clamp.
- Ground/reference and isolation plan; no unexpected earth/USB-ground current
  or DP_PWR backfeed. Native tap has no CC/PD connection; adapter negotiation
  is not controlled by the observer.
- Source-to-sink continuity, unchanged terminations/bias, short symmetrical
  stubs and a verified main-link pass-through layout. No solderless protoboard
  in the HBR3 path, cut cable or improvised GPIO tap.
- Defined reset, brownout, powered-off, hotplug and failure behavior. Capture
  overflow cannot trigger bus writes, retries or automatic topology changes.

Not having an AUX transmitter is necessary but not sufficient for passive
safety. No experiment may touch the daily-use M5 under this milestone.

## Bench Validation

| Stage | Planned scope | Evidence needed to advance |
| --- | --- | --- |
| B0 | Synthetic vectors, decoder tests, timing/error simulation | Implemented; A-H and the current offline suite pass. No analogue circuit simulation claimed. |
| B1 | Generated AUX-like waveform from an independent bench source, not a Mac | Known amplitude/common-mode/clock, 0.4-0.6 us half-cell range, noise/jitter and quiet/turnaround states; waveform/sample conservation. No generated signal connects to a display link. |
| B2 | Specific front-end loopback with current-limited expendable setup | Powered/off R/C, clamps, thresholds, delay asymmetry, faults, input-output isolation, FIFO overflow and host-stall tests. Reviewed schematic and scope required first. |
| B3 | Known expendable DP source/sink pair | Verify no additional termination/bias/HPD activity, continuity and unchanged operation with/without observer. |
| B4 | Known SST AUX capture | Independent reference trace, correct request/reply framing/direction and loss receipts. |
| B5 | Known MST source/branch | Two-path LINK_ADDRESS, EDID/resource/allocation/ACT control, export reproducibility and seeded loss/negative checks on the bench. |
| B6 | Only after independent owner safety approval: M5 | Fresh generation and controlled attach; all prior bench gates closed. No carry-over authorization from build success. |

No B1-B6 action occurred. Do not skip to B6, force MST, issue private DCP calls,
disable platform security, or reinterpret the historical selector retirement.

## Native-DP Lab Hardware

Shortlist only, public Canadian prices checked 2026-09-18; no purchase or
shipping/tax estimate. These components do not qualify the passive tap.

| Component | Exact current candidate / evidence | Price and limits |
| --- | --- | --- |
| Native source exposure | [StarTech CDP2DP14B](https://www.startech.com/en-ca/display-video-adapters/cdp2dp14b): USB-C DP Alt Mode to DP 1.4, HBR3/DSC, no software driver; USB-C plug to DP adapter | PUBLIC_PRICE_VERIFIED: CAD 26.99 plus taxes on the manufacturer page. Not DisplayLink. Exact MST/HPD behavior and internal conditioning still need B3-B5 evidence; likely four-lane condition differs from ZMUIPNG. |
| Native MST branch | [StarTech MST14DP122DP](https://www.startech.com/en-ca/display-video-adapters/mst14dp122dp): DisplayPort input, two native DP outputs, MST/HBR3, USB power | PUBLIC_PRICE_VERIFIED: CAD 66.99 plus taxes. Manufacturer explicitly says Windows-only and no macOS support: a research branch/expendable-source candidate, **not** a promised working Mac extension solution. Chipset revision was not established from inspected page. |
| Tap/fixture | No final product selected | Main-link transparency and front-end loading remain unqualified. These cannot be replaced with a cheap generic breakout. |

The adapter plus branch list prices total CAD 93.98 before power/cables/taxes,
not an observer BOM or spending recommendation. Keep actual monitor inputs,
link rate/lanes, DSC and conversion controlled in any later plan. A vendor's
OS support list is relevant product evidence, not an architectural M5 proof.

## Prototype BOM

No approved three-tier **build BOM** is issued because the prototype gate is
not met. The following is a priced candidate/requirements worksheet, not a
parts order or schematic. Critical front-end/protection/PCB parts are held,
not silently assumed suitable.

| Tier | Candidate components / purpose | Price evidence / substitutes / unresolved items |
| --- | --- | --- |
| 0: existing bench reference | Existing specified differential probe + scope, known native-DP fixture | No existing inventory or exact probe price verified. Reuse only if R/C/range/memory/export conditions pass. A two-probe subtraction setup is conditional, not automatically equivalent. Suitable for short B1/B2 observations, not currently a complete W1 rig. |
| 1: lowest-cost exploration | TLV3502 candidate receiver + conditioned digital acquisition; Pico/Pico 2 only for short non-Mac burst studies | TI lists TLV3502AID about USD 2.705 at **1,000-unit** pricing, not a one-off quote; Pico/Pico 2 advertised from USD 4/5. Protection, PCB, connectors, qualified transport and standalone part prices remain unresolved. These low prices do not make an adequate continuous observer. |
| 2: reusable streaming architecture | 40 MHz receive-only FPGA capture, 64-bit clock, >=1 MiB effective FIFO and validated fast host transport | Arty A7-100T USD 314.00 documented, but transport/headroom/toolchain/front end still need work; Glasgow analyzer2 is a useful software/hardware architecture, with revision/availability caveats. ECP5/Gowin may substitute only with equivalent memory/transport evidence. No final board selected. |

AD830/INA821/SN65LVDS2 are comparison candidates, not substitutes approved from
their names. TI's public quantity prices and Saleae CAD 710.00 are separately
scoped data points; no unsupported dollar total is assigned to a safe tap.

## Commercial vs Self-Built

`SELF_BUILT_AUX_OBSERVER_PRIMARY` describes the engineering programme, not a
claim that hardware is ready. A useful commercial capture may still accelerate
comparison; lack of replies never stops B0/design/simulation work.

| Dimension | Temporary DPA-400 | MacMST-owned observer |
| --- | --- | --- |
| Time to useful trace | Depends on availability, cable fit/export/loss qualification | B0 pipeline works now; electrical design/bench validation still required; no fabricated delivery estimate |
| Raw access | Documented binary/HTML, exact lossless format unresolved | Neutral raw inputs/bundle preservation implemented; real acquisition not built |
| MST decode | Advertised by vendor | Twelve messages and conservative reassembly/evaluator tested synthetically |
| Completeness confidence | Buffer/overflow semantics still need evidence | Explicit losses/unknowns block negatives; physical loss instrumentation not yet validated |
| Buffer depth | Manual says 14 MB; host streaming limits uncertain | Calculated FIFO/streaming targets, not installed hardware |
| Electrical risk | Designed instrument, exact USB-C assembly still unqualified | Higher development risk; no Mac connection until B1-B5 and approval |
| Up-front cost | Quote/access dependent, no actual offer | Some component prices known; safe complete BOM unknown |
| Reusability | Access duration/licensing dependent | Own formats, tests and source; hardware portability designed in |
| Independence | Third-party scheduling | No external reply dependency |
| Debuggability | Vendor UI/exports | Raw artifacts and code available; analogue faults still need a reference instrument |

Additional public recheck included Unigraf FAQ, current manual/datasheet/catalogue,
[public AUX-monitor presentation](https://www.unigraf.fi/resource/how-to-monitor-aux-channel-communication-of-dp-interfaces/),
and [Ellisys public screenshots](https://www.ellisys.com/products/ctr1/screenshots.php)
alongside M5P6's retained support/download material. Those do not supply a
qualified complete export/loss/fixture contract. These remain public-evidence
gaps; no `VENDOR_CONFIRMATION_REQUIRED` classification is used as a progress
dependency, and no contact/form was sent.

## Prototype Gate

`MORE_ELECTRICAL_RESEARCH_REQUIRED`.

The next self-owned work is specific and falsifiable: choose a powered-off-safe
input topology; bound differential/common-mode/transient/clamp behavior; model
receiver+protection+stub R/C against the timing/amplitude envelope; choose a
transport/FIFO with worst-case margin; and review a non-Mac B1/B2 plan. The
current candidate comparator's rail clamps are a concrete unresolved risk,
not an excuse to wait for a vendor or to probe the Mac.

Parts cannot yet be selected without guessing critical electrical loading or
failure behavior. Therefore neither `AUX_OBSERVER_PROTOTYPE_BUILD_WARRANTED`
nor `OBSERVER_SAFE_FOR_BENCH_VALIDATION` is asserted. The software implementation
and digital synthetic simulation are completed deliverables, not hardware proof.

## Physical-State Policy

`CURRENT_HUB_STATE_NOT_REQUIRED` for M5P7. The user may use the ZMUIPNG hub
normally, including with other computers. No connect/disconnect request is made.
Immutable M5P3/M5P4 evidence is not invalidated by ordinary later use.

Every future hardware milestone must establish a fresh state and generation.
After a separately approved, assembled and bench-validated observer exists:

1. Verify the complete observer/tap and all bench-validation receipts.
2. Establish hub disconnected from M5, regardless of previous milestone state.
3. Attach both target monitors to the hub and power them as required by that plan.
4. Create a new capture generation with actual hardware/OS/topology provenance.
5. Arm the observer.
6. Verify clean capture-loss status and pre-attach coverage.
7. Perform exactly one fresh M5-to-hub attach.
8. Let normal mirrored state settle without display-setting changes.
9. Stop capture and preserve stop/loss metadata.
10. Hash raw artifacts before decoding; this lifecycle alone is the W1 event.

These are future gates, not authorized instructions to execute now.
`RETIRED_ON_DAILY_USE_M5`, `NOT_READY_FOR_DPCD_TEST`,
`STATIC_PACKETIZER_ANALYSIS_FROZEN`,
`NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED` and the frozen
`OFFLINE_OBSERVER_PIPELINE_READY` remain. No private calls, probes, AUX/DPCD
commands, firmware/boot/security changes or m1n1 sibling access occurred.

## Outreach Status

`OUTREACH_CAN_RUN_IN_PARALLEL`, but it is not a prerequisite and no messages
were sent. M5P6's contact package remains byte-for-byte historical evidence;
its prior `USER_OUTREACH_REQUIRED` strategy is superseded for M5P7.

### Verification and Source Receipts

Build and offline CTest passed with 200 preserved tests plus 94 new tests.
Only Python offline tests ran; no native display executable was invoked.
Code diagnostics are clean. New code has no IOKit, DCP, USB/GPIO, network or
electrical capture interface. The JSON and waveform limits are explicit.

The implemented decoder/evaluator revision is
`eb57ee0fe748231e967f35e08f35c02518bc0701` (following the protocol-decoder
commit). Eight local, ignored synthetic bundles are retained under
[artifacts/probes/m5p7/synthetic-v1](../../artifacts/probes/m5p7/synthetic-v1),
with this exact decoder commit, per-module source hashes, original input bytes
and checked output hashes. A-E are complete synthetic intervals; F-H are
incomplete. A/B establish one/two synthetic control allocations respectively;
F-H never return an exclusive count. These are reproducible B0 artifacts,
not acquired waveforms, hardware observations or published third-party material.

Final preservation checks found all 119 non-coordination baseline tracked
files byte-identical, all 453 old ledger rows retained, the 13 M5P5 and 19
M5P6 source hashes unchanged, and every historical runtime bundle hash valid.
The 477 M5P4 records, M2F marker/two receipts and absent M2G read marker are
unchanged. All 48 pre-M5P7 published head/tag/peeled identities matched locally
and remotely before publication. Only this new branch is to be pushed; no
merge, PR, tag change or external material is part of the publication.

Unmodified public sources retained locally under
[artifacts/probes/m5p7/sources](../../artifacts/probes/m5p7/sources):

| File | SHA-256 |
| --- | --- |
| `sn75dp130.pdf` | `44d2d57dbea2e3067fbea5b68a3992fa52e3369053a88afa97d2e34a2593ddb5` |
| `slla343.pdf` | `b55ffef81e7f28d76da8a6e18bd06bd7483f4398d344e0c4d0c39239b8d6682e` |
| `sn65dsi86.pdf` | `b2f05500709185415d8d21f6722abb4dd8a444bc2098b36f423d55554e7eb6ff` |
| `tlv3502.pdf` | `fcfbeffce874629849fe7b2324fa40731a41453b587b8f50782f0ff42311b946` |
| `scopehal-aux.cpp` | `b01a0b6512ad86b1497e3762e49e68a6d0a1e643f995266905ddc7f0faad5e91` |
| `saleae-lla.cpp` | `9f14997f46ef53dd1f0a08d9d3d39c9646355b62236f0218bc5d12fcbe32c277` |
| `saleae-generator.cpp` | `fc5522a367b941b3dce9eab81f311a2dc1429544a8528607eaeeeb22bcb189cc` |
| `saleae-hla.py` | `48128fd3638cdf9327ae6544b2aa27ac277e389b2be92e14ba0ef0aaf6432855` |
| `sigrok-aux.py` | `298a11a44894ca195fe1124cc46196aa06b4ed856b227e930e4ddbf9ca8096e6` |
| `mithro-intercept.sch` | `df3097efcd584c4dbc50ee0b7a8d13d26c4066b842f04dfe33d6aebbe6c13d56` |
| `display_port.lib` | `16d78c3e5e1410123d11cd7341162b99bb13fe5300923b00b8d6914cd8557746` |
| `glasgow-analyzer.html` | `154af8793962923a5317539721d8177ffce65582bf89a4ad82917f0f4b183a2d` |
| `glasgow-analyzer2.py` | `79619e360f00024b1468decc85fb283b0f03c6c4679e2531e4bf9fe7372706d9` |
| `glasgow-analyzer2-protocol.md` | `ea4316a7b31c57e0c89e9ba9f4a7d0e34465eca5d21e17cda67fd4056ee91a96` |
| `glasgow-license.txt` | `dfa1438f18c282a9900954605781be566246826518d15883e835a9fbc14c5096` |
| `checkpoint-license.txt` | `a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499` |

URLs/revisions appear in the relevant sections. Some product pages were readable
with the webpage tool while byte-download attempts returned 403; their prices
are dated page observations, not invented retained hashes or guaranteed quotes.
No proprietary VESA text, manufacturer PDF or external project is republished
as new MacMST source. No analog SPICE or real capture validation is claimed.