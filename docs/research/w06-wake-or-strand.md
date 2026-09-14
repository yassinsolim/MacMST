# M2I: W06 Wake Or Stranding Proof

## Scope

This is the final planned static investigation of one submitted native DCPDP read
and its W06 waiter. No private open/close, selector, DPCD operation, read helper,
attempt marker, abort, close race, security change or physical disconnect is
performed. The consumed M2F-ATTEMPTED marker is preserved; the
M2G-DPCD-READ-ATTEMPTED marker remains absent. No selector has been executed.

The open ABI, selector ABI, DPCD revision semantics, public I2C, MST, userServer,
general provider/lifecycle analysis and reply completeness remain frozen retained
evidence. The only question is whether the specific stack context must be safely
completed independently of a reply, or a reachable removal can strand it.
NO_TRANSPORT_READY, NOT_READY_FOR_ONE_BYTE_DPCD_READ and NOT_READY_FOR_DPCD_TEST
remain in force while that question is examined.

VERIFIED_ON_CURRENT_KERNEL means retained static bytes with a running-kernel UUID
match, not execution of a private method. PRIMARY_SOURCE means pinned source with
its stated revision scope. INFERRED and UNKNOWN mark deductions and missing proof,
respectively. A source match does not override a different current implementation.

## Integration, Tag And Branch

M2H started clean on research/inflight-read-termination at
`8ceede2e618ceb02a1f65d5f4884e84ca6b0035a`, equal to upstream with zero divergence.
Its three linear commits and seven changed UTF-8 blobs across five documentation
paths were audited. Main was `2b1565ee61337a368d75980af281621a5959000e`;
all 18 historical branch/tag/peeled identities matched locally and remotely.

The --no-ff merge is `1a014d8d3c3cd35ed5381160b809cf4803d79d69`, message
`merge: record in-flight selector termination investigation`, with parents
`2b1565ee61337a368d75980af281621a5959000e` and
`8ceede2e618ceb02a1f65d5f4884e84ca6b0035a`. Its tree equals the audited M2H tree.
Main was pushed. Annotated tag `inflight-read-safety-v0.5`, object
`9d794c6592dff959808e42f02815e8cd9ef8c6d7`, peels to that merge; its message is
`Verified MacMST in-flight selector termination assessment before any DPCD transaction.`
The tag was pushed and read back before creating research/w06-wake-or-strand
from the tagged merge. Historical branches and tags were not deleted or moved.

At 2026-09-13T11:38:54Z, macOS remained 26.6.2 (25G83), kernel UUID
`447D769E-1CB7-3086-A0B4-32226837B587`. The successful and stopped M2F receipt
hashes and consumed marker hash were rechecked. The latter remains
`2f3da1f224c0602dc46f812d3f6eb2c1560fe7a82c1a89f93eedb725b2726efc`.

## Exact CommandContext

VERIFIED_ON_CURRENT_KERNEL: the context is in
DCPAVProxy::performCommandGated, called synchronously from the read's response-
taking block. It is not an inline object in DCPDPDeviceProxy::readDPCD itself.
Let S be SP after the 80-byte subtraction at 0xfffffe000a018f44, and let B be
SP after the caller block's 32-byte subtraction at 0xfffffe000a0090a8. Both are
runtime kernel-stack addresses; no actual address value was measured.

The 24 bytes used as C start at S+8. The pair store at 0xfffffe000a018f7c
(`ff9300a9`) writes zero to S+8 and x4 to S+16; the store at
0xfffffe000a018f80 (`e50f00f9`) writes x5 to S+24.

| Stack / Context Offset | Width | Established Purpose | Writer(s) | Reader(s) |
| --- | --- | --- | --- | --- |
| S+8 / C+0 | 4 bytes | Completion status, initialized zero; no separate done bit | Initial zero store; handleResponse at 0xfffffe000a0190e8 writes incoming status | performCommandGated at 0xfffffe000a019030 after normal sleep return |
| S+12 / C+4 | 4 bytes | Zeroed by the 8-byte initialization; no additional meaning established | Initial zero store | No semantic read established in these complete context bodies |
| S+16 / C+8 | 8 bytes | Pointer to the kernel OSData reply region | Initial x4 store, passed from the response-taking block | handleResponse at 0xfffffe000a0190b4; used as copy destination when nonnull |
| S+24 / C+16 | 8 bytes | Pointer to reply-size storage in the caller block, B+8 | Initial x5 store | handleResponse at 0xfffffe000a0190c0/e0; abnormal sleep-return cleanup at 0xfffffe000a019020 |
| B+8, reached through C+16 | 8 bytes | Caller-local reply capacity/result size, initially logical message size | Caller block at 0xfffffe000a0090b8; handleResponse at 0xfffffe000a0190e4; abnormal return stores zero at 0xfffffe000a019028 | handleResponse bounds its local copy using the pointed-to value |

The output bytes live outside C in kernel OSData, not in the helper's userspace
buffer. No command pointer, callback object, separate error field or completed
flag is stored in the 24 used context bytes. Those roles must not be assigned to
the zeroed four-byte remainder. The first outgoing stack argument at S+0 is NULL,
outside C; proxy+200 is a separate outstanding counter, not part of C.

