# M5P8 Passive AUX Front-End Electrical Qualification

2026-09-18. Electrical research, analytical modelling and offline tests only.
No equipment order, assembly, connection change, Mac probe or real capture.

## Objective

Qualify a receive-only native DisplayPort AUX front end for the MacMST-owned
observer. The eventual objective remains independent displays from the base M5
through ordinary DP MST, without DisplayLink or separate Thunderbolt tunnels.
This milestone does not reopen MST theory, private transport or frozen DCP
packetizer analysis. Outreach is not a dependency.

The preferred **architecture** is symmetric AC-coupled sensing into a low-bias
comparator, with a forward-only isolated digital output. A concrete, editable
**analysis circuit** and reproducible loading/conditioned-signal models are
provided. They expose relevant failure corners; they are not a released PCB
schematic, a qualified full BOM or permission to construct hardware.

Result: `MORE_ELECTRICAL_RESEARCH_REQUIRED`. The remaining deficiencies are
specific: actual worst-case receiver capacitance/low-overdrive timing, matched
common-mode transfer, coordinated transient protection, power-sequencing
backfeed, and a finalized physical PCB/acquisition implementation.

## M5P7 Baseline

Reconciled `research/m5-aux-observer` at
`277ff81437f3d5443eba58375495f86b3c5fcb41`, with matching
`origin/research/m5-aux-observer`, ahead/behind 0/0 and clean worktree.
The three linear commits are:

1. `0706e1f9ce595dd554e567ac44af7731ce7ef6a1`: AUX/MST decoders.
2. `eb57ee0fe748231e967f35e08f35c02518bc0701`: W1 evaluator/scenarios/tests.
3. `277ff81437f3d5443eba58375495f86b3c5fcb41`: research report/coordination.

Their base is M5P6 `research/m5-aux-access` at
`e909e471cbf5982749de2c67655197d091438a27`. All 49 previous head/tag/peeled
identities matched locally/remotely. M5P3/M5P4 runtime bundle hashes, M5P5/M5P6
reports, all 48 M5P5-M5P7 source receipts, A-H synthetic bundle hashes and
manifest-bound decoder source hashes were verified. M2F's consumed marker and
both receipts were unchanged; the M2G DPCD-read marker remains absent.

`cmake --build build-m5p4-offline` and the five existing `offline` CTests
passed: **294 tests**. No native display executable ran. The new branch
`research/m5-aux-frontend` was created from that exact M5P7 HEAD.

All four M5P7 wire modules, their 94 tests and existing bundles are frozen.
New modelling support is separate; no capture transport or device API is added.
Historical findings and the current hub state are not re-observed.

## Verified AUX Electrical Requirements

Classification vocabulary:

- `VERIFIED_VALUE`: the cited public document states the value or property in
  its stated context. This is not a fresh M5 measurement.
- `BOUNDED_FROM_PUBLIC_COMPONENT_DATA`: a documented endpoint/component range
  informs design exploration, not a universal DisplayPort conformance limit.
- `ASSUMED_FOR_SIMULATION`: a model parameter or engineering target, not a
  recovered normative requirement.
- `UNKNOWN_DESIGN_PARAMETER`: no sufficiently qualified bound was established.

Authoritative public references used below:

