# Open Questions And Next Experiment

Statuses refer to [the evidence ledger](evidence-ledger.md). Feasibility of native
MST on M5 is **M5_MST_SOURCE_FEASIBILITY_UNRESOLVED**.

## M3A Source Feasibility Decision

[M3A](m5-mst-source-feasibility.md) starts from the integrated M2I state
`a882c1dc75501c03347050f1cdb91c38df2af39d`, tagged `selector0-retired-v0.6`.
The pinned protocol oracle and bounded scan of 24 current host images establish
ordinary DP capability/link/DSC control, but no qualified MST sideband codec,
GUID/RAD topology model or PBN/VCPI payload allocator. The single controlling
unknown is the M5 DCP link/stream firmware behind high-level timing/link messages,
including one-link stream-to-payload packetization. Multiple pipes or Thunderbolt
DP tunnels do not resolve it.

The next step is to determine whether an M5-attributed, read-only firmware image
or control specification can expose that boundary. No such usable image was
located in the bounded local search. A host-side negative and older-generation
Asahi findings do not establish M5 hardware incapability.

Selector 0 is **RETIRED_ON_DAILY_USE_M5**: no improvement, wrapper, retry, cancel,
repeated open or lifecycle investigation is authorized. Keep
**NOT_READY_FOR_DPCD_TEST**, the consumed M2F marker and absent DPCD-read marker.
No next hardware experiment is scheduled. The earlier proposals below remain
historical and must not be used to resume the retired transport.

## M2I Final Selector-Transport Decision

[M2I](w06-wake-or-strand.md) starts from the audited M2H merge
`1a014d8d3c3cd35ed5381160b809cf4803d79d69`, tagged `inflight-read-safety-v0.5`.
Primary result: **W06_WAKE_STATE_UNRESOLVED**. Exact event E=C=S+8 and the used
context fields are known. Cleanup acts on the same pending K list, but no eligible
unwoken-cleanup ordering or complete future-producer/quiescence proof closes the
eight-step stranding test. A local no-wake body is not a reachable counterexample.

**Stop further static expansion of this selector transport. Recommend abandoning
it on the daily-use Mac.** Do not start M2J as another generic graph search or
propose a selector run, repeated open, forced wake, close race or hardware
disconnect. Any alternative non-daily-use/reboot-risk environment would require
a separate future decision and explicit authorization; none is scheduled.

CALLBACK_QUIESCENCE_UNRESOLVED and LATE_RESPONSE_STACK_SAFETY_UNRESOLVED remain.
STACK_PRESERVED_WHILE_W06_BLOCKED is a scoped ordinary-wait/source-corroborated
result, not callback quiescence after return. 500_MEANING_UNRESOLVED contributes
no independent exact-C wake. Keep NO_TRANSPORT_READY,
INFLIGHT_READ_TERMINATION_NOT_PROVEN, NOT_READY_FOR_ONE_BYTE_DPCD_READ and
NOT_READY_FOR_DPCD_TEST. M2F-ATTEMPTED remains consumed; the DPCD read marker
remains absent. Earlier next-step proposals below are historical, not authority
to resume investigation or execute this transport.

## M2H In-Flight Termination

[M2H](inflight-read-termination.md) starts from M2G's audited merge
`2b1565ee61337a368d75980af281621a5959000e`, tagged `selector0-safety-v0.4`.
Result: **INFLIGHT_READ_TERMINATION_NOT_PROVEN**. Sixteen scoped wait/deferred
sites, the actual command lifetime and distinct wake events are recorded without
reopening open ABI, revision semantics, provider ownership or userServer analysis.

The single lowest-level blocker is **W06: the event wait for the stack
CommandContext in DCPAVProxy::performCommandGated**. Raw flag 0 reaches
_assert_wait with no deadline. No response-independent path is proved to wake
that context and drain its callback safely. Concurrent close can serialize behind
the read under the source locking contract; task death is not an assured wake.
Conditional Offline replies and command-list cleanup must not be conflated.

Constant 500 is precisely a serialized uint32 firmware-request parameter:
500_MEANING_UNRESOLVED, with no demonstrated host deadline or expiry transition.
Late-reply handling, universal disconnect completion and the complete read-abort
set remain unresolved. One-byte reply completeness is a separate unchanged gate.

Keep NO_TRANSPORT_READY, NOT_READY_FOR_ONE_BYTE_DPCD_READ and
NOT_READY_FOR_DPCD_TEST. The M2F marker remains consumed; the DPCD attempt marker
remains absent. No selector execution, repeat open, close race, private abort or
physical disconnect is proposed. Historical milestone questions below are not
new experiment instructions.