## Exact W06 Event

The enqueue context and W06 event are the same pointer: **E = C = S+8**.
Instructions at 0xfffffe000a018fa4 and 0xfffffe000a018fdc both compute
`add x1, sp, #8` (raw `e1230091`). The latter is followed by raw w2=0 at
0xfffffe000a018fe0 (`02008052`) and gate+512 call at 0xfffffe000a018fe8.
The retained lower path forwards flag 0 to _assert_wait with no deadline.

The known completion writer/waker is DCPAVProxy::handleResponse at
0xfffffe000a01908c: incoming context x2 becomes x19, status is stored at [x19]
at 0xfffffe000a0190e8, and x19 is passed as the event at 0xfffffe000a019110
before the gate+520 tail call at 0xfffffe000a01913c. Its last context access
precedes that wake. This is a local ordering property, not yet a universal
callback-quiescence proof.

The adapter callback at 0xfffffe000926e0a8 loads its captured context from
block+56 and forwards it to the response handler when the submission-failure
boolean is false. Its true branch writes a separate by-reference submission
result, not C's status and not E's wake. The normal post-wait wake at
0xfffffe000a019068 uses proxy+200, not E, and cannot rescue W06 itself.

## Local Proof Question

The falsifiable hypothesis is that the suspicious local-list cleanup applies to
the very command carrying C, but a reachable cleanup-only ordering while W06 is
asleep is not yet established. The discriminating check is pointer/field identity
from enqueue through tag lookup/removal, plus the cleanup caller's gate and
preconditions. A mandatory prior C-completion and callback drain would refute
stranding; a reachable cleanup without them would support a constructive proof.
No generic graph expansion or hardware experiment is needed to formulate this
check, and neither conclusion is assumed from class names alone.

## Bounded Exact-Event Wake Set

The concrete W06 status writer and event-wake site are one pair:
handleResponse's status store at 0xfffffe000a0190e8 and event-E tail wake at
0xfffffe000a01913c. Several triggers can reach that pair; they are not independent
fallback wakers. The registered DCP response wrapper at 0xfffffe000a0198cc
forwards its incoming context to that handler by the direct tail branch at
0xfffffe000a0198e4. The adapter callback and AFKEndpointInterfaceClient wrapper
at 0xfffffe000926ea68 preserve the same context pointer.

The bounded set below is the set established in the retained native read/response/
cleanup bodies. It is not a whole-kernel alias/wake completeness theorem. Indirect
transport callbacks and unestablished teardown triggers cannot be represented as
either nonexistent wakes or guaranteed wakes.

| Trigger | Function / Address | Condition | Status Before E Wake? | Callback Quiesced? | Command Removed First? | Guaranteed? | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Normal matching response | handleClientResponse 0xfffffe000928384c -> response task -> deliverResponse 0xfffffe0009278414 -> adapter 0xfffffe000926e0a8 -> registered wrapper 0xfffffe000a0198cc -> handleResponse | K is found by tag, dispatcher exists, response task is delivered, captured C is live | Yes, in final handler | Final handler's last C access precedes wake; universal no-future-invocation proof is absent | Yes, removeCommand unlinks K before asynchronous dispatch | Conditional, not a missing-response guarantee | VERIFIED_ON_CURRENT_KERNEL |
| Delivered transport or operation error | Same response-delivery chain and final writer/waker | Nonzero delivered status or returned payload error; no discarded callback | The handler writes delivered status first; the separate payload error is read later by the DP frame | Same local ordering and unresolved global quiescence | Yes on queued asynchronous response path | Only if actually delivered | VERIFIED_ON_CURRENT_KERNEL |
| Synthesized Offline error | createErrorResponses 0xfffffe0009283734 -> normal tagged handler | Notification 4, or report 19 with its flag; report 20 funnels through notification 4; task delivery must still run | Yes through the same final handler; raw Offline 0xe00002d7 | Not a firmware cancel/drain acknowledgement; late-response exclusion incomplete | Yes, normal removeCommand path | Trigger/order/delivery not universal or bounded | VERIFIED_ON_CURRENT_KERNEL / UNKNOWN |
| Immediate submission failure | Adapter callback's submission-failure branch at 0xfffffe000926e0b4-0c4 | Failure flag true before successful enqueue return | No C write or E wake; separate by-reference return status is written | No W06 wait has been entered on this failed-submission path | No successfully listed waiting K required | Not a wake route for an already sleeping W06 | VERIFIED_ON_CURRENT_KERNEL |
| Optional synchronous AFK response completion | KextV2 callback invocation at 0xfffffe0009276cb0 | The AFK synchronous-response option is selected | Can reach the same handler while enqueue is still active | Different ordering, not a cancellation path | Optional synchronous path has different command ownership | Excluded by the retained selected asynchronous options; not an extra W06 rescue | VERIFIED_ON_CURRENT_KERNEL, selection retained from M2H |

The payload-error distinction above does not revisit reply completeness. A
delivered callback's status is the only evidenced C status write after
initialization. There is no done/completed predicate checked before W06 sleeps;
the submitted asynchronous path relies on its gated delivery ordering, not a
newly invented completion flag in C+4.

### Rejected Wake Substitutions

