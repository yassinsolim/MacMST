# M5P11 - Low-Capacitance Receive Stage And Powered-Off Qualification

Date: 2026-09-22. Offline source qualification and numerical experiments only.
No hardware build, connection, purchase, capture, Mac display query or outreach.

## Decision

**AUX_FRONTEND_PROTOTYPE_STILL_BLOCKED**. No examined concrete architecture
satisfies every electrical gate. **W1_CAPTURE_SYSTEM_NOT_READY** independently.
No comparator, threshold, construction schematic, PCB or BOM is released.

The most useful conditioned example is two **OPA810IDR** input followers, an
OPA810IDR difference stage and two downstream **TLV9031DBVR** slicers. Its
representative capacitance is **3.4 pF per AUX leg**, but this uses typical IC
values and an assumed PCB allowance. Its guaranteed maximum is **UNKNOWN**.
More decisively, the OPA810 documents input-to-supply ESD paths: it cannot be
treated as transparent when its supply collapses. It is a rejected direct-
attachment candidate, not a selected frontend.

The qualified new conclusion is a concrete power-off constraint, not merely
another incomplete parts list. Holding an unpowered OPA810 input within its
documented +0.5 V stress limit from a 3 V source through 100.1 kohm requires
at least **24.975 uA**, incompatible with the frozen **100 nA** loading limit.
This KCL contradiction does not depend on choosing a convenient diode knee.

## Baseline

Starting branch: `research/m5-aux-differential-frontend`; exact HEAD/upstream
`cceefb962834a86183d119ba5bb356b9e5fd6dd5`, clean and 0/0 ahead/behind. Model
commit `f73a84c8a17f9261b823987db8f357a6ad6c26a7` and M5P9 parent
`2977255832c17714bb3ee273b52d0d85e4fb30e9` were verified. All 52 previously
published head/tag identities were recorded before creating
`research/m5-aux-low-cap-receiver` directly from M5P10.

Before the first code edit, all 412 old tests passed and the unchanged M5P10
tool reproduced all **69 retained files plus its hash manifest byte-for-byte**.
The new [baseline receipt](../../artifacts/probes/m5p11/baseline-reproduction.json)
records:

| Quantity | Reproduced result |
| --- | ---: |
| Legacy combined error | 14.210133691040062 mV |
| Legacy with perfect resistors | 14.208157935157194 mV |
| M5P10 combined receive margin | 64.94067328800656 mV |
| M5P10 combined CM conversion bound | 0.0022746787272428562 V/V |
| M5P10 bench-only protection omission | 7.5 pF/leg |

Receipt SHA256:
`be6db18777218f6068735973a87788da1e994482b54964e5e1e20fc64cc97fda`.
The [baseline replay](../../artifacts/probes/m5p11/m5p10-baseline/manifest.json)
is a new ignored generation. No M5P9/M5P10 evidence artifact was modified.

## Evidence Rules

| Label | Meaning |
| --- | --- |
| VERIFIED_FROM_DATASHEET | Exact published limit or circuit statement, with its pin, supply, voltage, frequency and temperature conditions. It is not a whole-circuit guarantee. |
| TYPICAL_ONLY | Representative value; no fabricated maximum, minimum tracking, or production-corner guarantee. |
| INFERRED | Derived consequence, such as KCL, capacitance arithmetic or a junction path; assumptions and conditions stated. |
| ASSUMED | Explicit experimental parameter, not a component specification. |
| UNKNOWN | Missing specification or applicability; retained as null, never silently replaced by zero. |
| BLOCKING | A demonstrated failure or unresolved design-critical obligation that prevents release. |

[receivers.json](../../hardware/aux-observer/receivers.json) is the machine-readable
source and candidate inventory. Each candidate records exact parts, C type and
test conditions, typical/maximum values, current, input ranges, supply, delay,
hysteresis, temperature coverage, protection, off behavior and external networks.
Unavailable ADI/Nexperia documents are explicitly retrieval-limited entries,
not negative evidence and not numerically qualified parts.

## Frozen Electrical Budget

The [M5P9 criteria](../../hardware/aux-observer/closure.json) remain unchanged.
Their canonical JSON SHA256 is
`bcfb58e9d6311337084552720658a70bec52bf864b199c34b89d4218355c3b95`.

| Requirement | Frozen value |
| --- | ---: |
| Per-leg DC input impedance | >=100 Mohm |
| Per-leg leakage / pair imbalance | <=100 nA / <=20 nA |
| Added per-leg capacitance / imbalance | <=4 pF / <=0.1 pF |
| CM-to-differential conversion | <=0.005 V/V |
| Source/sink amplitude change | <=1% |
| Residual differential margin | >=10 mV |
| Added crossing error / edge dispersion | <=25 ns / <=25 ns |
| Off-rail voltage / sustained backfeed | <=0.1 V / <=1 uA |
| Intentional AUX drive | None |

The 4 pF ceiling is an **engineering target**, not presented as a normative
VESA limit. It is not relaxed. A bandwidth-only argument cannot replace the
loading, weak-bias, transient and mismatch budget. Neither a typical value below
4 pF nor a successful packet proves the maximum is below that ceiling.

