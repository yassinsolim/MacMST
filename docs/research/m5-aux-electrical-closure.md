# M5P9 AUX Front-End Electrical Closure and Build Release

2026-09-18. Public-source qualification, analytical derivation and executed
numerical circuits only. No purchase, assembly, hardware capture, Mac query,
connection change, outreach or system-software installation.

## Objective

Close the specific M5P8 electrical blockers, or demonstrate why construction
still cannot be released. The eventual objective remains independent external
displays from the base M5 through ordinary DP MST, without DisplayLink or
separate Thunderbolt DP tunnels. This milestone does not investigate DCP,
main-link video or new runtime Mac behavior.

The principal new result is a correction to the matching hypothesis: the
reproduced 14.2 mV error is overwhelmingly **capacitive-ratio mismatch**, not
resistor tolerance. Perfect resistors do not remove it. A fail-safe comparator
improves one powered-off current path, but does not close negative-input,
capacitance, timing or idle-slicing requirements.

`MORE_ELECTRICAL_RESEARCH_REQUIRED`. Numerical execution is now real and
reproducible; construction is still withheld. M5P8's proposed name for a future
M5P9 bench build is superseded by the owner's present electrical-closure scope.
A bench-build milestone would now be **M5P10**, only after a build release and
separate authorization.

## M5P8 Baseline

Reconciled branch `research/m5-aux-frontend`, HEAD/upstream
`a68448e87d21b09bf7cd6a55ccf3541aa76cf7f1`, clean and ahead/behind 0/0.
The two linear commits from M5P7 are:

1. `c5368a54d4ca56558a54bc70dda4e827fc6c0403`: electrical model/circuit/tests.
2. `a68448e87d21b09bf7cd6a55ccf3541aa76cf7f1`: report and build gate.

Base M5P7 remains `277ff81437f3d5443eba58375495f86b3c5fcb41` on
`research/m5-aux-observer`. All four wire modules matched that commit exactly.
All 327 existing offline tests passed before edits. The 50 published
head/tag/peeled identities, M5P7 A-H bundles and source hashes, M5P8 model
generation/source hashes, M5P3/M5P4 runtime bundles, 60 earlier source receipts
and safety markers verified unchanged.

The original model reproduced S4 at 1 MHz:
`common_to_differential_gain=0.04736711230346687`, or
**14.210133691040062 mV** for 0.3 V common mode.
`research/m5-aux-electrical-closure` was created from exact M5P8 HEAD.
The M5P7 stack, M5P8 model/tool/tests/circuit and historical reports remain
unchanged. New modelling is independent and file-only.

## Open-Item Closure Matrix

The machine-readable table is
[hardware/aux-observer/closure.json](../../hardware/aux-observer/closure.json).
It preserves the exact wording/state of all sixteen M5P8 items, gives each a
stable ID, evidence requirement, final result and result evidence. Tests compare
it directly against the historical M5P8 table. No failed or unresolved item is
removed by splitting, renaming or silently redefining its requirement.

| ID | Exact M5P8 item | Before | M5P9 | Disposition |
| --- | --- | --- | --- | --- |
| P8-01 | Ordinary-AUX bounded input exploration envelope | PASS | PASS | Scoped public values and unknowns preserved |
| P8-02 | Instantaneous common-mode/transient range at chosen tap | UNRESOLVED | UNRESOLVED | Simulated CM/step amplitudes are not a guaranteed connector envelope |
| P8-03 | Actual DC input impedance/leakage | UNRESOLVED | UNRESOLVED | Full voltage/temperature/PCB leakage bounds absent |
| P8-04 | Actual maximum capacitance | UNRESOLVED | UNRESOLVED | Typical input C is not a max or matching specification |
| P8-05 | Sense-path matching | FAIL | FAIL | Capacitive mismatch dominates; precision resistors do not close it |
| P8-06 | Powered-off transparency/backfeed | UNRESOLVED | UNRESOLVED | Negative excursion leaves fail-safe contract; actual clamp/rail bounds missing |
| P8-07 | Protection coordination | UNRESOLVED | UNRESOLVED | Standoff, overshoot, pulse ratings and comparator clamp coordination unclosed |
| P8-08 | No intentional drive path | PASS | PASS | Input-only sense and independent forward-only digital boundary retained |
| P8-09 | PCB main-link routing implementation | UNRESOLVED | UNRESOLVED | No qualified connector/stackup/launch implementation |
| P8-10 | AUX branch geometry implementation | UNRESOLVED | UNRESOLVED | No extracted geometry/parasitic matching guarantee |
| P8-11 | Ground/reference strategy | PASS | PASS | DP-referenced analogue side, isolated USB digital side |
| P8-12 | Backend voltage compatibility and exact acquisition unit | UNRESOLVED | UNRESOLVED | Concrete analyzer candidates narrowed, complete acceptance unclosed |
| P8-13 | Actual overflow detection / 180 s storage | UNRESOLVED | UNRESOLVED | Public stop/export facts improved; exact duration/loss receipt absent |
| P8-14 | B1/B2 measurement procedure | PASS | PASS | Non-DP generated signal and power-state plan retained/refined |
| P8-15 | Offline model/decoder regressions | PASS | PASS | 327 preserved plus 34 new tests pass |
| P8-16 | Nonlinear SPICE / construction schematic review | UNRESOLVED | UNRESOLVED | Numerical execution subitem PASS; construction review still UNRESOLVED |

Six additional release categories are explicitly tracked as P9-17..P9-22:
comparator, total error budget, construction schematic, BOM, executed numerical
model, and decoder-through-front-end behavior. The complete review is below.

## AUX Electrical Constraints