| Candidate | Actual Event / Effect | Why It Is Not An Independent E Wake |
| --- | --- | --- |
| releaseCommand, 0xfffffe0009285590 | AFK interface+144 after count+145 decrements | Capacity event, not S+8 |
| KextV2 close callback, 0xfffffe0009275a30 | Endpoint object passed at 0xfffffe0009275a88 | Endpoint-state admission event, not C |
| performCommandGated's final wake, 0xfffffe000a019068 | DCP proxy+200 | Runs only after W06 returns and uses the counter address |
| Gate removal / enable | Gate enabled field or gate+72 | Entry/removal handshake, not an in-action CommandContext |
| Selected abort, 0xfffffe0009279284 | Complete hint/ret body | No status write, E argument consumption, tag removal or wake |
| cleanupRemoteContext / local-command release | List/tail/count changes and node/transport-buffer disposal | Neither directly invokes C's callback nor writes/wakes C |
| clearAll / event-source free | Response allocation/task disposal or empty-queue assertions | Callback data lifetime is not converted into E completion |
| Client/task teardown | Retained M2H guards/deferred cleanup | No new exact-C waker is established by the narrow context path |

The three start-time callback wrappers are not interchangeable: 0xfffffe000a0198cc
directly forwards to the known completion handler, while 0xfffffe000a009494 and
0xfffffe000a0094a8 tail to other functions. No additional E wake is inferred from
their shared start-related names.

## Pointer Identity: The Suspicious List Is This Read's List

Let P be the retained KextV2 endpoint receiver and I its embedded
AFKEPInterfaceV2 subobject at **P+160**. These are relative identities, not a
measured runtime address. The read's submission block at 0xfffffe0009277060
passes P+160 to AFKEPInterfaceV2::enqueueCommand at 0xfffffe0009277158/7178.
That enqueue routine inserts the successful command K into **I+40**, updating
tail **I+48** at 0xfffffe00092856d4-6dc. It assigns an eight-bit tag from I+146,
and the constructor writes that tag at **K+41** at 0xfffffe000925ea48.

The callback pointer travels separately from the node tag:

| Boundary | Exact Pointer / Store | Consequence |
| --- | --- | --- |
| Adapter block construction | enqueue adapter saves C in x23 at 0xfffffe000926de90 and stores it at its stack block+56 via 0xfffffe000926df9c | Callback captures raw C; C is not copied into the block |
| KextV2 submitted command | Submission block passes callback pointer in x1 at 0xfffffe0009277164 to enqueueCommand | Context argument for this AFK command is the callback pointer, not C directly |
| AFK local-command constructor | Incoming context x4 is kept in x26; 0xfffffe000925e92c stores it at K+24 | K+24 references the per-read callback; K+41 is its lookup tag |
| Response lookup | removeCommand at 0xfffffe0009283af4 starts with I+40 and compares node+41 | The response tag identifies this same K, not another remote list |
| Response dispatch | handleClientResponse loads K+24 at 0xfffffe0009283a1c and passes it to dispatchResponse | The callback can move into a queued task after K is unlinked |
| Suspected cleanup | cleanupRemoteContext at 0xfffffe0009283a70 removes local nodes from I+40, updates I+48 and calls K's release at 0xfffffe0009283ad4 | This is the pending-read list, not merely the separately cleared remote list at I+56 |

Enqueue, removeCommand and cleanupRemoteContext each load I+16 and call the same
gate-check target **0xfffffe000927bcac** at 0xfffffe000928560c,
0xfffffe0009283b10 and 0xfffffe0009283a88. handleClose at
0xfffffe0009285040 runs its cleanup block under that workloop; the block at
0xfffffe000928511c loads I from block+32 and tail-calls cleanupRemoteContext.
closeHelper at 0xfffffe000927553c supplies P+160 to handleClose. Thus the object
and list correspondence is supported by offsets and argument forwarding, not
class names alone.

Local applicability is established **if that cleanup executes with K still
pending**. It remains a different obligation to prove an allowed DCPDP trigger
can enter that state while W06 sleeps without a mandatory prior completion or
drain. The same-list proof does not silently discharge that reachability condition.

## Pending-Command Removal Paths

This is the central removal artifact. It inventories the concrete removals in the
retained selected path and names incomplete boundaries separately. It is not an
assertion that all possible indirect owners or dispatcher writers were enumerated.
The retained R7 direct-call evidence identifies three calls to the local command's
release: response handling at 0xfffffe0009283a38, list cleanup at
0xfffffe0009283ad4, and enqueue failure/optional synchronous completion at
0xfffffe0009285704. The separately freed remote list is not K's list.

In the table, before/during/after refers to removing K from normal tag lookup,
or to disposing its already detached response task. "No local wake" describes
the inspected body, not an unproved absence of every earlier or later wake.