## M2G One-Byte Readiness

[M2G](selector0-one-byte-readiness.md) reconciles the successful M2F runtime
receipt, integrates it at `3f5f0cd887ed2ef5c8dbadc9abb278792c3150be` and preserves
the annotated `dpdv-open-runtime-v0.3` baseline. It reuses current-image evidence
to assess one future selector-0 call at address 0x000 with length 1, without
repeating open/close or submitting a read. NO_TRANSPORT_READY;
NOT_READY_FOR_ONE_BYTE_DPCD_READ; NOT_READY_FOR_DPCD_TEST unchanged.

The single smallest blocker is a target-attributed **bounded, cancel-safe
termination contract for an in-flight one-byte read when its reply is lost**.
Pre-enqueue admission and post-enqueue reply waits lack a finite local deadline.
Constant 500 remains UNRESOLVED, and READ_CANCELLATION_UNRESOLVED is not repaired
by a parent watchdog, same-thread close or unproved concurrent close. Separately,
the actual firmware reply length is discarded; a changed sentinel, size 1 and
plausible revision byte cannot prove a complete live reply.

The existing marker remains consumed and M2G-DPCD-READ-ATTEMPTED is not created.
No read helper is implemented. Historical milestones below retain their original
questions and stop states; they are not instructions to repeat an experiment.

## M2F Recovery

