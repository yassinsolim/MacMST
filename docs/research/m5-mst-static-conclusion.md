# M3E0: Static Ceiling Integration And Experimental Handoff

## Executive Result

**MACMST_STATIC_FEASIBILITY_INCONCLUSIVE**.

Identified J704AP/T8142 production DCP firmware contains real MST control and
source packetizer machinery. The completed static program establishes neither
two independently timed streams on one physical M5 DPTX nor a global single-stream
architectural limit. Architectural viability remains unresolved.

M3E0 integrates completed M3D and freezes its results. It does not repeat M3D,
restart from M3C, add reverse engineering or implement an experiment.

**STATIC_PACKETIZER_ANALYSIS_FROZEN**.
**NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED**.

The recommended new evidence source is **SACRIFICIAL_DYNAMIC_EXPERIMENT**,
conceptually assessed only. It requires a separate non-daily-use environment,
an independently reviewed observation method and new explicit risk approval.
No such experiment is implemented or executed in this milestone.

## Static Program Scope

The frozen target is Apple M5, Mac17,2/J704AP, CPID0x8142/BDID0x22,
macOS26.6.2 build25G83, with the production DCP component selected by Apple's
BuildManifest. This is a firmware/build association, not independent attestation
of the bytes currently executing on the machine. Results from older SoCs are
not substituted for M5 evidence.