| Removal Path | Reachable While W06 Waiting? | W06 Wake Before / During / After; Future Waker | Callback Invoked / Destroyed Uninvoked? | Late Reply Lookup | Result |
| --- | --- | --- | --- | --- | --- |
| M01: matching response removes K; removeCommand 0xfffffe0009283af4, then handleClientResponse | Yes on the retained asynchronous normal-response route | No required prior wake; no E wake during unlink; E wakes later only if the queued callback is delivered. The task is a possible future producer, not a universal delivery guarantee | Normal delivery invokes callback then releases its block. K is freed after dispatch, not before callback state has been transferred | Old K is no longer listed; a duplicate with no matching live tag is dropped | Conditional normal completion, not response-independent wake |
| M02: synthesized Offline response through M01 | Conditional qualifying notification/report and delivery | Same unlink-before-wake order; status is written before the eventual E wake | Same normal callback path if dispatched; not firmware quiescence | Old tag removed before later firmware reply; generation/session barrier not fully proved | Real conditional fallback, not a must-wake theorem |
| M03: matching response with dispatcher I+120 null | Conditional branch exists at 0xfffffe0009283958/395c; writer/lifecycle establishing null while this K waits is not attributed | No prior E wake required by the local branch; none during node release; no later E producer is established by this branch | Dispatch skipped. Local-command release does not load/release/invoke K+24; callback disposition beyond this body is unknown | K removed; a missing-tag reply is dropped, not completed | Potential lost completion, but trigger reachability is unproved |
| M04: cleanupRemoteContext clears pending local list I+40 | Same I/K list proved; end-to-end trigger ordering while W06 waits remains unresolved | No C write or E wake in cleanup or local-command release. Mandatory prior error delivery and any remaining later producer are not proved | K+24 is not invoked or released by the local release body. Node disposal does not prove callback destruction or quiescence | K's node removed and freed; no lookup of that old node remains. Other-session/tag reuse protection is not established here | Central suspected stranding path; not yet a constructive counterexample |
| M05: clearAll discards a queued type-1 response task | Local task type/fields match dispatchResponse; cleanup-vs-delivery entry ordering for this pending read is unresolved | K was unlisted earlier. No E wake in the type-1 discard branch; no guaranteed replacement producer is established | Releases task+24 data allocation and frees task; no load/invoke/release of task+32 callback in this branch. Uninvoked callback destruction is not demonstrated | No old K in list; queued data/task destroyed | Different loss point after unlink, with the same reachability/lifetime proof gap |
| M06: event-source free, 0xfffffe000925e7d4 | Requires current-task+80 and queued-head+88 both null; otherwise cold assertion paths | No E wake; empty queue is not a completion receipt for previously discarded tasks | No automatic per-read callback invocation or drain added by free | Normal dispatcher unavailable only if its owner/link state changes; no independent tag invalidation theorem | Final resource disposal, not a proven additional cancellation path |
| M07: enqueue failure or optional synchronous command release | Failed submission does not enter W06; synchronous mode is not the selected asynchronous request | No E rescue for the already waiting asynchronous command | Submission failure sets separate return status and releases owned block when copied; optional synchronous mode has separate lifetime | No successfully pending asynchronous K in the failed-submission case | NOT_RELEVANT_TO_DCPDP_READ under the one submitted asynchronous-read premise |
| M08: normal callback _Block_release after invocation | Normal deliverResponse, after handler returns | E wake precedes release within normal delivery; release itself does not wake E | Invoked first at 0xfffffe0009278474; then __Block_release at 0xfffffe000927847c. It is not evidence that all other possible owners/invocations are quiesced | K already unlisted and response ownership separate | Normal owned-reference disposal only |
| M09: dispatcher registration loss / final endpoint-context destruction | Relevant as a possible loss of the future producer, but complete writer/final-owner ordering is not recovered | No exact-C wake follows merely from a null registration or destroyed owner | All final block owners, disposal helpers and synchronization are not fully attributed | Depends on surviving endpoint/session state, not a guaranteed drop/completion rule | Explicit unclosed removal boundary; do not assert full removal-set closure |

AFKEPCommandLocal::release at 0xfffffe000925ea84 has a fully retained 84-byte
body: it conditionally cleans transport allocations at K+72 and K+80, then frees
K. It never loads K+24 or calls its invoke pointer. Therefore M04 is not secretly
normal completion in that body, and freeing K cannot be called a release of C.
Effects inside the transport-allocation cleanup callback are not an established
exact-C cancellation contract either.

clearAll's type-1 branch at 0xfffffe000925e6e0-704 uses the response allocation
at task+24 and then frees the task. dispatchResponse at 0xfffffe000925e46c sets
that task type to 1 and stores its callback context at task+32. The clearAll
branch does not read task+32. This distinguishes a discarded response task from
the normal deliverResponse invocation/release path. It does not prove the block
is necessarily destroyed; an uninvoked retained block could instead be stranded.

## Suspicious Cleanup: Entry And Ordering

The exact local chain is:

```text
KextV2 endpoint P close
	-> close block (P+168 outer gate)
		 if captured EPIC client is null OR P+136 collection count <= 1:
			 closeHelper(P)
				 -> handleClose(I = P+160)
						requires I+8 gate; runs block under I+16
							-> cleanupRemoteContext(I)
								 requires I+16 gate
								 removes local K from I+40 and frees it
								 zeros reservation count I+145
				 -> later event-source cleanup may call clearAll
		 -> wake(P), not wake(C)
```