With renewed explicit authorization after recovery, the committed no-open helper
agreed with the fresh public target, then one isolated DPDV open/close completed
with raw results 0/0, zero selectors and unchanged sampled public state.
[The runtime record](dpdv-open-check.md#recovery-and-renewed-authorization)
establishes DPDV_OPEN_CLOSE_RUNTIME_VALIDATED. The private userServer value,
failure cancellation and DPCD-read guarantees were not resolved by success.

The one-shot marker is consumed; do not repeat M2F or run selector 0. The next
separately authorized milestone must reassess the known unbounded reply wait,
cancellation limitations, short replies and one-byte 0x000 contract. The global
NOT_READY_FOR_DPCD_TEST gate remains unchanged. A preceding system watchdog panic
was observed during recovery; its underlying cause is not established.

## M2F Update

[M2F](dpdv-open-check.md) implements and audits the separately authorized isolated
open/close helper, but the dry-run coordinator's fresh public preflight found zero
active external displays and raw LinkRate=0/No Link. The mandatory stop occurred
before any helper spawn or private operation. EXPERIMENT_NOT_RUN; no retry or
display reconfiguration was attempted and no AFTER experiment state exists.

The next separately authorized work must first re-establish active public display/
HBR3 state and complete committed-code no-open target agreement. Do not run
selector 0 or resume this stopped experiment automatically. The private userServer
state remains unknown and NOT_READY_FOR_DPCD_TEST is unchanged.

## M2E.1 Update

The [runtime userServer discriminator](dpdv-open-path.md#m2e1-runtime-userserver-discriminator)
verified the selected native kernel class/personality, measured the field-chain
offsets and checked public markers against writer/teardown contracts. No mandatory
equivalent marker was established: membership can disappear before pointer clearing,
and class provenance is not private field state. USER_SERVER_RUNTIME_STATE_UNRESOLVED.

The one remaining fact is the live provider userServer chain at factory entry.
Direct privileged observation is rejected; this milestone stops static expansion.
No native-path gates are advanced, no M2F contract/backend is produced, and both
NOT_READY_FOR_ISOLATED_DPDV_OPEN_CHECK and NOT_READY_FOR_DPCD_TEST remain unchanged.

## M2E Update

The [M2E proof](dpdv-open-path.md) resolves the native gate's workloop origin and
never-used removal semantics, and traces native registry/task relationships without
confusing them with provider.open ownership. Whole generic graph completeness is
not required. The specific alternate factory branch tests private
provider reserved/uvars/userServer state before class-based DPDV construction.
That state and delegated work are not established by the public class property.

The single smallest next discriminator is proving that this user-server route is
excluded, or cannot create ownership/external work for the selected provider.
Other relevant callback obligations remain explicit; resolving one branch is not
a promise of automatic readiness. No M2F backend/design for execution is added.
NOT_READY_FOR_ISOLATED_DPDV_OPEN_CHECK and NOT_READY_FOR_DPCD_TEST remain unchanged.

## M2D Update

The [pre-selector proof](dpdv-open-path.md) separates passive local initialization
from external-method dispatch and finds real provider-close messaging behind an
owner guard. Whole-graph exclusion is still incomplete. Selector-command teardown
and callback quiescence therefore have UNKNOWN applicability, not automatic
open-only failure status and not an unproved N/A label.

The next discriminator is the remaining generic lifecycle/shared-workloop graph
and owner-guard invariant, not a repeated selector-0 cancellation investigation.
The open-only result remains NOT_READY_FOR_ISOLATED_DPDV_OPEN_CHECK for those
independent gaps. The global NOT_READY_FOR_DPCD_TEST gate remains unchanged.

## M2C Update

The [public-path investigation](public-dp-native.md) found no exposed
IOFramebuffer/I2C route on the tested M5 topology and is now integrated.
[M2C](dpdv-isolation-safety.md) reconstructs conditional user-client close/death
and deferred finalization, traces AFK storage release, and tests a separate mock
helper. It does not prove real open/teardown completion or callback quiescence:
**NOT_READY_FOR_ISOLATED_DPDV_OPEN_CHECK**.

The next work is stronger evidence for shared workloop progress, post-construction
authorization-failure cleanup and process-death lifetimes, not a private open or
read. A mock watchdog bounds parent observation only. Every original DPCD gate
remains unchanged and **NOT_READY_FOR_DPCD_TEST** still applies. No future
hardware experiment is authorized by this milestone.

## Milestone 2A Update

The historical question table below describes the Milestone 1 baseline. A
controlled connected/disconnected/reconnected ZMUIPNG hub experiment now confirms
one external logical display and repeatable External DCPEXT0 DP/AV object
appearance. See [external-dock-diff.md](external-dock-diff.md) and E025-E031.

Questions 3 and 9 now have a correlated USB-C/External service path, but no MST
branch identity. Questions 5/6/8 now have the [IODP API inventory and local wrapper
analysis](iodpdevice-api.md), not an executed native read. Questions 10-14 still
lack hardware transport/MST evidence. The status is **NOT_READY_FOR_DPCD_TEST**.
[ABI-02](iodpdevice-abi-02.md) now resolves CF lifecycle, authenticated caller
bindings, and the DPDV/selector-0 host path to a DCP register RPC. The next
discriminator is lower RPC reply validation, bounded waiting and native read-only
firmware semantics. No further cable cycling is needed for the recorded
association unless the topology changes; no private read has been executed.

The milestone branch now adds G5/R4/R5: admission can block before firmware
receives a command, notification-driven error recovery is conditional, and
endpoint list/task cleanup is not a proven cancellation response. Current
authorization remains category E. Use [the normalized readiness matrix](dcp-dpcd-rpc-03.md#readiness-gates)
for the next decision, not the count of reconstructed functions. No private
operation is authorized by publishing or completing this static milestone.

[RPC-03](dcp-dpcd-rpc-03.md) now traces AFK submission/replies and host zero-fill,
but finds a no-deadline uninterruptible wait and a no-op abort hook. The raw 500
unit, complete firmware reply/read-only contract and actual process authorization
remain unresolved. G4 revalidates the display path with new IDs, while explicitly
recording USB count 9 versus 10 rather than claiming every attachment is unchanged.

## Research Question Coverage

| # | Question | Current Answer And Next Discriminator |
| --- | --- | --- |
| 1 | What display engines exist on M5? | VERIFIED_ON_M5: dcp0/dcpext0/dcpext1 expert objects; UNKNOWN physical engine/packetizer inventory. Trace specific M5 hardware/firmware implementation, not just names. |
| 2 | How are external displays represented through DCP/DCPEXT? | VERIFIED_ON_M5: two DCPEXT paths and four remote-port proxies. PRIMARY_SOURCE: Asahi EPIC/PHY model. Actual connected external mapping remains UNKNOWN. |
| 3 | Which registry objects correspond to the active USB-C path? | UNKNOWN: only the inactive built-in HDMI transport object was observed. Correlate a controlled dock topology. |
| 4 | How does macOS communicate with DP sinks? | PRIMARY_SOURCE: DP native/I2C AUX protocols, public IOI2C API and private AV/DP symbol families. UNKNOWN exact active M5 external call path. |
| 5 | What does DCPAVServiceProxy expose? | VERIFIED_ON_M5: Embedded/Unit=0 and user-interface-supported flag. PRIMARY_SOURCE: AV service and EDID-copy protocol. Actual user-client call behavior remains UNKNOWN. |
| 6 | What does IOAVService expose? | VERIFIED_ON_M5: selected I2C/EDID/property/link symbols resolve. PRIMARY_SOURCE: DDC library declarations. Functions were not invoked. |
| 7 | Can userspace perform I2C-over-AUX? | PRIMARY_SOURCE: reproducible IOAVService DDC implementations exist. UNKNOWN success/routing on this M5/dock; no DDC commands sent. |
| 8 | Can userspace perform native AUX? | HYPOTHESIS: IODPDeviceReadDPCD is a viable candidate; VERIFIED_ON_M5 symbol presence. UNKNOWN ABI, target binding, live native behavior, permissions. |
| 9 | Is the dock visible as an MST branch? | UNKNOWN: the reported connected topology was not observed. No branch-capability field was measured. |
| 10 | Can the dock's DPCD space be accessed? | UNKNOWN: no native transport call, and current DP device is Embedded. |
| 11 | Can DP_MSTM_CAP at 0x021 be read? | HYPOTHESIS dependent on question 8; decoder and exact constants are ready. A future approved one-byte read is the test, not an I2C-offset substitution. |
| 12 | Can MST sideband messages be sent? | UNKNOWN. PRIMARY_SOURCE: native DPCD message-buffer addresses are known. Writing sideband/setup state is explicitly outside this phase. |
| 13 | Is there an M5 MST packetizer? | UNKNOWN. Neither the number of DCP objects nor a sink's MST flag nor the DPCD API establishes it. |
| 14 | Is there dormant DCP firmware MST functionality? | UNKNOWN. Firmware code was not inspected; no source-specific evidence. Asahi's No MST statement is recorded with its missing M5 scope. |

## Historical Priority Order

1. **P0: a valid measured topology.** Identify the dock and expose/correlate an
   External AV/DP service. Without this, probing the existing Embedded device risks
   answering the wrong question about the internal panel.
2. **P1: native read ABI and permissions.** Trace IODPDeviceReadDPCD and
   CreateWithService in the installed implementation. Verify types, lengths,
   read semantics and user-client binding; do not infer from export names.
3. **P1: first approved DPCD read.** Only after the first two gates and lifecycle/
   dispatch verification, plan/request approval for exactly one byte at 0x000.
   Additional addresses, including 0x021, must wait for a successful first-read
   evaluation and a separate decision.
4. **P2: branch identity and topology.** A receiver MST bit may establish branch
   capability, but vendor/chip identity may still require additional evidence.
   MST sideband discovery needs a separate state-changing-experiment approval.
5. **P2: source and firmware capability.** Investigate source stream scheduling,
   payload allocation/ACT handling, packetizer implementation, and DCP control
   interfaces. This is separate from proving native AUX or receiver capability.

## M2-01 Plan (Completed)

The original plan below was completed in C1/D1/C2. See
[the recorded results](external-dock-diff.md); it is not a request to repeat it.

**M2-01: correlate one explicitly identified two-monitor dock with External
DCPDP/AV objects, without invoking private APIs.**

Hypothesis: the intended connected dock topology will expose an External
DCPDPDeviceProxy/ServiceProxy or a distinguishable alternative display service
whose path and appearance correlate with the new external logical display.

Prerequisites: the owner confirms the dock make/model, cable, physical USB-C
port, power state, monitor models and occupied outputs. No serial numbers are
needed. Physical connection/disconnection is an owner-approved action; the agent
does not change it automatically. No display settings, firmware or security
settings are changed.

1. Preserve a disconnected/current snapshot using the existing collector.
2. The owner connects/powers the specified dock and both monitors, waits for the
   visible display state to settle, and confirms what each physical screen shows.
3. Run `python3 tools/capture_baseline.py --probe build/macmst`. Compare the two
   snapshots' logical displays, DCPDP/AV Location/Unit/paths, USB descriptors,
   and published transport fields. Keep new raw values and capture hashes.

Expected observation: a correlated External service and external logical display
appear. The reported mirroring hypothesis predicts one external logical display
for the two physical screens, but that is not assumed in advance.

Disconfirming/alternative observations: still no external display; only Embedded
objects; a different service family; multiple independently enumerated displays;
or evidence of a different transport. These outcomes change the next investigation
step rather than proving MST impossible. No zero-result query is a silicon verdict.

Stop if the topology remains ambiguous, permissions fail, the display behavior
changes unexpectedly, or a tool requests hardware/state-changing access. Success
means **target identity and reproducibility**, not MST capability. The next gated
native-AUX experiment is specified in [aux-access.md](aux-access.md#smallest-safe-discriminating-experiment).