| Completed Milestone | Established Scope | Frozen Source |
| --- | --- | --- |
| M3A | Bounded host-side search did not qualify host MST codec/topology/allocation machinery; firmware remained opaque | [M3A report](m5-mst-source-feasibility.md), branch19cc4e33799a3dff5a0393687b75b22a2bb036b1 |
| M3B | Identified production T8142 firmware contains MST control, codec and topology machinery | [M3B report](m5-dcp-firmware-mst.md), branch2a2f27a373b8e52495788a767f0e5de318ed0420 |
| M3C | Concrete source payload-table programming and hardware-facing activation, without independent stream binding proof | [M3C report](m5-dcp-mst-packetizer.md), branch60eec80b622b3788e83b0df78ab4eab2c65c8804 |
| M3D | Final ownership pass did not distinguish multi-stream ownership from a positive architectural one-stream limit; static expansion stopped | [M3D decision](m5-dcp-stream-ownership.md#stream-ownership-result-and-viability), branchad601949c3d7bf15eff217ebde8d785269dc7b8e |

M3A's negative result remains host-scoped. M3B's positive firmware findings are
not weakened by M3D's unresolved ownership result. Multiple physical outputs,
downstream topology ports, compositor planes, DSC structures, register banks
or sequential reconfiguration do not establish two independent same-link sources.

### Actual State Reconciliation

The actual starting branch was research/m5-dcp-stream-ownership at
**ad601949c3d7bf15eff217ebde8d785269dc7b8e**. Its origin branch and configured
upstream matched, divergence was0/0, and the worktree was clean. Main and
origin/main were **5beb1ac304a1715dc9fb7cad9b3322819b8fd140**. The v0.9 tag
object **4b8cf98419fa4678d931ad014ba16c306c2f722d** still peeled to that main.
All33 then-existing remote head/tag/peeled identities matched the local refs.
No M3E0 tag, branch or conclusion document existed, locally or remotely.
No legitimate advance needed preservation and no rewind or recovery was needed.

The two completed M3D commits, **54af4693a2fb4a2d395a6920840627550fcd8094** and
**ad601949c3d7bf15eff217ebde8d785269dc7b8e**, were audited across all seven changed
text paths. The only executable-source change was exact-output-root confinement
and its synthetic test; no private experiment was added. M3D records zero
hardware/private display operations. The unchanged commits, markers and retained
receipts corroborate that recorded scope; Git alone is not an execution monitor.

### Permanent Integration

M3D was not already merged. Authorized --no-ff merge
**c5bc1b1bacd7742a4bbc1b54285336e9d51302a5** has parents
5beb1ac304a1715dc9fb7cad9b3322819b8fd140 and
ad601949c3d7bf15eff217ebde8d785269dc7b8e. Its tree exactly equals M3D, with a
clean worktree and no unrelated changes. Message:
`merge: record final M5 stream-ownership static investigation`.
Main was pushed and verified before the handoff work.

Permanent annotated tag **m5-mst-static-ceiling-v1.0** has object
**08234296452af2f9d5056cfc743e79801cef92e9** and peels to that merge. Its message is:

> MacMST static investigation complete: T8142 MST control and source packetizer established; same-link independent stream ownership remains unresolved.

The tag was pushed and remotely verified. Research/m5-mst-static-conclusion
was then created from it. This branch contains conclusion/status documentation
only and is not to be merged or turned into a PR by M3E0. Historical tags and
branches remain intact; the ceiling tag must not be moved or recreated.

## What Was Proven

**VERIFIED / STRONG STATIC EVIDENCE**, in the identified production firmware:

| Established Machinery | Frozen Evidence | Qualification |
| --- | --- | --- |
| MST manager and MST port abstraction | [M3B topology model](m5-dcp-firmware-mst.md#topology-model); E188; [M3C layouts](m5-dcp-mst-packetizer.md#recovered-object-layouts) | Concrete object/control evidence, not only matching names |
| MSTM capability/control handling | [M3B payload and ACT](m5-dcp-firmware-mst.md#payload-and-act); E189 | Capability/mode control exists; control availability is not proof of multiple display streams |
| Sideband message processing, routed parsing and CRC handling | [M3B sideband codec](m5-dcp-firmware-mst.md#sideband-codec); E187 | Structural routed-message/CRC implementation was qualified in M3B; no new protocol analysis here |
| MST topology concepts and path-resource handling | [M3B topology model](m5-dcp-firmware-mst.md#topology-model); E188 | Branch/port/route relationships and resource handling are established |
| PBN-related logic | [M3B payload and ACT](m5-dcp-firmware-mst.md#payload-and-act); E189/E201 | Bandwidth calculation/serialization exists; complete multi-source allocation policy is not proved |
| Source payload-table programming and hardware-facing DPTX payload writes | [M3C hardware-facing binding](m5-dcp-mst-packetizer.md#hardware-facing-binding); E195/E197/E198 | Source table updates reach a concrete DPTX register owner |
| ACT-like source activation behavior | [M3C ACT and completion](m5-dcp-mst-packetizer.md#act-and-completion); E197/E202 | Concrete source trigger is established; set-wide completion and multi-stream runtime success are not |

These are positive implementation findings. They remain valid despite the
unresolved project-level feasibility result. Static existence is not an
end-to-end native MST display demonstration.

## What Was Locally Observed

The completed [M3C component results](m5-dcp-mst-packetizer.md#component-results)
and [M3D ownership findings](m5-dcp-stream-ownership.md#selected-device-and-timing-ownership)
establish the following within the inspected paths:

- The selected-device pointer is scalar in the inspected controller.
- Selected-device state uses local replacement/clear semantics.
- The current timing cache is scalar locally.
- One qualified source descriptor returns payload ID1.
- One inspected table-update invocation programs one source entry, clearing
  sixteen slot words before repopulation in that path.

**These facts do NOT prove that the complete T8142 DPTX architecture is
single-stream.** A local field or one implementation cannot establish the
cardinality of all source controllers associated with a physical transmitter.
Sequential timing changes do not prove simultaneous independent timing either.

## What Was Not Proven

- One controller per physical DPTX.
- Multiple controllers per physical DPTX.
- A second independent timing generator on the same physical DPTX.
- Multiple simultaneous source streams on that transmitter.
- Distinct simultaneous source payload IDs on that transmitter.
- A stream-to-payload source selector.
- Two independently timed streams on one physical DPTX.

The frozen [eleven-row M3D map](m5-dcp-stream-ownership.md#ownership-evidence-map)
contains the precise local qualifications. Neither a multi-stream capability
claim nor an architectural impossibility claim follows. Owner-reported panel
mirroring and one logical external display do not decide either question.

## Exact Remaining Opacity

**Runtime source-controller membership of one physical T8142 DPTX register owner.**

Possible runtime model A:

```text
DPTX0
`-- Source Controller A
```

Possible runtime model B:

```text
DPTX0
|-- Source Controller A
`-- Source Controller B
```

In model B, A and B could potentially own independent timing state. That is a
hypothesis, not an observed topology or an assertion that the firmware supports
this model. Static firmware evidence did not distinguish the two models.
This boundary is frozen. No further static task is created to distinguish them.

## Why Static Analysis Stops Here

M3D was the final planned ownership pass. Its unresolved outcome is a ceiling
of the completed evidence program, not a proof of absent silicon capability.
Repeating searches, reconstructing additional object graphs or reinterpreting
the same scalar findings would not constitute the genuinely new evidence
required by this handoff.

**STATIC_PACKETIZER_ANALYSIS_FROZEN**.
**NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED**.

M3E0 performs no T8142 call-graph, boundary, vtable, cardinality, payload-ID,
timing-generator, packetizer or selector search; no M4 differential, sideband
or DPCD analysis; and no scanner, disassembler or firmware replay. Historical
reproduction commands are evidence provenance, not authorization to resume
that work. No M3E firmware-graph milestone or M4A host-command discovery is
proposed. New evidence must come from one of the four categories below.

## Safety History

The historical M2F recovery experiment performed exactly one explicitly
authorized DPDV open/immediate-close and zero selectors. An earlier recovery
followed a watchdog panic whose cause was not established; neither the panic
nor the successful open proves safe in-flight reads. M2G-M2I did not establish
bounded completion/quiescence for the selector path, and it was retired on
the daily-use M5. See [the historical runtime record](dpdv-open-check.md#recovery-and-renewed-authorization)
and [the final selector decision](w06-wake-or-strand.md).

M3A-M3D did not revive that transport. M3D's documented zero-operation scope is
preserved, not repeated. M3E0 performs zero private display/user-client calls,
DPDV opens, selectors, IOConnectCallMethod invocations, DPCD/AUX/MST transactions,
firmware execution/loading/patching, display-link changes or security changes.
No recommended future experiment is executed. The only current-system checks
beyond Git/files are the bounded public property-name/log reads described below.

### Integrity Checks

The following retained files were checked by SHA-256 only. No firmware decoder,
scanner, replay or disassembly was run. These checks preserve evidence; they
do not add hardware-functionality evidence.

| Retained Artifact | SHA-256 |
| --- | --- |
| M2F-ATTEMPTED | 2f3da1f224c0602dc46f812d3f6eb2c1560fe7a82c1a89f93eedb725b2726efc |
| Successful M2F result | 86ee9fdd87eb631e7552b0087471a149c183667c2162e838866ce993e1dd3d04 |
| Stopped M2F result | 79387346acdaebed1efb2284a531de8f2cf5aad1d64915a3f5f527040ebae840 |
| M3D ownership-final receipt | 15c7c3540072bfa087ba297749b72c347a445cbc35e5c8e83ac1b7fbb740b17f |
| M3D timing-final receipt | 62b8f579283a9159ce417491c900548a9d8b8e3ed96fbcacd4d9be92ab039baf |
| M3C source-final receipt | 4f2487e9529ab2ececb9c522fc5ebb61bbdb147a9a95e64d725cd914bd703876 |
| M3C ownership-verified receipt | e12f3103e707b89960ee0868f002e948fd46f8dc0be65cd6d39fd23d820ca7c7 |
| Retained T8142 raw IM4P | 3f1424dbd80664128041bff2585e09bcf7fed9a75ac38e6c5a273f0b6494f219 |
| Retained decoded T8142 payload | 9c4d1b86ecbc897109235fabf6dbf0d83330e1e0f2f76ccd135484e708fefb7c |
| Retained BuildManifest | e8ff2cdd3e8ab3a668132bf9453948b70f1863b849a6185914f54a9ec25356d3 |
| Retained J704AP DeviceTree IM4P | 13f4dce18ca0936616c71eb9ccbb18ad791bcc01d06d287405d5cd0b4dc2c962 |
| Frozen protocol oracle | ba7b651e9bf9d73043abc9176f6f74f464e702772dc7c7a99a63c8e43a3e3073 |

M2F-ATTEMPTED remains consumed. M2G-DPCD-READ-ATTEMPTED is absent. No marker
was created, reset or deleted. Raw paths and prior provenance remain in the
historical reports; retained firmware and captures stay ignored, not published.

### Handoff Validation

Only this conclusion and the current root/research README, open questions and
append-only evidence ledger change on the handoff branch: five documentation
files, no code, tests, configuration or raw artifacts. The audited integration
contains the already completed M3D tree, not newly performed analysis.

| Required Check | Result |
| --- | --- |
| Actual Git reconciliation and M3D commit audit | PASS; exact completed branch/HEAD/upstream, clean0/0, two expected commits; no partial handoff or rewind |
| M3D merge and ceiling tag | PASS; required parents, exact M3D tree, annotated tag message/object/peeled commit; main and tag verified remotely |
| Document structure and decisions | PASS; exactly14 required sections, four evidence categories, one recommendation, A-E unmet, exact opacity and six final states |
| Local links, anchors and fences | PASS across all five changed documents |
| Ledger continuity/preservation | PASS; E001-E215/S01-S69 byte-preserved; append E216-E224/S70-S73 |
| Frozen M3A-M3D reports | PASS; byte-identical to integrated M3D and recorded SHA-256 values below |
| Retained artifact and marker hashes | PASS; all12 values in the integrity table match; DPCD-read marker absent |
| Protected refs | PASS before conclusion publication; all35 head/tag/peeled identities match, including the permanent ceiling and every historical branch/tag |
| Git scope, whitespace and editor diagnostics | PASS; documentation-only change set, no whitespace errors or reported diagnostics |

Frozen report SHA-256 values are:

| Report | SHA-256 |
| --- | --- |
| M3A | 4ba9ba55ec0290c73ba4811179fac8a6b7c9c2de1a4dcc994259763c478ededc |
| M3B | 6cb9adf8a4c642c82bd50f6c52eb2687fd1bae8d1280881a391addcb3090e9a2 |
| M3C | 556a2ebe964536a6b088fe0a800f24f2cd268cbd11c990796bec35930f020adb |
| M3D | a70fe18a63601c52e26c32437ec67648a8f4a45103f324fc0fe9e57b203f3575 |

No builds or unit suites were rerun for this documentation-only milestone;
their prior results remain in M3D. No firmware tool was imported/executed and
no retained disassembly was opened for new analysis. Final conclusion commit,
clean-tree and upstream identities are reported after the branch-only non-force
push with push.followTags=false, without claiming this document's future hash.
The conclusion branch is not merged; no PR or branch deletion is requested.

## New Evidence Sources

Exactly four categories are evaluated. B and C are conceptual capability/risk
assessments, not findings that an observation system is already available.
No acquisition, experiment implementation or new external source survey occurs.

### A - Passive Runtime Observability

**NO_PASSIVE_RUNTIME_DISCRIMINATOR_IDENTIFIED**.

The retained [M3A public observation](m5-mst-source-feasibility.md#public-m5-observation)
covered public display reports and names on DP device/service proxies, remote
ports, transport state and framebuffer shims. It identified no source-stream
count, payload-ID or equivalent source-membership discriminator. Logical display
counts and proxy object counts are not firmware source-controller counts.

A narrow public read-only M3E0 check at **2026-09-14T08:32:44Z** used
`ioreg -a -r -c CLASS -d 1`, without opening a user client or changing displays:

| Class / Surface | Command Result | Bounded Observation |
| --- | --- | --- |
| AppleDCPDPTXProxy | Exit0, empty stdout, no parseable plist | No usable record; not proof of zero controllers |
| DCPDPDeviceProxy | Exit0,2 root records,24 unique top-level property names | No candidate ownership/payload/context-count property name |
| DCPDPServiceProxy | Exit0,2 root records,21 unique top-level property names | No candidate ownership/payload/context-count property name |
| Existing unified logs | Exit0,4 emitted records in fixed ten-minute window | No candidate ownership/payload/context-count message identified by the bounded filter |

The log query used `log show --style ndjson` from local
2026-09-14 02:22:44 to02:32:44, UTC offset-06:00, restricted to kernel or
WindowServer messages containing DPTX or DCPDP. It neither enabled debug logging
nor requested firmware telemetry. Candidate screening covered payload-ID, VCPI,
stream/timing context or count, and source/controller owner or membership terms.
Only aggregate results/property names were processed for reporting; raw property
values and messages are not reproduced. Capture stdout digests were:

- Device proxies: `80c436e1c51d6472176ed68920fc5b9c98ee69cfb495e17b2caed4778e5efbce`.
- Service proxies: `aa68f97984adb5bdf7c6f921882e361b38df3e7fa0851bf9f33534f6b808d2c3`.
- Log window: `a4a76b0f5204817d6f2b9df15643ccded1d5acae2c4994934930e5efa91d568f`.

These are transient stdout identities, not archived raw captures or a promise of
byte-identical later output. This is a bounded negative identification result,
not an exhaustive telemetry audit: private/redacted/unemitted fields, differently
named records and unobserved events may exist. A compiled firmware log string
does not establish an already exported public runtime surface. No normal report
or existing public telemetry schema examined here maps all source controllers,
their timings or payload IDs to one physical DPTX.

A qualifying passive discriminator would need stable transmitter identity plus
explicit source membership/count and independently attributable timing/payload
state. Merely seeing two registry objects, two panels, two external DCP engines
or several messages would not qualify. No such discriminator is invented or
recommended on safety grounds alone.

### B - External Physical Protocol Observation

**EXTERNAL_PROTOCOL_OBSERVATION_CAN_RESOLVE_RUNTIME_MST_STATE**.

A suitably capable passive observation of the physical DP link could show what
is actually emitted: MSTM control changes, existing sideband exchange/branch
enumeration, ALLOCATE_PAYLOAD and payload identities, ACT signaling, and VC
payload traffic. Full-link main-stream decoding, not AUX-only visibility, is
needed to establish simultaneous independently packetized streams and their
timings. A control message or allocated ID alone does not prove active video.
These are conceptual observable facts, not a new sideband/DPCD analysis.

Passive observation cannot make the host request a second stream and cannot
reveal the count of internal firmware controller objects. If the host emits only
one source in ordinary use, that trace does not decide whether another source
could coexist. Positive simultaneous traffic on distinct VCs, with independent
timing on the same M5-originated physical link and no second-link/tunnel ambiguity,
would satisfy resume gate E even without revealing internal object layout.

To elicit such a positive trace when none exists, the host would first have to
attempt a second stream. That is a separate action requiring a separate risk
decision, not part of passive observation or M3E0 authorization. Installing an
inline observer may itself require physical reconnection and can affect signal
integrity; no installation, display change, purchase or specific hardware
recommendation is made here. This category can resolve observed wire state,
not necessarily the exact frozen software-ownership boundary.

### C - Sacrificial Dynamic Software Experiment

**SACRIFICIAL_DYNAMIC_EXPERIMENT_COULD_RESOLVE**.

On a separately provisioned, non-daily-use M5-class system, a validated dynamic
observation mechanism could correlate runtime source-controller creation,
attachment and lifetime with one physical DPTX register owner, then distinguish
independent timing and payload bindings from replacement. Correlated existing
firmware telemetry or host-to-DCP IPC traces could additionally show whether a
second source is requested and represented. This is the most direct potential
evidence for the frozen membership boundary.

No working instrumentation route is asserted. Access to the required runtime
events, correct physical-instance attribution, complete coverage and acceptable
observer effects must first be established outside the current machine. An
equivalent environment must match or justify applicability to the M5 SoC,
firmware/build and ownership path; a different chip's behavior is not a substitute.
Two simultaneous, independently timed same-owner contexts would be positive
evidence. A trace showing only one context during one scenario is not a universal
single-stream limit.

Evidence quality is conditional on timestamped identities, unmodified raw event
provenance, reproducible scenarios and checks for missed events. Risks include
crashes, hangs, data loss, misleading instrumentation and device recovery. A
sacrificial system separates those risks from the user's daily-use M5; it does
not make the experiment inherently safe. No implementation, instrumentation
code, debugger attachment, firmware command or security weakening is provided
or performed. A new explicit risk decision and a concrete reviewed method are
prerequisites, not permission implied by this handoff.

### D - Future Independent Research

Potential new sources include Asahi M5 display/DCP enablement, new m1n1 tracing,
future Apple source/documentation releases, newer firmware with genuinely exported
diagnostics, and independently reproduced DCP research. None is claimed to have
resolved this question, and no new static analysis of the retained T8142 image
is proposed under this category.

Evidence would count only when it is M5-attributed and reproducible: a trace or
supported runtime/API contract establishing two independent source contexts or
timing generators on one transmitter, two simultaneous source payload bindings,
an explicit same-link multi-stream-index/mapping API, or physical evidence of
independently packetized simultaneous VCs. A positive architectural impossibility
decision would instead require an applicable documented source/feed maximum or
equivalent complete ownership constraint, not silence in a trace.

Release notes saying MST, generic symbol names, multi-display support on separate
links, older-chip results and diagnostics that are only present in binary text
are insufficient. A newer-firmware finding must state its version and scope;
it does not retroactively prove behavior of25G83. Waiting has low direct risk/cost
but uncertain timing, availability and relevance.

## Evidence-Source Ranking

Rank expresses usefulness for answering this handoff's question, with daily-use
safety, feasibility, cost and reproducibility explicit. It is not authorization.

| Rank | Source | Safety | Evidentiary Value | Reproducibility | Cost | Resolves Exact Opacity? |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | C. Sacrificial dynamic | No current-machine exposure if isolated; potentially high risk on test system | Direct membership/lifetime/timing attribution if suitable instrumentation exists | Conditional on supported access, complete trace and matched build | High setup, machine and engineering cost | Potentially yes; route not yet established |
| 2 | D. Future independent research | No current-machine experiment | Potentially decisive M5-specific independent evidence | Depends on released artifacts/method; timing unknown | Low direct cost, unbounded waiting | Only if it supplies the explicit observation/contract above |
| 3 | B. External protocol observation | Read-only observer concept; installation/reconnection not authorized here | Strong positive wire-state proof, including gate E if multi-VC traffic occurs | Good with complete calibrated traces; second-stream stimulus may be missing | Potentially high access/setup cost | No direct internal membership count; positive wire evidence can bypass that need |
| 4 | A. Passive runtime | Lowest risk within existing public read-only surfaces | Current bounded check identified no discriminator | Queries repeatable; emission/retention/redaction vary | Low | Not with any surface identified here |

## Recommended Next Evidence Source

**SACRIFICIAL_DYNAMIC_EXPERIMENT**.

This is the single recommendation because a runtime trace on a separately
approved non-daily-use, M5-applicable system could answer source membership
directly. Passive surfaces currently offer no qualified discriminator; external
wire observation cannot induce a missing second-stream request or enumerate
internal controllers; future independent research has no predictable delivery.

The cost and risk are substantial and the observation route is unproven. Before
any future execution, require a concrete risk-reviewed method, suitable isolated
machine/recovery arrangements, privacy/provenance plan and fresh explicit user
approval. If those prerequisites cannot be met, the project stays frozen; this
document does not authorize a fallback private experiment on the current M5.
No recommended experiment, equipment acquisition or implementation occurs now.

## Daily-Use M5 Policy

**RETIRED_ON_DAILY_USE_M5** is permanent for selector0 on this machine.
**NOT_READY_FOR_DPCD_TEST** remains unchanged.

Allowed within ordinary use and the frozen scope:

- Ordinary display use.
- Public read-only system inspection.
- Passive reading of already emitted public logs/telemetry.
- Offline integrity checks and evidence summaries of already-retained artifacts;
  this does not override the frozen T8142 reverse-engineering scope.
- Normal Git and documentation work.

Not authorized by this handoff or routine development, and requiring a new
explicit risk decision for any reconsideration:

- DPDV selector0 or DPCD read experiments. The current-machine selector retirement
  is not reopened by the recommendation of a separate sacrificial environment.
- Arbitrary private IOKit display calls or new DCP commands.
- Firmware patching or loading.
- Kernel memory modification or kernel debugger attachment.
- SIP or AMFI weakening.
- NVRAM/boot-argument experimentation.
- Active MST payload manipulation or experimental display-link reconfiguration.

There is no firmware/system-security modification, state-changing hardware
experiment or private command submission in M3E0.

## Implementation Resume Gate

At least one of the following must be positively established before MacMST
implementation work resumes. FAIL below means the evidentiary gate is not met,
not that the hardware capability has been disproved.

| Gate | Required New Evidence | Current State |
| --- | --- | --- |
| A | Two independent source contexts attached to one physical DPTX | FAIL - not established |
| B | Two independent timing generators attached to one physical DPTX | FAIL - not established |
| C | Two simultaneous source payload bindings on one physical DPTX | FAIL - not established |
| D | An Apple host-to-DCP API explicitly accepting stream index/payload mapping that supports more than one stream on one physical DPTX | FAIL - not established |
| E | External physical observation of multiple independently packetized VCs/streams emitted by one M5 DPTX | FAIL - not observed |

Every gate requires physical-instance attribution and evidence distinguishing
independence/concurrency from sequential replacement or separate links.
Existing static evidence satisfies none. Passing a gate would permit a separately
scoped implementation decision, not automatically authorize hardware operations
or revive the retired selector.

## Final Project State

```text
MACMST_STATIC_FEASIBILITY_INCONCLUSIVE
MACMST_ARCHITECTURAL_VIABILITY_UNRESOLVED
M5_DCP_STREAM_OWNERSHIP_UNRESOLVED
M5_DCP_MST_PACKETIZER_PRESENT_BUT_STREAM_BINDING_UNRESOLVED
RETIRED_ON_DAILY_USE_M5
NOT_READY_FOR_DPCD_TEST
```