At 0xfffffe0009275a48, the close block checks the captured client; otherwise it
loads P+136, queries the collection count, and at 0xfffffe0009275a78 skips
closeHelper for count greater than one. These are actual entry predicates, not
proof the live DCPDP endpoint satisfies them. handleClose's block at
0xfffffe000928511c has only the captured receiver load and direct cleanup tail
call. That local block contains no preceding createErrorResponses or C wake.

List cleanup resets I+145 but does not reset I+146's next-tag byte or perform an
individual tag-reservation release/wake operation. K becomes unreachable through
I+40 because its node is unlinked, not because a new E-completion bit is set.
The returned-reservation event I+144, even if another path later wakes it, is not
C. A late reply can no longer find the removed old node in this list.

W06 releases its own workloop's recursive lock while asleep, so it does not by
itself rule out other gated work. However, that is not proof that a physical
disconnect, endpoint-offline transition, provider stop or client death may reach
the chain above with K still listed and no earlier queued/completed error. The
outer close eligibility, gate/progress relationships and error-vs-cleanup ordering
for the selected endpoint remain obligations, not facts inferred from a callsite.
The retained DCP close/stop evidence is not an instruction to bypass those guards.

### Cleanup Trigger Reachability

Reachability below means the full trigger-to-removal path for this selected
read while W06 is still pending. A class-local function that could manipulate K
is not automatically reachable from every trigger.

| Trigger / Subpath | Classification | Established Link / Missing Condition |
| --- | --- | --- |
| Local handleClose(I) -> cleanupRemoteContext(I), with pending K already in I+40 | REACHABLE_FOR_DCPDP_READ, conditional on entry | Identical P+160 receiver and pending list proved; this conditional local classification does not prove the trigger or error ordering |
| Physical sink/hub disconnect -> that cleanup with unwoken C | REACHABILITY_UNRESOLVED | No mandatory HPD-to-this-close transition or proof it precedes normal/synthesized completion |
| DCP endpoint offline -> notification/report -> command disposal | REACHABILITY_UNRESOLVED | Qualifying notifications can synthesize Offline completion; not every offline condition's dispatch, cleanup and quiescence order is recovered |
| Selected provider service stop -> endpoint closeHelper while K pending | REACHABILITY_UNRESOLVED | Retained conditional endpoint close exists, but eligibility and prior drain/error ordering are not proved with this active read |
| Process/client teardown -> selected endpoint cleanup | REACHABILITY_UNRESOLVED | A client is not the pre-existing endpoint; retained IPC/action/lifecycle deferral does not establish this trigger reaches cleanup while C waits |
| Remote list I+56 or optional synchronous-command branch | NOT_RELEVANT_TO_DCPDP_READ | Neither is the selected asynchronous local K list/lifetime; no counterexample may substitute it |

### Eight-Step Constructive Proof Test

| Step | Obligation | Result |
| --- | --- | --- |
| 1 | Specific native read creates stack C | PROVEN_LOCAL: exact stores and live caller/perform frames |
| 2 | K carries the callback that refers to C | PROVEN_LOCAL: block+56 raw C -> K+24 callback, K+41 tag |
| 3 | Successful submission reaches W06 waiting on E=C | PROVEN_LOCAL for the selected asynchronous path; raw event/flag known |
| 4 | No normal response has completed K | Valid counterexample premise; not a measured M5 failure |
| 5 | Reachable teardown T removes K while C is still waiting | NOT_PROVEN: same-list cleanup is established, but trigger eligibility and completion-vs-cleanup ordering are not |
| 6 | T does not wake E | PROVEN_LOCAL for cleanup/release/type-1 discard bodies; not proof of absence of all earlier/later wakes |
| 7 | No remaining reachable object guarantees E completion after T | NOT_PROVEN: callback/dispatcher/session ownership and complete wake/removal closure are incomplete |
| 8 | W06 is uninterruptible and deadline-free | Current flag/callee evidence plus retained pinned XNU semantics, unchanged from M2H |

The eight obligations do not all pass. M04 cannot be promoted to a proven
stranding path by assuming steps 5 and 7. Conversely, the missing before/after
completion-and-drain invariant prevents a response-independent-wake proof. This
milestone will not manufacture a reachable schedule from local no-wake code alone.

## Callback Ownership And Quiescence

Result: **CALLBACK_QUIESCENCE_UNRESOLVED**. The following local ownership facts
are established without pretending to know a total block reference count.