| Source | Exact document / location | Scope |
| --- | --- | --- |
| P1 | TI [SN65DSI86 SLLSEH2C](https://www.ti.com/lit/ds/symlink/sn65dsi86.pdf), October 2020, AUX electrical table p. 11, switching table p. 14, section 8.4.5.2 | Endpoint implementation; retained M5P7 PDF unchanged |
| P2 | TI [SLLA343](https://www.ti.com/lit/an/slla343/slla343.pdf), October 2013, sections 2.3.2-2.3.3 | Endpoint coupling, detection bias and routing, not an extra-observer allowance |
| P3 | TI [SN75DP130 SLLSE57E](https://www.ti.com/lit/ds/symlink/sn75dp130.pdf), March 2015, section 7.3 p. 7 | Location-qualified AUX snoop voltage/rate/jitter data |
| P4 | TI [TDP142 SLLSEZ1C](https://www.ti.com/lit/ds/symlink/tdp142.pdf), May 2019, AUX rows p. 7, application/section 11.1 | HBR3 component's AUX snoop/PCB guidance; no redriver is added to our design |
| P5 | TI [TLV350x SBOS321E](https://www.ti.com/lit/ds/symlink/tlv3502.pdf), April 2016, sections 6.1, 6.6, 6.7, 7.3.2 | Comparator, not an AUX receiver specification |
| P6 | TI [TLV321x SNOSDK9C](https://www.ti.com/lit/ds/symlink/tlv3211.pdf), September 2026, sections 5.1, 5.3, 5.7-5.8 | Current primary candidate electrical data |

| Design-critical quantity | Value / finding | Classification |
| --- | --- | --- |
| Ordinary AUX rate/encoding | Nominal 1 Mbit/s before Manchester-II encoding; differential, half-duplex, bidirectional and AC-coupled, P1/P2 | VERIFIED_VALUE |
| Fast AUX | P3 separately lists 720 Mbit/s FAUX; not supported by this design or implied by HBR3 main-link rate | VERIFIED_VALUE |
| Manchester interval | P1 UIMAN 0.4-0.6 us; nominal half-cell 0.5 us follows ordinary 1 Mbit/s Manchester. P3 instead specifies 0.8-1.2 Mbit/s before encoding | BOUNDED_FROM_PUBLIC_COMPONENT_DATA |
| TX swing | P1 differential peak-to-peak 0.18-1.38 V, defined as twice the absolute pin difference | BOUNDED_FROM_PUBLIC_COMPONENT_DATA |
| RX voltage envelope | P1 differential peak-to-peak 0.18-1.36 V; P3 snoop input 0.3-1.4 Vpp | BOUNDED_FROM_PUBLIC_COMPONENT_DATA |
| Receiver threshold | These amplitude rows do not specify a universal switching threshold, idle threshold or noise margin | UNKNOWN_DESIGN_PARAMETER |
| Pin-side common mode | P1 AUX DC common mode 0-1.2 V; turnaround common mode 0.3 V. P3 source common mode 0-2 V explicitly before coupling caps | BOUNDED_FROM_PUBLIC_COMPONENT_DATA |
| Cable/snoop-side bias | P3 AUX+ DC -0.5 to 0.4 V and AUX- DC 2-3.6 V in its DP configuration. P4 AUX+ 0-0.4 V, AUX- 2.7-3.6 V | BOUNDED_FROM_PUBLIC_COMPONENT_DATA |
| Exact connector instantaneous envelope | DC limits cannot simply be treated as DC-plus-AC peak limits. Actual offset, swing superposition, hotplug and ground offsets remain unqualified | UNKNOWN_DESIGN_PARAMETER |
| Termination | P1 AUX termination typical 100 ohm and doubly terminated channel | VERIFIED_VALUE |
| Driver source impedance | A typical termination is not a guaranteed Thevenin output impedance. No universal source impedance bound established | UNKNOWN_DESIGN_PARAMETER |
| Model impedances | 50 ohm per driven leg, 100 ohm differential sink; sweep source legs 25/50/75 ohm | ASSUMED_FOR_SIMULATION |
| Coupling caps | P1/P2/P3 75-200 nF at endpoint coupling locations; P2 recommends 100 nF for its bridge | BOUNDED_FROM_PUBLIC_COMPONENT_DATA |
| Detection bias | P2 illustrates 100-kohm networks; P4 explicitly requires AUX+ 100-kohm pulldown and AUX- 100-kohm pullup on its side of the 100 nF caps | VERIFIED_VALUE |
| Observer bias | No resistor or termination is added directly across the link. Proposed local 1 Mohm bias is behind 2.2 pF DC-blocking sense caps | ASSUMED_FOR_SIMULATION |
| Edge rise/fall | No ordinary-AUX universal rise/fall envelope established from the inspected tables. Main-link picosecond rows are not AUX specifications | UNKNOWN_DESIGN_PARAMETER |
| Model edge | 10 ns source ramps in the authored SPICE decks; sensitivity to real edge shape remains necessary | ASSUMED_FOR_SIMULATION |
| Jitter | P1 TX 0.08 UIMAN and RX 0.04 UIMAN; P3 adjacent-cycle 0.05 UI and within-cycle 0.1 UI in its stated receive conditions | BOUNDED_FROM_PUBLIC_COMPONENT_DATA |
| Idle | Existing cable-side bias can create a large static pin difference. It is not valid Manchester data and is not necessarily zero differential voltage | BOUNDED_FROM_PUBLIC_COMPONENT_DATA |
| Turnaround timing | P1's controller uses a 400 us reply wait and 100 us retry interval. Those are not a universal minimum turnaround time | VERIFIED_VALUE / UNKNOWN_DESIGN_PARAMETER |
| Maximum continuous activity | No universal duty-cycle guarantee established. Budget 100% recorder activity and retain idle time | ASSUMED_FOR_SIMULATION |
| Packet bound | Ordinary native AUX carries up to 16 data bytes; the PHY still needs preamble, delimiters, interpacket time and error preservation | VERIFIED_VALUE |
| ESD environment | Board/system IEC discharge exposure and required severity depend on fixture/enclosure/use. IC HBM/CDM ratings are not a system-port guarantee | UNKNOWN_DESIGN_PARAMETER |
| Input absolute maxima | P5 comparator input rails +/-0.3 V with current-limited excursions; P6 rails +/-0.5 V, input current +/-10 mA and differential +/-6 V are stress ratings | VERIFIED_VALUE |
| M5-specific values | None measured or newly queried in M5P8 | UNKNOWN_DESIGN_PARAMETER |

The simulation uses a loaded differential peak of 90 mV (180 mVpp) as a
challenging component-derived case, not proof that every connector has that
minimum. Its open-source stimulus is normalized to the assumed load; do not
confuse an ideal source's open-circuit voltage with P1's transmit-pin rating.

## Observer Loading Budget

The observer is a branch, not a third endpoint. Two effects must be modelled
separately: active-signal loading and weak idle-bias loading.

For the illustrative DC network with two 100-kohm endpoint bias resistors and
2.7 V open-circuit differential bias:

$$V_{loaded}=2.7\frac{R_{observer}}{200000+R_{observer}}.$$

A 200-kohm differential probe leaves 1.35 V and draws 6.75 uA in this network.
A 200-Mohm differential observer leaves about 2.697 V. This is a model, not a
claim about the actual hub's bias circuit. It disproves the shortcut that a
load negligible beside 100 ohm must also be negligible during idle/detection.

Proposed acceptance targets, all `ASSUMED_FOR_SIMULATION` / engineering choices:

| Property | Target before any link use | Rationale / qualification still needed |
| --- | --- | --- |
| DC input resistance to local reference | >=100 Mohm per conductor; >=200 Mohm differential under symmetric conditions | Limit disturbance of weak detection bias; check insulation and contamination, not just comparator bias current |
| Leakage | <=100 nA per conductor across the qualified voltage/temperature envelope, powered and off; mismatch <=20 nA | 100 nA through 100 kohm gives 10 mV shift per conductor; engineering target, not a DP allowance |
| Added shunt capacitance | <=4 pF per conductor, including unpowered state, trace/pads/connector/protection/sense branch | Nominal conservative off bound 3.2 pF; not a normative permitted load |
| Differential equivalent | <=2 pF for two matched 4 pF shunts to a fixed reference, plus separately bounded direct cross-pair capacitance | Do not add differential and common-mode capacitance specifications as though identical |
| Capacitance imbalance | <=0.1 pF at the cable reference plane | Layout, component tolerance and powered-off junctions all count |
| Sense transfer mismatch | <=0.005 V/V over the useful band | Limits conversion of a hypothetical 0.3 V CM stimulus to 1.5 mV; matching terminal load alone does not guarantee matched sense gain |
| Active waveform change | <=1% amplitude change through 10 MHz; added edge displacement <=25 ns and no new threshold crossings | Decoding-oriented bench criteria, not electrical compliance |
| Digital timing | Rise/fall delay asymmetry <=25 ns plus measured jitter budget; adequate margin at 40 MS/s | Fixed delay is less harmful than differential delay or false edges |

Nominal sense parameters per leg: 1 kohm at the branch, protection represented
by 0.5 pF, 2.2 pF coupling, 2.2 kohm input limiter, 1 Mohm local bias, 2.5 pF
total receiver-side capacitance and 0.5 pF unisolated board stray capacitance.
The 2.5 pF is an **assumption**, not TLV3211's maximum input capacitance.

At frequencies above the bias high-pass corner, the approximate signal gain is
$C_s/(C_s+C_i)=0.468$ and the nominal high-pass time constant is 4.7 us.
The capacitor-series equivalent is about 1.17 pF; adding protection and board
stray gives about 2.17 pF. If unpowered clamps conduct, the conservative bound
becomes $C_s+C_{protection}+C_{stray}=3.2$ pF, not the powered value.

The exact small-signal two-node model retains source coupling caps, a resistor
**across** the sink pair, independently modelled bias paths, and both observer
branches. Differential termination is not silently grounded at its midpoint
for common-mode analysis. Source-leg/coupling sweeps cover 25/50/75 ohm and
75/100/200 nF; these bracket assumptions, not an established universal channel.

At 10 MHz the computed relative sink amplitudes are 0.99944 (S1), 0.99851
(conducting-clamp S2), 0.99894 (S3), and 0.99944 (S4). The model supports low
active loading under these assumptions. It does not bound fast hotplug, ESD,
connector resonance or a real component's off-state junction behavior.

S4 uses opposing sense-cap errors (+/-0.1 pF), a 0.25 pF receiver-capacitance
imbalance and +/-1% resistor errors. At 1 MHz its source-common-mode to
sense-differential conversion is **0.04737 V/V**, almost ten times the target.
A hypothetical 0.3 V CM input then yields about **14.2 mV** error. Good bus
loading therefore does not establish adequate measurement fidelity.

## Front-End Architectures

`COMPARATOR_FRONTEND_PREFERRED` for continued qualification, not build release.

| Architecture | Quantified strengths | Limitation / decision |
| --- | --- | --- |
| A: differential active probe + scope | Tek [TDP1500, 51W-20565-9](https://www.tek.com/en/datasheet/differential-probes): typical 200 kohm differential, <1 pF, 1.5 GHz warranted bandwidth, +/-7 V common mode, +/-850 mV at 1X or +/-8.5 V at 10X; typical <2 mV RMS noise at 1X | Good controlled B1 reference if available, but 200 kohm can disturb weak bias. No off-state transparency guarantee located. Scope/probe cost and continuous capture remain separate. Not approved for a live DP link. |
| B: conditioned high-Z comparator | Very low powered bias current; AC sensing can reject static cable-side bias and bound added capacitance even when input clamps conduct | Preferred modest-complexity architecture. It still needs gain matching, transient/protection and max-capacitance closure. Direct raw-AUX comparator connection is rejected. |
| C: differential amplifier then comparator | Gain can improve downstream threshold margin and provide an analogue output | The first amplifier still owns loading, common-mode and power-off problems. More parts, rails, noise and loop-stability work; no demonstrated need yet. Fully differential feedback amplifiers can present resistor-network loading, not automatically high-Z inputs. |
| D: dedicated differential receiver | Simplifies slicing when its electrical contract matches | SN65LVDS2's +/-100 mV threshold envelope exceeds the 90 mV differential-peak exploration case; 5.8 pF typical input and up to 20 uA off current at the specified test point are poor matches. No added 100-ohm termination. Not selected. |

TDP1500 is a concrete **reference-probe candidate**, not a backend purchase
recommendation. Its exact current price was not resolved from the inspected
model listing; the manufacturer's CDN 5,160 family entry is for ADA400A and
must not be reassigned. The ADA400A's 1 MHz / about 55 pF is not our desired
front end. At 20 MS/s a 10 Mpoint scope still stores only 0.5 s, not 180 s.

## Component Qualification

Current manufacturer lifecycle/order pages were checked 2026-09-18. ACTIVE or
production status is not proof of immediate single-unit stock. No order/login
or contact was made. Manufacturer datasheets are primary electrical evidence.

| Component / function | Input Z and C | Common mode / speed | Powered-off behavior | Package / current status / decision |
| --- | --- | --- | --- | --- |
| TLV3502, dual comparator, P5 | Typical 10^13 ohm || 2 pF CM and 10^13 ohm || 4 pF differential; +/-10 pA at stated midpoint condition, not production tested | Table range (V-)-0.2 to (V+)-0.2; CMRR/application text uses wider limits. 4.5 ns typical at 20 mV overdrive; 12 ns maximum at 5 mV overdrive over temperature | Rail clamps; no transparent VDD=0 leakage contract established | SOIC-8 / SOT-23-8; ACTIVE, stock behind login. Retain as comparison, not preferred |
| [TLV3201, SBOS561C](https://www.ti.com/lit/ds/symlink/tlv3201.pdf), May 2024 | Very low powered input bias; no bounded maximum input C established from inspected data | 2.7-5.5 V, CM extends 0.2 V beyond rails; 40 ns class | Section 7.3.2 explicitly describes input rail diodes | SOT-23-5 / SC70-5; ACTIVE, page offered no available stock. Does not solve off-state problem |
| TLV3211DCKR, single comparator, P6 | 1.5 pF **typical**, 1600 Gohm differential and 550 Gohm CM typical; input bias 1 pA typical, 1.2 nA maximum over -40..125 C at stated 5 V/midpoint; offset-current maximum 250 pA | 1.8-5.5 V recommended; CM rails +/-0.2 V. Offset +/-6 mV and hysteresis <=4 mV at stated 5 V conditions. At 20 mV overdrive, about 54/56 ns typical rise/fall delays; the 100 mV-overdrive maxima do not establish low-overdrive bounds | Rail clamps; current-limited rail excursions are stress limits. POR is output startup behavior, not input transparency | SC70-5; ACTIVE, order/login page. Primary **candidate** for conditioning; capacitance and low-overdrive corner qualification incomplete |
| [TLV3601, SNOSDB1E](https://www.ti.com/lit/ds/symlink/tlv3601.pdf), high-speed comparator | 1 pF typical; 67 kohm differential and 5 Mohm CM typical; bias up to 5 uA | 2.4-5.5 V, rails +/-0.2 V, 2.5 ns class | Input rail clamps | SOT-23-5/SC70-5; ACTIVE, stock unavailable on inspected page. Faster, but inferior bias/loading for this passive sense network |
| [MCP6561, DS20002139E](https://ww1.microchip.com/downloads/aemDocuments/documents/MSLD/ProductDocuments/DataSheets/MCP6561-1R-1U-2-4-1.8V-Low-Power-Push-Pull-Output-Comparator-DS20002139E.pdf), Microchip comparator | Typical 10^13 ohm || 4 pF CM and 10^13 ohm || 2 pF differential; about 1 pA typical at 25 C, not a guaranteed off current | 1.8-5.5 V, CM extends slightly beyond rails; 56 ns typical/80 ns maximum high-to-low at 100 mV overdrive and 1.8 V | Rail-limited absolute input range; no transparent-off guarantee established | Several SOT/SC70 variants, in production; manufacturer lists stock for some variants and USD 0.56 at 1-24 units, not a confirmed exact-package BOM price. No clear loading advantage over conditioned TLV3211 |
| [LTC6752](https://www.analog.com/en/products/ltc6752.html), ADI comparator lead | Input Z/C not qualified here | 2.9 ns class and rail-to-rail advertised | Not qualified | Recommended for new designs; TSOT/SC70/MSOP/QFN family. Datasheet retrieval failed, so not selected from headline speed |
| [AD830](https://www.analog.com/en/products/ad830.html), difference-amplifier lead | Exact input loading/off behavior not qualified | 85 MHz unity gain and wide common mode advertised under appropriate supplies | Unresolved | Production; not selected without full input/protection proof |
| [INA821](https://www.ti.com/product/INA821), instrumentation-amplifier comparison | Low powered input bias does not establish off behavior | 4.7 MHz typical minimum-gain bandwidth, reduced at gain | Unresolved | Not selected: little margin against the proposed 10 MHz front-end target, and gain does not fix the first input stage |
| [SN65LVDS2, SLLS373M](https://www.ti.com/lit/ds/symlink/sn65lvds2.pdf), dedicated receiver | 5.8 pF typical; input-current limits in microamps, not high-Z comparator territory | Receiver threshold bounds +/-100 mV; input operating range is supply dependent | Up to 20 uA at VCC=0, both inputs 2.4 V | SOT-23-5/SOIC-8, ACTIVE. Reject for the current minimum-amplitude/loading targets |
| [TPD1E01B04DPYR, SLVSDG3C](https://www.ti.com/lit/ds/symlink/tpd1e01b04.pdf), bidirectional protection candidate | 0.20 pF typical / 0.23 pF max for DPY at 0 V, 1 MHz, 25 C; <=10 nA leakage at +/-2.5 V | +/-3.6 V standoff; 6.4 V minimum breakdown; typical TLP clamp 7 V at 1 A, 9.2 V at 5 A, 15 V at 16 A | Rail-independent two-terminal device; not a zero-leakage component | DFN1006-2, ACTIVE, login for stock. Voltage headroom/pulse coordination not closed |
| [TPD1E05U06](https://www.ti.com/product/TPD1E05U06), protection comparison | 0.5 pF typical, <=10 nA catalogue leakage | 5.5 V standoff but **unidirectional** | Negative excursions can forward-bias it | Not selected merely because it is sold for USB/HDMI |
| [PESD5V0U1UL](https://www.nexperia.com/product/PESD5V0U1UL), protection comparison | 2 pF typical, 1 nA advertised leakage | 5 V standoff, **unidirectional** | No appropriate bipolar input guarantee established | DFN1006-2, production. Higher capacitance and wrong polarity characteristic for the intended envelope; not selected |
| [ISO7710FDR, SLLSER9E](https://www.ti.com/lit/ds/symlink/iso7710.pdf), forward-only digital isolation | No conductive signal/ground path across barrier; barrier capacitance still exists | 2.25-5.5 V on each side; 100 Mbit/s family, 11 ns typical delay; use supply-specific table for bounds | F variant defaults output low on loss of input-side power/signal under specified conditions | SOIC-8, ACTIVE. Proposed mitigation for USB ground/backpower path, not isolation of the AUX analogue receiver itself |

High-value precision resistors and low-pF C0G capacitors are specified by value
in the model, but exact voltage/pulse/tolerance/insulation-qualified MPNs are
not released. At 2.2 pF, pads and matching can dominate nominal component
tolerance. A generic 0402 resistor or ceramic capacitor is not automatically
an ESD-rated protection element. No analogue switch is added: its off leakage,
capacitance, charge injection and power sequencing would be another interface
to qualify, not a free solution.

## Comparator Selection

`TLV3502_NOT_PREFERRED` for this observer, not a declaration that it can never
work with suitable conditioning.

TLV3502's speed is ample and its powered bias is attractive, but its published
CM/differential capacitances, 6 mV typical hysteresis, rail clamps and lack of
a transparent unpowered-input specification dominate this application. Its
2.7-5.5 V characterized supply range and 4.5 ns headline do not close those
gaps. P5's table/text common-mode discrepancy is retained; use the more
restrictive range for design, not an unsourced favourable interpretation.

At 3.3 V, direct connection to cable-side AUX is rejected. Static AUX- bias
can be near/above a supply rail, while AUX+ may be negative; when power is off,
input clamps become current paths. Attenuation alone also reduces the already
small differential signal. Level shifting must account for both DC bias and
transients, not merely move a nominal sine wave into range.

TLV3211 is the better **component candidate** for the AC-coupled topology:
1.5 pF typical input C, lower hysteresis, sufficient nominal speed and small
SC70 package. It is not yet electrically qualified. Its typical C is not a
maximum, and delay specified at 100 mV overdrive cannot be applied to an
attenuated 10-20 mV signal. The behavioural 40 ns delay and tested sweeps are
assumptions, not a timing guarantee for this IC at 3.3 V.

No comparator is selected solely on nanoseconds, nor is an amplifier added to
conceal the receiver's input qualification problem.

## Protection Network

Analysis topology, duplicated symmetrically:

```text
source AUX ================================ sink AUX
                   |
                  1k     branch resistor at the junction
                   |
                 PROT ---- bidirectional TVS to analogue reference
                   |
                 2.2pF   DC-blocking sense capacitor
                   |
                 2.2k    comparator clamp-current limiter
                   |
                  IN ---- 1Meg to fixed local midpoint
                   |
              comparator input capacitance / internal clamps
```

The TVS is **before** the DC-blocking sense capacitor. Putting a 10 nA leakage
source after it creates 10 mV across a 1 Mohm bias resistor; that placement
failed the 8 pF + 20 mV offset behavioural case. At the revised position it
does not create that comparator bias error, but still loads the link's idle
bias: 10 nA through an assumed 100 kohm endpoint gives 1 mV per conductor.

The model uses 0.5 pF protection C, deliberately above TPD1E01B04DPYR's
specified test-point maximum to allow a budget, not to declare tolerance at
all voltages/temperatures. Added pad/trace C is separate. No Schottky rail clamp
is selected without quantifying its leakage and capacitance; no protection
device is connected to an externally controlled digital rail.

TPD1E01B04's +/-3.6 V standoff is **not yet sufficient** for a defensible
instantaneous cable envelope: P3's 3.6 V is DC, not an established total peak.
At 15 V post-TVS excursion, a 2.2 kohm input limiter would bound current into
a hypothetical 0.3 V unpowered clamp to about 6.68 mA. That is below P6's
10 mA stress limit but is **not** acceptable proof of transparency, rail-current
handling or survival of an IEC pulse. Actual overshoot, resistor pulse energy,
capacitor withstand, device snapback and local ground inductance remain open.

The authored TVS uses a symmetric piecewise-linear 6.4 V/0.57 ohm approximation;
the input diodes are generic. Neither is a manufacturer macromodel. They must
not be used to claim certified ESD protection or powered-off isolation.

## RX-Only Enforcement

`HARDWARE_RX_ONLY_ENFORCED` **at the proposed circuit architecture level**:

- AUX and HPD are continuous source-to-sink conductors; no transmitter,
  GPIO output, DAC, switch or programmable bias is connected to them.
- The two AUX branches terminate at analogue comparator **inputs**.
- The comparator output feeds the input side of a **1-forward/0-reverse**
  ISO7710F boundary. The sampler sees only its output side.
- Analogue supply/midpoint are fixed and independently powered, not controlled
  by sampler VIO or a GPIO. ISO output-enable, if used, is tied locally; it is
  not a control signal crossing toward AUX.
- No HPD control, DPCD bank, EDID emulation, main-link active component or
  intentional feedback resistor to AUX exists.

The isolation stage is justified by a concrete concern: a USB-connected sampler
can otherwise add a ground-return/backpower path, and a misconfigured output
GPIO could contend with the comparator output. Removing the intentional reverse
path addresses that concern; it does **not** prove zero parasitic coupling,
arbitrary-fault containment or physical-board safety. All components have
parasitics. This is not a claim that hardware was assembled or tested.

Structural tests check that the analysis subcircuit contains no independent or
dependent source on AUX and that RXD appears only at the forward output source.
They are not a substitute for schematic/ERC/layout review of an actual board.

## Powered-Off Behaviour

`POWERED_OFF_BEHAVIOR_UNRESOLVED`.

With the sense capacitors intact, there is no intended DC path from AUX to the
comparator rails. In the conducting-clamp small-signal bound, receiver input
impedance is replaced by 10 ohm and the link still sees the series 2.2 pF sense
capacitance plus parasitics. This is a useful bound, not a real VDD=0 model.

For a 3.6 V step, one 2.2 pF sense cap can transfer up to 7.92 pC. A 10 ns
ramp implies 0.792 mA by C*dV/dt before other circuit effects. The 1 kohm
branch resistor separately limits a 3.6 V step to at most 3.6 mA. Small total
charge is not zero injection: it can charge an unpowered rail, cause a brief
bus disturbance or change the comparator's effective capacitance.

Under a crude 25-ohm active source/load equivalent, 0.792 mA corresponds to
about 20 mV instantaneous disturbance, much larger than a 1% criterion at
90 mV. This is a conservative illustrative bound, **not** a simulated or
measured glitch. It shows why frequency-domain loading alone cannot close the
power-off gate.

Required cases include power-on, gradual/abrupt power-off, brownout, USB backend
powered while analogue supply is absent, hotplug with discharged/charged sense
caps, both AUX transmitter directions, and one-rail faults. The digital isolator
removes an intended backend power-return route; it does not remove comparator
input clamps, TVS leakage or charge stored in the sense network. No switch or
relay is assumed to become safe merely because its enable defaults low.

## Ground Strategy

The analogue front end is **differential but non-isolated from DP reference**.
The proposed digital output is galvanically isolated from the USB capture host.
Use one defined analogue-reference connection to the DP reference-ground
network; never use AUX- as ground. Connector shell continuity and signal ground
must be designed intentionally, not improvised with clips.

Analogue power is a separate current-limited isolated bench supply for B1/B2,
or later a qualified battery/regulator assembly. Do not power it from DP_PWR
or the sampler's programmable output supply. Do not connect a battery charger
across the intended isolation boundary during a capture. The exact supply/BOM
is not yet selected; the SPICE ideal 3.3 V rail is not a regulator design.

For controlled B1/B2, generator and scope references may share the single
intentional bench reference. For later DP use, check source/sink/charger/scope
earth relationships before attachment. A differential probe can still have
finite paths to scope earth. Attaching a normal scope ground lead to an
isolated node can defeat the isolation. Never lift protective earth or float a
mains-powered scope as a workaround.

This is functional isolation to avoid an extra USB ground/backpower path, not
a certification that the complete board is safe for mains isolation. Follow
ISO7710's layout, clearance, decoupling and separate-ground requirements.

## DP Tap Board

`PURPOSE_BUILT_DP_TAP_PCB_PREFERRED`.

Use a short rigid, controlled-impedance native-DP interposer. Source/sink
connector choice, footprint orientation and HBR3 channel qualification remain
open. No existing generic breakout was established as acceptable. A full DP
connector pin map must be verified against the actual manufacturer's drawing,
not only the prior public KiCad symbol.

Requirements:

- Four main-link pairs, AUX pair and HPD pass continuously between connectors.
- Only AUX branches to the sense network; no test pads or observer stubs on
  main-link pairs, and no HPD measurement/control branch in this minimum design.
- Preserve required grounds/shields and native configuration contacts without
  adding bias or emulation. Do not blindly bridge DP_PWR pin 20: the observer
  must not create a source-to-sink power/backfeed connection. Its handling needs
  the exact connector/cable plan; no observer power is drawn from it.
- No retimer, redriver, MST silicon, active EDID or AUX driver is present.
- Receiver/protection assembly should be near the AUX junction, with the
  isolated digital boundary away from the high-impedance sense nodes.

No board layout or fabrication files are released. A two-connector interposer
still adds channel loss/discontinuities; 'passive' does not mean electrically
invisible. Do not substitute a cut cable or solderless breadboard.

## Main-Link Routing

P4 section 11.1 recommends **100 ohm differential +/-10%**, intra-pair
matching within 5 mil (0.127 mm), and keeping the pairs away from other
high-speed signals. This is concrete HBR3 component design guidance, not a
guarantee that our unbuilt interposer passes DisplayPort compliance.

TI [SPRAAR7J](https://www.ti.com/lit/an/spraar7/spraar7.pdf), February 2023,
sections 3.3-3.12, supports continuous reference planes, pair symmetry,
minimized layer transitions and via stubs; its examples recommend stubs below
15 mil or back-drilling. USB-specific impedance rows in that guide must not
be substituted for the native-DP 100-ohm target.

Proposed engineering constraints: shortest direct surface routing between
connector launches, no intentional main-link branches, no added AC coupling
caps or filters, zero signal vias if the connector footprints permit, symmetric
transitions otherwise, and return-path stitching adjacent to transitions.
Preserve pair geometry through bends and match at the location of mismatch.

Use a fabricator-defined four-layer minimum stackup with a close uninterrupted
ground plane below the signal layer; six layers may help if connector/power
routing demands it. Width/gap cannot be specified honestly without laminate
Dk, copper thickness, plane spacing, solder mask and connector launch geometry.
Request a field-solved impedance/coupon with the actual fabrication data in a
later authorized procurement step. No quote or manufacturer contact occurs now.

HBR3 is 8.1 Gbit/s/lane, UI about 123.46 ps and Nyquist 4.05 GHz. A short
interposer still needs loss/return-loss/launch validation at relevant harmonics.
FR-4 is not automatically disqualified for a short path, but neither is an
unspecified FR-4 stackup automatically adequate. No high-speed compliance,
S-parameter or eye-diagram result is claimed.

## AUX Routing

Engineering targets, not DisplayPort-mandated dimensions:

- Keep the unisolated AUX tee to the first branch resistor **<=2 mm**, matched
  between conductors. Place the resistor at the tee, not at the far end of a
  long stub. Keep the rest of the front end within roughly 5 mm where practical.
- Preserve the through AUX differential geometry; do not insert the sense cap
  or resistor into the source-to-sink path.
- Put branch protection after the first resistor and before the sense cap;
  use a short local reference connection. The ESD tradeoff remains unqualified.
- Keep the two local bias/input networks symmetric and away from comparator
  output edges, isolation carriers, regulators and main-link fields.
- No ground-plane cut should interrupt through-path return current. Any local
  pad-capacitance optimization needs field analysis, not arbitrary plane removal.

For an assumed 50-ohm single-ended geometry and 6 ps/mm propagation delay,
$C'=t'/Z_0$ gives roughly **0.12 pF/mm**. A 2 mm pre-resistor stub is about
0.24 pF before pads/connector effects, compatible with the nominal 0.5 pF
budget only if the actual geometry is verified. Flight time is tiny beside
0.4 us, but capacitance and unequal gain can still dominate. Nominal 1 Mbit/s
therefore does not justify loose or asymmetrical wiring.

## SPICE Model

`SPICE_MODEL_INSUFFICIENT`.

No ngspice, Xyce, Qucs-S or KiCad CLI was found on PATH; common LTspice/KiCad/
Qucs application locations were also absent. No simulator or numerical package
was installed. **SPICE decks are authored, not executed.** The numerical
results in this report come from independent complex-network equations and a
limited behavioural RC/slicer model, not from a SPICE run.

Artifacts:

- [Model Parameters](../../hardware/aux-observer/model.json): explicit assumed
  component/source parameters, worst corners and non-authorizing status.
- [Analysis Subcircuit](../../hardware/aux-observer/aux-sense.cir): editable
  SPICE text containing the two receive-only branches, local bias/decoupling,
  generic protection/clamps, ideal comparator and ideal one-way digital boundary.
- [Model Tool](../../tools/dp_aux_frontend_model.py): deterministic calculations,
  S0-S5 deck generation and conditioned digital fixtures.
- [Tests](../../tests/test_dp_aux_frontend.py): numerical limiting cases,
  pair/half-circuit consistency, waveform regressions and artifact checks.

| Case | Authored circuit / executed calculation | Findings and limits |
| --- | --- | --- |
| S0 | No observer instance; source/coupling/differential termination/bias network | Reference transfer, relative amplitude 1 |
| S1 | Nominal powered observer | At 1 MHz relative sink amplitude 0.999978 and sense ratio 0.46757 |
| S2 | Unpowered deck with generic rail diodes; separate AC calculation pessimistically substitutes a conducting 10-ohm clamp | At 10 MHz relative sink amplitude 0.998506. These are different conservative/behavioural models, not an asserted macromodel match |
| S3 | 8 pF receiver-side C and 3 pF bus stray | At 1 MHz sense ratio 0.21559. Total off-cap budget can be exceeded; nominal-C success is not a corner guarantee |
| S4 | Opposing capacitor/resistor errors; authored deck also includes a 0.3 V common-mode pulse | 0.04737 V/V CM conversion at 1 MHz in the assumed network, exceeding the transfer-match target |
| S5 | Representative framed Manchester AUX request | Nominal behavioural waveform decodes; deliberate malformed/corner cases do not silently become valid |

The AC solver compares differential amplitude and common-mode conversion.
The behavioural model compares sensed level/droop and threshold/edge timing.
SPICE transition time, settling, nonlinear symmetry and rail-injection waveforms
remain **unmeasured/unexecuted**, not inferred from an AC magnitude table.
The PWL testbench sources exist outside the observer subcircuit; they are
bench models, never an AUX transmit function in the observer.

Reproduction, local synthetic data only; each output must be new:

```sh
python3 tools/dp_aux_frontend_model.py
python3 tools/dp_aux_frontend_model.py --capture --output artifacts/probes/m5p8/reproduction/nominal.json
python3 tools/dp_aux_decode.py artifacts/probes/m5p8/reproduction/nominal.json
python3 tools/dp_aux_frontend_model.py --capture --profile capacitance_offset --output artifacts/probes/m5p8/reproduction/corner.json
python3 tools/dp_aux_frontend_model.py --spice-case S2 --output artifacts/probes/m5p8/reproduction/S2.cir
ctest --test-dir build-m5p4-offline -L offline -R '^dp_aux_frontend$' --output-on-failure
```

The deck syntax/parameters and absence of AUX sources receive structural
checks. No ngspice parsing, manufacturer-macromodel, EDA ERC, PCB DRC or analogue
transient result is claimed. The model excludes distributed cable/connector
effects, nonlinear input capacitance, detailed ESD snapback and device faults.

## Decoder Through Conditioned Signal

The unchanged M5P7 AUX decoder receives generated `digital_samples` with
explicit `evidence_kind=synthetic` and synthetic direction provenance. No
direction is electrically recovered or invented from amplitude.

| Behavioural condition | Result in focused tests |
| --- | --- |
| Nominal 90 mV differential peak, 2.2/2.5 pF network | Raw request `90002100` recovered; about 27.5 mV minimum sampled midcell magnitude in this particular frame |
| Equal 100 ns delay | Same bytes; absolute timing shifted |
| 50/30 ns rising/falling delay plus alternating +/-10 ns jitter | Same bytes in this model |
| Threshold +/-8 mV | Same bytes at nominal input and tested high-C corner |
| Half-cells 400/500/600 ns, sampler 40 MS/s | Same bytes; 16/20/24 samples per half-cell |
| 8 pF and 20 mV threshold error | Not a valid recovered packet; risk exposed, not hidden |
| One missed edge, short glitch, inversion | Malformed/truncated output retained; no automatic inversion repair |
| 150 mV threshold | No fabricated valid request |

The behavioural filter approximates sense-cap attenuation and RC droop. It is
not the nonlinear SPICE circuit, does not calculate link-side transient voltage,
and does not model transistor-level overdrive recovery or random hardware noise.
Its 40 ns default comparator delay is an assumption, not a guaranteed TLV3211
value. Its low-pass approximation does not include every PCB/protection pole.
The exact AC network and B1 measurements must validate that approximation.

There are **33 new offline tests**. Existing decoder format is sufficient for
these fixtures; no rewrite or live acquisition abstraction was needed. Tests
show behavior for selected deterministic vectors, not all possible AUX packets
or physical jitter distributions.

## Acquisition Backend

`ACQUISITION_PLATFORM_UNRESOLVED` for an exact ready-to-order complete backend.

Design target remains **40 MS/s**, 25 ns sample grid, one comparator channel
(5 MB/s packed) or provision for two conditioned channels (10 MB/s packed),
64-bit accumulated sample position, explicit start/stop/gap records and 180 s
continuous recording. Storage is 0.9/1.8 GB respectively before metadata.
One MiB buffer covers about 210/105 ms of a host stall, not an unlimited pause.

Exact-model alternatives assessed:

- Glasgow revD/analyzer2 has a strong documented memory/transport/overflow
  architecture but is pre-launch, with no verified purchasable price or tested
  instance. It is not automatically substituted with revC.
- Saleae Logic 8 is advertised in stock at **CAD 710**, up to 100 MS/s and
  continuous host streaming, with Logic 2/Python API. Exact enabled-channel
  rate, timestamp/export integrity and overflow/stop acceptance for this
  workflow have not been demonstrated. It is a concrete comparison, not a
  qualified purchase. Never attach its GPIO directly to AUX.
- An unqualified low-cost FPGA board would add memory-controller, transport and
  gateware work. No new board is named merely because it has an FPGA.

An existing qualified scope may serve short B1/B2 work before the continuous
backend is selected. The project must not interpret nominal USB line rate,
unlimited-duration marketing, or a GUI screenshot as lossless capture proof.

## Glasgow Evaluation

`GLASGOW_BACKEND_VIABLE_NOT_PREFERRED` **as a future architecture**, not as an
available first purchased unit.

The [current revision description](https://glasgow-embedded.org/en/revisions/index.html)
and [revD campaign](https://www.crowdsupply.com/fully-automated/glasgow-interface-explorer-revd)
state ECP5U-25F, two 64 MB PSRAM channels, memory-controller validation to
120 MHz, digital I/O standards 1.2-5 V and up to 42 MB/s sustained combined
USB throughput. These are project/manufacturer claims, not MacMST measurements.
The 3.3 V isolated comparator output fits its digital I/O voltage range; its
250 kHz analogue inputs are not a substitute AUX waveform front end.

Pinned implementation remains
`ead3a00e37f6f68203bdd98134831ffb9bc73b0b`,
`software/glasgow/applet/interface/analyzer2/__init__.py` and `protocol.md`.
`DigitalFormat` rounds stride to a power of two; one/two channels use one/two
bits. `set_sampling_rate` derives an integer divisor from the actual assembly
clock and checks both rate error and memory limits. Do not assume a specific
physical unit can sample exactly 40 MHz without identifying its reference
clock and verifying timing. The public approximate 50 MHz I/O capability is
not a guaranteed practical samplerate for every applet.

At the proposed 40 MS/s/two-bit format, 10 MB/s is about 24% of the documented
42 MB/s transport ceiling. A fully allocated 64 MiB buffer would hold about
6.7 s; actual allocation is queried through the API, not inferred from total
board RAM. Host storage must sustain the stream for 180 s. Timestamping is
sample index + reference frequency/divisor; it is not an independent timestamp
on every edge. Preserve configuration, format and block boundaries.

The COBS protocol exposes Overflow and Complete trailers. Overflow stops the
sampling pipeline via a sticky circuit breaker; the last marked word can be
unreliable. The Python API requires draining sample data before another command
can execute correctly. Future integration must retain raw blocks and make
overflow invalidate the affected capture interval, not quietly reconnect and
concatenate streams.

The project offers source/docs/designs under 0BSD or Apache-2.0; dependencies
have their own terms. No Glasgow source is modified, vendored, built or run.
The first-use benefit is reuse of its existing sampler/host path, not custom
gateware. Current availability prevents preferring it as an immediate model:
revD is **Coming Soon**, no public price confirmed; the inspected revC store
listing is **CAD 255, sold out**, and does not establish analyzer2 support.

## MCU Evaluation

`MCU_AUX_CAPTURE_MARGIN_INSUFFICIENT` for **Pico 2/RP2350 with stock USB
full-speed and uncompressed continuous raw-sample retention**. This is not a
theorem that every MCU or a redesigned external-storage platform is unsuitable.

The [official RP2350 documentation](https://www.raspberrypi.com/documentation/microcontrollers/microcontroller-chips.html#rp2350)
states up to 150 MHz, 520 kB SRAM, 12 PIO state machines, 16 DMA channels and
USB 1.1. The conditioned signal is digital only; raw AUX never reaches GPIO.

| Quantity | Calculation / implication |
| --- | --- |
| PIO clock | At 150 MHz, 6.67 ns instruction cycle. One `IN` per cycle with integer divider 5 gives proposed 30 MS/s / 33.33 ns grid; not implemented firmware |
| Samples per 0.4 us half-cell | 12 at 30 MS/s; 60 core cycles. Sampling itself is plausible |
| DMA | Two-bit samples packed into 32-bit words require 1.875 million words/s, 7.5 MB/s; about 80 core cycles/word. Bus/DMA arbitration still needs measurement |
| One-channel raw rate | 3.75 MB/s at 30 MS/s, already 2.5 times the **raw** 12 Mbit/s USB ceiling of 1.5 MB/s |
| Two-channel raw rate | 7.5 MB/s, five times that ceiling before USB overhead |
| SRAM-only upper bound | Even treating all 520 KiB as buffer gives about 71 ms for two channels or 142 ms for one; actual available memory is smaller |
| Full 180 s | 1.35 GB for two channels at 30 MS/s, not SRAM/ordinary Pico flash capacity |
| Overflow | A stalled PIO/autopush/DMA pipeline cannot backpressure AUX. A capture needs independent time/loss indication and must not present resumed samples as contiguous |

Edge/run compression or real-time AUX byte decoding can reduce typical data
volume, but arbitrary noise/glitches and ambiguous timing are evidence too.
No bounded lossless compression ratio has been established. External PSRAM/SD
or a faster host bridge changes the platform and needs a new budget; it is not
a reason to label the current Pico 2 solution feasible. A short B1 waveform
generator or burst recorder is a separate, narrower use.

## Bench Signal Generation

Design only; no B1 signal was generated electrically.

Use two phase-related arbitrary-waveform outputs with known 50-ohm impedances,
or a differential AWG output, to create complementary Manchester waveforms.
Use actual programmed/load-referenced amplitudes, not assumed panel settings.
Through the model's two source legs and 100-ohm differential load, normalize
to measured differential peaks 90, 150 and 690 mV for exploration. These are
component-derived test cases, not a claimed complete normative AUX test suite.

Include source/sink-style 75/100/200 nF coupling and separately switchable
weak DC bias emulation so AC common mode and cable-side bias are not confused.
Use preamble/start/data/stop shapes, 0.4/0.5/0.6 us half-cells, quiet gaps,
opposite-direction bursts and bounded common-mode changes. The authored S4
deck adds a 0.3 V, 10 ns-edge common-mode pulse as an explicit stress assumption.

If a Pico/FPGA is used as the bench source later, its GPIO must drive a reviewed
attenuator/buffer/differential waveform network. A raw 3.3 V GPIO trace applied
to the analogue input is neither representative nor approved. An ideal SPICE
voltage source also does not establish AWG output/ground safety.

Only a separately approved current-limited, non-DP bench assembly may be used
for B1/B2. Do not connect any test generator, prototype, USB backend or probe to
the daily-use M5 under this milestone.

## Bench Measurements

All thresholds below are proposed engineering acceptance criteria, not VESA
conformance limits. A failed or unmeasurable critical item blocks B3.

| Measurement | Method / proposed pass condition |
| --- | --- |
| DC loading/leakage | Guarded low-current measurement over the eventually qualified per-pin voltage range, both polarities, powered/off/brownout; >=100 Mohm and <=100 nA per leg, <=20 nA mismatch |
| Effective capacitance | Calibrated impedance measurement/de-embedded comparison of fixture alone vs fixture+front end; <=4 pF per leg and <=0.1 pF imbalance. Account for connector, pad and probe capacitance |
| Differential amplitude | Same reference instrument/load for before/after measurements; <=1% added loss through relevant waveform band, no bias-state shift beyond the defined budget |
| Edge timing/settling | Overlay before/after traces; <=25 ns added crossing displacement, no extra crossings, and settled levels inside the measured threshold margin before sampling |
| Common-mode conversion | Inject separately controlled CM excitation; sense mismatch <=0.005 V/V or an independently justified revised error budget. Current S4 model fails this target |
| Comparator output | Clean compatible logic levels at actual load; measure low-overdrive delay, asymmetry and jitter, not only large-signal nominal delay |
| False/missed edges | Compare counted expected transitions to captured transitions for preambles, delimiters, maximum payload and long gaps; retain all exceptions |
| Powered-off input | Link-emulator waveform/bias remains inside loading targets with rails zero; measure current into rails, rail rise and both input currents rather than assume coupling caps eliminate them |
| Supply sequencing | Ramp and abruptly remove analogue/backend supplies in every order; no excessive bus glitch, persistent rail injection, oscillation or output interpretation as valid traffic |
| Fault/protection | Reviewed low-energy/current-limited fault tests first. No IEC ESD-gun test or high-energy fault until separate equipment/procedure review; verify input/series-part stress and rail absorption |
| Overflow | Force backend drain stalls with synthetic digital input. Recorder must produce a sticky loss/stop receipt, never silently delete time or infer no traffic |
| Decoder | Recover known raw bytes at declared sample rate; preserve malformed/lost/direction-unknown cases and source hashes. Existing tests are the oracle, not a substitute for bench evidence |

Probe loading is part of the experiment. Do not put a 1 pF probe on a 2.5 pF
sense node and then treat it as unchanged; measure/de-embed the change or probe
a buffered node. Check scope earth/reference paths before any measurement.
B1/B2 are followed only by separately approved expendable-source B3, known SST
B4, known MST B5, and independent M5 approval at B6.

## Native-DP Lab Hardware

Revalidated 2026-09-18, no purchase:

| Role | Exact candidate / primary source | Price / qualification |
| --- | --- | --- |
| Native adapter | [StarTech CDP2DP14B](https://www.startech.com/en-ca/display-video-adapters/cdp2dp14b): USB-C DP Alt Mode to DP 1.4, HBR3/DSC, no software/driver | CAD 26.99 plus taxes, page reports stock. Native DP, not DisplayLink; M5 MST behaviour not established |
| Genuine MST branch | [StarTech MST14DP122DP](https://www.startech.com/en-ca/display-video-adapters/mst14dp122dp): DP input, two DP outputs, DP1.4/HBR3/MST, USB Micro-B power | CAD 66.99 plus taxes, page reports stock. Manufacturer explicitly Windows-only/no macOS, ChromeOS or Linux support; retain as research candidate, not promised Mac compatibility |

Subtotal CAD 93.98 excludes cables, power, fixture, tax/shipping and backend.
The model/channel may differ from the historical two-lane ZMUIPNG path.

```text
Future only, after separate bench and owner approval:
M5 -> native DP Alt Mode adapter -> AUX tap -> native DP MST branch -> A / B
```

This topology is not assembled or authorized for use in M5P8. Initial B1/B2
have no DP device; B3-B5 use expendable/known non-M5 sources.

## Schematic

The [editable SPICE subcircuit](../../hardware/aux-observer/aux-sense.cir) is a
concrete **analysis schematic/netlist**, not a KiCad construction schematic.
It names each branch/protection/coupling/limiting/bias element, analogue supply
decoupling, comparator and one-way isolated output. Test nodes are `AUXP`,
`AUXN`, `PROTP/N`, `INP/N`, `BIAS`, `VDD`, `CMP`, `RXD`, `AGND` and `DGND`.
There is no AUX transmitter or HPD control.

The generated deck supplies source and sink emulators outside that subcircuit.
The future physical through-path is unbroken; its main-link/HPD routing is a
board requirement, not modelled by the low-frequency analogue netlist.

**A build-ready EDA schematic is deliberately withheld** because input/power-off/
protection/connector choices remain critical unresolved items. No fabricated
pin mapping, exact supply circuit, released footprint, ERC pass or PCB routing
is claimed. The conditional requirement to produce a construction schematic
applies only once the front end is sufficiently qualified; it is not met here.

## Preliminary BOM

No qualified orderable BOM is released. The following separates exact candidate
ICs from value-only model elements and external laboratory candidates. HOLD
means it must not be mistaken for a purchasing instruction.

| Group / references | Manufacturer / part | Qty | Role / package / spec | Current source / indicative price / substitute |
| --- | --- | --- | --- | --- |
| Tap PCB, J1/J2 | Connector MPNs not selected | 2 | Actual native DP launches/pin orientation/HBR3 behaviour must be qualified | HOLD; no price or substitute fabricated |
| Tap PCB | Fabricator/stackup not selected | 1 | Short controlled 100-ohm differential through path | HOLD; no invented fabrication price |
| Front end U1 | TI TLV3211DCKR | 1 | SC70-5 comparator; 1.5 pF typical, not max | TI current page USD 0.345 at **1,000-unit** quantity; not a one-piece quote. TLV3502/MCP6561 not drop-in qualified substitutes |
| Front end D1/D2 | TI TPD1E01B04DPYR candidate | 2 | DFN1006-2, 0.23 pF test-point max, +/-3.6 V standoff | TI USD 0.039 at **1,000-unit** quantity; HOLD for voltage/pulse qualification |
| Front end R1/R2 | MPN not selected, 1 kohm nominal | 2 | Tee branch resistors; pulse/voltage rating required | HOLD; no generic resistor price used |
| Front end R3/R4 | MPN not selected, 2.2 kohm nominal | 2 | Comparator clamp-current limiters | HOLD; tolerate pulse energy and parasitics |
| Front end C1/C2 | MPN not selected, 2.2 pF C0G nominal | 2 | Sense caps; matching, insulation, working/pulse voltage and layout crucial | HOLD; +/-0.1 pF is only a model corner, not an accepted matching guarantee |
| Front end R5/R6 | MPN not selected, 1 Mohm nominal | 2 | Fixed midpoint input bias | HOLD; precision/leakage/contamination budget |
| Front end midpoint/decoupling | MPNs not selected, 2x10 kohm, 100 nF midpoint, 100 nF + 1 uF supply | 1 set | Model values, not a finalized regulator/noise design | HOLD; no BOM total |
| Digital boundary U2 | TI ISO7710FDR | 1 | SOIC-8, forward-only isolated output, default-low variant | TI USD 0.548 at **1,000-unit** quantity; independent input power required |
| Analogue power | Isolated current-limited supply or qualified battery/regulator | 1 | No DP_PWR or sampler-controlled supply | HOLD; exact model not selected |
| Digital backend | Not selected | 1 | See backend sections | Glasgow revD unpriced/pre-launch; revC CAD 255 sold out is not a substitute; Saleae Logic 8 CAD 710 is a comparison |
| Native lab adapter | StarTech CDP2DP14B | 1 | Native DP Alt Mode/HBR3 | CAD 26.99 plus taxes |
| Native lab MST branch | StarTech MST14DP122DP | 1 | DP input, two DP outputs, USB powered | CAD 66.99 plus taxes; OS-support caveat preserved |

Manufacturer lifecycle/order pages and datasheets are linked in the component
and hardware sections. IC quantity prices must not be summed as if they were
single-unit procurement costs. No obsolete component is chosen to force a low
headline total. A final substitute must be requalified electrically and by pin
mapping; similar speed/function is insufficient.

## Cost Tiers

| Tier | Intended use | Honest cost position |
| --- | --- | --- |
| 0 | Existing qualified AWG/scope/reference probe for short B1/B2 work | Existing inventory unknown; zero incremental cost is not assumed. Exact probe/scope availability and loading still need qualification |
| 1 | Lowest-cost repeatable self-built continuous observer | No qualified total: front-end/PCB/backend selections are incomplete. Pico 2's low advertised board price does not solve its continuous raw-USB bandwidth deficit |
| 2 | More reusable streaming observer with isolated digital output and robust loss reporting | No qualified total: Glasgow revD has no verified current price/availability; Logic 8 is CAD 710 but not yet an accepted workflow/backend |

The only established native lab component subtotal is **CAD 93.98**. Adding
the Logic 8 comparison produces **CAD 803.98** for those three advertised
products only, before taxes/shipping and **excluding the entire front end,
PCB, bench instruments and cables**. This is not an observer BOM or an order
recommendation. No quote-only or unavailable-model price is invented.

## Design Review

Pre-build review of the **proposed design**, not a hardware test report.
Critical FAIL or UNRESOLVED blocks build authorization.

| Item | Status | Evidence / closure required |
| --- | --- | --- |
| Ordinary-AUX bounded input exploration envelope | PASS | P1-P4 values/location distinctions pinned; unknown universal limits explicitly retained |
| Instantaneous common-mode/transient range at chosen tap | UNRESOLVED | DC cable bias and component ratings do not close hotplug/power-step envelope |
| Actual DC input impedance/leakage | UNRESOLVED | Targets/calculations exist; no qualified cap/PCB/protection leakage stack |
| Actual maximum capacitance | UNRESOLVED | Nominal/off bounds computed, but comparator max/nonlinear C and physical parasitics unqualified |
| Sense-path matching | FAIL | S4 gives 0.04737 V/V versus 0.005 target; component/layout matching strategy required |
| Powered-off transparency/backfeed | UNRESOLVED | Small-signal cap bound does not close rail injection and sequencing |
| Protection coordination | UNRESOLVED | +/-3.6 V standoff headroom, pulse withstand/overshoot and rail absorption not closed |
| No intentional drive path | PASS | Comparator input-only sense and independently powered forward-only digital boundary; no TX/HPD control |
| PCB main-link routing implementation | UNRESOLVED | Sound routing constraints, no finalized connectors/stackup/launch/channel result |
| AUX branch geometry implementation | UNRESOLVED | <=2 mm pre-resistor target and capacitance budget, no extracted board geometry |
| Ground/reference strategy | PASS | DP-referenced analogue side, isolated digital USB side, no protective-earth lifting; physical layout still to review |
| Backend voltage compatibility and exact acquisition unit | UNRESOLVED | 3.3 V interface defined; no fully qualified available backend |
| Actual overflow detection / 180 s storage | UNRESOLVED | Glasgow semantics and rate budgets known; no recorder instance or host-stall receipt |
| B1/B2 measurement procedure | PASS | Explicit methods, pass/fail criteria and non-DP scope |
| Offline model/decoder regressions | PASS | 33 tests, generated fixture boundary, no M5P7 decoder changes |
| Nonlinear SPICE / construction schematic review | UNRESOLVED | No installed simulator/EDA CLI; analysis deck checks are not SPICE/ERC/DRC |

Summary: **5 PASS, 1 FAIL, 10 UNRESOLVED**. Passing architectural items do not
waive unresolved implementation details or turn on-paper RX-only structure
into a hardware safety certification.

## Prototype Gate

`MORE_ELECTRICAL_RESEARCH_REQUIRED`.

Concrete progress beyond M5P7: weak idle-bias loading is quantified; a symmetric
capacitive sense topology separates DC bias from slicing; moving protection
ahead of the cap removes its leakage from the 1 Mohm comparator-bias path;
current-limiter and off-capacitance/charge bounds are calculated; common-mode
mismatch and high-C/threshold failure cases are reproducible; HBR3 board and
isolated digital-boundary requirements are explicit.

The next work remains narrow and self-owned:

1. Close the sense-gain match/max-C/low-overdrive error budget with a qualified
   component model or a revised matched topology; do not assume typical values.
2. Run and review nonlinear power-sequencing/protection transients using an
   appropriate simulator and defensible device models. Close standoff,
   resistor/cap pulse ratings and rail-current handling.
3. Finalize the actual connector, stackup, local power and available capture
   backend; then produce and review a construction schematic/BOM.

No external reply is required to continue these engineering steps. No new
static DCP analysis, Mac probing or live DP capture is justified by these gaps.

**M5P9 - Bench Prototype Build and B1/B2 Validation** is the conditional next
hardware milestone only after every critical pre-build item passes and the
owner separately authorizes procurement/assembly. It would begin with generated
bench signals and no DP device or daily-use M5. M5P9 is not performed here.

## Current Hardware State

`CURRENT_HUB_STATE_NOT_REQUIRED`.

No hub state was assumed or queried, and no plug/unplug request was made.
Normal hub use with another computer does not invalidate immutable M5P3/M5P4
evidence. Every later real capture needs a fresh controlled baseline, new
generation, bench-qualified observer, pre-attach arming and separate approval.

`RETIRED_ON_DAILY_USE_M5` and `NOT_READY_FOR_DPCD_TEST` remain. Also preserve
`STATIC_PACKETIZER_ANALYSIS_FROZEN`,
`NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED` and the frozen
`OFFLINE_OBSERVER_PIPELINE_READY`. No m1n1 sibling access, private/user-client/
AUX/DPCD command, firmware/security change, live DP test, purchase, assembly
or outreach occurred.

### Validation And Provenance

Only build/offline tests and synthetic/analytical checks are authorized:

```sh
cmake --build build-m5p4-offline
ctest --test-dir build-m5p4-offline -L offline --output-on-failure
python3 -m py_compile tools/dp_aux_frontend_model.py tests/test_dp_aux_frontend.py
```

Build, all six offline CTests (**327 tests**) and Python compilation passed.
Final validation includes 294 preserved tests plus 33 new tests, local links,
model/deck parameter/RX-path consistency, previous source and runtime/bundle
hashes, safety markers, historical ledger preservation and Git scope. It does
not include SPICE execution, EDA ERC/DRC, a fabricated complete BOM, or hardware
verification. Captured manufacturer PDFs remain ignored local evidence.

Final preservation audit passed: **125 other baseline tracked files** are
byte-identical, including all M5P7 wire modules/tests and historical reports.
All runtime/synthetic bundle hashes, 477 historical M5P4 records, 48 earlier
source receipts plus 12 M5P8 receipts, and the consumed M2F marker/two receipts
validate. The M2G read marker remains absent. All **49** pre-M5P8 published
head/tag/peeled identities matched locally/remotely before publication.
Coordination changes are additive; all 477 prior ledger rows remain. Publication
is limited to the new branch, with no merge, PR, tag or external-source upload.

The local ignored [model-v1 generation](../../artifacts/probes/m5p8/model-v1)
contains 22 hashed files plus its hash receipt: analytical results, seven
conditioned raw/decoded pairs, six authored SPICE decks and a manifest binding
the exact model/test/circuit/decoder source hashes. Nominal, equal-delay and
jitter profiles recover the known request; high-C/offset, inversion, glitch
and missed-edge profiles do not. `spice_executed=false` and
`hardware_authorized=false` are explicit. Existing M5P7 bundles are untouched.

New retained receipts under `artifacts/probes/m5p8/sources`, retrieved
2026-09-18 (URLs above; byte hashes below):

| File | SHA-256 |
| --- | --- |
| `tlv3211.pdf` | `4c99cb9fd279f93f098ef302189bfbb801a94563955bf481a97a543fb30cf961` |
| `tlv3201.pdf` | `1777bba814c74772bb54c6f1f56702985039043ce2fb2affaf996a83eaf1076e` |
| `tlv3601.pdf` | `4cc4248683737d1a6539a01ef67db29b8300dcf7806f7b14b3f49cdbb294ca2d` |
| `tpd1e01b04.pdf` | `5222dc8e1a92dd54d3e03765a06bc1338fee12329b745d7db71204609d411447` |
| `sn65lvds2.pdf` | `2830b1f2b732d16f46bd45a1626e1aa25b308bb4220a5f476d780deff15d4dce` |
| `mcp6561.pdf` | `71dca2c5be18dd8b3dcc83f58368ecf5059733ef58dd9344d79f743cee075c73` |
| `tdp1500.pdf` | `96c862120052e102ef1cfd938ffd171ec0120f693bf44f04cdb8d0eebb005790` |
| `spraar7.pdf` | `4a14e9b00afc174f336386cf0097f3a5e7a6a367840331fbb22070053ec36f41` |
| `tdp142.pdf` | `013702c79c9da72a4fafc8204fea206aa64ddf9e040ccdf33391bc5d528bbd9e` |
| `iso7710.pdf` | `42fc3c704c9ca0c451282373b4a7ffb22d4691d56029b2b485ab111f3cc431c5` |
| `glasgow-revisions.html` | `e76a7f56776670b4a570ec47ef430a43e7f0d4698e664a751191049262d39738` |
| `glasgow-revd.html` | `d63fd7e62f08411010067084f27a1ee9cc62d8708be5291392dbeed7e80fd820` |

P1/P2/P3/P5 and pinned Glasgow source bytes remain in the previously verified
M5P7 receipts; they were not overwritten. Product prices are dated public-page
observations, not guaranteed offers. The guessed SN65DP141 URL returned 404;
the valid TDP142 document was inspected instead. ADI LTC6752 PDF retrieval
failed/reset/timed out, and the initial Nexperia PDF path was wrong/forbidden;
those failures are not negative capability or lifecycle evidence. No credential
or access-control workaround was used.