The inherited public endpoint evidence distinguishes approximately 0.18-1.36 Vpp
differential reception from peak amplitude: half of that is 90-680 mV. Those
values are location-qualified, not an established instantaneous connector range.
Cable bias and receiver-pin CM must be considered separately; the model's
0.3/3 V idle pins, -0.5..3.6 V exploration, 0.3 V CM modulation and source
0.18 V differential **peak** remain ASSUMED, not measured M5 values.

## Concrete Architectures

| ID | Actual circuit considered | Disposition |
| --- | --- | --- |
| A_TLV9031_DIRECT | 100-ohm branches into TLV9031DBVR, no added AUX bias/termination. | Fails DC rejection: approximately -2.7 V bias dominates AC. Positive fail-safe is useful, but maximum Cin and negative/off envelope remain unknown. |
| A_TLV3601_DIRECT | 100-ohm branches into TLV3601DCKR. | Low typical Cin, but 1 uA typical/5 uA maximum bias and 67 kohm typical differential resistance are incompatible with passive weak-bias loading. Also DC bias and rail clamps. |
| B_OPA810_BUFFERED | Two OPA810IDR unity followers on proposed +/-5 V, an OPA810IDR difference stage with four nominal 10 kohm resistors, one output 10 nF/10 kohm high-pass and two TLV9031DBVR local window comparators. | Conditional powered operation is credible, but no maximum Cin and documented off-state rail paths. No construction survivor. |
| C_MMBF4416_FOLLOWERS | Two MMBF4416 N-JFET source followers, drain/source bias networks, OPA810IDR subtraction and two TLV9031DBVR slicers. | Ciss maximum already 4 pF at its test point; parasitics/protection exceed budget. Gate forward conduction while off and unconstrained device matching block it. |
| D_INA851 | INA851RGTR gain-one instrumentation input on proposed +/-15 V, OPA810IDR output conversion, one high-pass and two TLV9031DBVR slicers. | Explicit input C is too large in the representative model. Overvoltage protection routes current into supplies; survival is not passive off behavior. |
| E_OPA858_LOW_C | OPA858IDSGR input stages considered with downstream TLV9031DBVR. | Attractive typical C, but not a drop-in unity follower: gain/noise-gain stability and range require additional circuitry. Input-to-input diodes can load the input through feedback even with output disabled. |

No new input pull-up, differential termination, transmitter, HPD driver or
output-feedback path into AUX is introduced. Input current through protection
or faults is still real loading; a receive-only intent does not prove no
backdrive under every operating/power condition. That separate gate stays open.

The concrete buffered path avoids the old per-leg capacitive divider. However,
the numerical profiles intentionally approximate the receiver with the existing
M5P10 finite-bandwidth transfer, not a complete transistor model of each listed
part. In particular, an OPA858 proxy decoding does **not** prove a unity-gain
OPA858 circuit works. External resistor values without a selected network and
layout are design assumptions, not a released assembly list.

## Component Specifications

All quoted capacitances below are per the named datasheet definitions. A table
of common/differential capacitance does not automatically identify every element
of the physical matrix. For a real mutual C across AUX, differential-effective
per-leg loading contains **2 x Cmutual**. For separate unity buffers, the
input-to-feedback-output C is local, not a capacitor across AUX; the conservative
example takes no bootstrap credit.