| Phase | Storage / Owner | Exact Evidence And Limit |
| --- | --- | --- |
| Adapter construction | A stack block Q at adapter-frame SP+16 | invoke pointer at Q+16 names 0xfffffe000926e0a8; Q+32 is a separate by-reference submission-result object, Q+40 the endpoint pointer, Q+48 the endpoint-client pointer, Q+56 raw C. Stores at 0xfffffe000926df94-9c establish these captures |
| Submission block | KextV2 submission callback initially carries Q | At 0xfffffe000927711c/7120 the asynchronous case passes Q to the copy/retain target 0xfffffe000bf69c94; resulting pointer is supplied as the command context. This target's full current body is not retained in the bounded evidence set, so its allocation/dispose-helper details are not upgraded to current-byte proof |
| Pending K | Context field K+24 carries the callback pointer | It does not hold C itself or an owned copy of C. Local-command release has no callback field access |
| Response task | dispatchResponse transfers the callback pointer to task+32 and data allocation to task+24 | K can then be freed; task lifetime and delivery no longer depend on finding K in the pending list |
| Normal invocation | deliverResponse invokes callback at 0xfffffe0009278474, then releases it at 0xfffffe000927847c | It releases the AFK capacity reservation before invoking Q. The adapter calls the endpoint-client's stored response block, which reaches the registered DCP wrapper and final C handler |
| Normal block disposal | __Block_release at 0xfffffe000bf69e20 | Complete retained 264-byte body decrements flags/refcount and conditionally runs a dispose helper before freeing. It does not invoke Q's completion entry or wait for an independently executing callback |
| Cleanup without delivery | M04/M05 remove the node or task that carries Q | Neither local branch invokes Q nor calls __Block_release on its stored pointer. Whether another owner releases it uninvoked, retains it, or later invokes it is not fully attributed |

PRIMARY_SOURCE: pinned XNU f6217f891ac0bb64f3d375211650a4c1ff8ca1ea,
[libclosure/runtime.cpp](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/libkern/libclosure/runtime.cpp),
_Block_copy copies stack block storage or increments a heap block's reference
count, invoking a copy helper when present. _Block_release invokes a disposal
helper only on the final owned release; it is not the block's completion invoke
function. This corroborates the ownership distinction, not a recovered complete
current descriptor/copy/dispose layout for Q. No retain operation on C is present
in the exact raw-C stores and forwarding bodies.

Normal completion has a useful narrower property: after the final handler writes
status and tail-wakes E, it performs no further C loads/stores. Q and outer
callback frames can still exist until their ordinary returns and block release.
Thus "callback object still exists after wake" is not by itself a C access after
scope. Conversely, waking E does not prove no other invocation or queued producer
can later use C. K's single normal removal eliminates another normal lookup of
that old node, but callback aliases, dispatch disposal and tag/session reuse are
not fully closed. No atomic done flag, once-only C completion primitive or
cancel-and-join barrier was recovered for all removal paths.

The current __Block_release body hash is
`fb90a29fcb21b6c134067e9e08e3b579ddc5b02f6295a843cce0b495c157effb`.
Its optional disposal helper is not a reason to assert that every callback is
destroyed or invoked on command cleanup. A command free, a block release and an
invocation-quiescence barrier are three distinct operations.

## Late-Response Race

Result: **LATE_RESPONSE_STACK_SAFETY_UNRESOLVED**. Analyze two local competitors:
T attempts pending-list cleanup; R receives a response for K's old tag.

| Ordering | Established Local Behavior | Limit For Stack C |
| --- | --- | --- |
| R unlinks K first under the required list gate | removeCommand returns the raw node, with no extra node retain in that body. K is no longer in I+40; R transfers Q/data into its response task before releasing K | A later traversal of I+40 cannot free that now-unlisted node. Q may be invoked after node removal as designed. Full task-delivery/cleanup ordering and C's final scope remain separate |
| T removes/frees K first under the required list gate | A later lookup with no matching live tag returns null and drops/logs the response without accessing the freed old K | This local missing-tag drop does not wake E. A reused tag and outer session/generation policy are not resolved by this local lookup |
| T discards an already queued response task | The type-1 discard releases its data allocation and frees its task without Q invocation | No E completion or Q quiescence follows from that discard. The exact trigger/serialization against an in-progress task remains unproved |
| Q is already executing when E is woken | Final handleResponse's last C access precedes its wake, then ordinary callback return/release follows | Normal local ordering is compatible with safe scope exit, but does not prove all other Q references/invocations are excluded |
| W06 returns abnormally while K/Q remain | Its branch calls the selected no-op abort and returns an error after zeroing the size output | This would require a callback-drain proof. A reachable independent abnormal-wake schedule for this exact uninterruptible wait has not been established, so it is not declared a stack UAF |

The shared gate requirement supports serialization of the legitimate local list
operations; it is not a recovered global command-retain protocol. The exact
gate-check target is known from calls, but its body and the complete caller/task
locking set are not independently closed here. We therefore do not assert a
response can free K concurrently with cleanup, or that removal synchronizes with
all already detached callback tasks. No concrete stack use-after-free sequence
is proved; no exploit or hardware race experiment is proposed.

## Task-Death Stack Lifetime

Result: **STACK_PRESERVED_WHILE_W06_BLOCKED**, scoped to the ordinary retained
no-continuation wait and corroborating pinned XNU lifetime contract. This is not
proof of callback quiescence after the wait returns or of prompt task reaping.

VERIFIED_ON_CURRENT_KERNEL: the mutex-sleep path supplies x0=0, x1=0 and w2=0
before its blocking call at 0xfffffe000b8093d0. The retained target
0xfffffe000b8231d4 preserves those incoming arguments and at
0xfffffe000b823270 stores the continuation/parameter pair at current-thread+216
as zero. Its ordinary return resumes the caller stack. This target is 488 bytes,
SHA-256 `5e820be8fc12e3a7d96a40975fe99cc8b6545a5d835362c64c50be7c0ba5530a`;
the semantic thread-field names are corroborated by pinned source, not inferred
from the offsets alone.

