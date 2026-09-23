# M5P10 - Differential-First AUX Front-End Topology Closure

Date: 2026-09-22. Offline electrical design and numerical experiments only.
No hardware observation, purchase, assembly or outreach.

## Objective

Replace the fragile capacitive-divider input without changing M5P7 or its
acceptance criteria. CM conversion remains <=0.005 V/V, receive margin >=10 mV.
Hypothesis: direct high-Z sensing from a low-impedance source reduces conversion
from shunt-C mismatch. Initial AC/DC checks confirm that modeled improvement,
but disprove direct threshold reception of the illustrative -2.7 V DC bias.

A differential receiver followed by local DC removal and a window slicer
resolves nominal synthetic decoding. Its physical input stage is not qualified:
**DIFFERENTIAL_FRONTEND_UNRESOLVED**. This is not a conclusion about M5 MST.

Separate gates: **AUX_FRONTEND_PROTOTYPE_STILL_BLOCKED** for analogue reasons;
**W1_CAPTURE_SYSTEM_NOT_READY** with additional live-DP/capture requirements.
Exact180-second recorder selection does not block a safe B1/B2 frontend by itself.

## M5P9 Baseline

Base branch `research/m5-aux-electrical-closure`, HEAD/upstream
`2977255832c17714bb3ee273b52d0d85e4fb30e9`, was clean and0/0 ahead/behind.
Its two linear commits,51 published head/tag identities, historical captures,
477 M5P4 records, safety markers and71 prior source receipts were verified.
New branch: `research/m5-aux-differential-frontend`, directly from that HEAD.

All361 baseline tests passed. [Legacy replay](../../artifacts/probes/m5p10/legacy-baseline/manifest.json)
reproduces all50 M5P9 output files plus hashes exactly, including E0-E10 and
six pipeline profiles: **LEGACY_FRONTEND_BASELINE**, not a repaired old run.
[M5P9](m5-aux-electrical-closure.md), older models/tests and all four M5P7
modules remain unchanged. The existing RC/PWL solver is reused.

The canonical JSON SHA256 of [frozen criteria](../../hardware/aux-observer/closure.json)
is `bcfb58e9d6311337084552720658a70bec52bf864b199c34b89d4218355c3b95`.
[New configuration](../../hardware/aux-observer/differential.json) verifies it.
M5P9's6 PASS/2 FAIL/14 UNRESOLVED and incomplete nominal result remain historical.
Future physical work is now conditional **M5P11**, superseding old build labels.

## Legacy Failure Reproduction

At1 MHz and0.3 V CM amplitude, the unchanged model gives:

| Original case | Differential error, mV |
| --- | ---: |
| Nominal |0|
| Resistors only, opposing +/-1% |0.169396180|
| Sense capacitors, opposing +/-0.1 pF |6.782004749|
| Input capacitors, opposing +/-0.125 pF |7.454815569|
| Combined |**14.210133691**|
| Same capacitors, perfect resistors |**14.208157935**|

Isolated phasor magnitudes are not scalar terms to add blindly. In the divider
band $k=C_s/(C_s+C_i)$ and $V_{err}=V_{CM}(H_+-H_-)$. The old requirement remains
about2.008% capacitive-ratio tracking, or0.0502 pF input difference with ideal
sense-cap matching. Raising coupling to47 pF helps conversion but gives a
47.73 pF conducting-clamp loading bound, failing the fixed4 pF target.

## Differential-First Architectures

| Path | Discriminating check | Disposition |
| --- | --- | --- |
| D1 direct comparator | Remove input series-C divider; solve AC and DC. | AC improves, but roughly-2.7 V DC dominates wanted AC. Direct zero/small window thresholds stay negative. Reject for this cable-side envelope. |
| D2 symmetric attenuation | Joint DC loading/bandwidth calculation. |50 Mohm/50 Mohm meets ideal100 Mohm input but with3 pF shunt delivers only0.0955 mV from90 mV at1 MHz. Precision R does not fix bandwidth. Near-unity attenuation returns to D1; compensation needs bounded C ratios. |
| D3 high-Z receiver then comparator | Subtract first, tolerate DC, remove it once at a low-Z output, use local references. | Useful conditional direction; finite-bandwidth/error model executed. Actual input matrix, range, off-state and AC CMRR unqualified. |
| D4 dedicated differential receiver | Require real impedance/range/threshold/off contracts, not an LVDS label. | AD8130 is genuine but its1 Mohm differential input fails weak-bias leakage target. No eligible dedicated part selected; generic LVDS/RS-422 not automatically suitable. |
| D5 intentional input AC coupling | Require guaranteed ratios, matrix/parasitics and off loading. | Small legacy caps fail matching; large caps fail clamp loading. No qualified new divider; do not retain by default. |

D3 uses one high-pass after differential conversion, not two unmatched filters
hidden by ideal subtraction. FDA feedback resistors count as input loading.
Additional buffers require their own tracking, protection and power-state bounds.

## Architecture Rejection Rules

Reject tighter-than-guaranteed matching, equality of typical Cin treated as
matching, range violations, or materially loading off clamps. No AUX bias,
extra termination, output-feedback hysteresis or GPIO drive is allowed. Reject
protection/receiver variation alone exceeding conversion limits, and passes
requiring ideal components, deleted faults or unknown terms set to zero.

The conditional D3 model passes conversion/margin but fails representative
loading. Byte recovery cannot override that. Limited evidence does not prove
that every alternative receiver is impossible.