| Exact part | C specification and conditions | Bias/leakage | Input, supply, timing and temperature limits |
| --- | --- | --- | --- |
| TLV9031DBVR | TYPICAL_ONLY 3 pF common, 2 pF differential; VS=5 V, VCM=VS/2, 25 C; frequency and maxima UNKNOWN. | 5 pA typical bias, 1 pA offset current; maxima UNKNOWN. | VS 1.65-5.5 V; normal CM rails +/-0.2 V at stated 1.8/5 V and -40..125 C. Differential may span valid pin voltages. Offset +/-2 mV stated PVT. HL/LH 100/115 ns typical at 100 mV overdrive, 5 V, 15 pF; no maximum. No internal hysteresis. |
| TLV3601DCKR | TYPICAL_ONLY 1 pF Cin; common/differential definition and measurement frequency UNKNOWN. | 1 uA typical / 5 uA max over -40..125 C; Rdiff 67 kohm, Rcm 5 Mohm typical. | VS 2.4-5.5 V, CM rails +/-0.2 V; pin/differential stress limits are not an off-operation guarantee. 2.5 ns typical, 4.5 ns max at 50 mV over/underdrive and stated PVT. Hysteresis 1.5/3/5 mV min/typ/max. Cin/dispersion maxima not supplied. |
| OPA810IDR | TYPICAL_ONLY common 2 pF at +/-5 V (2.5 pF at +/-12 V), local differential 0.5 pF; 25 C, frequency UNKNOWN. Common impedance 12 Gohm typical. | 2 pA typical / 20 pA stated max at +/-5 V, midsupply, 25 C; off/full-temperature leakage bound UNKNOWN. | Total supply 4.75-27 V; CM rails +/-0.2 V under specified offset criterion. Typical allowable differential is lower of +/-7 V or total supply. 140 MHz headline/70 MHz GBW are not pair-delay bounds. Drift max 10 uV/C at stated temperatures; no pair gain/phase tracking guarantee. Linear stage, no intended hysteresis. |
| MMBF4416 | VERIFIED_FROM_DATASHEET Ciss <=4 pF, Crss <=0.9 pF, Coss <=2 pF at VDS=15 V, VGS=0, 1 MHz, 25 C; no typical Ciss or full-PVT maximum. Crss is part of Ciss, not an extra Ciss addition. | Reverse IGSS <=1 nA at VGS=-20 V, VDS=0, 25 C; <=200 nA at 150 C. Does not apply to forward gate current. | No IC supply/CM/differential/propagation specification. VGS at 0.5 mA is -1..-5.5 V; gm 4.5..7.5 mS at stated 15 V/0 V/1 kHz/25 C. Drain/source headroom and chosen bias must be designed. Gate-forward stress 10 mA; no complete transient/ESD immunity. |
| INA851RGTR | TYPICAL_ONLY common 7 pF, differential 1 pF, 100 Gohm; +/-15 V, midsupply, gain one, 25 C; frequency/max C UNKNOWN. | Bias 5 nA typical / 18 nA stated temperature max, offset current 0.5 nA typical / 6 nA max. | Total supply 8-36 V; input roughly VS-+2.5..VS+-2.5 with gain/output-headroom dependence. 15 MHz typical gain-one bandwidth, not propagation/skew guarantee. 86 dB min CMRR is DC-60 Hz, not MHz. Differential range depends on internal/output headroom. No intended hysteresis. |
| OPA858IDSGR | TYPICAL_ONLY common 0.62 pF, differential 0.2 pF; VS=5 V, gain seven, midsupply, 25 C; frequency/maxima UNKNOWN. | 0.4 pA typical / 5 pA max at stated 25 C condition; off/PVT bound UNKNOWN. | VS 3.3-5.25 V; at 5 V the CM high limit has 3.4 V min/3.6 V typical, low 0/0.4 V values at its stated CMRR condition. Signed exploration not covered. 1 V differential is an absolute stress limit. Gain-seven 1.2 GHz/8 ns settling are typical; lower noise gain can peak/oscillate. No signal hysteresis; PD-pin hysteresis is not receive hysteresis. |

OPA810's C entries are explicitly test level C, typical-only. Other level-A/B
limits have their own test/characterization conditions, not automatic off-state
coverage. INA851's +/-40 V beyond-rail protection and approximately 16 mA
typical limiting concern survival, not the 100 nA passive loading requirement.

LTC6268IS6#TRMPBF remains a **retrieval-limited lead**, not an additional
qualified profile. The earlier 450 fF advertised Cin cannot be promoted to a
maximum or full matrix; its exact input range/off-state contract remains UNKNOWN
here. AD8130ARZ retains M5P10's 1 Mohm differential-input rejection, without a
new complete datasheet qualification. BF256B retrieval returned 403. No missing
datasheet values were estimated and none of these retrieval failures proves
that a manufacturer's other devices are unsuitable.

## Capacitance Accounting

Representative sums include 0.5 pF/leg **ASSUMED** PCB/pad allowance. ESD122
typical model terms are 0.2 pF ground plus 2 x 0.1 pF mutual. These sums are
INFERRED from typical/test-point/assumed inputs, never guaranteed maxima.

| Candidate | Receiver contribution | With ESD122 + PCB | Bench without added TVS | Guaranteed total |
| --- | ---: | ---: | ---: | --- |
| TLV9031 direct | 3 + 2x2 = 7 pF | 7.9 pF | 7.5 pF | UNKNOWN |
| TLV3601 direct | 1 pF assumed mapping | 1.9 pF | 1.5 pF | UNKNOWN |
| OPA810 buffers | 2 + 0.5 = 2.5 pF, no bootstrap credit | 3.4 pF | 3.0 pF | UNKNOWN |
| MMBF4416 followers | 4 pF test-point maximum | 4.9 pF | 4.5 pF | UNKNOWN over full envelope |
| INA851 | 7 + 2x1 = 9 pF assumed matrix | 9.9 pF | 9.5 pF | UNKNOWN |
| OPA858 input stage | 0.62 + 0.2 = 0.82 pF | 1.72 pF | 1.32 pF | UNKNOWN |

No candidate has a defensible complete <=4 pF maximum. A resistor or source-
follower bootstrap may reduce measured effective input C in one operating mode,
but does not give an unpowered bound or a guaranteed production maximum.
No PCB exists to turn the 0.5 pF allowance into a verified value.

## TLV9031 Conditioning

**TLV9031_REQUIRES_CONDITIONING** remains correct, but does not prefer it over
other parts. It needs (1) rejection of cable differential DC before comparison,
(2) translation to a qualified input common-mode range, (3) bounded idle/noise
thresholds, (4) coordinated signed-input protection and power sequencing.

Three concrete alternatives were compared:

| Path | Executed evidence | Decision |
| --- | --- | --- |
| Direct TLV9031 | Representative 7.9 pF with ESD122; direct model remains negative and produces no complete packet. | Fails DC rejection/loading evidence; positive fail-safe alone does not help. |
| Original per-leg AC conditioning | Each leg: 1 kohm branch, pre-coupling protection, 2.2 pF coupling, 2.2 kohm limiter, 1 Mohm to local 1.65 V bias; model 3 pF common + 2 pF mutual receiver and 0.5 pF PCB. E1 margin 17.1027 mV; E8 margin 1.16538 mV / CM gain 0.0148107. | Reproduces the original capacitive-ratio failure; do not improve only resistor tolerance. E1 bytes are not nominal completeness. |
| Buffered differential conversion, then local AC/window | OPA810 inputs supply the AUX loading; TLV9031 input C loads the receiver output instead of directly adding to AUX. Example 3.4 pF. | Numerically better, but first-stage rail clamps and missing Cin max block it. Buffer reverse transfer/output-input fault paths remain UNKNOWN, not zero. |

The old E7 off-state replay still reaches -0.302164 V at an input, outside the
TLV9031's 0..5.5 V fail-safe contract. Its very small simulated positive-rail
injection does not establish signed-input transparency. Increasing the old
coupling capacitance to 47 pF approaches the mismatch target but gives a
47.73 pF conducting-clamp load bound. These exact legacy comparisons are retained
in [tlv9031-conditioning.json](../../artifacts/probes/m5p11/model-v4/tlv9031-conditioning.json).

The buffer path is not justified merely to keep TLV9031. TLV3601 provides a
faster alternative comparator, but its own input bias forbids direct AUX use.
No downstream comparator is selected until the complete input stage qualifies.

## Powered-Off Equivalents

**POWERED_OFF_BEHAVIOR_UNRESOLVED** for the frontend. The following paths are
now explicit rather than inferred from a marketing phrase:

| Candidate | Equivalent and provenance | Consequence |
| --- | --- | --- |
| TLV9031 | VERIFIED input has no upper diode for 0..5.5 V at VDD=0/ramping; negative diode and unspecified snapback to V- remain. Output has V+ clamp. | Positive-input high-Z statement is real, but no numerical worst-case leakage/max Cin or full negative/transient guarantee. Backend drive at OUT can power the rail despite fail-safe inputs. |
| TLV3601 | VERIFIED input/output diodes to both rails; finite differential/common resistance and bias. | Positive input can charge an off rail or load a held-zero rail; weak bias already loaded while powered. |
| OPA810 followers | VERIFIED all pins have supply ESD diodes (7.3.2/Figure7-2). OUT is tied to IN- in a follower. Local differential C couples AUX-facing IN+ to that feedback/output node. | Upper/lower supply paths plus output clamps must be included; unity feedback does not isolate the input while off. |
| MMBF4416 | N-JFET PN gate-channel paths INFERRED from structure, consistent with explicit forward-gate voltage/current ratings. Gate-drain to collapsed drain rail; gate-source to 10 kohm source return. | Reverse IGSS specification does not apply when positive AUX forward-biases a gate junction. |
| INA851 | VERIFIED 8.3.4/Figure8-11 overload current flows through input protection into supply rails; typical current limiting about16 mA. | A current-limited survival circuit can still back-power or materially load AUX. Exact zero-supply IV is UNKNOWN. |
| OPA858 | VERIFIED 8.4.2, pp.20-21, back-to-back input diodes create a signal-input-to-output path through feedback during power-down. Equivalent includes 453-ohm feedback/75-ohm gain return. | A high-Z disabled output is not input isolation. Separate zero-supply rail IV remains UNKNOWN. |

The solver executes held-zero and floating rails, both supply-sequencing orders,
weak 100 kohm and active 50-ohm source cases, 0.3/3 V idle pins, -0.5/3 V signed
pins, 3.6 V common inputs, output backdrive, and a 100 nA leakage sensitivity.
It retains current from AUX into each receiver pin, current from each source,
current into rails, explicit inter-input resistance current and mutual-C
displacement current. It does not assume that absent DC pair conduction means
no displacement current between AUX legs.

The PWL diode knees (0.3 V rail / 0.6 V junction), 10-ohm dynamic slopes,
1.1 uF rail storage and 1 ohm/1 Mohm supply return are **ASSUMED witnesses**,
not guaranteed device IV curves. INA851's nonlinear limiter and op-amp shutdown
circuits are not replaced with claimed transistor-accurate models. Strong-source
examples can exceed stress-current ratings; they show why a path is unacceptable,
not a recommendation to apply those conditions or a prediction after damage.

For 0.3/3 V sources through 100 kohm plus 100-ohm branches:

| Witness | Rail | Positive rail current | AUX- pin current |
| --- | ---: | ---: | ---: |
| Upper clamp, rail held through 1 ohm | 26.970 uV | 26.970 uA | 26.970 uA |
| Upper clamp, 1 Mohm floating-rail return | 2.45430 V | 2.45430 uA | 2.45430 uA |
| JFET gate paths, 1 Mohm rail return | 0.21621 V | 0.21621 uA | 21.8160 uA |
| OPA858 input-feedback diode path | 0 V in this limited equivalent | 0 | 23.9557 uA |