Use the location-qualified values and primary references in
[M5P8](m5-aux-frontend.md#verified-aux-electrical-requirements), not a new broad
DisplayPort survey. Ordinary AUX is differential, Manchester-II, half-duplex
and nominally 1 Mbit/s. TI endpoint data provides 0.4-0.6 us Manchester
intervals, 75-200 nF endpoint coupling and a typical 100-ohm differential
termination. It does not establish a universal third-observer loading budget.

The small differential AC waveform is superimposed on potentially quite
different cable-side DC biases. A comparator accepting 0..5.5 V does not
automatically accept negative AUX excursions; a 3.6 V DC bias row is not an
instantaneous DC-plus-AC peak limit. The 90 mV loaded differential-peak
exploration case is component-derived, not a newly measured M5 minimum.

The engineering criteria were written into the closure table **before E0-E10**:
>=100 Mohm DC input per leg; <=100 nA leakage per leg, <=20 nA imbalance;
<=4 pF added capacitance per leg, <=0.1 pF imbalance; CM conversion <=0.005 V/V;
<=1% amplitude change; <=25 ns added crossing error and edge dispersion;
>=10 mV residual differential margin; off rail <=0.1 V and sustained backfeed
<=1 uA; no intentional drive path; worst accepted model must decode.

These are project design targets, **not VESA limits**. They were not relaxed
after results. Component maxima, PCB extraction and physical waveform
acceptance are still required before those targets become a hardware claim.

## Matching Error Root Cause

For a simplified leg, let $C_s$ be series sense capacitance, $C_i$ shunt input
capacitance, $R_b$ the bias resistance, and $R_s$ total series resistance.
Ignoring the extra protection pole and source loading only for this derivation:

$$H(s)=\frac{s C_sR_b}{1+s[R_sC_s+R_b(C_s+C_i)]+s^2R_sR_bC_sC_i}.$$

In the capacitive-divider band:

$$H\simeq k=\frac{C_s}{C_s+C_i},\qquad
V_{error}=V_{CM}(H_+-H_-).$$

For small **pairwise relative** mismatches $\Delta\epsilon_s$ and
$\Delta\epsilon_i$:

$$\Delta k\simeq k(1-k)(\Delta\epsilon_s-\Delta\epsilon_i).$$

M5P8 used $C_s=2.2$ pF, $C_i=2.5$ pF, opposing sense-cap errors +/-0.1 pF,
opposing input-cap errors +/-0.125 pF, and +/-1% resistors. The exact divider
difference is $2.3/4.675-2.1/4.725$, giving **14.26025 mV** at 0.3 V CM.
The complete M5P8 complex network gives **14.21013 mV**. The close agreement is
an independent explanation, not a fit to the result.

| Isolated M5P8 perturbation | Error at 0.3 V CM, 1 MHz |
| --- | --- |
| No mismatch | 0 mV |
| Resistors only, +/-1% | 0.16940 mV |
| Sense caps only | 6.78200 mV |
| Shunt input caps only | 7.45482 mV |
| Combined | 14.21013 mV |

These are phasor magnitudes, not independent scalar quantities that can simply
be summed. Finite bias impedance/source loading alter phase and magnitude
slightly. Comparator bias current, offset, ESD leakage and noise were **not
present in the original S4 calculation** and did not cause that 14.2 mV.
They are additional real-design error terms, not retroactive explanations.

| Per-leg resistor tolerance with the same bad capacitors | Combined error |
| --- | --- |
| 0.1% | 14.208265 mV |
| 0.05% | 14.208209 mV |
| 0.01% | 14.208168 mV |
| Perfect resistors | 14.208158 mV |

The frozen 0.005 V/V target requires approximately
$|\Delta\epsilon_s-\Delta\epsilon_i|\leq0.0200818$ for this divider: about
**2.008% capacitive-ratio tracking**. Even with perfectly matched sense caps,
the input-capacitance difference must be <=**0.0502 pF** at the original
2.5 pF operating point. Neither the inspected comparator nor PCB has that
guaranteed matching bound.

Alternatives were tested/qualified as follows:

| Alternative | Evidence | Result |
| --- | --- | --- |
| Precision discrete resistors | Deterministic 0.1/0.05/0.01% sweeps above | Useful for bias/timing consistency, not a cure for the dominant capacitive divider |
| TI RES11A10DDFR matched network | [SLPS785A](https://www.ti.com/lit/ds/symlink/res11a.pdf), October 2025, pp. 6-8: individual divider ratio +/-500 ppm, inter-divider matching +/-1000 ppm; ratio drift +/-2 ppm/C, matching drift +/-0.05 ppm/C **typical**; pin C 2.5/1.6/3.5 pF **typical**; 85 V catalogue maximum divider voltage | ACTIVE, SOT-23-THN-8, USD 0.778 at 1ku; stock behind login. Low-kohm values and pF substrate parasitics do not replace the high-Z matched capacitive sense network |
| ADI LT5400 A-grade | [Manufacturer](https://www.analog.com/en/products/lt5400.html): 0.01% matching, 0.2 ppm/C matching drift advertised, +/-75 V operating, MSOP-8, recommended for new designs | Serious ratio-tracking reference, but no qualified pin-C/max/stock/single-unit price obtained. PDF retrieval timed out; do not promote headline drift to a complete guaranteed envelope |
| Increase $C_s$ | 47 pF gives about 1.49985 mV divider error under the same absolute mismatch assumptions | Just meets the approximate CM target but yields >=47.73 pF conducting-clamp shunt bound, failing <=4 pF. 100 pF improves matching further but worsens that bound |
| Direct fail-safe comparator input | Removes external AC-divider matching | Static AUX+ versus AUX- bias can swamp the wanted AC differential signal; negative/off input contract and loading still matter. Not a valid direct-wire receiver merely because inputs are fail-safe |
| Differential amplifier/buffer first | Could replace uncontrolled divider matching with a specified CMRR | Requires a qualified first-stage input C, leakage, power-off behavior, gain/noise and CMRR over frequency. A resistive difference amplifier can add unacceptable DC loading; no eligible stage was qualified |

`MATCHING_ERROR_REMAINS_BLOCKING`. The root cause is resolved analytically;
the physical matching requirement is not.

## Error Budget

The retained error-budget JSON enumerates every required contributor. Its
guaranteed total worst-case field is **null**, not zero, because missing bounds
cannot be silently omitted. No Monte Carlo or RSS estimate substitutes for a
worst-case guarantee.

| Contribution | Nominal / bounded or assumed value | Remaining qualification |
| --- | --- | --- |
| Resistor ratio | 0 nominal; 0.1694 mV original +/-1% isolated model | Exact component/ratio topology not selected |
| Resistor temperature tracking | RES11A divider drift +/-2 ppm/C; 100 C implies +/-200 ppm per divider, subject to stated conditions | Matching drift typical and actual selected network/range differ; not a comparator-C tracking bound |
| Comparator offset | TLV9031 +/-0.3 mV typical; +/-2 mV over stated temperature/supply conditions | Full intended supply/CM/overdrive envelope unqualified |
| Bias-current mismatch | 1 pA typical input offset current times 1 Mohm = 0.001 mV | No guaranteed maximum in inspected table; +/-5 nA per-leg sweep is an assumption, not a rated bound |
| Sense-cap ratio | 6.782 mV original isolated corner | Actual matched part and temperature/voltage tracking missing |
| Input-capacitance mismatch | 7.455 mV original isolated corner | C common-mode/differential and their PVT matching not bounded |
| Protection leakage imbalance | Before the sense cap, ideal DC contribution to comparator input is blocked | Still shifts cable idle bias; changing leakage, capacitor leakage and transients remain relevant |
| PCB parasitic mismatch | No honest maximum yet | No connector/stackup/geometry extraction |
| Supply variation | About 0.0293 mV for assumed +/-0.165 V using 75 dB PSRR | Does not include midpoint transient, C variation or power-off behavior |
| Comparator intrinsic CMRR | 0.0949 mV typical at 0.3 V using 70 dB; 0.9487 mV using the conservative inspected 50 dB condition | Conditions differ with supply; external-network CM conversion is additional |
| Threshold/noise | TLV9031 has no internal hysteresis | Idle-state threshold/window and noise margin unqualified; external output feedback into AUX is prohibited |
| Delay asymmetry/dispersion | Fixed delay separated from variable crossing error | No full low-overdrive/PVT maximum; cannot convert unknown timing into zero voltage error |

The enumerated nominal scalar subtotal is **0.39587 mV** under its stated
assumptions. It is not total expected error or an RSS distribution. The
combined numerical E8 case uses bounded **assumed sweep endpoints**, not a
manufacturer-guaranteed combined worst case; it leaves only **1.165 mV**
sampled differential margin, below the frozen 10 mV target.

## Comparator Candidates

Fresh search focused on useful input contracts, not extreme speed. M5P8's
TLV3502 assessment remains intact; the new lead is TLV9031's explicit absence
of a positive-supply input clamp.

| Candidate | Input/timing facts from primary evidence | Decision |
| --- | --- | --- |
| TI TLV9031DBVR | [SNOSDA3H](https://www.ti.com/lit/ds/symlink/tlv9031.pdf), November 2025: 1.65-5.5 V supply, push-pull SOT-23-5; 0.3 mV typical offset, +/-2 mV stated temperature limit; bias 5 pA and offset-current 1 pA **typical**; Cdiff 2 pF and Ccm 3 pF **typical**; about 100 ns delay **typical** | ACTIVE, USD 0.413 at 1ku, inventory behind login. Best new conditional lead for lower offset and positive-voltage power-off input behavior, not a qualified selection |
| TI TLV3211DCKR | Preserved SNOSDK9C: 1.5 pF typical input C, 1.8-5.5 V recommended supply, low powered bias, about 54/56 ns at 20 mV overdrive; positive and negative rail clamps | Retained comparison; faster nominal slicing and internal hysteresis do not solve off-state loading |
| TI TLV1811DBVR | [SNOSDC8E](https://www.ti.com/lit/ds/symlink/tlv1811.pdf), July 2025: micropower, 2.4-40 V; table at 12 V/50 pF gives about 900 ns at 10 mV overdrive and 420/450 ns at 100 mV; 500 kHz stated toggle frequency | ACTIVE, USD 0.391 at 1ku. Low-power does not automatically mean sufficient pulse response for 0.4 us half-cells; not selected |
| Microchip MCP6561 family | Preserved DS20002139E and current manufacturer page: 1.8-5.5 V, pA typical bias, CM 4 pF/differential 2 pF typical; 56 ns typical/80 ns max in stated 100 mV-overdrive condition | Production, some variants show stock and USD 0.56 at 1-24 units. Exact package/off-state/low-overdrive envelope not qualified; no price transplanted to an unspecified variant |
| onsemi NCS2200SN1T1G | [NCS2200/D](https://www.onsemi.com/pdf/datasheet/ncs2200-d.pdf): pA typical bias, substantial hysteresis/offset ranges; representative 20 mV-overdrive delays 1080/900 ns | Current product page marks this variant active. The delay asymmetry/pulse response is unsuitable for the current timing allocation; no unqualified catalogue price treated as one-piece offer |
| ADI ADCMP600 | [Manufacturer](https://www.analog.com/en/products/adcmp600.html): production, 2.5-5.5 V, about 3.5 ns, rail-to-rail claim | No newly qualified off-state/C-max advantage established; PDF retrieval did not yield usable evidence. Speed alone is not a selection |

Renesas comparator/product-document lookups did not yield a usable current
datasheet at the checked URLs. This is a retrieval limit, not a claim that
Renesas lacks suitable components. The shortlist is deliberately not a catalogue.

Fixed delay is not the dominant timing constraint. If an edge appears at
$t_i+d_0+\delta_i$, pulse width error is $\delta_{i+1}-\delta_i$; $d_0$
cancels. A regression using **1 us ideal fixed transport delay** still decodes,
whereas **250 ns rise/fall asymmetry** does not. This does not prove that a
physical 1 us comparator passes 400 ns pulses: bandwidth, inertial behavior,
overdrive recovery and minimum pulse response must also be qualified.

The unchanged decoder accepts 10 MS/s or faster binary samples, recovers its
half-cell clock and uses a 25%-of-half-cell run tolerance. At a 400 ns
half-cell that is only 100 ns. Quantization, source jitter, front-end dispersion
and threshold movement share that budget. A 100 ns **fixed** comparator delay
can be reasonable; a guaranteed <=25 ns dispersion target is more important.
No inspected typical-delay plot supplies the required whole-envelope guarantee.

## Selected Comparator

`COMPARATOR_SELECTION_UNRESOLVED`.

TLV9031DBVR is a **conditional lead**, not the selected build part. It improves
offset and has an explicit fail-safe input contract. It does not establish
input-C maximum/matching, bias maximum, full low-overdrive delay dispersion,
negative-input transparency or quiet idle output. It is not selected merely
to fill a BOM row.

Its data sheet section 6.4.2.2 defines fail-safe as maintaining high input
impedance for **0..5.5 V**, independent of supply, including supply zero or
ramping. Inputs are not clamped to V+. Section 6.4.2.3 retains a negative
clamp to V-. Section 6.4.3 says snapback clamp performance is **not specified**;
external clamping is required for normal excursions beyond maximum ratings.
Section 6.4.5 explicitly says **no internal hysteresis**.

The model was corrected to zero hysteresis when that fact was read; criteria
were not loosened. Its nominal offset uses the documented typical 0.3 mV,
not a fabricated guaranteed offset that conveniently suppresses idle transitions.

## Protection Network

`PROTECTION_NETWORK_UNRESOLVED`.

Retain symmetric branch resistance before protection, then a DC-blocking sense
cap and a separate input-current limiter. Protection remains ahead of the
high-impedance local bias node so its DC leakage does not directly flow through
the 1 Mohm bias resistor. Neither a USB marketing label nor ESD kV rating is
enough to qualify loading or clamp coordination.

| Exact candidate | Electrical data / package / status | Qualification |
| --- | --- | --- |
| TPD1E01B04DPYR | Preserved SLVSDG3C: bidirectional +/-3.6 V standoff; 0.23 pF maximum at stated test point; <=10 nA at +/-2.5 V; typical TLP clamp 7/9.2/15 V at 1/5/16 A; DFN1006-2, ACTIVE; USD 0.039 at 1ku | Small C, but instantaneous input headroom and pulse/rail coordination remain unclosed |
| TI ESD401DPYR | [SLVSE49B](https://www.ti.com/lit/ds/symlink/esd401.pdf), August 2024, p. 5: bidirectional +/-5.5 V; 0.77 pF typical/0.95 pF max at 0 V, 1 MHz, 25 C; <=10 nA at +/-2.5 V; TLP clamp **11/16/24 V** at 1/5/16 A, 0.7 ohm dynamic resistance; DFN1006-2, ACTIVE; USD 0.066 at 1ku | Better standoff, more capacitance, and still far above comparator pin limits during ESD. The catalogue's 15 V clamp figure is a different surge condition, not the 16 A TLP value |
| TI TPD1E10B06DPYR | [Datasheet](https://www.ti.com/lit/ds/symlink/tpd1e10b06.pdf) and current page: bidirectional +/-5.5 V, 12 pF **typical**, catalogue <=100 nA leakage; DFN1006-2, ACTIVE; USD 0.033 at 1ku | Already exceeds the 4 pF per-leg budget before sense/PCB capacitance; not selected |
| Nexperia PESD5V0C1BLS-QYL | [Manufacturer](https://www.nexperia.com/product/PESD5V0C1BLS-Q): production, 5 V bidirectional, approximately 0.3 pF, 0.35 ohm advertised dynamic resistance; DFN1006BD-2 | Promising headroom/C combination, but PDF returned 403; complete max leakage/clamp/price evidence not established. Not selected from headline values |

For the 2.2 pF sense network, a simple conducting-clamp capacitance budget with
ESD401's 0.95 pF plus 0.5 pF board allowance is 3.65 pF per leg, before further
unqualified parasitics/tolerances. It is a useful calculation, not a complete
qualified maximum. A regression confirms that increasing the protection C
reduces the modelled sink peak.

At a hypothetical -24 V protected-node excursion, a 2.2 kohm limiter and
0.3 V ground clamp imply about **10.77 mA**, already above a 10 mA input stress
limit. The 24 V value is itself a stated typical TLP condition, not a universal
upper bound. Positive snapback, resistor pulse energy, capacitor voltage rating,
overshoot and ESD return inductance are not closed by this resistor estimate.

All prices above are manufacturer quantity indications, not one-unit quotes;
stock may require login. No order or enquiry was made. Generic model diodes
are not certified TVS/macromodels and cannot prove IEC survival.

## Powered-Off Analysis

`POWERED_OFF_BEHAVIOR_UNRESOLVED`.

The executed equivalent circuit contains, per leg:

```text
AUX -> 1k branch -> rail-independent TVS node -> 2.2pF -> 2.2k -> input
                                                                |
                           ground clamp <-----------------------+
                                                                |
                                   1Meg -> midpoint -> divider -> off rail
```

The off rail has modelled storage capacitance and leakage, rather than an ideal
zero-voltage sink. The candidate model omits a positive input-to-VDD clamp
because TLV9031 explicitly lacks it, but retains a negative clamp and the
**external bias-divider route** into the rail. The model can separately enable
an upper clamp for comparison. A reference test produces about 2.725 V phantom
rail voltage through a diode/resistor path, proving that the numerical engine
does not suppress backfeed by construction.

E7 starts unpowered, includes the ordinary packet plus an assumed 3.6 V,
10 ns-edge CM step, and executes clamp conduction. It produces approximately:

- Input minimum **-0.3022 V**, outside the 0..5.5 V fail-safe contract.
- Input maximum **1.4742 V**.
- Maximum model rail **0.32 uV** with the specified 1.1 uF storage/divider.
- Positive rail injection peak **0.00821 uA**.
- Maximum generic diode current **0.2336 mA**.
- No recovered valid packet, as expected for an unpowered receiver.

These are results of explicit assumed RC/PWL elements, not guaranteed physical
leakage, clamp voltage, repeated-transient accumulation or regulator behavior.
A low rail voltage in this one model is insufficient to claim transparency.
Input capacitors block steady ideal DC, but dielectric leakage, negative
rectification, changing bias, supply sequencing and parasitic paths remain.

The comparator's output has its own rail clamp. The independently powered,
forward-only digital isolation prevents the backend from intentionally driving
that output/rail, but the complete power/layout design is still unreleased.
Brownout, slow/fast discharge and arbitrary fault waveforms are not silently
covered by E7's initially unpowered case. No off-state pass is asserted.

## RX-Only Enforcement

`HARDWARE_RX_ONLY_ENFORCED` for the **proposed architecture**, not an assembled
board or arbitrary-fault certification.

There is no GPIO on AUX, AUX output driver, programmable termination, driver
switch, HPD output, EDID/DPCD emulator or active main-link component. The sense
network ends in comparator inputs/protection, with fixed independently powered
bias. The comparator output crosses a 1-forward/0-reverse isolated digital
boundary; no sampler-controlled signal or supply returns to AUX.

In particular, TI's generic suggestion to add output-feedback hysteresis is
**not adopted** here: an intentional comparator-output path into the sensed
network conflicts with this architecture's RX-only requirement. A fixed
receive threshold/window would need its own qualified design and error budget.
Parasitic coupling, ESD current and faults are separate from intentional drive.

## Executed Circuit Model

`NUMERICAL_CIRCUIT_MODEL` was **actually executed**. No SPICE simulator was
present on PATH or in the checked common application locations. No global
software or numerical package was installed. No SPICE-deck execution is claimed.

[tools/dp_aux_closure.py](../../tools/dp_aux_closure.py) implements a bounded
nodal RC solver using backward Euler, pivoted linear solves and explicit
piecewise-linear diode conduction. It preserves source/sink coupling caps,
differential sink termination, weak DC bias, board/protection/input capacitance,
separate cross-input capacitance, bias network, rail storage and leakage.
The ideal slicer has separately declared offset, delay, hysteresis and jitter.

Reference tests verify a resistor divider, RC exponential, AC transfer,
capacitor DC blocking, current injection, phantom-rail path and singular-circuit
refusal. KCL residuals are checked. A 5 ns versus 1 ns convergence test bounds
the selected nominal peak/midcell metrics to 1 mV/0.1 mV respectively; this
does not prove convergence for every conceivable nonlinear fault.

Final output is retained under
[artifacts/probes/m5p9/model-v2](../../artifacts/probes/m5p9/model-v2).
Its 50 hashed files plus hash receipt include per-case CSV waveforms, digital
capture inputs, decoded events, scenario metrics, matching/error-budget/sweep
data, six pipeline captures/analyses and a source/criteria-bound manifest.
All 49 numerical/fixture outputs are byte-identical to the earlier model-v1
run; only the manifest changed when the closure table acquired final dispositions.

Each CSV includes source differential and common-mode stimulus, sink and bus
differential voltages, both observer inputs, observer differential voltage,
rail voltage/current and digital output. Sink peak is not forced to 90 mV:
the assumed AC-coupled reference has about **122.343 mV peak** including its
transient behavior. Loading is compared to that same source/sink reference.

| Case | Perturbation | Peak-amplitude change | Residual margin | CM conversion at 1 MHz | Request recovered |
| --- | --- | --- | --- | --- | --- |
| E0 | No observer | 0% | N/A | N/A | N/A |
| E1 | Nominal declared network | 0.33195% | 17.103 mV | Numerically zero | Yes, but idle errors remain |
| E2 | +/-1% resistor mismatch | 0.33194% | 17.100 mV | 0.0002746 V/V | Yes |
| E3 | 2 mV offset endpoint | 0.33195% | 15.403 mV | Numerically zero | Yes |
| E4 | 0.5 pF protection-cap sweep endpoint | 0.34555% | 17.103 mV | Numerically zero | Yes |
| E5 | 8 pF shunt input-cap sweep endpoint, plus 2 pF cross-input | 0.35400% | 11.882 mV | Numerically zero | Yes |
| E6 | +/-5 nA input leakage and +/-10 nA protection leakage | 0.33195% | 10.751 mV | Numerically zero | Yes; extra edges remain |
| E7 | Initially unpowered + CM step | 0.33113% | N/A | Nonlinear, not reported as linear CMRR | No, expected |
| E8 | Combined declared resistor/cap/offset/leakage corners | 0.36309% | **1.165 mV, FAIL** | **0.0148107 V/V, FAIL** | Yes for this packet only |
| E9 | Maximum-length representative alternating-byte Manchester request | 0.33195% | 17.103 mV | Numerically zero | Yes |
| E10 | Request then 10 us gap and opposite-end reply | 0.0000823% versus its own no-observer sequence | 17.103 mV | Numerically zero | Request and reply bytes recover |

E2-E8 maxima are **declared assumed sweep endpoints**, not missing manufacturer
limits renamed as guarantees. E4's 0.5 pF is the original model budget, not
ESD401's 0.95 pF maximum; that alternative is separately tested. E8's mere
packet recovery does not override its failed criteria.

Timing is reported only when the number of modelled output edges matches the
expected sequence. E1 has 91 versus 90 edges, so its timing fields are **null**,
not falsely successful; E3/E5 have a measured model crossing error of 10 ns
with matched edge counts. Settling is reported to 1% within the finite recorded
window; continuous CM feedthrough can prevent settling and is not discarded.
All detailed values remain in the raw/summary files.

The model is not transistor-level, does not supply missing component PVT
bounds, and excludes transmission-line/PCB field effects, snapback physics,
thermal damage, EMI and real random noise. A zero-offset/no-hysteresis ideal
slicer is numerically ill-conditioned: quiet differential roundoff was about
3e-14 V. That is flagged, not claimed as measured comparator noise.

Reproduce to a **new** output directory:

```sh
python3 tools/dp_aux_closure.py
python3 tools/dp_aux_closure.py --output artifacts/probes/m5p9/reproduction-01
ctest --test-dir build-m5p4-offline -L offline -R '^dp_aux_closure$' --output-on-failure
```

The M5P8 SPICE subcircuit remains historical and unchanged; it is not quietly
relabelled as the new fail-safe network. Current connections/values are explicit
in `network()` and the closure JSON numerical assumptions. No construction
schematic is inferred from the executable model.

## Tolerance Analysis

Thirty-five deterministic one-factor points cover resistor ratio, input offset,
sense-cap mismatch, input-cap mismatch, protection-cap mismatch, input leakage
and protection leakage. No random seed is needed because no Monte Carlo is
used. E8 supplies a combined assumed corner, but the sweep is **not** an
exhaustive PVT or combinatorial global-worst-case proof.

| Ranked variable in the new model | Maximum contribution in declared sweep |
| --- | --- |
| Input leakage imbalance, +/-5 nA per leg | 10.000 mV DC |
| Input-capacitance mismatch, +/-0.25 pF per leg | 6.894 mV at 0.3 V CM |
| Offset, +/-6 mV stress sweep | 6.000 mV; includes values beyond TLV9031's stated offset corner |
| Sense-cap mismatch, +/-0.1 pF per leg | 3.758 mV at 0.3 V CM |
| Protection-C mismatch, +/-0.1 pF per leg | 0.0922 mV |
| Resistors, +/-1% per leg | 0.0825 mV |
| Protection leakage before ideal DC-blocking caps | Approximately zero comparator DC error in this ideal model |

These ranks are sensitive to the declared sweep ranges and the new cross-input
capacitance; they must not be compared as though all were rated maxima of one
selected circuit. The near-zero last entry does **not** mean protection leakage
is harmless: idle cable bias and changing leakage/transient effects remain.
The original 14.2 mV decomposition and this new sensitivity ranking are separate
models with explicitly different input-capacitance representations.

## Decoder Through Front End

The pipeline is: numerical source/sink/observer circuit -> ideal declared
comparator output -> neutral digital samples -> unchanged AUX decoder ->
unchanged MST reassembler -> unchanged W1 evaluator.

| Profile | Result | Important limit |
| --- | --- | --- |
| Nominal, no internal hysteresis, 0.3 mV typical offset | CAPTURE_INCOMPLETE; MST enable unresolved | Idle-transition/framing errors remain; not suppressed |
| Bounded accepted model profile: E5 input C with 2 mV offset | COMPLETE_FOR_INTERVAL; synthetic enable and payload 1 | A passing declared profile, **not** a guaranteed hardware worst case |
| Jittered, 2 mV offset and +/-5 ns declared jitter | COMPLETE_FOR_INTERVAL; synthetic enable and payload 1 | Does not establish a comparator jitter specification |
| Asymmetric, -2 mV offset and 115/100 ns delay | CAPTURE_INCOMPLETE; enable unresolved | Error retained |
| Powered off | CAPTURE_INCOMPLETE; enable unresolved | No fabricated capability or packet |
| Deliberate glitch | CAPTURE_INCOMPLETE; enable unresolved | Later payload 1 observation retained without exclusive-count proof |

The full pipeline uses **DC-initialized packet windows**, not one uninterrupted
analogue simulation of the entire attach. `continuous_analog_state=false` is
stored in every pipeline input. The separate E10 test carries actual continuous
analogue state across one direction transition. The W1 completeness labels are
synthetic software-contract results; they do not prove analogue continuity,
losslessness, real source ownership or hardware authorization.

No decoder tolerance, raw-error retention or completeness condition was weakened.
The nominal full pipeline failure is a release blocker, not an excuse to tune
the decoder to the circuit. It may require a qualified receive threshold/idle
representation as well as electrical changes. No new hardware importer or
capture interface was added.

## Electrical Pass Criteria

The frozen JSON criteria remain unchanged throughout E-scenario runs. The
manifest records their canonical SHA-256 independently from review prose.

- Loading must meet both weak idle-bias DC limits and active waveform limits.
- Capacitive matching, leakage, offset, PCB and supply terms need actual bounds;
  unknown terms cannot be filled with nominal values or an RSS estimate.
- The complete comparator/protection power-off path must stay within component
  contracts and the link-loading/backfeed targets, not merely survive in one model.
- Fixed delay can be calibrated; variable delay, noise and pulse rejection must
  remain comfortably inside the decoder timing budget.
- No intentional AUX/HPD transmit path or output-feedback path is permitted.
- Worst accepted model and nominal pipeline must preserve valid bytes and honest
  completeness. Successful decoding cannot overrule a failed electrical margin.
- Construction schematic, actual BOM and compatible acquisition path are
  mandatory before build release. All critical review rows must be PASS.

The `evaluate_model()` result always keeps hardware/build authorization false.
Passing an assumed numerical case is deliberately not an automated build gate.

## Backend Requirements

The backend observes only the isolated conditioned logic output, never raw AUX.

| Requirement | Derived target / rationale |
| --- | --- |
| Channels | One conditioned data channel minimum; two if a future qualified window/validity output requires it |
| Voltage | 3.3 V CMOS on digital side, compatible output load/threshold; no GPIO connection to analogue sense nodes |
| Sampling | Decoder hard minimum 10 MS/s; engineering minimum 20 MS/s conditional on remaining timing margin; prefer **50 MS/s or higher** for 20 ns or finer grid |
| Timestamp | Preserve sample interval and 64-bit sample/edge index or losslessly convertible timestamps; 50 MS/s x180 s =9 billion samples, exceeding a 32-bit index |
| Clock error | Proposed <=100 ppm recorded/reference-qualified clock target, not assumed from a brand. At 400 ns this adds only 0.04 ns locally, but 18 ms over180 s matters for external correlation |
| Raw throughput | 50 MS/s packed one/two-bit:6.25/12.5 MB/s;180 s:1.125/2.25 GB before format overhead |
| Transition format | 2.5 million edges/s x8-byte time records is20 MB/s or3.6 GB/180 s before metadata. RLE is not guaranteed compression, especially with glitches |
| Duration |180 s continuous pre-attach through stop, not triggered segments with hidden dead time |
| Loss | Sticky overflow/early-stop/error receipt, exact retained interval, no circular overwrite or silent time deletion |
| Interface | USB2 high-speed/USB3 or another demonstrably adequate host path; a USB-UART programming bridge is not a sample FIFO |
| Storage/export | Preserve unfiltered raw transitions/samples and final timestamp/count, settings, stop reason and hashes. Never infer completeness from a displayed waveform alone |

At 400 ns half-cells, the decoder's100 ns run-tolerance allowance must include
source jitter/adaptation, quantization and analogue dispersion. A20 ns grid
and<=25 ns front-end dispersion leave more budget than a50 ns grid; neither
constitutes an all-source timing proof. The selected clock rate and real
comparator pulse response must be verified in B1, not guessed from CPU GHz.

## Backend Candidates

This is a bounded comparison of conventional conditioned-input acquisition,
not a renewed survey of arbitrary FPGA boards.

| Candidate | Evidence and fit | Remaining gap |
| --- | --- | --- |
| Saleae Logic8 | Manufacturer documents100 MS/s on up to3 digital channels,50 on up to6,40 on up to7; real-time USB-to-PC streaming; raw transition export includes final sample; current product price carried from dated public page CAD710 | Installed memory is the buffer and digital format is pseudo-compressed. Exact clock/host memory/error/export acceptance for180 s not validated; hardware not queried |
| DSLogic U3Pro16 | [Current manufacturer page](https://www.dreamsourcelab.com/dslogic-u3pro16/) lists $299, in stock, USB3,2Gbit hardware memory,16G stream sample depth,16 channels at125 MS/s stream maximum,250 kohm/approximately13 pF digital input, adjustable threshold | Concrete potentially cheaper analyzer, but sample-depth units/mode, chosen clock and overflow/export contract need closure. Linked PDF/user guide retrieval returned406; no assumption that5 Gbit/s USB means loss-free recording |
| Digilent Cmod A7-35T,410-328-35 | [Manufacturer](https://digilent.com/shop/cmod-a7-breadboardable-artix-7-fpga-module/): USD104 listed,512KB SRAM, USB-JTAG and USB-UART | Sampler logic is feasible; standard transport is not a demonstrated6.25-12.5 MB/s FIFO. Would require additional engineering, not selected as cheaper simply from board price |
| Glasgow revD | Existing documented memory/42 MB/s architecture and sticky overflow remain credible | Pre-launch/price/available-instance issues unchanged. No need to redo its implementation research or select it merely because source exists |

Saleae documentation now resolves specific prior uncertainties:
[rates](https://www.saleae.com/support/logic-software/capturing-data/what-sample-rate-settings-are-available),
[duration](https://www.saleae.com/support/logic-software/capturing-data/how-long-can-i-record-data),
[memory/stop errors](https://www.saleae.com/support/troubleshooting/capture-and-recording-issues/capture-stopped-error),
and [raw export](https://www.saleae.com/support/logic-software/saving-and-exporting-data/exporting-data).
Timer capture can stop early on memory exhaustion; loop/trigger modes may
discard oldest processed data and stop on backlog. Those modes/settings must
not masquerade as full pre-attach coverage. Exporting only decoder results is
insufficient. No software was installed or acquisition attempted.

## Backend Selection

`ACQUISITION_PLATFORM_UNRESOLVED`.

The preferred **class** is now an ordinary streaming logic analyzer behind the
qualified front end, with Logic8 and DSLogic U3Pro16 as concrete candidates.
Developing a new FPGA transport is not currently justified by the signal rate.
Exact clock, host-buffer/stop behavior and raw-export acceptance still prevent
a full backend selection. A documented available sampler can be chosen later
without revisiting the AUX protocol stack or waiting for outreach.

No model is declared selected with an unverified180 s/loss contract. Short
bench captures are a narrower capability than a complete W1 attach capture.

## Tap Schematic

**No construction schematic is released.** The conditional release criteria
are not met. M5P8's analysis SPICE file is retained unchanged and is not
misrepresented as the current fail-safe candidate or a checked KiCad schematic.

The proposed structure remains:

```text
DP source ===== main-link/AUX/HPD through path ===== DP sink
                          |
                      AUX only
                          |
              symmetric protected high-Z sensing
                          |
                  receive comparator input
                          |
                  one-way digital isolation -> logic analyzer
```

The numerical network is fully specified in code/JSON and reproducible, but
it is not a pin-complete, power-complete, footprint-reviewed fabrication design.
No fake ERC/DRC pass or placeholder comparator BOM is issued. A conceptual PCB
layout cannot fix unqualified analogue input behavior and is not produced for
appearance alone.

## PCB Constraints

Retain the qualified public routing guidance from M5P8:

- Main-link:100-ohm differential target using the actual fabricator stackup,
  straight-through pairs, no observation stubs/test pads, minimum vias and
  symmetric launches; TDP142's HBR3 guidance gives +/-10% and5 mil intra-pair
  matching, not a guarantee for an unbuilt board.
- AUX:continuous through pair; pre-resistor observation stub<=2 mm as a derived
  engineering target; symmetric short branches, protection/local return and
  separation from comparator/isolator/output edges.
- No active main-link component, added link termination, HPD driver or emulator.
- Preserve shield/reference strategy; do not blindly bridge DP_PWR or power
  the observer from it. Exact connector orientation and power-pin treatment
  require the construction design.
- Analogue midpoint/supply are fixed and separately powered; digital USB ground
  remains on the isolated output side. Scope/charger grounds must not bypass
  that separation. Never lift protective earth.
- Decoupling, ESD return inductance, pulse ratings and pad capacitance are part
  of the error/protection budget. No solderless breadboard in the DP main link.

These are preliminary rules, not extracted impedances, S-parameters or a
qualified layout. No PCB is fabricated or ordered.

## BOM

**No complete preliminary build BOM is released.** Comparator, coordinated
protection, power, connectors/PCB and acquisition acceptance remain critical
unresolved items. Candidate MPNs and sourced values above are a qualification
record, not an orderable BOM with hidden TBDs.

For a future release, the six required groups remain explicit: frontend,
protection, power, PCB/connectors, digital backend, and native-DP laboratory
hardware. Each requires actual part/package/quantity, design-critical bounds,
supplier, dated unit price/stock and qualified substitutes. A1ku price is not a
single-unit price, ACTIVE is not confirmed stock, and a typical capacitance is
not a substitute's guaranteed maximum.

The existing StarTech native-DP adapter/MST branch remain historical lab
candidates with their vendor OS caveat, not a promised working M5 arrangement.
Their earlier CAD26.99/CAD66.99 observations are dated M5P8 evidence; they were
not purchased or connected in M5P9.

## Cost

There is no honest complete observer price yet.

| Cost group | Current evidence / limit |
| --- | --- |
| Observer electronics | Comparator/protection/network quantity prices documented, but unqualified power/PCB/connector choices prevent a one-unit total |
| Capture backend | Logic8 dated CAD710; DSLogic U3Pro16 currently lists $299; Cmod A7-35T USD104 but requires unqualified transport work. Do not compare currencies or board-only prices as complete systems |
| Native-DP lab setup | Historical M5P8 adapter+MST branch subtotal CAD93.98, excluding cables/power/tax/shipping; vendor Windows-only hub support caveat retained |
| Optional bench equipment | No AWG/scope/probe inventory assumed. Existing access would reduce incremental cost only after actual availability/qualification |

Commercial AUX access could avoid front-end development but depends on an
available, correctly configured unit/export contract; no new outreach or cost
guess is made. Self-owned numerical work continues independently. No purchase,
quote request, university contact or waiting for replies occurred.

## B1/B2 Plan

Conditional **M5P10 - AUX Observer Bench Prototype Build and B1/B2 Validation**
is not authorized by this report. Before ordering/assembly, every critical
release row must pass and the owner must separately authorize the build.

**B1, no DP source:** use a reviewed differential or synchronized two-output
AWG network with known source impedance, coupling and separately controlled
DC/common-mode bias. Normalize at the load, not merely the generator display.
Exercise400/500/600 ns half-cells, smallest/large differential cases, preamble,
delimiters, payload patterns, gaps, jitter and both transmitter directions.
A raw3.3 V GPIO is not a representative analogue AUX source.

Measure loading before/after attachment, per-leg leakage/C and imbalance,
common-mode conversion, low-overdrive threshold/delay, edge dispersion, idle
transitions and decoder completeness. Use the frozen criteria. Account for
probe input C and weak-bias loading; do not use a200-kohm probe and assume it
is transparent merely because it is large beside100 ohm.

**B2, still no DP source:** test powered, unpowered and both supply-sequencing
orders, including backend on/analogue off, slow/fast ramps and brownout. Measure
rail rise and current rather than treating missing power as an open circuit.
Apply reviewed current-limited low-energy transients first; no ESD-gun/high-energy
test without its own protection/procedure review. Confirm one-way output
isolation and force digital capture overflow with synthetic data so loss is
reported, not hidden.

Expected observations and rejection conditions are numerical: failures of
loading, CM conversion,10 mV margin,25 ns timing allocations, off-rail/backfeed
or complete decoder coverage stop progression. Do not adjust limits after a
failed bench result merely to advance. Retain raw waveforms, setup, clock,
temperature, power states, part/PCB revisions, stop reasons and hashes.

## Future DP Validation Ladder

| Stage | Scope | Authorization |
| --- | --- | --- |
| B0 | Synthetic/numerical offline evidence | Executed; not hardware proof |
| B1 | Generated AUX-like waveform, no DP device | Future, after build release/approval |
| B2 | Front-end powered/unpowered bench measurements | Future, after B1 and reviewed safety scope |
| B3 | Expendable known DP source/sink | Separately gated; B1/B2 do not automatically authorize it |
| B4 | Known real SST AUX capture | Requires actual pass-through/loading/loss evidence |
| B5 | Known real MST branch capture | Requires correct raw topology/allocation reconstruction |
| B6 | Base M5 | Separate owner approval and fresh controlled capture generation; never implied by bench success |

No B1-B6 action occurred in M5P9.

## Design Review

All22 rows are critical release requirements. PASS on a modelling or strategy
row is scoped to that work, not a physical safety certification.

| ID | Requirement | Result |
| --- | --- | --- |
| P8-01 | Scoped input exploration envelope | PASS |
| P8-02 | Instantaneous input/CM/transient compatibility | UNRESOLVED |
| P8-03 | Actual DC impedance/leakage | UNRESOLVED |
| P8-04 | Maximum front-end capacitance | UNRESOLVED |
| P8-05 | Sense-path/common-mode matching | FAIL |
| P8-06 | Powered-off transparency/backfeed | UNRESOLVED |
| P8-07 | Protection coordination | UNRESOLVED |
| P8-08 | RX-only intentional path | PASS |
| P8-09 | Main-link PCB/launch implementation | UNRESOLVED |
| P8-10 | AUX branch/parasitic implementation | UNRESOLVED |
| P8-11 | Ground/reference strategy | PASS |
| P8-12 | Exact backend compatibility/selection | UNRESOLVED |
| P8-13 | Overflow/180 s capture acceptance | UNRESOLVED |
| P8-14 | Non-DP B1/B2 procedure | PASS |
| P8-15 | Offline regressions/preservation | PASS |
| P8-16 | Original combined model/construction review | UNRESOLVED |
| P9-17 | Comparator selection | UNRESOLVED |
| P9-18 | Complete worst-case error budget | UNRESOLVED |
| P9-19 | Construction schematic completeness | UNRESOLVED |
| P9-20 | Complete actual-parts BOM | UNRESOLVED |
| P9-21 | Executed numerical circuit model | PASS |
| P9-22 | Nominal/full-envelope decoder-through-front-end | FAIL |

**PASS =6; FAIL =2; UNRESOLVED =14.** Every original M5P8 FAIL/UNRESOLVED item
remains explicitly dispositioned. P8-16 is not promoted just because numerical
execution is now complete; its construction-review half is still open.

## Prototype Gate

`MORE_ELECTRICAL_RESEARCH_REQUIRED`.

The build rule is unchanged. Matching, protection, powered-off behavior,
comparator selection, backend acceptance, whole-envelope decoder behavior,
construction schematic and actual-parts BOM are not all PASS. No M5P10 build,
procurement or assembly is released.

The **smallest next evidence-producing task** is a bounded differential-first
input-network analysis, not more precision-resistor shopping: qualify a
receiver/buffer input capacitance matrix and fixed receive threshold/idle
behavior against **<=0.005 V/V CM conversion and >=10 mV residual margin**,
without relying on unguaranteed <=0.0502 pF shunt-C matching or adding an
output-feedback path to AUX. Reuse the present solver and E1/E8/E10/pipeline
fixtures. Reject a candidate immediately if its public C/PVT/off-clamp model
cannot support the bound; do not finish a BOM around it first.

This specifically addresses the demonstrated capacitor/idle failures and gives
a falsifiable next design test. It is still offline component/model work;
missing bounds are not permission for a Mac probe or outreach dependency.
Protection, backend and layout acceptance remain listed and cannot disappear
when that next local analogue requirement is solved.

## Physical-State Policy

`CURRENT_HUB_STATE_NOT_REQUIRED`. The hub may be on another laptop; no state
was assumed, queried or changed, and no connect/disconnect request was made.
No M5 result depends on the physical state during this milestone.

`RETIRED_ON_DAILY_USE_M5` and `NOT_READY_FOR_DPCD_TEST` remain. Preserve the
static packetizer freeze, the no-further-T8142-analysis boundary and the frozen
offline observer pipeline. No private/user-client/AUX/DPCD command, native
display executable, firmware/security change or m1n1 sibling access occurred.

### Validation And Receipts

Build, Python compilation, diagnostics and all seven `offline` CTests pass:
**327 preserved +34 new =361 tests**. Source/matrix/record checks validate
analytical decomposition, RC/PWL behavior, AC response, convergence, tolerances,
power-off paths, fixed versus asymmetric delay, circuit-to-W1 behavior and
new-output refusal. No live hardware test or system installation occurred.

```sh
cmake --build build-m5p4-offline
ctest --test-dir build-m5p4-offline -L offline --output-on-failure
python3 -m py_compile tools/dp_aux_closure.py tests/test_dp_aux_closure.py
```

No BOM or construction schematic was released, so no EDA ERC/DRC or fabricated
BOM-completeness pass is claimed. The inherited schematic/model sources and all
historical captures remain preserved, not silently corrected in place.

Final preservation checks passed: **130 other baseline tracked files** are
byte-identical, including the frozen wire stack and M5P8 models/tests/circuit.
All498 earlier ledger rows remain. Historical runtime and M5P7/M5P8/new model
bundle hashes validate, including477 M5P4 records and current source hashes for
the final model generation. All60 earlier plus11 new source receipts match;
the consumed M2F marker/two receipts and absent M2G read marker are unchanged.
All50 pre-M5P9 published head/tag/peeled identities matched locally/remotely
before publication. Only the new branch is to be pushed; no merge, PR, tag or
external-source/raw-capture upload is part of this milestone.

New source receipts under `artifacts/probes/m5p9/sources`, retrieved in this
milestone, remain ignored and unmodified. URLs are in the relevant sections.

| File | SHA-256 |
| --- | --- |
| `tlv9031.pdf` | `97f124d3a40b1e55e74dda66ca81654b0c2eb782ec8aa1e9b18d2a40bd65627d` |
| `tlv1811.pdf` | `fe6a20ce3d711eefc8c800ed94182645f9e07c4ece03c4cb6e3e5ed3ddc49319` |
| `res11a.pdf` | `4fd07aedeabefea04a2f27c89c3b1b0e631bb06c11c2669b3390a0f7b4e3a6f2` |
| `tpd1e10b06.pdf` | `6ffe72cb5f5e607fcafd05eef9809632402241eb44cd859a3652f43a35323da9` |
| `esd401.pdf` | `a5633671490376defbdb95c629f52bb4024393ec5dc1e7e904b0eab2705e701f` |
| `ncs2200.pdf` | `8451e43d4806d1885b5be55ea8fb420f8ef5b91984b271af541aa4def6158d37` |
| `saleae-rates.html` | `15a03ec0b493baacaa1ab2d1ee6816f0d7936f804555fbd1edbb756873a4496e` |
| `saleae-duration.html` | `06dd609ab3ad9e2264d16e8544fc4566ea612b712a5734d167f90506a6f761d6` |
| `saleae-stopped.html` | `16d9e61ed62abedf7859e0f5c4f553753f2242fb1ccc383528c7f7d37da4cb47` |
| `saleae-export.html` | `52b82388623116a3616ac1423d70e6ec60f13f913476a8fb71da0c46f4ddc3c5` |
| `dslogic-u3pro16.html` | `7dbc40e6f4841eee65106bd7984cc4cf18a79a83150d227291e998876e4a174b` |

Failed PDF/page retrievals are recorded as limits, not component absence or
compatibility proof. No challenge, login or credential mechanism was bypassed.
No manufacturer, university or lab was contacted, and no reply is required
for the next bounded engineering task.