PRIMARY_SOURCE: in pinned
[sched_prim.c](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/kern/sched_prim.c),
thread_block_reason stores continuation/parameter; thread_dispatch discards a
blocked thread's kernel stack only for a nonnull continuation. The W06 path uses
THREAD_CONTINUE_NULL. Pinned
[thread.c](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/kern/thread.c)
requires final reference count zero and TH_TERMINATE2 before final thread
deallocation and stack_free. The retained M2H interruption/AST evidence says task
death requests abort but does not immediately dispose of an already-blocked
TH_UNINT frame.

INFERRED from these local bytes and source contracts: while the thread remains
blocked in W06, C stays in its kernel stack. A killed process with such a pending
kernel call is therefore compatible with retained stack/resources, not automatic
stack destruction at signal delivery. There is no evidence here that SIGKILL
alone frees C beneath Q. The current binary's entire final-deallocation graph is
not claimed proved, and a future wake/return still requires quiescence before
the retained raw pointer can safely outlive that frame. This narrow preservation
result cannot turn a hang into a safe terminal state.

## Constant 500: W06 Relevance Only

**500_MEANING_UNRESOLVED** is retained. No examined path associated with the
serialized field independently writes C's status, invokes Q, wakes E or drains
callback ownership. An actually delivered error could use the known completion
chain, but a presumed firmware timeout with an absent reply is not that chain.
No new 500-unit/expiry speculation or broader constant search was performed.

## Decision Matrix

| Question | Result |
| --- | --- |
| Exact W06 event known | YES: E=C=S+8 in the live performCommandGated frame; status/output/size layout recovered |
| Exact W06 wake writers known | Known local pair and bounded producer set established; complete all-route closure NOT_PROVEN |
| All command removal paths enumerated | NO: M01-M09 bound the retained set; final dispatcher/owner and indirect transport closure incomplete |
| Suspicious cleanup applies to this read | YES locally: same P+160 / I+40 list and K+24 callback / K+41 tag |
| Removal without wake reachable | NOT_PROVEN end-to-end: local no-wake branches exist, but trigger and prior/future completion ordering unresolved |
| Callback quiescence | CALLBACK_QUIESCENCE_UNRESOLVED |
| Late response stack safety | LATE_RESPONSE_STACK_SAFETY_UNRESOLVED |
| Task-death stack lifetime | STACK_PRESERVED_WHILE_W06_BLOCKED, source-corroborated ordinary wait; not post-return quiescence |
| Cleanup trigger reachability | REACHABILITY_UNRESOLVED for a selected DCPDP trigger while E remains unwoken |

## W06 Result And Mandatory Stop

Primary result: **W06_WAKE_STATE_UNRESOLVED**.

The response-independent proof fails because no universal status/write/wake/drain
invariant covers every removal/death/disconnect case. The constructive stranding
proof fails because local same-list disposal is not proof of an eligible
unwoken-cleanup schedule or of every remaining future producer's state. Neither
failure licenses the opposite conclusion. Local no-wake cleanup is real evidence,
but it is not promoted to CURRENT_SELECTOR0_TRANSPORT_UNSAFE without all eight
required stranding obligations. Nor is a wake without quiescence promoted to a
termination proof.

- Transport: **NO_TRANSPORT_READY**.
- In-flight termination: **INFLIGHT_READ_TERMINATION_NOT_PROVEN**, unchanged.
- One-byte gate: **NOT_READY_FOR_ONE_BYTE_DPCD_READ**.
- Global gate: **NOT_READY_FOR_DPCD_TEST**.

**STOP FURTHER STATIC EXPANSION OF THIS SELECTOR TRANSPORT.** Do not open M2J as
another generic graph search. The recommendation is to **abandon this selector
transport on the daily-use Mac**. This is a safety/engineering decision for the
current undocumented transport and evidence, not a claim about hardware MST
support or mathematical impossibility of a future proof.

No selector run, repeat open, concurrent close, forced wake, cancellation test or
physical disconnect is proposed. The optional alternative of a separately owned
non-daily-use/reboot-risk environment would require a distinct future decision
and explicit authorization; nothing is scheduled or executed automatically.
Reply completeness remains a separate frozen gate and is not reopened by this
unresolved result. Remaining work in M2I is validation and publication only.

## Provenance And Reproduction

M2I reuses retained R3/R4/R7/R9 bytes. No new kernel extraction, graph generation,
firmware search, source download or public display capture was performed. Each
report still records kernel UUID 447D769E-1CB7-3086-A0B4-32226837B587, matching
the running build. The shared container SHA-256 is
`b20d50fc8f445a5c578ac63bd974efeb6ae48a97116800301071891795fb26d9`.
Preferred addresses below are image evidence, not live callable addresses.

| Retained Report Under artifacts/probes | SHA-256 |
| --- | --- |
| R3: iodp-static-20260912T045748Z/iodp-static.json | `b80b5f6b1d9553ce1ee1b292f68102369d0c7e3d29cfdd6ab80ff3c9c199b263` |
| R4: iodp-static-20260912T095457Z/iodp-static.json | `1262f818b09a562b22c4649c97d94e77a5c865148268793cd2a9dc8d5c72ab1f` |
| R7: iodp-static-20260912T115605Z/iodp-static.json | `e52a1db96cad564a3ea0cfebf0884942e8d2139bbc481a8580517b6697077102` |
| R9: iodp-static-20260912T141129Z/iodp-static.json | `587ef7b55e8ed3a5fd0e88e69c0d160ac2973ddbcaa9a6ac86bf04a71dc1f966` |