Low rail voltage is therefore not transparency. Small rail current can coexist
with substantial current to another node. Positive-fail-safe numerical zero
upper-rail current is limited to that topology and excludes unknown leakage;
it is not promoted to a complete TLV9031 off-state pass.

The **datasheet-independent-of-diode-shape** OPA810 contradiction is:

$$
I_{min}=\frac{3.0-0.5}{100000+100}=24.975\,\mu\mathrm{A}.
$$

If current instead stays <=100 nA, the pin remains at least 2.98999 V, beyond
the zero-supply +0.5 V stress boundary. Clamping and transparency cannot both
hold for this direct connection. Raising series R to approximately 22-27 Mohm
for assumed 0.8-0.3 V clamp knees leaves only 0.260-0.212 mV from a 90 mV,
1 MHz input into 2.5 pF. It cannot preserve the 10 mV receive margin.

Cold-start transient runs begin at zero rails/source, ramp positive input in
10 ns, then introduce a negative excursion. Their short-duration rail rise is
reported separately from settled DC, not used as proof of indefinite safety.
The summary maximum includes declared output-backdrive cases; it is **not all
attributed to AUX**. Detailed rows preserve the source of each current.

## Protection

**BENCH_PROTECTION_OPTIONAL**, only for a future reviewed, current-limited,
externally protected, **non-DP** B1/B2 fixture. This is permission to consider
omission, not qualification of that fixture. **PRODUCTION_PROTECTION_UNRESOLVED**.
Omitting protection does not authorize eventual live DP or fix receiver clamps.

| Part | Capacitance and leakage | Clamp conditions / outcome |
| --- | --- | --- |
| ESD122DMXR | At 0 V, 1 MHz, 25 C: line 0.2 pF typ/0.27 max, mutual 0.1 typ/0.14 max, channel difference 0.01 pF max. Leakage <=10 nA at +/-2.5 V; bidirectional +/-3.6 V standoff. | Typical TLP 6.4 V at1 A /8.4 V at5 A, 25 C; not maximum overshoot. Its 0.4 pF representative effective load fits some budgets, but unequal AUX bias/PVT matching and clamp coordination are unresolved. |
| ESD401DPYR, one per leg | At 0 V, 1 MHz, 25 C: 0.77 pF typ/0.95 max. Leakage 0.03 nA typ/10 max at +/-2.5 V; +/-5.5 V standoff. Independent-part matching and layout mutual C UNKNOWN. | Typical TLP 11/16/24 V at1/5/16 A, not the distinct 8/20 us surge figures. OPA810 example becomes 3.77 pF with typical parts/PCB, but 2.5+0.95+0.5=3.95 pF is still not a guaranteed total because receiver/PCB are unbounded. |
| No added TVS | Zero contribution only from the omitted component. Receiver junctions, board C and external bench protection remain. | OPA810 example 3.0 pF, still unknown maximum and off clamps. No production readiness. |

The conservative ESD122 test-point allocation 0.27+2x0.14 pF plus assumed
0.5 pF PCB leaves 2.95 pF for the receiver. That is an allocation, not proof that
all capacitance measurement definitions or voltage/temperature conditions match.
The test suite separately exercises protection conduction; generic PWL breakdown
is a failure witness, not a complete snapback/IEC ESD qualification.

## Threshold And Timing

**FIXED_THRESHOLD_NOT_ESTABLISHED**. Actual guaranteed signal transfer, MHz
CMRR, noise, leakage imbalance, reference/temperature error and timing bounds
are missing. There is no justified hardware threshold or hysteresis selection.

For valid signed signal $S$, total false differential $F$, offset $O$, noise
$N$ and reference error $R$, the unchanged conservative condition is:

$$F+O+N+R<V_{TH}<S-F-O-N-R-10\mathrm{mV}.$$

The OPA810 combined **proxy** yields a conditional 4.9275..72.7061 mV interval.
The 20 mV simulation threshold is inside it; it is not derived from complete
component maxima. The existing output-only reference ladder and its assumed
tolerances remain a physical mechanism, not a selected reference/buffer BOM.

| Strategy | Decision |
| --- | --- |
| Single fixed threshold | Simplest binary slicer, but does not independently identify idle validity or prove a noise/offset gap. No guaranteed interval yet. |
| Hysteretic threshold | Can be internal or downstream of buffering, never feedback into AUX. Actual min/max thresholds, overdrive and release behavior required. It can hold an old state during idle. |
| Dual window | Retains positive/negative/idle/invalid states and fits existing offline adapter. Current diagnostic choice, not hardware selection; channel skew/power validity still required. |

TLV9031's actual table gives typical 100 ns falling/115 ns rising delay at
100 mV overdrive; the candidate proxies now exercise that asymmetry. No maximum
at this design's overdrive is supplied. TLV3601's bounded50 mV delay does not
make its input loading acceptable. Constant delay, bandwidth and variable edge
error must not be conflated; model 20 ns sampled crossing error/zero sampled
dispersion is not a full PVT timing certificate.

