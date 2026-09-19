# MacMST Phase 0 / Milestone 1

## Scope

Establish a reproducible, read-only baseline of this M5 host, its macOS display
services, and the attached USB-C dock. Do not attempt to enable MST. Neither
source MST hardware nor its absence is established.

## Results And Navigation

Milestone 1's internal-only captures remain below as history. Milestone 2A now
has a controlled ZMUIPNG hub connected/disconnected/reconnected cycle and an
External DCPEXT0 path. The updated probe reports actual graph neighbors and
conservative candidate pairs. ABI-02 now resolves CF cleanup, authenticated
caller bindings and the concrete DPDV/selector-0 host path. It reaches a DCP
register RPC. RPC-03 establishes host zero-fill and AFK reply handling but finds
no local reply deadline and a no-op abort hook. Complete-reply/firmware semantics
and selector-call authorization remain unestablished.
**NOT_READY_FOR_DPCD_TEST** remains the result.

The `research/dcp-rpc-safety` branch builds on the published RPC-03 report rather
than repeating the host ABI work. G5/R4/R5 add fresh target/signing provenance,
direct notification/recovery callers, pre-send admission waits and concrete
endpoint cleanup. The [explicit matrix](dcp-dpcd-rpc-03.md#readiness-gates) requires
every gate to be PASS. This completed milestone is now integrated by merge
`2ffc77d9d532502495fca5d88291d42eed61e45b`; its branch and baseline tag are retained.

The subsequent `research/public-dp-native` branch is enumeration-only. P1 observes
an active external display but a null public CG service and no published
IOFramebuffer/I2C interface, including the alternate registry search:
**PUBLIC_IOFRAMEBUFFER_PATH_UNAVAILABLE**. It makes no public or private
transaction, and every private RPC-safety gate remains unchanged.
The public milestone is now integrated into main by merge
`dd439c80f7b1190f0e033dcf1a19242de2bd3039`; both completed branches and the baseline
tag remain. M2C on `research/dpdv-isolation-safety` adds G6/R6/R7 lifecycle and
AFK release evidence plus mock-only process tests. Its separate result is
**NOT_READY_FOR_ISOLATED_DPDV_OPEN_CHECK**; the DPCD-read gate is unchanged.

M2C is now integrated by merge `a7dc7d647e3e8fccb2e40e5cd56e3f9a8410697b`.
M2D's [pre-selector proof](dpdv-open-path.md) uses current call paths, passive
gate evidence and the provider-close owner guard to reassess applicability.
It reports CALL_GRAPH_INCOMPLETE: selector risks are not automatic blockers,
but independent critical open/close proof gaps remain. The helper stays mock-only.

M2D is integrated by merge `73e0caaaf079b2177d5207f2320c5fc61dac9117`.
M2E's [current proof and matrix](dpdv-open-path.md#m2e-applicability-matrix)
resolve ordinary workloop identity and unused-gate removal, with hash-bound
frontier classifications. The provider's alternate user-server factory condition
remains a specific ownership/work uncertainty. Both not-ready gates stay intact.

M2E is integrated by merge `ce28518eb301592ed6dd3d2b75d152b1a8e54970`.
[M2E.1](dpdv-open-path.md#m2e1-runtime-userserver-discriminator) tests only the
userServer writer/observable discriminator. Native instance provenance is verified,
but the compiled writer set and public-equivalence proof remain incomplete.
USER_SERVER_RUNTIME_STATE_UNRESOLVED; static expansion stops without a private open.

M2E.1 is integrated at `1fc8f0241acec829fa732503c13a9ab588e26fb0`, with immutable
pre-operation tag `pre-dpdv-open-v0.2`. [M2F](dpdv-open-check.md) adds audited,
opt-in isolated open/close tools, but a fresh preflight observed no active external
display and No Link before helper spawn. EXPERIMENT_NOT_RUN; no private call,
retry or DPCD gate promotion. The actual helper selection path remains untested.

The subsequent explicitly authorized [M2F recovery](dpdv-open-check.md#recovery-and-renewed-authorization)
completed committed-code no-open agreement and one real open/immediate-close,
both returning 0, with a normally reaped helper and unchanged sampled public
state. DPDV_OPEN_CLOSE_RUNTIME_VALIDATED applies to that observation only;
userServer and selector safety remain unresolved. No further private call or retry.

The successful M2F state is integrated at
`3f5f0cd887ed2ef5c8dbadc9abb278792c3150be`, tagged `dpdv-open-runtime-v0.3` before
creating `research/selector0-one-byte-readiness`. [M2G](selector0-one-byte-readiness.md)
revalidates the runtime receipt and unchanged kernel identity, compares wrapper
and direct transports, and documents all 19 one-byte readiness gates. Result:
NO_TRANSPORT_READY; NOT_READY_FOR_ONE_BYTE_DPCD_READ. Reply completeness, bounded
waiting and cancellation are not repaired by requesting one byte. Constant 500
is UNRESOLVED and the global NOT_READY_FOR_DPCD_TEST gate remains unchanged.
Only transport-independent revision classification and synthetic short-reply
tests are added; no read helper or private operation is introduced.

M2G is integrated at `2b1565ee61337a368d75980af281621a5959000e`, with annotated
`selector0-safety-v0.4` created before `research/inflight-read-termination`.
[M2H](inflight-read-termination.md) reuses the UUID-matched wait/lifecycle bytes,
records sixteen scoped blocking/deferred-completion sites and the single command's
state machine, and returns INFLIGHT_READ_TERMINATION_NOT_PROVEN. Concurrent close,
task death, late replies and disconnect do not supply a universal terminal-state
proof. 500_MEANING_UNRESOLVED describes a precise firmware-payload field whose
meaning cannot bound the demonstrated host wait. READ_ABORT_SET_INCOMPLETE and
UNKNOWN failure containment remain explicit. No private call, new read helper,
kernel graph expansion or change to the one-byte/global not-ready gates occurs.

M2H is integrated at `1a014d8d3c3cd35ed5381160b809cf4803d79d69`, with annotated
`inflight-read-safety-v0.5` created before `research/w06-wake-or-strand`.
[M2I](w06-wake-or-strand.md) binds the exact 24 used context bytes, event E=C,
known status/wake pair, callback/tag identity and nine removal boundaries. The
suspicious cleanup is the same pending list, but constructive stranding steps 5
and 7 and universal wake/quiescence remain unproved. W06_WAKE_STATE_UNRESOLVED;
CALLBACK_QUIESCENCE_UNRESOLVED; LATE_RESPONSE_STACK_SAFETY_UNRESOLVED. The ordinary
blocked stack is preserved under the scoped current-byte/pinned-source contract,
not proved safe after every return. **Stop further static expansion of this
transport and abandon it on the daily-use Mac.** No selector implementation or
execution is authorized, and NO_TRANSPORT_READY plus both not-ready gates remain.

M2I is integrated at `a882c1dc75501c03347050f1cdb91c38df2af39d`, with annotated
`selector0-retired-v0.6`. **RETIRED_ON_DAILY_USE_M5** is permanent for this
transport. [M3A](m5-mst-source-feasibility.md) investigates source machinery:
24 selected host images, 62,740 functions, 203 function candidates and eight
non-MST data-table matches. No qualified host codec, topology model or payload
allocator was found; the one-link packetizer behind DCP link/timing firmware
remains opaque. **M5_MST_SOURCE_FEASIBILITY_UNRESOLVED** does not establish M5
hardware incapability. No private transaction occurred; **NOT_READY_FOR_DPCD_TEST**
remains. The next evidence target is M5-attributed firmware/control documentation,
not further selector analysis or execution.

M3A is integrated at `24f2d1c3065ec0d7f80b5a53077f3e169f79368f`, tagged
`m5-mst-host-scan-v0.7`. [M3B](m5-dcp-firmware-mst.md) resolves the exact J704AP
25G83 Ap,DCP2 component to t8142dcp.im4p and verifies its manifest digest,
DeviceTree association and decoded firmware. It finds a structural MST codec,
GUID/RAD topology and payload/ACT primitives. Result:
**M5_DCP_FIRMWARE_MST_CONTROL_EVIDENCE_FOUND_PACKETIZER_UNRESOLVED**.
The one-link independent multi-stream packetizer and complete multi-ID allocator
remain unproved; M3A's host-side negative is not erased. Only packetizer ownership
and timing-to-payload binding are the next evidence target. No private operation
occurred; selector retirement and **NOT_READY_FOR_DPCD_TEST** remain unchanged.

M3B is integrated at `c89bf66bac79893f4e6910e10d4a1126775edce7`, with annotated
`m5-dcp-mst-control-v0.8`. [M3C](m5-dcp-mst-packetizer.md) resolves the scalar
source record and ID-1 descriptor through constructor-bound controller/nub
methods into register slot fields and a source activation bit. Result:
**M5_DCP_MST_PACKETIZER_PRESENT_BUT_STREAM_BINDING_UNRESOLVED**.
Independent timings, simultaneous distinct payloads and source selection on one
link remain unproved; the inspected single-descriptor path is not an M5-wide
one-stream limit. M3C authorized one final packetizer-object ownership pass,
completed below, not another broad firmware or transport search. No hardware or private
display operation occurred; all retirement and DPCD gates remain unchanged.

M3C is integrated at `5beb1ac304a1715dc9fb7cad9b3322819b8fd140`, tagged
`m5-dcp-packetizer-v0.9`. [M3D](m5-dcp-stream-ownership.md) completes that final
pass: **M5_DCP_STREAM_OWNERSHIP_UNRESOLVED** and
**MACMST_ARCHITECTURAL_VIABILITY_UNRESOLVED**. Exact factory registration and
provider collections do not close runtime source-controller membership of one
physical DPTX; scalar device/timing state is not an architectural maximum.
**Stop static packetizer expansion.** No M3E firmware-graph search or M4A
host-control milestone is proposed. M3C's packetizer evidence is preserved;
selector retirement, immutable markers and **NOT_READY_FOR_DPCD_TEST** remain.
No hardware/private display operation occurred.

M3D is integrated at `c5bc1b1bacd7742a4bbc1b54285336e9d51302a5`, permanently
tagged `m5-mst-static-ceiling-v1.0`. [M3E0](m5-mst-static-conclusion.md) is the
documentation-only handoff, not another reverse-engineering pass:
**MACMST_STATIC_FEASIBILITY_INCONCLUSIVE**. The exact frozen opacity is
**Runtime source-controller membership of one physical T8142 DPTX register owner.**
Real MST control/source packetizer findings and all M3C/M3D classifications
remain intact. No passive discriminator was identified in the bounded public
check. The sole next-evidence recommendation is a separately approved
**SACRIFICIAL_DYNAMIC_EXPERIMENT** on a non-daily-use system; none is executed.
Implementation gates A-E remain unmet. **STATIC_PACKETIZER_ANALYSIS_FROZEN**;
**NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED**.
Earlier research/reproduction commands below are historical, not a new work plan.

[M4P](m5-sacrificial-dynamic-design.md) designs the conditional observation and
keeps its gate closed: **SACRIFICIAL_EXPERIMENT_REQUIRES_UNAVAILABLE_CAPABILITY**.
Public telemetry lacks qualified ownership data; m1n1 has T8142/M5 recognition
but no pinned M5 macOS guest or validated same-DPTX IPC observer in the checked
sources. Exact sacrificial Mac17,2 hardware is required by this design; ordinary
stimulus sufficiency remains unresolved. One blocked future IPC architecture,
five tiers, A-D success criteria and Apple Finder/DFU recovery are documented.
No tracing, display transition, boot/security change or dynamic experiment was
performed. The design branch starts directly from completed M3E0; neither
conclusion nor design is merged into main. All static and daily-use stops remain.

[M4Q](m5-observer-gap.md) qualifies observation infrastructure only:
**M5_OBSERVER_REQUIRES_MAJOR_PLATFORM_ENABLEMENT** for the identified m1n1 path.
Fresh pins confirm real T8142 bring-up and active M5 work, including a recent
SPRR/GXF development branch, but not a qualified newer-XNU/SPTM macOS guest.
The current tracer requires a controlled guest, target discovery data and a raw
record extension; source-ownership semantics remain unresolved. Ordinary
one-source validation is separate from proving multi-stream capability.
Recommendation: wait for upstream M5 enablement; purchase is premature.
No code, boot, trace, security change, display operation or new firmware analysis
is performed. M4Q branches directly from M4P without merging it.

The completed M3E0/M4P/M4Q chain is now integrated into main by no-fast-forward
merge `7250caac7a9f627f381b91ab9dfeb86191344ed9`, with a tree exactly equal to
M4Q, and permanently tagged `m5-observer-platform-gap-v1.1`. Earlier unmerged
statements above describe the pre-integration history. The separate
[upstream resume gates](m5-upstream-resume-gates.md) record
**MACMST_PROJECT_STATE_UPSTREAM_BLOCKED** and **OBSERVER_WORK_REMAINS_BLOCKED**.
U1-U5 are **WAITING**; a complete selected route may use U1 or an alternative
U2 environment, but must cover transport, ownership and useful stimulus/evidence.
Purchase remains premature. Future reviews are bounded gate checks, not M4Q
reruns or experiment approval. The resume-gates branch is documentation only
and is not merged; no PR, technical investigation or hardware operation occurs.

[M5P0](m5-observer-self-enable.md) records the owner's subsequent authorization
of a separate compile/offline platform-development track. This supersedes the
project-wide wait restriction, not the daily-use or firmware-analysis stops.
Platform work is blocked by the pinned upstream repository's no-AI instruction,
encountered before a build or source edit. The independent MacMST JSONL consumer
and 21 synthetic tests are implemented; MacMST compiles and its offline CTest
entry passes. No producer, platform patch series or qualified target-test path
exists. **M5_OBSERVER_CODE_NOT_READY_FOR_TARGET_TEST** and
**SACRIFICIAL_M5_STILL_PREMATURE**. No hardware operation occurred.

[M5P1](m5-observer-self-enable.md#m5p1-offline-observer-pipeline) completes the
independent offline observer pipeline: **OFFLINE_OBSERVER_PIPELINE_READY**.
The frozen schema, deterministic synthetic producer, replay, explicit
correlation, conservative A-E evidence evaluator, golden/adversarial corpus and
neutral capture-bundle validator pass 124 focused tests plus the strict MacMST
build and offline-only CTest. All positive evidence results are synthetic;
there are zero real-evidence passes. The sibling platform repository is untouched
beyond status/HEAD/remotes verification. The [human-only handoff](m1n1-human-platform-handoff.md)
contains no platform patch. **M5_OBSERVER_CODE_NOT_READY_FOR_TARGET_TEST**,
**SACRIFICIAL_M5_STILL_PREMATURE** and **USB_C_HUB_CONNECTION_NOT_REQUIRED** remain.

[M5P2](m5-host-stream-control.md) investigates a newly authorized static host
path above the frozen firmware boundary. Nineteen current 25G83 host images and
57 captured functions distinguish service identity, link roles, virtual-device
emulation, display records, concrete host RPC forwarding and physical-port
allocation. **HOST_STREAM_CONTROL_PATH_UNRESOLVED** and
**RUNTIME_OBSERVER_STILL_REQUIRED**: none proves independent sources sharing one
physical DPTX. The virtual-device source role, mirror source model, mechanism
and MST policy gate remain unresolved, not impossible. The 124 observer tests,
12 new host tests, 24 selected host-parser tests and strict build pass; offline
CTest is 2/2. Schema v1 and the historical reports are unchanged. No display,
private API, firmware, security or sibling-platform operation occurred.

[M5P3](m5-passive-runtime-topology.md) completes the specifically authorized
passive unplugged/connected-mirrored differential, honoring the user-confirmation
pause before the second capture. Both 42-query captures use identical committed
public-read code on 26.6.2/25G83. There are 22 new relevant records, including
one external DP/AV device/service/video tuple under DCPEXT0, all advertised as
Unit 0, while the preexisting controller/port Units 0 and 1 persist. One logical
VG248 record and a two-lane HBR3, non-tunneled USB-C port state are exposed.

**PASSIVE_RUNTIME_TOPOLOGY_PARTIAL** and
**PASSIVE_SAME_DPTX_SOURCE_EVIDENCE_NOT_ESTABLISHED**. The EPIC-to-physical-owner
and mirror runtime model remain unresolved; no virtual-device runtime object
was observed in the retained scope. The selected next route is
**TARGETED_PUBLIC_LOG_OBSERVATION_WARRANTED**, with an exact future predicate
but no log collection now. The frozen observer pipeline and all private-call,
daily-use and firmware gates remain. All 33 snapshot tests and the preserved
offline suites pass; CTest is 3/3. Captures stay local and ignored, and the
completed branch is local-only, with no push, merge or PR.

[M5P4](m5-public-log-correlation.md) first audits and publishes that exact
M5P3 branch at `369b5e5f202640f906904d2dc91413bd1b0930f3`, with no merge or PR.
One bounded, unprivileged `log show` using M5P3's exact kernel predicate and
recorded UTC bracket returns **477 retained records**. The historical
routing/service, sink/EDID, training and link-start evidence is sufficient to
avoid a new reconnect: **HISTORICAL_LOG_EVIDENCE_SUFFICIENT**.

**PUBLIC_LOG_RUNTIME_PARTIAL**. A logged aggregate sink-count change to 2
differs from M5P3's later public SinkCount 1, but the counting namespaces and
distinct downstream identities remain unresolved. Opaque log tokens, link-role
`source=Upstream`, interface tokens and zero `extraPipes` do not establish
source ownership or a mirror/MST prohibition. The next route is
**EXTERNAL_DP_PROTOCOL_CAPTURE_WARRANTED**, meaning a separately approved
passive measurement plan, not execution. No live stream or physical change
occurs in M5P4; the hub remains connected. All four offline CTests pass (200
tests, including 31 new log tests). M5P4 itself remains local-only.

[M5P5](m5-dp-observation-plan.md) publishes the exact M5P4 branch at
`db517239b496168b05490a6c3d71af1f88329382`, superseding its historical local-only
status above, with no merge, PR or tag changes. This milestone is research/design
only. **AUX_CAPTURE_CAN_RESOLVE_NEXT_GATE** for complete upstream branch topology,
per-port EDID/DPCD and payload-control evidence. Actual simultaneous VC/video
traffic requires a later main-link observation; AUX ACT status is receiver
reporting, not captured ACT packets or source ownership.

**UPSTREAM_USB_C_DP_PATH_MUST_BE_OBSERVED** for the current hub.
**NATIVE_DP_MST_LAB_TOPOLOGY_VALID** is a controlled M5-source contrast, not an
explanation of the ZMUIPNG counts. Dedicated DPA-400 2.1 and Ellisys Std DP
routes warrant temporary AUX-access qualification, but prices, raw-export/loss
behavior and the exact cable/electrical assembly still need acceptance.
**PURCHASE_NOT_YET_JUSTIFIED**; no practical low-cost AUX package was established.
The independent wire-schema design does not modify the frozen DCP pipeline.
All 200 existing offline tests pass; 13 source/document hashes and 19 report
sections validate. No electrical capture, query, physical change or purchase
occurred. **KEEP_CURRENT_HUB_CONNECTED**; all safety/firmware boundaries remain.

[M5P6](m5-aux-access.md) publishes M5P5 unchanged at
`54d30598f013b617282375d5295a6b37269fb5b9` and qualifies practical temporary
AUX access without more theoretical source analysis. Current Unigraf HTML
identifies DPA-400 2.1 product **065055**, software bundle **2.1.10**, and
USB-C cable **546109**, conflicting with manual v13's **546127**. The exact
dock/PD/USB3 assembly, loss reporting and complete exports remain unconfirmed:
**DPA400_TOPOLOGY_COMPATIBILITY_UNRESOLVED** and
**ELLISYS_W1_REQUIREMENTS_PARTIAL**.

**AUX_ACCESS_NOT_READY**. The specific next request is
**TEMPORARY_DPA400_ACCESS_FIRST**, not a purchase or guaranteed loan. Official
USA/Canada contacts, UCalgary Technical Services and GRL's published DPA-400
MST-equipment claim give concrete enquiry routes; no available unit, appointment
or price was secured. **ACCESS_PATH_DEPENDS_ON_AVAILABLE_EQUIPMENT**;
**DO_NOT_PURCHASE_ANALYZER_YET**. The
[contact package](m5-aux-access-contact-package.md) contains four unsent drafts:
**USER_OUTREACH_REQUIRED**. W1's single future attach and eight analysis gates
require separate approval. Nineteen current receipts and the preserved 13 M5P5
receipts validate; all 200 offline tests pass. No messages, signal capture,
runtime query, purchase or hardware changes occurred. Keep the current hub
connected; all daily-use and firmware boundaries remain.

[M5P7](m5-selfbuilt-aux-observer.md) publishes M5P6 unchanged at
`e909e471cbf5982749de2c67655197d091438a27` and advances the independent,
MacMST-owned observer track. **SELF_BUILT_AUX_OBSERVER_PRIMARY** means continued
engineering, not ready hardware. Neutral AUX bytes/samples/symbols, twelve MST
message types, loss-aware reconstruction, nine W1 gates, raw bundles and A-H
scenarios are implemented. All 294 offline tests pass; zero real wire captures
or source-ownership gates are established.

Public endpoint electrical evidence and capture/FIFO budgets support
**NATIVE_DP_AUX_TAP_PREFERRED**, but powered-off clamps, allowable added loading
and a specific protected receiver remain unqualified:
**MORE_ELECTRICAL_RESEARCH_REQUIRED**. Scopes are currently qualified only as a
short-transaction architecture; the complete MCU path is unresolved. Native-DP
adapter/branch candidates have dated prices, not a compatibility guarantee or
approved observer BOM. B0 passes; B1-B6 are future gated work.

**CURRENT_HUB_STATE_NOT_REQUIRED** supersedes earlier keep-connected policy.
**OUTREACH_CAN_RUN_IN_PARALLEL** supersedes mandatory outreach: no external reply
is a progress dependency, no message was sent, and the contact drafts remain
unchanged. A future W1 requires a new baseline and generation. The daily-use
selector retirement, DPCD not-ready gate and static firmware freeze remain.

[M5P8](m5-aux-frontend.md) reconciles exact M5P7 at
`277ff81437f3d5443eba58375495f86b3c5fcb41` and freezes its decoder stack.
**COMPARATOR_FRONTEND_PREFERRED**, with symmetric AC-coupled sensing and an
independently powered one-way digital boundary. The model distinguishes active
termination loading from weak idle bias: a 200-kohm differential probe can
halve a modelled 2.7 V bias held by two 100-kohm resistors. Capacitive sensing
reduces DC load, but worst-case sense mismatch converts 0.3 V common mode into
about 14.2 mV error; typical input capacitance is not a guaranteed maximum.

**MORE_ELECTRICAL_RESEARCH_REQUIRED**. The pre-build review records 5 PASS,
1 FAIL and 10 UNRESOLVED. The editable SPICE subcircuit is analysis-only; no
simulator or EDA execution, construction schematic, qualified BOM or hardware
build is claimed. Thirty-three new behavioural/model tests plus the preserved
294 tests pass in six offline CTests. Powered-off protection and a complete
capture backend remain unqualified. **CURRENT_HUB_STATE_NOT_REQUIRED**; no Mac
query, connection change, purchase, assembly, outreach or private operation.

[M5P9](m5-aux-electrical-closure.md) starts from exact M5P8
`a68448e87d21b09bf7cd6a55ccf3541aa76cf7f1` and preserves its models and the
M5P7 wire stack. The 14.2101 mV failure is predominantly capacitive matching:
perfect resistors still leave 14.2082 mV. A machine-readable table preserves
every original review item; actual numerical RC/PWL E0-E10 waveforms, tolerance
sweeps and six circuit-to-W1 profiles are executed and retained.

**MORE_ELECTRICAL_RESEARCH_REQUIRED**. Review: 6 PASS, 2 FAIL, 14 UNRESOLVED.
Matching and nominal full-pipeline completeness fail; comparator/protection,
powered-off, backend, construction schematic and actual BOM remain unqualified.
TLV9031's fail-safe positive input is a useful new lead, not a selected build
part. All 361 offline tests pass; no SPICE execution, purchase, assembly, Mac
query or signal capture is claimed. **CURRENT_HUB_STATE_NOT_REQUIRED**.
Future bench build is now conditional **M5P10**, not this milestone.

- [Evidence ledger](evidence-ledger.md): canonical claims, captures, exact sources.
- [M5 display stack](m5-display-stack.md): DCP/DCPEXT and current service paths.
- [AUX access](aux-access.md): IODPDeviceReadDPCD candidate, alternatives, safety gates.
- [DisplayPort/MST](displayport-mst.md): source-backed constants and decoder limits.
- [Dock observations](dock-observations.md): unobserved versus user-reported topology.
- [Open questions](open-questions.md): all 14 questions and the Milestone 2 experiment.
- [ADR 0001](../adr/0001-language-and-architecture.md): language and architecture choice.
- [External differential](external-dock-diff.md): C1/D1/C2 repeatability and G2 graph.
- [IODP API investigation](iodpdevice-api.md): A1 static evidence and remaining gates.
- [ABI-02 read contract](iodpdevice-abi-02.md): G3/A2, resolved lifecycle/dispatch,
  per-argument confidence, exact caller bindings, preflight and one-byte proposal.
- [RPC-03 safety contract](dcp-dpcd-rpc-03.md): G4/R3, request/reply layouts,
  short replies, no-deadline waits, failure/cancellation and all 13 readiness gates.
- [DPDV authorization](dpdv-authorization.md): class-local versus outer policy
  gates, on-disk probe identity and the unresolved actual-access classification.
- [Public DP-native investigation](public-dp-native.md): installed SDK ABI,
  pinned implementation comparisons, P1 mapping/capabilities, validation and limits.
- [M2C isolated-open investigation](dpdv-isolation-safety.md): current close/death,
  ownership, pre-selector effects, mock watchdog tests and the separate open-only gate.
- [Runtime discriminator and open-only proof](dpdv-open-path.md): current M2E.1
  writer/observable evidence plus preserved M2E/M2D findings and gate states.
- [M2G one-byte selector readiness](selector0-one-byte-readiness.md): authoritative
  runtime baseline, transport comparison, one-byte semantics and current 19-gate matrix.
- [M2H in-flight termination](inflight-read-termination.md): exact wait flags,
  command/tag/callback lifetime, close/death/disconnect and the single remaining wait object.
- [M2I W06 wake or stranding proof](w06-wake-or-strand.md): exact context, wake/removal
  matrices, explicit constructive proof gaps and final static-expansion stop.
- [M3A source feasibility](m5-mst-source-feasibility.md): scoped host search,
  attributed DP census, requirement evidence map and opaque firmware packetizer.
- [M3B identified DCP firmware](m5-dcp-firmware-mst.md): manifest-backed mapping,
  static codec/topology/allocation evidence and unresolved multi-stream packetizer.
- [M3C one-link packetizer](m5-dcp-mst-packetizer.md): source payload writers,
  object layouts, hardware slot table, exact proof map and unresolved stream binding.
- [M3D final stream ownership](m5-dcp-stream-ownership.md): controller creation,
  selected-device/timing ownership, eleven-row proof and static-expansion stop.
- [M3E0 static conclusion](m5-mst-static-conclusion.md): permanent static ceiling,
  four new evidence categories, one conditional recommendation and implementation gates.
- [M4P sacrificial dynamic design](m5-sacrificial-dynamic-design.md): qualified
  method/access limits, exact-target recovery, one blocked architecture and no-go gate.
- [M4Q observer capability gap](m5-observer-gap.md): current platform/guest
  dependencies, portable tracer pieces, source-schema limits and upstream-wait decision.
- [Upstream resume gates](m5-upstream-resume-gates.md): integrated observer-gap
  baseline, U1-U5, alternative complete routes, purchase gate and bounded recheck contract.
- [M5P0 self-enablement](m5-observer-self-enable.md): changed strategy, upstream
  policy blocker, proposed independent trace format and tested offline importer.
- [Frozen observer schema v1](dcp-observer-schema-v1.md): authoritative offline
  record, validation, correlation, evidence, topology and bundle contracts.
- [Human-only platform handoff](m1n1-human-platform-handoff.md): existing facts,
  manual checklist and provenance-return path; no AI-generated m1n1 patch.
- [M5P2 host stream control](m5-host-stream-control.md): exact host object/RPC
  evidence, virtual/mirror distinctions, physical binding gaps and runtime-observer outcome.
- [M5P3 passive runtime topology](m5-passive-runtime-topology.md): validated
  unplugged/connected pair, exact object/EPIC diff, visibility limits and future-log proposal.
- [M5P4 public log correlation](m5-public-log-correlation.md): exact historical
  predicate/window, retained lifecycle sequence, count/identity limits and passive wire-planning route.
- [M5P5 external observation plan](m5-dp-observation-plan.md): AUX versus main-link
  gates, upstream USB-C/native-DP controls, manufacturer evidence, wire schema and access/purchase decision.
- [M5P6 AUX access qualification](m5-aux-access.md): current cable/software facts,
  Canadian access leads, export/loss gates, costs and one-attach W1 design.
- [M5P6 contact package](m5-aux-access-contact-package.md): four user-controlled,
  unsent vendor/university/lab enquiries and the required response package.
- [M5P7 self-built AUX observer](m5-selfbuilt-aux-observer.md): electrical facts,
  capture budgets, passive front-end gates, offline tools, synthetic scenarios
  and independent physical-state/outreach policy.
- [M5P8 front-end qualification](m5-aux-frontend.md): component electrical
  limits, quantitative loading/protection, analysis circuit, conditioned-signal
  tests, ground/backend decisions and formal pre-build review.
- [M5P9 electrical closure](m5-aux-electrical-closure.md): capacitive matching
  derivation, full closure matrix, executed circuit scenarios, error budget,
  unchanged-decoder results and explicit construction-release refusal.
- [MST signature oracle](mst-source-signatures.json): pinned Linux protocol
  addresses, masks, codec/allocator shapes and candidate-only scan rules.

The user reports two physical monitors connected to one USB-C dock showing the
same image. This is an input to investigate, not proof of the dock's transport,
chipset, MST support, or the number of source streams.

## Initial Inspection

Observed at 2026-09-12T00:14:24Z (local date 2026-09-11):

- Repository initially contains only the Copilot instructions, read-only researcher
  definition, and VS Code setup audit. No application, tests, or build files exist.
- Git branch `main` has no commits; `.github/` and `docs/` are untracked. No local
  AGENTS.md, CLAUDE.md, or scoped instruction files were found. Preserve existing
  configuration documentation and do not push.
- Host reports Apple M5, arm64, macOS 26.6.2 (25G83).
- Xcode 26.6 (17F113) is selected at `/Applications/Xcode.app/Contents/Developer`;
  active macOS SDK is 26.5, older than the running OS.
- Apple Clang 21.0.0 (clang-2100.1.1.101), Swift 6.3.3, Swift Package Manager
  6.3.3, CMake 4.4.1, Ninja, make, Homebrew, Python 3, Git, and ripgrep are present.
  Objective-C++ interoperability will be verified by compilation, not assumed.
- No dependency installation is planned. No system configuration changes are
  authorized. The existing chat's permission state is still Allow All; do not
  treat that as permission to execute anything outside this task's safety scope.

## Execution Plan

1. Capture targeted system_profiler and IORegistry observations, keeping only
   relevant fields and redacting serial numbers, UUIDs, addresses, and unrelated
   devices before writing artifacts. Record commands, UTC time, OS, schema, and
   failures. Preserve raw numeric values and their provenance.
2. Inspect primary Linux DisplayPort definitions, Asahi/m1n1 DCP implementations,
   Apple public interfaces, and reproducible IOAVService projects. Pin important
   sources to revisions. Separate source evidence from this M5's observations.
3. Write a language/architecture ADR. Evaluate C, C++, Objective-C++, Swift, and
   mixed stacks against available SDKs, resource lifetime, binary parsing, testing,
   portability, and private-interface experiments. Keep protocol code separate.
4. Build the smallest `macmst probe` using public read-only host, display-list,
   and IORegistry APIs. Report unknowns explicitly; never infer physical monitor
   count, USB-C routing, or MST capability from unrelated USB devices.
5. Add a small hardware-independent DPCD capability decoder using source-backed
   register definitions and synthetic tests. Do not implement a fake AUX transport,
   invoke IOAVService private calls, or send DDC/AUX/MST transactions.
6. Run strict builds, deterministic tests, sanitizer checks where supported, and
   a separately identified read-only hardware probe. Reconcile the evidence ledger,
   prioritize unanswered questions, and propose one bounded Milestone 2 experiment.

Local hypothesis: public display-list and registry reads can establish the number
of macOS logical displays and named DCP services without establishing MST source
capability. Discriminating check: compare an independently captured profiler/
registry baseline with the new probe; disagreement or permission failure must be
reported rather than replaced with guessed data.

## Evidence Labels

- `VERIFIED_ON_M5`: directly observed on this physical host, with reproduction.
- `PRIMARY_SOURCE`: demonstrated by cited code/documentation; its chip/version
  scope is part of the claim, not an implicit statement about M5.
- `INFERRED`: reasoned interpretation, with assumptions identified.
- `HYPOTHESIS`: experimentally testable explanation, not a conclusion.
- `UNKNOWN`: no adequate evidence or no experiment performed.

The evidence ledger will be the source of truth. A zero-result registry query is
not evidence that a hardware feature is absent. A DPCD MST-capability bit belongs
to the addressed receiver/branch, not automatically to the Mac's source engine.

## Testing Strategy

- Application type: local diagnostic CLI; no server, database, browser, Docker,
  credentials, or network service is needed to run it.
- Canonical tests: CTest after CMake configuration. No legacy test assets exist.
- Journeys: enumerate host/displays; report unavailable observations explicitly;
  serialize sanitized evidence; reject invalid CLI arguments; decode synthetic
  DPCD blocks without hardware.
- Unit tests use synthetic byte arrays and privacy fixtures. Hardware tests are
  opt-in and separately labeled. No physical I/O transport is mocked as available.
- Require strict compiler warnings, malformed/truncated input tests, preservation
  of raw protocol bytes, and proof that privacy filters remove unique identifiers.
- Build and unit tests must work without the dock. Hardware success means only
  the named read-only observations succeeded, never that MST can be enabled.
- Capture failures and verification gaps explicitly. No sudo, security weakening,
  firmware changes, persistent system settings, or state-changing hardware calls.

## Verification Run

On the M5/toolchain above:

- `cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug`, `cmake --build build`:
  passed with strict warnings as errors. GNU shorthand conditional warnings were
  fixed without disabling diagnostics.
- `ctest --test-dir build -L unit --output-on-failure`: six CTest entries pass,
  including 42 synthetic DPCD checks, registry privacy, five capture/privacy
  unittest methods, and exact CLI argument/exit-code tests.
- `cmake -S . -B build -DMACMST_ENABLE_HARDWARE_TESTS=ON` and
  `ctest --test-dir build -L hardware --output-on-failure`: one explicitly opt-in
  public read-only hardware test passes. Empty successful IOService queries are
  handled separately from invalidation errors.
- `cmake -S . -B build-sanitized -G Ninja -DCMAKE_BUILD_TYPE=Debug -DMACMST_ENABLE_SANITIZERS=ON -DMACMST_ENABLE_HARDWARE_TESTS=OFF`,
  build, and `ctest --test-dir build-sanitized -L unit --output-on-failure`:
  all six deterministic entries pass under AddressSanitizer/UndefinedBehaviorSanitizer.
- `python3 tools/capture_baseline.py --probe build/macmst`: B03 saved 32 read-only
  command observations plus SDK/driver metadata, with no failures.

These checks establish software behavior and the named host observations, not
working DDC, native AUX, DPCD access, MST sideband communication, or source MST.
No code from another display project was executed; no firmware was extracted.

## Milestone 2A Verification

- `cmake --build build`: strict warnings-as-errors build passes.
- `ctest --test-dir build -L unit --output-on-failure`: seven entries pass,
  preserving the 42 synthetic DPCD checks and adding External pairing/ambiguity/
  incomplete-observation tests plus ten static parser/byte/branch tests.
- `ctest --test-dir build -L hardware --output-on-failure`: one separate opt-in
  public read-only hardware test passes, including graph and unverified-status checks.
- `cmake --build build-sanitized` and
  `ctest --test-dir build-sanitized -L unit --output-on-failure`: all seven
  deterministic entries pass under AddressSanitizer/UndefinedBehaviorSanitizer.
- Existing capture tool ran for C1, owner-disconnected D1, and owner-reconnected
  C2 with the unchanged Milestone 1 binary. The external display and External
  device/service/AV objects followed the transition; Embedded objects remained.
- G2 adds explicit graph and interface-flag evidence: 33 read-only commands,
  zero failures. A1 records 97 IODP names and static library/caller evidence.
- Failed debugger attachment was not bypassed. Cached dyld_info inspection worked
  without attachment; raw bytes/LLVM expose and document symbolication limitations.

No private IODP/IOAV function, IOServiceOpen, IOConnect transaction, DPCD write,
MST sideband message, forced HPD, link-training change, or firmware operation was
executed. Physical cable transitions were performed by the owner as requested,
not by software. No local commits or pushes were made in this milestone.

## M2A-ABI-02 Verification

- `cmake --build build`: strict build passed, already up to date; native probe
  and decoder code were not changed for ABI-02.
- `ctest --test-dir build -L unit --output-on-failure`: all seven entries passed,
  including 24 static-parser tests and the existing 42 DPCD synthetic checks.
- `ctest --test-dir build -L hardware --output-on-failure`: the one opt-in public
  read-only probe test passed. No DPDV open, private object or DPCD read was tested.
- `cmake --build build-sanitized` and
  `ctest --test-dir build-sanitized -L unit --output-on-failure`: all seven entries
  passed. Native targets use ASan/UBSan; Python tests still use the normal interpreter.
- `python3 tools/inspect_iodp.py --baseline artifacts/probes/20260912T021152Z --server`:
  A2 completed with 97 symbol names, 25 IOKit blocks, six PS190 blocks, four CF
  lifecycle records, exact bindings for the three required caller methods,
  59 selected host-kernel function blocks, and six resolved dispatch rows.
  Other unresolved/aliased call bindings remain explicitly marked in the report.
- G3's probe binary and eight core/capture source hashes are unchanged. A2's
  three tool-source digests match the current sources. All 118 artifact hashes
  across B03, C1/D1/C2, G2, A1, G3 and A2 verified successfully.
- Local document links/fences, ledger E001-E052/source S01-S17 uniqueness,
  changed-file whitespace and editor diagnostics passed. Git remains on main
  without a HEAD, with 32 untracked files; no staging, commit, branch or push.

The [ABI-02 report](iodpdevice-abi-02.md) resolves client lifetime and host
dispatch but records **NOT_READY_FOR_DPCD_TEST**. Remaining lower-RPC reply,
wait and native read-only semantics must be established before the separately
approved first experiment: exactly one byte at 0x000. No transport scaffold,
new cable cycle, updater execution, security change, or firmware write occurred.

## M2A-RPC-03 Verification

This is the original pre-publication verification record. The milestone branch's
separate 37-test run, G5/R4/R5 provenance and 161-artifact verification are recorded
in [RPC-03 validation](dcp-dpcd-rpc-03.md#validation).

| Command / Check | Result |
| --- | --- |
| `cmake --build build` | PASS, strict build already up to date. Native source and probe unchanged. |
| `ctest --test-dir build -L unit --output-on-failure` | PASS, 7/7 entries; existing 42 DPCD synthetic checks preserved. |
| `ctest --test-dir build -L hardware --output-on-failure` | PASS, 1/1 public read-only probe entry; no private hardware test. |
| `cmake --build build-sanitized` | PASS, existing sanitizer build up to date. |
| `ctest --test-dir build-sanitized -L unit --output-on-failure` | PASS, 7/7 entries. ASan/UBSan cover native targets; Python uses its ordinary interpreter. |
| `python3 -m unittest discover -s tests -p 'test_iodp_static.py' -v` | PASS, 33 deterministic tests. |
| Final static capture | PASS, R3; full exact selection command is in the RPC report. No inspected code executed. |
| Artifact/provenance checks | PASS, 139 artifacts across B03/C1/D1/C2/G2/A1/G3/A2/G4/R3, 14 reference files, 3 current tool sources. Three source blob IDs independently match GitHub. |
| Unchanged probe/core checks | PASS, G4 probe binary and all 8 recorded core/capture source hashes still match. |
| Documentation/diagnostics | PASS, 13 root/research documents' local links/anchors/fences, E001-E069/S01-S21 uniqueness, changed-file whitespace and editor diagnostics. |

R3 is `artifacts/probes/iodp-static-20260912T045748Z/`, with 26 IOKit function
blocks, six PS190 blocks, 206 selected host-kernel functions and the same running
kernel UUID as ABI-02. The new parser uses declared function boundaries, preserves
duplicate names by address, supports exact string/address captures, and records
undecoded instructions explicitly. Three allocation/growth instructions remain
undecoded; no claim depends on pretending otherwise. Source captures remain ignored.

The full then-current 32-file project was read before completing that investigation;
two research reports were added. At that pre-publication point, Git was still on
main without a HEAD, with 34 untracked project files. No files had yet been staged,
committed, pushed or reverted in that investigation.
No model/global VS Code configuration, firmware or security setting was changed.

The result is [RPC-03's gated safety assessment](dcp-dpcd-rpc-03.md#readiness-gates)
and [authorization category E](dpdv-authorization.md#authorization-categories):
**NOT_READY_FOR_DPCD_TEST**. There is no private transport or runnable experimental
DPCD-read command. The proposed first operation remains exactly one byte at 0x000,
only after resolving the blockers and receiving separate explicit approval.