Of the analysis's 72 distinct concrete code addresses, 70 occur in 31 retained
full bodies. Concatenated instructions[].bytes_hex matches each body's declared
size and SHA-256; overlapping report copies agree. Two addresses are explicitly
target-only evidence: the common list-gate check at 0xfffffe000927bcac and the
copy/retain call target at 0xfffffe000bf69c94. Their incoming raw branch targets
are checked, but their bodies are not retained in this bounded set. They were
not silently classified as complete or expanded after the stop decision.

| Body / Preferred Address | Bytes | SHA-256 |
| --- | --- | --- |
| performCommandGated, 0xfffffe000a018f40 | 332 | `98bf09b907fc17558a5f487ba143182ab3e613585f21ae6f8e30c63c153efee3` |
| handleResponse, 0xfffffe000a01908c | 184 | `1f742a141915f52fe31f893cfcaaa392ed3c594bfe9f247152d9e5ddd32c7cf7` |
| Caller response-taking block, 0xfffffe000a0090a4 | 64 | `9da8d72d6ee5e3dd42bfa1e1328b6c059975c0262ed1f6ee2759ae43ca600845` |
| Adapter callback, 0xfffffe000926e0a8 | 60 | `db1b1890ef169bcb0634177f6f1dfbfe8be3684c8f4154eea6a05c2e81049a7b` |
| Adapter enqueue, 0xfffffe000926de54 | 496 | `fec6d8c7c7f29cbb063654fc9f2118d4b9271c48135212f1d8b6661060afdc2e` |
| Submission block, 0xfffffe0009277060 | 324 | `76533a33f9678d3122419f39a1034407c611bf1490de4104f0f6257c62021da4` |
| Local-command constructor, 0xfffffe000925e8c4 | 448 | `3bf480c3817092a6ec60a48c8cca53f0a4391d8c784c8e69ee19fc03eda0e6c2` |
| Registered DCP response wrapper, 0xfffffe000a0198cc | 28 | `313bbafb439f66f8af1cd1a07c5d47a999b2f38df7fb93db0a5662280e1085d8` |
| KextV2 close block, 0xfffffe0009275a30 | 164 | `d75135feba828f22dfdae4eb73a69c4f030dd46494b60b7b182226ccba6c99a0` |
| handleClose cleanup block, 0xfffffe000928511c | 12 | `e86e89ce9f8ab4b9c7710ad902031b408786e86294a2425719cdc4243cee5dd4` |
| clearAll, 0xfffffe000925e660 | 372 | `b2379fb34a1c9dc47a5ff9619c18d942b678635a1b2cfea42f07fdefaf6608a8` |
| __Block_release, 0xfffffe000bf69e20 | 264 | `fb90a29fcb21b6c134067e9e08e3b579ddc5b02f6295a843cce0b495c157effb` |
| Blocking handoff, 0xfffffe000b8231d4 | 488 | `5e820be8fc12e3a7d96a40975fe99cc8b6545a5d835362c64c50be7c0ba5530a` |

The three narrow source files were compared byte-for-byte with the retained XNU
archive at revision f6217f891ac0bb64f3d375211650a4c1ff8ca1ea, archive SHA-256
`0763146d2b5459b070d802aaba9526cead7fb0d55d0d51ba0069818030150b15`. M2I did not
extract or execute that archive. Source-only lifetime rules remain labeled as
source corroboration rather than exact current-binary ownership proof.

| Path In Pinned XNU | SHA-256 |
| --- | --- |
| libkern/libclosure/runtime.cpp | `5491b762a75e4660612be5ae0b07886bea187aa11c4f1a285f0dd99f0f72d927` |
| osfmk/kern/sched_prim.c | `b2a2654b21d7731fce2f51f839c378a85e901d58f0c4a8d7d9effd5d39f83dbf` |
| osfmk/kern/thread.c | `8a4d00524913a5082c8d157b33e9ed52c0899c82de371e1188b6f5c3143426e2` |

Safe checks of already retained evidence and identities:

```sh
sysctl -n kern.uuid
git rev-parse inflight-read-safety-v0.5
git rev-parse 'inflight-read-safety-v0.5^{}'
shasum -a 256 artifacts/probes/iodp-static-20260912T045748Z/iodp-static.json
shasum -a 256 artifacts/probes/iodp-static-20260912T115605Z/iodp-static.json
shasum -a 256 artifacts/sources/m2e1/xnu-f6217f8.tar.gz
shasum -a 256 artifacts/probes/M2F-ATTEMPTED
```

A fresh clone does not contain ignored captures, archives or binaries. Missing
evidence is not a reason to fabricate a hash match, substitute another kernel
build or restart static/private investigation. The completed M2H report remains
the retained source for frozen lifecycle/wait conclusions; this milestone narrows
the context and proof obligations rather than rewriting that history.