## Matching

The legacy capacitive-divider error remains 14.2101 mV, or14.2082 mV with ideal
resistors. No old topology is rehabilitated by tighter R. New input-network
sensitivities, at 1 MHz for the buffered example, are:

| Disturbance | Modeled external CM conversion |
| --- | ---: |
| 0.1 pF input mismatch | 0.0000784940 V/V |
| 0.1% opposing branch resistors | 0.00000339105 V/V |
| 1% opposing branch resistors | 0.0000339105 V/V |
| 0.01 pF protection mismatch | 0.00000784940 V/V |
| Combined input/branch/protection | 0.0000897344 V/V |

A separate four-resistor unity-difference stage with independent0.1% tolerance
has a worst low-frequency ratio-conversion term of0.002002002 V/V. This is a
realistic conditional tolerance example, not a selected network's guaranteed
MHz tracking. Its input/parasitic phase and buffer gain matching remain unknown.
Adding an assumed0.001 intrinsic receiver term gives the combined proxy bound
**0.003091736 V/V**. Absolute input-plus-protection mismatch0.11 pF in that
sweep already exceeds the separate frozen0.1 pF balance target. The sweep is
diagnostic, not an accepted production envelope.

At the MMBF4416 gm test point, a10 kohm follower return and gm4.5..7.5 mS imply
gains0.978261..0.986842, a0.00858124 V/V CM error before other contributors.
That exceeds0.005. It is an INFERRED test-point example, not guaranteed gain at
the proposed follower bias or MHz. No device matching is assumed because two
FETs share a nominal part number.

Temperature evidence is limited: OPA810's10 uV/C offset-drift maximum would
allow opposite input-buffer drift of2 mV over100 C, before other stages;
post-difference AC coupling rejects steady offset but not arbitrary changing
offset, startup or noise. TLV9031's typical0.5 uV/C drift and typical bias
doubling per10 C are not maxima. JFET reverse leakage reaches200 nA at its
150 C test condition. No unspecified capacitor temperature matching, resistor
ratio TCR or AC gain/phase tracking is assigned a convenient bound.

## Numerical Profiles

M5P10 is **extended, not replaced**. Optional parameters add input bias,
differential resistance, branch mismatch, comparator rise/fall delay and candidate
pipeline configuration. Default N0-N12 and the window adapter are unchanged in
behavior. M5P7 AUX/MST/W1 files are byte-identical. The new module reuses the
same solver and conservatively separates representative arithmetic from guaranteed
gates; `hardware_authorized` stays false even for a synthetic all-gates-PASS test.

Each profile outputs per-leg C, residual margin, CM conversion, explicit maximum
modeled off-rail injection, crossing error, power-off classification, packet
recovery, completeness and authorization. Every guaranteed C/margin/CM/current
field is null when evidence is unavailable. Successful proxies must not be read
as measurements or component-valid simulations.

| Combined profile | Representative pF/leg | Margin mV | CM bound V/V | Max modeled off injection uA | Packet / completeness |
| --- | ---: | ---: | ---: | ---: | --- |
| A TLV9031 direct |7.9|-2629.954|0.003092360|2.99934, output backdrive case|No / incomplete|
| A TLV3601 direct |1.9|-604.316|0.003089524|40740.74|No / incomplete|
| B OPA810 buffered |3.4|64.6336|0.003091736|40740.74|Yes / complete proxy|
| C MMBF4416 |4.9|62.0671|0.011674853|36995.97|Yes / complete proxy despite CM/loading failure|
| D INA851 |9.9|64.6370|0.003097376|40740.74|Yes / complete proxy despite loading failure|
| E OPA858 |1.72|64.6339|0.003089629|2.99934, output backdrive case|Yes / idealized proxy, not viable gain/range proof|

The large current entries include strong-source conditions beyond component
stress limits; they are assumed network witnesses, not guaranteed physical maxima.
For OPA858, absence of input-to-rail current in the limited equivalent does not
remove its approximately24 uA weak-source input-to-feedback loading. Raw rows
retain that current separately. All profiles remain `POWERED_OFF_BEHAVIOR_UNRESOLVED`.

Valid conditioned packets give20 ns sampled added crossing error; direct cases
have no qualified crossing sequence. Nominal and combined proxies produce eight
complete continuous pipeline intervals, while the four direct intervals are
incomplete. Completeness does not override any electrical rejection. Fixed source
and common-mode amplitudes, 20 MHz receiver abstraction (15 MHz for INA851),
1 mV noise/reference allowances and2 mV slicer offset remain assumptions.

1 ns/5 ns comparisons for direct TLV9031, buffered OPA810 and discrete JFET
preserve packet outcomes. Largest listed sink-peak difference is0.196074 mV;
margin difference0.001007 mV; off-rail difference27.564 uV. M5P10 N0-N12 and
its retained convergence evidence remain unchanged. Continuous pipeline
integration is20 ns, while per-packet/off transients use5 ns; metadata says so.

## Reproduction And Tests