## Comparator Search

Current manufacturer observations are dated2026-09-22. Preserved older datasheet
observations keep their dates. ACTIVE is not stock,1ku prices are not one-unit
quotes, and retrieval failures are not component absence findings.

| Comparator | Evidence | Assessment |
| --- | --- | --- |
| TLV9031DBVR | [TI SNOSDA3H](https://www.ti.com/lit/ds/symlink/tlv9031.pdf), November2025. Positive fail-safe, low offset, no hysteresis. ACTIVE USD0.413/1ku; stock behind login. | Requires conditioning; detailed below. |
| TLV9032DGKR / TLV9032DR | Same family datasheet. [Current page](https://www.ti.com/product/TLV9032): dual push-pull, ACTIVE; VSSOP8 USD0.664/SOIC8 USD0.577 at1ku. | Downstream window lead; packaging does not guarantee channel timing/C matching. |
| TLV3211DCKR | Preserved SNOSDK9C:1.5 pF typical,54/56 ns around20 mV overdrive, rail clamps/internal hysteresis. | Lower typical C does not close max-C/off behavior. |
| TLV3502 | Preserved SBOS321E:2 pF common/4 pF differential typical,6 mV typical hysteresis, clamped inputs. | Prior not-preferred result retained; speed does not cure loading/bias. |
| TLV1811DBVR | Preserved SNOSDC8E, July2025:2.4-40 V; about900 ns at10 mV overdrive under12 V/50 pF conditions;500 kHz toggle figure. | No qualified400 ns physical pulse response. |
| MCP6562 family | [Microchip](https://www.microchip.com/en-us/product/mcp6562), production, DS20002139E;4/2 pF common/differential typical;56 ns typical/80 ns max at stated100 mV overdrive. | Several variants show stock and family1-24 pricing fromUSD0.75. Exact variant/low-overdrive/off envelope not selected. |
| NCS2250SQ2T2G | [onsemi page](https://www.onsemi.com/products/signal-conditioning-control/amplifiers-comparators/comparators/ncs2250):50 ns low-voltage RR push-pull, ACTIVE variants; [NCS2250/D](https://www.onsemi.com/pdf/datasheet/ncs2250-d.pdf) retained. | Faster alternative to prior NCS2200, not Cin/off/skew qualification from a headline. |
| LT1716 / ADCMP600 | [ADI LT1716](https://www.analog.com/en/products/lt1716.html) production over-the-top; [ADCMP600](https://www.analog.com/en/products/adcmp600.html) fast production comparator. | Neither inspected evidence closes C, off and low-overdrive bounds; neither label removes DC differential bias. |

| Receiver stage | Primary evidence | Limit |
| --- | --- | --- |
| INA851RGTR | [SBOS999A](https://www.ti.com/lit/ds/symlink/ina851.pdf), October2022 section7.5:7 pF common/1 pF differential and100 Gohm typical;18 nA bias/6 nA offset-current temperature limits;15 MHz gain1/22 MHz gain0.2 typical;8-36 V. ACTIVE USD3.997/1ku. | No <=4 pF complete input matrix.86 dB gain1 minimum CMRR is DC-60 Hz, not MHz. Overvoltage protection permits current, not off transparency. |
| AD8130 | [ADI](https://www.analog.com/en/products/ad8130.html), AD8129/AD8130 Rev.C:270 MHz genuine receiver,1 Mohm differential input, broad CM,80 dB minimum CMRR at2 MHz. | Microamps through biased1 Mohm violate <=100 nA target despite useful CMRR. |
| THS4551 | [TI](https://www.ti.com/product/THS4551), ACTIVE differential ADC driver. | Feedback resistors are not an instrumentation-style high-Z input; extra input stage needed. |
| LTC6268 / LTC6269 | [ADI](https://www.analog.com/en/products/ltc6268.html): recommended for new designs,450 fF advertised Cin,500 MHz GBW,3 fA typical/4 pA max at125 C,3.1-5.25 V supply. | Low-C buffer classes exist. Full matrix/maxima, tracking, range and both-rail off behavior remain unqualified; no build variant selected. |
| OPA810 | [TI](https://www.ti.com/product/OPA810), RRIO FET,4.75-27 V,140 MHz advertised bandwidth; ACTIVE OPA810IDBVR USD1.479/1ku. | Useful range/buffer lead; complete C/off/pair-tracking contract absent. |

The remote ADI PDF conversion stalled and was cancelled without repeated retries.
Completed TI conversions, old sources and bounded HTTP downloads supplied usable
evidence. Renesas/Nexperia short URLs returned404; some ADI downloads failed
HTTP/2; Microchip raw download returned403 despite readable product-page content.
No access controls were bypassed and missing guarantees remain unknown.

Nine retained raw receipts remain ignored; no manufacturer PDFs are vendored:

| Receipt | SHA256 |
| --- | --- |
| [tlv9031.pdf](../../artifacts/probes/m5p10/sources/tlv9031.pdf) | `97f124d3a40b1e55e74dda66ca81654b0c2eb782ec8aa1e9b18d2a40bd65627d` |
| [ina851.pdf](../../artifacts/probes/m5p10/sources/ina851.pdf) | `b6836363e32f3d5fdc1b85d731ba7ee8c2c687d3f86a81eeec403ff8ba869752` |
| [esd122.pdf](../../artifacts/probes/m5p10/sources/esd122.pdf) | `16ba54c64476aa5abbadc84ce72e60cee6baf710c958be0aad90cf363393f3ab` |
| [ncs2250.pdf](../../artifacts/probes/m5p10/sources/ncs2250.pdf) | `3c2ee4debc923bdfc6ca38a982a77d91a0ca0dcaea618c686151333e14fd82cb` |
| [tlv9032.html](../../artifacts/probes/m5p10/sources/tlv9032.html) | `62621a0ee5d9cd4fd56ec56210b71e5beb19bea754193c7a9f366dbd0983d684` |
| [dslogic-u3pro16.html](../../artifacts/probes/m5p10/sources/dslogic-u3pro16.html) | `79b4f3669006275f1a44b07e963d0cb49072e6da8508c4dbd3513fa1f1317786` |
| [saleae-rates.html](../../artifacts/probes/m5p10/sources/saleae-rates.html) | `15a03ec0b493baacaa1ab2d1ee6816f0d7936f804555fbd1edbb756873a4496e` |
| [saleae-logic.html](../../artifacts/probes/m5p10/sources/saleae-logic.html) | `3b388e3e8c984b9259ea209fa00f6369c103aed78e3cbe2d9364c4247a7916d4` |
| [glasgow-analyzer2.html](../../artifacts/probes/m5p10/sources/glasgow-analyzer2.html) | `154af8793962923a5317539721d8177ffce65582bf89a4ad82917f0f4b183a2d` |

## TLV9031

**TLV9031_REQUIRES_CONDITIONING**. SNOSDA3H sections6.4.2.2-6.4.5 distinguish:

| Property | Meaning |
| --- | --- |
| Supply/normal CM |1.65-5.5 V supply, normal input CM about rails+/-0.2 V at stated conditions; actual instantaneous voltages must fit. |
| Positive fail-safe |High-Z0..5.5 V independent of VDD including zero/ramping; no input clamp to V+. |
| Negative input |Clamp to V- remains; positive guarantee does not cover arbitrary negative AUX excursions. |
| DC differential |About-2.7 V illustrative bias swamps wanted AC; direct zero/window slicing stays asserted. |
| Cin |3 pF common/2 pF differential typical, not maxima, tracking or unique full matrix. |
| Offset/current |About+/-0.3 mV typical offset,+/-2 mV stated PVT limit;5 pA bias/1 pA offset current are typical despite ambiguous catalogue max labeling. |
| Delay |About100 ns typical is not full low-overdrive dispersion, skew or minimum-pulse guarantee. |
| Hysteresis |None; do not invent a guaranteed minimum offset or hysteresis to suppress idle. |
| Protection |Snapback performance explicitly unspecified; stress ratings do not coordinate ESD/current. |
| Output/startup |Push-pull rail protection; POR is not complete dual-channel brownout/isolator validity. Never drive outputs from GPIO. |

A qualified differential receiver/DC removal can present a local signal near
1.65 V to local references. That is conditioning, not direct AUX qualification.

## Comparator Selection

**COMPARATOR_SELECTION_UNRESOLVED**. TLV9031 and dual TLV9032 are downstream
leads, not a qualified whole chain. Constant delay cancels from pulse width;
rise/fall variation and channel skew do not. The old ideal1 us delay test cannot
prove physical400 ns pulse response. New60 ns ideal model delay is likewise
an assumption, not a TLV9031 specification.

## Threshold Strategy

| Strategy | Decision |
| --- | --- |
| T1 natural offset |No guaranteed nonzero minimum/sign/noise immunity; not an idle guarantee. |
| T2 fixed threshold |Potentially valid after conversion, inside a guaranteed nonempty interval. |
| T3 hysteresis |Internal or local post-buffer only, with bounded thresholds/timing; no feedback to AUX. Binary latching alone does not report idle. |
| T4 dual threshold |Explicit positive/negative/dead-band/invalid; preferred conditional representation, two channels and skew requirement. |

A two-input comparator has no independent third differential-threshold input.
Threshold generation is after the receiver; no offset current is injected into AUX.

## Dual-Comparator Slicer

$u=V_{MID}+HPF(LPF(G(V_P-V_N)+e_{CM}))$. Comparators test
$u>V_{MID}+V_{TH}$ and $u<V_{MID}-V_{TH}$. The receiver must handle DC before filtering.

| CH0,CH1 | State | Packed integer |
| --- | --- | ---: |
|1,0|POSITIVE|1|
|0,1|NEGATIVE|2|
|0,0|IDLE / DEAD BAND|0|
|1,1|INVALID|3|

Bit0 is CH0, bit1 CH1. Real skew can produce11; the40 ns skew witness does,
and stays incomplete. [The separate adapter](../../tools/dp_aux_differential.py)
preserves raw states. It annotates midpoint reconstruction only for short00
gaps between opposite polarities. Short same-polarity gaps and11 become errors;
long gaps split regions; unobserved sample intervals become losses.

Default40 ns interpolation is a representation rule, not25 ns physical timing
proof. Phase/slew/skew still need bounds. Idle records still undergo metadata,
origin and loss checks. Direction is never inferred from voltage or alternation;
synthetic provenance cannot become hardware evidence, even in all-idle captures.

## Threshold Derivation

For minimum valid signal $S_{min}$, false differential $F_{max}$ (including CM,
leakage/protection), offset $O_{max}$, noise $N_{max}$ and reference/buffer error
$R_{max}$, a conservative sufficient condition is:

$$
F_{max}+O_{max}+N_{max}+R_{max}<V_{TH}
<S_{min}-F_{max}-O_{max}-N_{max}-R_{max}-10\mathrm{mV}.
$$

| Contributor | Conditional model | Missing design bound |
| --- | --- | --- |
| Valid signal |N6 midcell87.9407 mV|Full source/receiver/PVT envelope|
| CM error |0.002274679 V/V x0.3 V =0.682404 mV|MHz CMRR/phase and actual C matrix|
| Offset |2 mV corner,0.3 mV nominal|Complete chosen circuit conditions|
| Noise |1 mV deterministic injection/allowance|Real bandwidth/reference/PCB noise|
| Reference |+/-1 mV error|Buffer/drift/leakage/sequencing|
| Leakage/temperature |1 Gohm assumed input|Actual component/PCB/PVT currents|
| Protection |0.1 pF assumed difference|Unequal-bias/PVT;0.01 pF ESD122 only at test point|
| Timing/startup |Finite receiver bandwidth, ideal delays|Physical pulse/skew/POR/recovery|

Conditional interval: **4.6824 mV < VTH <73.2583 mV**;20 mV is a simulation
value within it, not a released setting. The signal minimum already includes
model disturbances; subtracting allowances again is conservative. No RSS replaces
worst-case bounds; timing also requires minimum slew and dispersion bounds.
**FIXED_THRESHOLD_NOT_ESTABLISHED**: guaranteed interval/total remain null.

## Threshold Reference

Realizable local example, never on AUX:

```text
3.3 V --10k-- VTH+ --124R-- VMID --124R-- VTH- --10k-- GND
                            |
                 buffer -> post-receiver AC bias
```

Nominal threshold20.2094 mV;32 assumed0.1% resistor/0.5% reference corners give
20.0684..20.3509 mV. Buffer error, drift, noise, currents, leakage and sequencing
are missing; no guaranteed total. Illustrative10 nF/10 kohm output high-pass
gives100 us without uncontrolled per-leg input-C ratios. Output loading/recovery
still require review. These are candidate values, not released MPNs/BOM.

## Capacitance Model

Ground and mutual C are separately stamped:

$$i_P=G_Pv_P+C_{Pg}\frac{dv_P}{dt}+C_{PN}\frac{d(v_P-v_N)}{dt}.$$

Mutual C contributes twice its value to each balanced differential leg, not
two grounded capacitors in CM analysis. The true100-ohm differential sink stays.
Assumed stamps: receiver3 pF ground/2 pF mutual, protection0.25 pF ground/0.1 pF
mutual, PCB0.5 pF per leg. They are not a guaranteed datasheet Cin mapping.
Effective nominal load **7.95 pF** fails4 pF. N6 gives13.2 pF and0.35 pF
imbalance, outside fixed loading/balance limits despite decoding.

100-ohm branches with0.25 pF input/0.1 pF protection difference give external
CM gain0.000274717 at1 MHz (0.082415 mV at0.3 V), about0.002741 at10 MHz.
Approximately $|\Delta H|\simeq\omega R_{effective}|\Delta C|$, with125 ohms,
instead of the old sensitive divider. Conversion-only first-order allowance is
about6.37 pF at1 MHz/0.637 pF at10 MHz before intrinsic CMRR reservation.
The **independent0.1 pF physical imbalance criterion is unchanged**.

**MATCHING_ERROR_REMAINS_BLOCKING**: actual C maxima/tracking, AC CMRR and PCB
extraction absent.7.95 pF is this model, not a lower bound for all D3 receivers.

## Protection Matching

| Option | Disposition |
| --- | --- |
| P1 matched array |ESD122 supplies an actual limited-condition matching specification, not merely one package. |
| P2 separate low-C parts |Two0.23 pF maxima do not prove <=0.1 pF difference without proper matching/lower bounds, voltage and PCB effects. |
| P3 relocate/limit current |Post-buffer clamps cannot protect its first input; series R trades current against bandwidth/conversion. |
| P4 omit AUX TVS on bench |Only for reviewed, current-limited, externally protected **non-DP** B1/B2. Not live-DP release; model still7.5 pF without TVS. |

[ESD122 SLVSDP5A](https://www.ti.com/lit/ds/symlink/esd122.pdf), August2018,
sections6.4/6.6: bidirectional+/-3.6 V; at0 V/1 MHz/25 C, line C0.2 typ/0.27 max
pF, **channel difference0.01 pF max**, mutual0.1 typ/0.14 max pF. Leakage<=10 nA
at+/-2.5 V; TLP6.4 V at1 A/8.4 V at5 A are typical, not maximum overshoot.
ESD122DMXR ACTIVE, observedUSD0.182/1ku, stock behind login; ground1, channels2/3.

Do not extend equal-bias matching to AUX+ near0.3 V/AUX- near3 V over temperature.
The0.1 pF simulated difference is not an ESD122 spec. Conservatively reserving
0.27+2x0.14 pF for protection and0.5 pF PCB leaves **2.95 pF receiver allocation**;
full matrix measurement definitions still need confirmation. Receiver/PCB must
also fit the remaining0.1 pF balance budget. TPD2E2U06 is dual but unidirectional,
about1.5 pF typical, not a matching/off-negative solution by package symmetry.
Unavailable Nexperia URL establishes no absence. No ESD experiment performed.

## Powered-Off Design

**POWERED_OFF_BEHAVIOR_UNRESOLVED**. Powered high impedance, overvoltage survival
and output disable are different properties. N7 adds generic input rail/ground
clamps,1.1 uF off rail and1 Mohm discharge, starting at settled unpowered DC.
Under the assumed3.6 V CM step, rail reaches **2.54804 V**, sink-peak change
**327.439%**, failing0.1 V/1% targets. Peak injection **29.5353 mA** is transient,
not a sustained leakage measurement; do not compare it directly to the1 uA limit.

This is a clamped-input counterexample, not a selected-IC prediction. Powered
cases omit upper clamps by assumption; their zero injection is not qualification.
Receiver/reference/protection/comparator/isolator/backend paths need both power
orders, ramps, brownout and negative-input review. No DP_PWR, AUX bias or earth
lifting. Real00 silence also needs independent analogue-power validity evidence.

## Numerical Model

[Tool](../../tools/dp_aux_differential.py), [configuration](../../hardware/aux-observer/differential.json),
[tests](../../tests/test_dp_aux_differential.py): executed conditional model,
not SPICE, vendor transistor/ESD simulation or EDA. Old pivoted-LU RC/PWL solver
unchanged. Source50 ohms/leg, sink100 ohms differential,100 nF endpoint coupling,
100 kohm bias,0.3/3 V illustrative DC. Internal0.18 V differential peak is not
the published0.18 Vpp receiver minimum. Input voltage is solved; near-end voltage
drives requests, far-end current replies; ordinary CM0.3 V/1 MHz.

Receiver100-ohm branches/1 Gohm assumed input, gain1/20 MHz, intrinsic CM0.001,
illustrative output clip+/-4 V, then100 us high-pass. Slicer+/-20 mV,0.3 mV offset,
60 ns ideal delay, no invented hysteresis. N6:2 mV offset,1 mV reference/noise,
15 MHz, intrinsic CM0.002,8 pF input ground C/0.5 pF protection. These are finite
assumptions, not missing component guarantees replaced by bounds.

| Case | Test/result | Margin mV | CM bound V/V |
| --- | --- | ---: | ---: |
| N0 |No observer/loading reference, no decode required|n/a|n/a|
| N1 |Nominal request recovered|67.7725|0.001000000|
| N2 |0.25 pF input difference, recovered|67.7771|0.001196226|
| N3 |0.1 pF protection difference, recovered|67.7743|0.001078491|
| N4 |2 mV offset, recovered|66.0725|0.001000000|
| N5 |+1 mV reference, recovered|66.7725|0.001000000|
| N6 |Combined assumed corner, recovered; loading fails|64.9407|0.002274679|
| N7 |Off-clamp loading/rail fail, decode not required|n/a|Unqualified off-state|
| N8 |Maximum-length representative request recovered|67.7834|0.001000000|
| N9 |Reverse-end reply recovered|67.7834|0.001000000|
| N10 |Request,10 us turnaround, reply; continuous accepted transaction|67.7725 request|0.001000000|
| N11 |Idle, no assertions/packets|n/a|n/a|
| N12 |CM-only/mismatch, no assertion or false valid packet|n/a|0.001274717|

N2/N3 are declared sweep differences, not datasheet maxima. Fully bounded
production N6 is unavailable while critical terms are null; this conditional
case is not falsely called that missing qualification.5 ns integration/10 ns
ramps/20 ns sampling give20 ns added crossing error (constant delay removed),
0 ns sampled dispersion; nominal loading0.26749%, N6 0.34876%. Sampled zero is
not physical zero jitter.1/5 ns N1/N6/N7/N10 checks preserve decode/turnaround;
max sink-peak difference0.214093 mV, N1 margin difference0.001539 mV.

[model-v2 manifest](../../artifacts/probes/m5p10/model-v2/manifest.json) SHA256:
`bfea6aefc06468600a9e9e08a601f4c8d6e14f70123c57e1d208a27e9fe52633`.
[Hashes](../../artifacts/probes/m5p10/model-v2/hashes.json) SHA256:
`4bacfa861bf146245b3994723cf8deac14b676012ddc9fad214786111c9a258a`.
69 bound files:13 waveform/window/decoded triplets, five result/review files,
12 pipeline input/analysis pairs, manifest. All68 results exactly reproduce v1;
only source manifest changed after idle-validation hardening. Earlier hashes
remain historical. [Convergence receipt](../../artifacts/probes/m5p10/convergence.json):
`720603e621dd0be03d4bf7a259332732902a7af2a33dd57c6ebcf9622fc38d59`.

```sh
python3 tools/dp_aux_differential.py --output artifacts/probes/m5p10/reproduction-1
python3 -X dev -W error -m unittest discover -s tests -p test_dp_aux_differential.py -v
cmake --build build-m5p4-offline
ctest --test-dir build-m5p4-offline -L offline --output-on-failure
```

Output must be new/nonsymlinked. Eight offline CTests pass: **361+51=412 tests**.
CMake reconfigured/Ninja no native work. No native display binary/hardware test
or dependency install. Twelve longer pipeline runs explicitly use20 ns integration,
not falsely claimed5 ns numerical resolution.

## Legacy Comparison

| Metric | Legacy | New conditional model |
| --- | --- | --- |
| External error at0.3 V/1 MHz |14.210134 mV; perfect-R14.208158|0.082415 mV at stated0.35 pF mismatch, about172x lower|
| Combined CM |E8 0.0148107 fails|N6 0.002274679 bound passes|
| Matching |About0.0502 pF input difference with ideal coupling|Lower sensitivity; fixed0.1 pF balance and actual bounds unchanged|
| Margin |E1 17.103 mV/E8 1.165|N1 67.772/N6 64.941 after explicit threshold|
| Idle/nominal |Extra events/incomplete|N11/N12 quiet/nominal complete|
| Timing |Nominal edge mismatch/unresolved|20 ns sampled error, model only|
| Loading |Small caps trade matching/off loading|7.95 nominal/13.2 N6/7.5 no-TVS pF fail|
| Injection/protection |Positive fail-safe lead helps, negative/off open|2.548 V clamped witness; matched-array test-point data, whole budget open|
| Physical release |None|None|

Different topologies/matrices, not an identical-part hardware A/B test. Measurable
modeled improvement does not hide or resolve loading/range/off uncertainty.

## Decoder Pipeline

Numerical circuit -> raw two-bit window -> separate conservative adapter ->
unchanged AUX Manchester/native/I2C -> unchanged MST CRC/reassembly -> W1.
Sequence: coding/capability/enable/LINK_ADDRESS/allocation/slots/ACT-status.
RC/high-pass/comparator state persist across adjacent250 us windows with no DC
packet resets. Direction is declared synthetic stimulus, not measured by the tap.

| Profile | Completeness | Enable / payload IDs |
| --- | --- | --- |
| N1 nominal |COMPLETE_FOR_INTERVAL|Established/[1]|
| N2 input mismatch |COMPLETE_FOR_INTERVAL|Established/[1]|
| N3 protection mismatch |COMPLETE_FOR_INTERVAL|Established/[1]|
| N4 offset |COMPLETE_FOR_INTERVAL|Established/[1]|
| N5 reference |COMPLETE_FOR_INTERVAL|Established/[1]|
| N6 combined assumed corner |COMPLETE_FOR_INTERVAL|Established/[1]|
| N7 off |CAPTURE_INCOMPLETE|Unresolved/[]|
| Injected11 |CAPTURE_INCOMPLETE|Unresolved/[1]|
| Acquisition gap |CAPTURE_INCOMPLETE|Unresolved/[1]|
| Unknown direction |CAPTURE_INCOMPLETE|Unresolved/[]|
|40 ns channel skew |CAPTURE_INCOMPLETE|Unresolved/[]|
| Direct DC-biased slicing |CAPTURE_INCOMPLETE|Unresolved/[]|

**DIFFERENTIAL_FRONTEND_PIPELINE_PASS** is conditional/synthetic. Partial[1]
does not establish exclusivity. Running all consumers does not make every W1
question positive. No two sinks/payloads, actual main-link ACT, independent pixels
or source ownership inferred. No grammar/association/CRC/completeness relaxation.

```sh
python3 tools/dp_aux_differential.py --window-input artifacts/probes/m5p10/model-v2/pipeline-N1-window.json
```

## Nominal Completeness

**NOMINAL_CAPTURE_COMPLETENESS_RESOLVED** for the executed synthetic nominal
model. Legacy failure stays preserved. Success comes from conditioning/windowing,
not deleted errors. Compound P9-22 remains UNRESOLVED for a qualified physical
envelope; P10-26 is the separate nominal PASS. N12 is one declared CM stimulus,
not all transients. Startup,400/600 ns extremes, full PVT/noise and actual pulse
behavior remain component/bench work.

## Backend Requirements

| Requirement | Frozen contract |
| --- | --- |
| Signals/voltage |Two conditioned, one-way isolated3.3 V outputs; low<=0.4/high>=2.9 V at designed30 pF digital load/channel, never raw AUX|
| Sampling |Simultaneous shared clock>=50 MS/s/20 ns; parser10 MS/s floor is not this target|
| Index/clock |64-bit index or lossless equivalent; exact first/last/count/period; reference-qualify<=100 ppm (18 ms/180 s)|
| Polarity/states |Fixed positive CH0/negative CH1, all four states; no auto-inversion to rescue decode|
| Bench |Short complete generated-signal windows suffice for B1/B2|
| W1 |180 s pre-attach through stop; overflow/early-stop/no-discard receipts|
| Export |Raw unfiltered samples/transitions, clock/settings/versions/stop reason/hashes|
| Provenance |Direction and analogue power validity need separate qualified evidence|

Logical header POS,DGND,NEG,DGND,3V3_SENSE_ONLY,NC; no backend power/GPIO input.
It is an interface, not released footprint. Digital30 pF is not analogue4 pF.

## Backend Candidates

| Candidate | Primary evidence | Scope |
| --- | --- | --- |
| Saleae Logic8 | [Rates](https://www.saleae.com/support/logic-software/capturing-data/what-sample-rate-settings-are-available):100 MS/s <=3CH/50 <=6CH. [Comparison](https://www.saleae.com/logic):3.3 V level,1.8-5.5 V logic, CAD713 current. |Bench compatible on paper; actual revision/clock/load/export/180 s not validated. Older CAD710 stays historical.|
| Saleae Logic Pro8 | [Product](https://www.saleae.com/products/saleae-logic-pro-8):500 MS/s headline/USB3, CAD1427 in stock; comparison0.6-4.5 V thresholds/1.2-5.5 V logic. |Another compatible bench class, not no-loss W1 proof.|
| DSLogic U3Pro16 | [Manufacturer](https://www.dreamsourcelab.com/dslogic-u3pro16/):3.3 V,0-5 V threshold/0.1 V steps,250 kohm//about13 pF, USB3/2 Gbit buffer/16G stream claim,125 MS/s16CH/higher fewerCH, $299 in stock. |Operating-0.9..6 V differs from protected+/-30 V with leads; mode/clock/depth/export/loss still W1 work.|
| Glasgow revD/modest FPGA | [analyzer2](https://glasgow-embedded.org/en/applets/interface/analyzer2.html): DigitalFormat, clock, streaming, Overflow/Discard/Complete, supported libsigrok fork; revD pre-launch. |Prior42 MB/s architecture not exact host/format guarantee. No need for integrated FPGA to close frontend.|

Prior Saleae docs retain memory/backlog early-stop/loop-discard limits. USB5 Gbit/s
is not application throughput; MCU/USB-UART not presumed sufficient. No analyzer
queried/connected/bought/installed/controlled.

## Capture Compression

50 MS/s x2 packed bits: **12.5 MB/s,2.25 GB/180 s** before metadata. Byte/sample:
50 MB/s,9 GB. Nine billion sample indices exceed32 bits. At400 ns half-cells,
polarity can change2.5 million/s; window deassert/assert can make **5M events/s**.
An8-byte62-bit-index/2-bit-state event needs **40 MB/s,7.2 GB/180 s**, worse than
packed raw. Separate channel8-byte records have the same worst protocol count.
Noisy every-sample changes reach400 MB/s/72 GB in that format: adequate raw
fallback or explicit overflow required, never dropped glitches. Three packed
channels with health signal need18.75 MB/s/3.375 GB. No average-activity assumption.

## Backend Selection

**BACKEND_INTERFACE_REQUIREMENTS_FROZEN**. Multiple analyzers can accept two3.3 V
outputs at bench rates; no exact final W1 unit or embedded FPGA is prerequisite.
P8-12 exact-unit and P8-13 duration/loss remain UNRESOLVED for W1; P10-27 passes
the standard interface. Neither old row disappears or silently passes.

## Modular Architecture

**MODULAR_FRONTEND_BACKEND_PREFERRED**.

```text
Generated B1/B2 fixture (no DP)
 -> high-Z receiver [part/limits unresolved]
 -> single post-difference DC removal/local reference
 -> positive/negative comparators -> one-way isolation
 -> POS/NEG/DGND header -> qualified ordinary analyzer
```

Future DP pass-through/main-link/HPD review is separate. No AUX transmitter,
pull-up/termination, HPD emulator, DPCD responder or DisplayLink. Scope/charger
must not bypass isolation; never lift earth. Diagram is not a built circuit.

## Schematic

**Construction schematic released: no.** Conditional frontend gate has not passed.
No placeholder receiver or invented ERC/DRC. Old analysis SPICE stays unchanged.
Editable numerical stamps are not fabrication EDA; release needs actual receiver,
power/reference/buffer, comparator, protection/P4 fixture, isolator, decoupling,
pin states/connectors/footprints and construction review.

## Frontend BOM

**Frontend build BOM released: no.** Tables are qualification evidence, not orders.
Analogue C/off/reference/layout/timing blocks it, not missing exact W1 backend.
A frontend-only BOM may exclude final analyzer/computer/live-DP board but still
needs real MPN/package/quantity/power/sequencing/output/isolation/bench fixture,
dated stock/one-unit price and qualified substitutes. No cost fabricated from
1ku/family prices. Nothing purchased or assembled.

## PCB Feasibility

A small non-DP board/header is a feasible class, not parasitic qualification.
Pads/traces/protection/returns require C matrix/leakage/matching budget; separate
digital edges and account for probes/fixture loading, including weak DC bias.
A normal10x probe can exceed the entire C budget. Later live-DP routing retains
100-ohm through pairs, short symmetric AUX branches, no main-link test stubs or
extra termination, reviewed grounds/shield and no automatic DP_PWR. Connectors,
stackup/launch/loss/skew remain W1-only for a non-DP B1/B2 prototype.

## Review Matrix

All22 old rows remain in order with exact original requirement text in
[computed review](../../artifacts/probes/m5p10/model-v2/review.json); names below
abbreviated. F: frontend-critical; W: eventual W1-only for non-DP B1/B2.

| ID | Requirement | M5P9 | M5P10 | Scope/disposition |
| --- | --- | --- | --- | --- |
| P8-01 |Envelope|PASS|PASS|F: location-qualified evidence|
| P8-02 |Instantaneous range|UNRESOLVED|UNRESOLVED|F: actual envelope missing|
| P8-03 |DC/leakage|UNRESOLVED|UNRESOLVED|F:1 Gohm assumed|
| P8-04 |Maximum C|UNRESOLVED|UNRESOLVED|F:actual matrix open; witness fail P10-30|
| P8-05 |Matching|FAIL|UNRESOLVED|F:old divider rejected; real C/CMRR open|
| P8-06 |Off transparency|UNRESOLVED|UNRESOLVED|F:clamp witness fails|
| P8-07 |Protection|UNRESOLVED|UNRESOLVED|W:live-DP; critical P4 counterpart P10-28|
| P8-08 |No drive|PASS|PASS|F:local thresholds/forward boundary|
| P8-09 |Main-link PCB|UNRESOLVED|UNRESOLVED|W:no DP in bench module|
| P8-10 |Parasitics|UNRESOLVED|UNRESOLVED|F:bench extraction still needed|
| P8-11 |Ground/reference|PASS|PASS|F:strategy not implementation certificate|
| P8-12 |Exact backend|UNRESOLVED|UNRESOLVED|W:standard interface PASS separately|
| P8-13 |Overflow/180 s|UNRESOLVED|UNRESOLVED|W:not short B1/B2 requirement|
| P8-14 |B1/B2 plan|PASS|PASS|F:frozen criteria, future M5P11|
| P8-15 |Regressions|PASS|PASS|F:361old+51new|
| P8-16 |Model/construction|UNRESOLVED|UNRESOLVED|F:model PASS/construction open|
| P9-17 |Comparator|UNRESOLVED|UNRESOLVED|F:no qualified complete chain|
| P9-18 |Budget|UNRESOLVED|UNRESOLVED|F:missing bounds null|
| P9-19 |Schematic|UNRESOLVED|UNRESOLVED|F:withheld|
| P9-20 |Actual BOM|UNRESOLVED|UNRESOLVED|F:analogue parts open, not W1 equipment|
| P9-21 |Numerical execution|PASS|PASS|F:scenarios/convergence/receipts|
| P9-22 |Qualified-envelope decode|FAIL|UNRESOLVED|F:model passes, physical bounds open|
| P10-23 |D1-D5 discrimination|New|PASS|F:DC/bandwidth/loading|
| P10-24 |Threshold/reference|New|UNRESOLVED|F:local ladder, complete bound open|
| P10-25 |Window adapter|New|PASS|F:raw/errors/loss/provenance|
| P10-26 |Nominal completeness|New|PASS|F:continuous synthetic model|
| P10-27 |Modular interface|New|PASS|F:2CH3.3 V/>=50 MS/s|
| P10-28 |P4 bench safety|New|UNRESOLVED|F:exact input/current/power fixture open|
| P10-29 |PVT/skew/startup|New|UNRESOLVED|F:40 ns counterexample/device bounds open|
| P10-30 |Model loading|New|FAIL|F:7.95/7.5 pF above4 pF|

**10 PASS/1 FAIL/19 UNRESOLVED**, total30.26 frontend-critical:10 PASS,1 FAIL,
15 UNRESOLVED. All30 eventually matter to W1. Only P8-07/09/12/13 re-scoped,
not passed; every former FAIL/UNRESOLVED disposition explicit. P8-16/P9-22 are
not promoted because one numerical subproblem passed.

## Frontend Prototype Gate

**AUX_FRONTEND_PROTOTYPE_STILL_BLOCKED**; no schematic/BOM. Standard digital
compatibility is sufficient for backend portion, exact W1 recorder not blocker.
Remaining: P8-02/03/04/05/06/10/16, P9-17/18/19/20/22, P10-24/28/29/30.
Decisive issue: **qualified low-C, DC-tolerant differential input cell with bounded
unpowered behavior**. Threshold tuning/precision R cannot cure loading/off failure.

Next smallest task: offline qualify/falsify one low-C buffered input cell using
LTC6268-class or equally documented alternative. First establish full C matrix
within2.95 pF receiver allocation and signed-input unpowered current/clamp bounds;
reject immediately if either fails. Do not design around a typical450 fF headline.
No protocol rewrite, purchase or outreach dependency is needed for this task.

Only after all F rows pass could separately authorized
**M5P11_BENCH_FRONTEND_BUILD_AND_B1_B2** occur. B1: no DP, reviewed generated
source/impedance/weak bias,400/500/600 ns cells, idle/CM/turnaround/loading/raw
decode. B2: both power orders/ramps/brownout/rail currents with reviewed low-energy
limits. Frozen-limit failure stops progression; B1/B2 never authorize live DP/M5.

## W1 Capture Gate

**W1_CAPTURE_SYSTEM_NOT_READY** independently. W1 needs qualified live-DP tap/
protection, direction/power validity, exact clock,180 s worst-activity storage/
export/overflow/stop, known initial state and fresh controlled generation.
Extra health channels require budget; two states alone cannot identify transmitter.
Even complete AUX topology/allocation/ACT-status does not prove main-link packets,
independent pixels or ownership of one T8142 DPTX. Historical M5P4 count2 and
M5P3 SinkCount1 remain unbound, not retroactively correlated here.

## Physical-State Policy

**CURRENT_HUB_STATE_NOT_REQUIRED**. No current topology query, purchase, assembly,
capture, AUX/DPCD, Mac display interaction, hub manipulation, private helper or
outreach. Four drafts remain unsent; no sibling m1n1 access or security change.
Preserve **RETIRED_ON_DAILY_USE_M5**, **NOT_READY_FOR_DPCD_TEST**,
**STATIC_PACKETIZER_ANALYSIS_FROZEN**,
**NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED**,
**OFFLINE_OBSERVER_PIPELINE_READY**. Numerical success is not hardware approval.

Publish only this branch after verification; no merge/PR/tag/force-push/rewrite.
Old reports,518prior ledger/source rows, raw captures/M2F markers remain intact;
M2G DPCD-attempt marker absent. New raw/downloads ignored. Coordination additions
supersede old future-build labels without changing their historical meaning.