Final evidence: [model-v4](../../artifacts/probes/m5p11/model-v4/manifest.json).
It binds **82 files**: 12 waveform/window/decoded triplets, 12 off-state CSVs,
12 pipeline input/analysis pairs, nine result/catalog/gate files and manifest.
The directory and downloaded sources remain ignored.

| Receipt | SHA256 |
| --- | --- |
| Final manifest | `4d57f7317e7475d1eb67316cb2b8a346f152ef2457e88d914c1eb90addbdee30` |
| Final hashes.json | `cdd306651a50c2450275cc4702dca1ca0ebf216b79943a5600cef61d2fd83cb8` |
| Convergence results | `f64cf4595a64e084ccbf465107d48d6e37e198cf7c114f72c209e93ef7070d04` |

Generations v2 and v3 reproduce all82 files exactly. After strict negative-C
validation was added, all81 nonmanifest files in v4 still reproduce exactly;
only the changed source hash updates its manifest. v1 is an earlier retained
generation, not presented as matching the final catalog or summary format.

The golden M5P10 regression regenerates every file and checks an aggregate of
all68 result hashes. It normalizes **only** the extended model's source hash
when comparing the original manifest. Golden result aggregate:
`96c58e17b0ff3accf49b2430e59a0f4cd16940d00172d293bbe6b2b3669477c9`.
This is tested without requiring ignored historical artifacts in a fresh clone.

```sh
python3 -X dev -W error -m unittest discover -s tests -p test_dp_aux_receiver.py -v
python3 tools/dp_aux_receiver.py --output artifacts/probes/m5p11/reproduction-1
python3 tools/dp_aux_receiver.py --replay-m5p10 artifacts/probes/m5p11/m5p10-replay-2
cmake --build build-m5p4-offline
ctest --test-dir build-m5p4-offline -L offline --output-on-failure
python3 -m py_compile tools/dp_aux_differential.py tools/dp_aux_receiver.py tests/test_dp_aux_receiver.py
git diff --check
```

Use new nonsymlinked output destinations. Candidate evidence generation requires
the local source receipts listed below; tests/golden replay do not fetch sources
or interact with hardware. Builds and all **nine offline CTests** pass:
**412 old +46 new =458 tests**. Focused candidate/off-state tests, full replay,
deterministic artifact hashes, Python compilation and whitespace checks pass.
Native display binaries, public hardware tests and retired private helpers were
not run. No dependencies or external simulators were installed.

## Sources

These eight exact source receipts were read locally and hash-verified. Previously
downloaded M5P9/M5P10 PDFs are reused without modification. Source-derived
statements above refer to these revisions, not changing catalogue snippets.

| Source / exact sections | URL | SHA256 |
| --- | --- | --- |
| TLV9031 SNOSDA3H, Nov2025;5.7/5.8/6.4.2/6.4.3/6.4.5 | https://www.ti.com/lit/ds/symlink/tlv9031.pdf | `97f124d3a40b1e55e74dda66ca81654b0c2eb782ec8aa1e9b18d2a40bd65627d` |
| TLV3601 SNOSDB1E, Apr2023;6.1/6.5 | https://www.ti.com/lit/ds/symlink/tlv3601.pdf | `4cc4248683737d1a6539a01ef67db29b8300dcf7806f7b14b3f49cdbb294ca2d` |
| OPA810 SBOS799E, Aug2024;6.1/6.5/6.6/7.3.2 | https://www.ti.com/lit/ds/symlink/opa810.pdf | `74c61ac238989c94c1cf0d70da41bff6e167a590f86e06bae7cdd734d8fd26fa` |
| OPA858 SBOS629B, May2025;6.1/6.5/8.4.2/9.2.1.2 | https://www.ti.com/lit/ds/symlink/opa858.pdf | `151746979714ef541dbcd13293e9ce1c02e41af4465eac0805a0ed1c4b5f48b9` |
| MMBF4416/D, Jan2022 Rev2;p1; package appendix Aug2024 | https://www.onsemi.com/pdf/datasheet/mmbf4416-d.pdf | `7173611c77cfde450e05ce6fa610f4681c92013bf18f199e8e5ebd24ffb393ad` |
| INA851 SBOS999A, Oct2022;7.5/8.3.4, Figure8-11 | https://www.ti.com/lit/ds/symlink/ina851.pdf | `b6836363e32f3d5fdc1b85d731ba7ee8c2c687d3f86a81eeec403ff8ba869752` |
| ESD122 SLVSDP5A, Aug2018;6.4/6.6 | https://www.ti.com/lit/ds/symlink/esd122.pdf | `16ba54c64476aa5abbadc84ce72e60cee6baf710c958be0aad90cf363393f3ab` |
| ESD401 SLVSE49B, Aug2024;5.6 | https://www.ti.com/lit/ds/symlink/esd401.pdf | `a5633671490376defbdb95c629f52bb4024393ec5dc1e7e904b0eab2705e701f` |

Retrieval limits, not qualified sources: ADI `62689f.pdf` and `AD8129_8130.pdf`
downloads reached a15-second bound without bytes; the Nexperia BF256 PDF returned
403. Exact URLs and null hashes are recorded in `retrieval_limits` in the
configuration. A SHA cannot honestly be supplied for bytes not received. Those
missing documents supply no new guaranteed values. No unbounded conversion call,
credential change or access-control bypass was used. Existing M5P10 product leads
remain explicitly historical.

## Frontend And W1 Gates

The M5P10 30-row review remains untouched. M5P11 adds a separate per-candidate
12-condition gate: receive-only intent, maximum Cin, DC loading, CM range,
differential range, margin, timing, protection, powered-off transparency,
no backdrive, realistic matching and reproducible model. An UNKNOWN is blocking,
not a PASS. Intent-only receive mode and numerical reproducibility are narrower
than the complete no-backdrive or hardware-safety claims.

**AUX_FRONTEND_PROTOTYPE_STILL_BLOCKED**. No guaranteed complete input-C bound,
fully qualified power-off/input-range contract or whole-chain error/timing budget
exists. Actual OPA810 rail paths, OPA858 feedback clamps and JFET junction paths
now have concrete source-backed or structure-backed reasons for rejection.
Neither protection omission nor a successful waveform justifies a PCB/BOM.

**W1_CAPTURE_SYSTEM_NOT_READY**. The modular digital interface remains useful,
but exact acquisition unit/clock/export, direction and power validity, live-DP
tap/protection and180-second loss/overflow/storage acceptance are unqualified.
No synthetic result proves MST packetization, independent pixels or M5 source
ownership. Current hub state is irrelevant.

## Answers And Next Milestone

1. **Architecture surviving all gates:** none. Buffered differential conversion
   remains a conceptual direction, not an approved circuit.
2. **Exact enabling components:** none qualified. OPA810IDR and TLV9031DBVR
   constitute the closest fully sourced diagnostic example, rejected for off paths.
3. **Input C:** OPA810 example3.4 pF representative, using2 pF+0.5 pF typical
   input terms, ESD122 typical matrix and0.5 pF assumed PCB; maximum UNKNOWN.
4. **4 pF target met:** not defensibly. No complete guaranteed budget passes.
5. **Off equivalent:** AUX branch -> input upper/lower rail clamps, local feedback
   C/output clamp, off-supply storage/discharge; alternative JFET/feedback paths above.
6. **Off transparency proven:** no; specific direct connections are contradicted.
7. **Compatible protection:** ESD122 is a low-C test-point option, not a fully
   coordinated production solution; bench omission is separately conditional.
8. **Comparator selected:** none; `COMPARATOR_SELECTION_UNRESOLVED`.
9. **Threshold/hysteresis selected:** none; `FIXED_THRESHOLD_NOT_ESTABLISHED`.
10. **Worst-case CM:** guaranteed value UNKNOWN; OPA810 combined proxy0.003091736 V/V.
11. **Worst-case margin:** guaranteed value UNKNOWN; same proxy64.6336 mV.
12. **Matching assumptions:** declared C differences, four-resistor tolerance and
    assumed intrinsic AC CMRR; pair/PCB/temperature/frequency guarantees absent.
13. **Remaining UNKNOWN:** actual C matrix maxima, full signed envelope, leakage,
    protection coordination, reverse transfer, PVT noise/reference/timing and PCB.
14. **Prototype:** `AUX_FRONTEND_PROTOTYPE_STILL_BLOCKED`.
15. **W1:** `W1_CAPTURE_SYSTEM_NOT_READY`.
16. **Smallest next milestone:** **M5P12_OFF_STATE_ISOLATION_CELL_QUALIFICATION**,
    offline-only feasibility of one normally-open two-pole sense disconnect and
    its supply-validity sequencing. It must bound on/off C, leakage and isolation
    over signed inputs, including sudden power loss and any required supply hold-up
    until contacts/switches open. Reject it before board design if those bounds
    cannot coexist. This proposal is not approval, a selected switch, or a build.

The next question changes the documented off-current path instead of adding
precision resistors or assuming that a smaller typical input C cures it. It
does not claim that an isolation element will work, nor waive receiver maximum-C
or other remaining requirements.

## Physical State And Git

**CURRENT_HUB_STATE_NOT_REQUIRED**. M5P11 is analogue evidence qualification,
not M5P10's earlier conditional bench-build label. No physical Mac connection,
private IOKit/DCP/DPCD/AUX/m1n1 interaction, sudo, experimental driver, public
display query, hardware build/order, vendor/UCalgary contact or outreach occurred.
No system/security settings or sibling repositories were touched.

Preserved: **RETIRED_ON_DAILY_USE_M5**, **NOT_READY_FOR_DPCD_TEST**,
**STATIC_PACKETIZER_ANALYSIS_FROZEN**,
**NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED** and
**OFFLINE_OBSERVER_PIPELINE_READY**. M2F markers/captures remain unchanged;
`M2G-DPCD-READ-ATTEMPTED` remains absent. Old reports,544 evidence/source rows,
and raw historical artifacts are preserved. Only this new branch is published
after audit; no merge, force-push, PR or retagging. New raw evidence stays ignored.