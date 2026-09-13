# M2G: One-Byte Selector-0 Read Readiness

## Scope

This milestone assesses only a possible future selector-0 request at DPCD address
0x000 with requested output length one byte. It does not invoke a selector,
repeat DPDV open/close, read DPCD/AUX, change the link, or perform MST operations.
The consumed M2F attempt marker remains present. A proposed separate
M2G-DPCD-READ-ATTEMPTED marker is not created. The global execution gate remains
**NOT_READY_FOR_DPCD_TEST** regardless of this static assessment.

The verified M2F runtime observation is **DPDV_OPEN_CLOSE_RUNTIME_VALIDATED**.
It establishes connection acceptance and immediate-close viability in that one
calling context. It does not establish userServer==nullptr, native/delegated
routing, absence of internal work, selector safety, DPCD safety or MST support.

## Reconciled Runtime Baseline

The actual starting branch was experiment/dpdv-open-check, HEAD/upstream
`ae0dd1b18574205315f4bdc602627dd67b88ea5c`, clean with zero divergence. Main was
`1fc8f0241acec829fa732503c13a9ab588e26fb0`. The original stopped M2F receipt and
the later successful execution receipt were both checked; the earlier zero-attempt
state is historical, not the current runtime state.

| Runtime Fact | Retained Evidence |
| --- | --- |
| Successful receipt | artifacts/probes/m2f-20260913T012947590849Z/result.json |
| Executed implementation commit | `12538ab025ce5ab097aa0cd8665932fd3054b6f4`; native implementation from d7f41b8 |
| Wall-clock bracket | Public BEFORE at 2026-09-13T01:29:48Z and AFTER at 01:29:49Z; exact open-call wall-clock timestamp is not separately recorded |
| Selected provider | DCPDPDeviceProxy, External Unit 0 under RTBuddy(DCPEXT0), with matching supported External DCPDPServiceProxy |
| Transient device/service/transport IDs | 4294971118 / 4294971117 / 4294970218; comparison evidence only |
| Helper spawns / historical open attempts | 1 / 1; one-shot source/compiled callsite, consumed marker and returned terminal frame agree |
| Open return / duration | Raw 0 / 0x00000000, 22 microseconds |
| Connection returned | Nonzero, actual Mach port name not retained |
| Selector calls | 0 |
| Close attempted / return / duration | Yes, once / raw 0 / 0x00000000 / 99 microseconds |
| Helper exit / wait status | 0 / 0 |
| Parent observation / watchdog | 14 ms, no failure trigger, no timeout, no termination signal |
| Reaping | Successful; no remaining helper |
| Frame evidence | CLOSE_SUCCEEDED, flags=63, two matching-ID frames / 128 bytes, no stderr |
| Public comparison | NO_PUBLIC_DISPLAY_STATE_CHANGE: one 1920x1080@60 external display, DCPEXT0 endpoints, HPD High, two HBR3 lanes, no tunneling, sink count 1, no public errors |

All BEFORE/AFTER manifest artifacts and semantic comparisons were verified.
At M2G entry, the saved executed source and binary hashes matched the implementation
on disk; the post-stop commit changed only sanitized documentation. Subsequent M2G
rebuilds are distinguished from those executed binaries in the validation record
below. No missing result was inferred from an absent file or from the success
label alone.

| Immutable Receipt | SHA-256 |
| --- | --- |
| Original stopped result, m2f-20260912T154617081227Z | `79387346acdaebed1efb2284a531de8f2cf5aad1d64915a3f5f527040ebae840` |
| Successful result | `86ee9fdd87eb631e7552b0087471a149c183667c2162e838866ce993e1dd3d04` |
| Successful BEFORE public report | `9959711b39e43f541deab60091869048865c0e637b14bfb68124582a833f4552` |
| Successful BEFORE manifest | `60267d51a7ed07417d483ffc7b0028a5cf1026847b683d59aa7bdf89ec4b18af` |
| Successful AFTER public report | `3f46486f6884b7d9f7560832c7d410c165c9ab935fe31366673e2328e8a0e1f7` |
| Successful AFTER manifest | `adda3a3d430c469ef28e855c38d532588c2cad3f0cf7c3c0b01b663e8ca3a506` |
| Consumed M2F-ATTEMPTED marker | `2f3da1f224c0602dc46f812d3f6eb2c1560fe7a82c1a89f93eedb725b2726efc` |

## Integration And Tag

All three M2F commits and 20 unique changed text blobs were audited. The single
commit after the previously published stopped state changes five sanitized
documents only; no retry, raw capture, binary or private selector machinery was
introduced. The marker remains ignored and persistent.

M2F was integrated with --no-ff as
`3f5f0cd887ed2ef5c8dbadc9abb278792c3150be`, message
`merge: record first isolated DPDV open-close runtime validation`. Parents are
`1fc8f0241acec829fa732503c13a9ab588e26fb0` and
`ae0dd1b18574205315f4bdc602627dd67b88ea5c`; the merge tree equals the audited
M2F tree. Main was pushed without force or branch deletion.

Annotated tag `dpdv-open-runtime-v0.3`, object
`9d0341216b70251bfec37cddd47b8068ad9c1932`, peels to that merge. Its message is
`Verified MacMST state after first successful isolated DPDV open-close with zero selector calls.`
The tag was pushed and verified before research/selector0-one-byte-readiness was
created from it. The pre-open tag object
`f01208571d395ded9857a2c663f5276e12220c49` still peels to
`1fc8f0241acec829fa732503c13a9ab588e26fb0`; research-baseline-v0.1 and historical
branches are unchanged.

## Evidence Applicability And Hypothesis

The running kernel UUID is still `447D769E-1CB7-3086-A0B4-32226837B587`, on
macOS 26.6.2 (25G83), Apple M5. Retained ABI-02/RPC-03 server evidence therefore
remains the starting point; no fresh kernel call-graph expansion is needed.
An image UUID identifies the build, not the executed firmware route or every live
code page. The M2F success does not close the earlier routing uncertainty.

The local hypothesis to test is that length one changes the RPC allocation/copy
length but does not add a deadline or recover lost reply-completeness information.
The discriminating checks are the retained read/send/wait bodies and a synthetic
one-byte short-reply counterexample: a zero-filled host reply with insufficient
firmware bytes can overwrite a nonzero caller sentinel even if outer status is
zero. A complete-output-size or timeout guarantee in the actual one-byte path
would disprove or narrow this hypothesis. No hardware fault injection is permitted.

## Transport Choice

**NO_TRANSPORT_READY**. Option B is the smaller, evidence-backed candidate for a
future implementation, not an authorized or ready transport. Neither option fixes
the kernel wait, reply completeness or cancellation limits below. A successful
M2F open does not select between native and delegated implementations.

| Question | A: Private IODP Wrapper | B: Direct DPDV Selector 0 |
| --- | --- | --- |
| Userspace route | Private constructor, CF object, IODPDeviceReadDPCD, CF finalizer | Public IOServiceOpen/IOConnectCallMethod/IOServiceClose entrypoints with a private type/selector contract |
| Runtime-validated portion | Underlying type DPDV accepted once; private construction/read/finalization not executed | Exact type 0x44504456 open and immediate close accepted once; method dispatch not executed |
| Additional layers | Private object layout, allocator/CF lifetime and optional same-service AV construction | No CF wrapper, private symbol lookup or optional AV object |
| Address and length | Wrapper zero-extends its uint32 address to one uint64 scalar and caps uint32 length at 4096 | Future helper must fix address to 0x000 and size to 1; the server table does not enforce these particular values |
| Caller buffer | Caller initializes and retains one byte; wrapper does not provide a completeness guarantee | Caller initializes and retains one byte and the size_t variable; can inspect reported size |
| Size visibility | Local returned size discarded by wrapper | Reported userspace size observable, but not the actual firmware reply length |
| Cleanup after return | Release the owned CF object once, whose finalizer closes/releases its state | Exactly one close of the freshly opened connection after method return |
| Side effects | Additional construction/bookkeeping plus the shared read path | Less userspace bookkeeping, but the same unproved read/power/firmware behavior |
| Auditability | More private entrypoints, layout assumptions and ownership paths | One fixed method callsite can be audited; not implemented in M2G |
| Blocking and cancellation | No recovered bounded/cancel-safe read contract | Same unresolved contract; direct calling is not containment |

The public spelling of IOConnectCallMethod does not make an undocumented selector
a supported public DPCD API. No production backend, helper, dynamic symbol lookup
or executable call example is introduced in this milestone.

## Selector Contract

`PRIMARY_SOURCE`, native current-image path: IODPDeviceReadDPCD at `0x18487eeb0`
loads the connection from object+0x14 and calls IOConnectCallMethod at
`0x18487ef10`. Its exact ten-argument shape, specialized to the proposed request,
is the following contract, not an instruction to execute it:

| Position | Parameter | Future Fixed Value / Type |
| --- | --- | --- |
| 1 | connection | Fresh nonzero io_connect_t from the independently selected External DPDV open; never M2F's already closed connection |
| 2 | selector | uint32_t 0 |
| 3 | scalar input | Pointer to one live uint64_t containing zero, obtained from uint32_t address 0x000 |
| 4 | scalar input count | uint32_t 1 |
| 5 | structure input | NULL |
| 6 | structure input length | size_t 0 |
| 7 | scalar output | NULL |
| 8 | scalar output count pointer | NULL, matching the wrapper, not a pointer to a fabricated scalar result |
| 9 | structure output | Pointer to one initialized uint8_t with storage alive until the synchronous call returns |
| 10 | structure output length pointer | Pointer to live size_t initialized to 1; retain its returned raw value |

The table at `0xfffffe000845e058` has raw function pointer
`0x8030bcad037a865c`, resolving to `_readBytes` at `0xfffffe000a7ac65c`, with
checks `(scalar in=1, structure in=0, scalar out=0, structure out=0xffffffff)`.
The last value allows variable output size; it does not promise complete output.
`_readBytes` loads scalarInput[0] as uint32, structureOutput at arguments+88 and
structureOutputSize as uint32 at +96. It loads client interface+256 and tail-calls
its read slot with w4=500. The resolved interface thunk at `0xfffffe000a0207b0`
reaches DCPDPDeviceProxy::readDPCD at `0xfffffe000a020628`. Selector 1 is the
separate write entry and is outside this contract.

The complete 72-byte `_readBytes` body contains no store to
structureOutputSize. Public IOConnectCallMethod at `0x184860cd4` copies the
reported size back at `0x184860dd8`; pinned XNU is_io_connect_method likewise
returns args.structureOutputSize to the in-band count. A one-byte userspace
buffer is in-band, even though the lower AFK transfer can use its own OOL buffers.
The private wrapper discards its local returned size. The recovered native ABI
is not runtime proof that a future connection will dispatch through this table.

## One-Byte Reply Safety

`PRIMARY_SOURCE`: with requested length 1, readDPCD allocates OSData capacity for
129 bytes and zero-fills its actual capacity through appendBytes(NULL, capacity).
The logical service message remains 129 bytes, not a one-byte firmware message.
Address is at +64, requested count at +80, raw argument 500 at +96, initially zero
operation status at +112, and initially zero data at +128. The additions do not
overflow for the fixed length. OSData capacity may exceed the requested size.

AFK still allocates/reserves a command, correlates a tag and delivers a response.
The parsed inline span is not required to cover all 129 DPCD bytes. An OOL response
has separate descriptor/bounds/address checks; some malformed descriptors assert
or panic. These are not checks that the firmware produced a complete DPCD reply.
DCPAV::handleResponse at `0xfffffe000a01908c` copies the minimum of local capacity
and received size, writes that local size, sets transport status and wakes the
waiter. The response-taking block at `0xfffffe000a0090a4` discards the copied size.
On transport success, readDPCD copies the originally requested byte from +128
before loading operation status from +112. Both transports inherit this behavior.

`INFERRED`, synthetic counterexample: an honestly short service prefix of 128
bytes, delivered within an otherwise accepted AFK envelope with transport status
zero, can omit the data byte while leaving operation status zero. The host then
copies its initialized zero tail. A caller sentinel of 0xff changes to zero,
canaries remain intact, raw result can be zero and userspace output size can
still be 1. This disproves the proposed inference that these observations alone
establish a complete live DPCD read. It does not assert that a zero-byte AFK packet
passes framing, or that firmware actually produces such a response on M5.

The pure tests in [../../tests/dpcd_tests.cpp](../../tests/dpcd_tests.cpp) model
service prefix lengths 0, 8, 112, 116, 128 and 129. They check the bounded one-byte
copy, unchanged requested outer size, zero status, sentinel overwrite and revision
classification. They do not execute the captured kernel, AFK parser or firmware.
The zero-prefix case models delivery after framing, not an empty transport packet.

This establishes a local initialized-buffer/bounded-copy argument for honest
lengths, not end-to-end memory safety. OOL buffer initialization when firmware
misreports its writes and late-callback lifetime after abnormal completion remain
unknown. A plausible byte can also be stale or incorrectly reported. Byte-value
validation is useful negative evidence, never a transport-completeness oracle.

## DPCD 0x000

`PRIMARY_SOURCE`: Linux v6.12 at `adc218676eef25575469234709c2d87185ca223a`
and current Linux at `2f0c1cf72f4682178506f513bbf015e591b1aa4a` define
DP_DPCD_REV at 0x000 in the Receiver Capability section, with named encodings
0x10, 0x11, 0x12, 0x13 and 0x14. The major/minor nibbles describe the base DPCD
revision, not the Mac's MST support, the number of sinks, link health, or the
maximum capabilities of the physical panel. Linux notes that extended receiver
capabilities can exceed the revision at 0x000; no extended block is in scope.

The current [drm_dp.h](https://github.com/torvalds/linux/blob/2f0c1cf72f4682178506f513bbf015e591b1aa4a/include/drm/display/drm_dp.h)
and [drm_dp_helper.c](https://github.com/torvalds/linux/blob/2f0c1cf72f4682178506f513bbf015e591b1aa4a/drivers/gpu/drm/display/drm_dp_helper.c)
provide the following limited semantics:

- drm_dp_read_dpcd_caps rejects revision zero; the named revisions above are
  established examples, not an exhaustive future-version allowlist.
- drm_dp_dpcd_access uses native-read direction and rejects a short ACK with
  -EPROTO. Apple's captured path does not inherit that complete-transfer check.
- drm_dp_dpcd_probe explicitly documents possible sink wake as a read side effect.
  drm_dp_dpcd_read can perform a preliminary probe, and access can retry. Those
  behaviors must not be imported into the proposed one-call/no-retry experiment.
- The value at 0x000 is capability data, not a write, clear or MST command in
  these definitions. This is evidence for read-only register intent, not a
  firmware-level guarantee that accessing it is free of power or link effects.

The transport-independent classify_revision_byte in
[../../src/displayport/dpcd/capabilities.cpp](../../src/displayport/dpcd/capabilities.cpp)
returns PlausibleKnown for 0x10-0x14, Implausible for 0x00 and 0xff, and
Unrecognized for every other byte. The 0xff classification is a conservative
all-ones plausibility policy, not proof the value is impossible or reserved by
all future specifications. Values such as 0x15, 0x20 or 0x21 are retained as
unrecognized, not declared transport errors. Byte value 0x21 is not a request
to read address 0x021. All 256 encodings are covered by synthetic tests.

A future caller would initialize the one byte to **0xff** and preserve raw status,
returned size, byte, initial sentinel, canaries and timing independently. On any
nonzero status, discard the byte as a DPCD result even if it changed: the driver
copies before checking operation status. On size !=1 or a changed canary, reject
the result. On unchanged sentinel or an implausible byte, record inconclusive
data, with no retry. Unrecognized values remain UNKNOWN pending source review.
Even PlausibleKnown plus status zero, size 1 and intact canaries means only a
plausible reported byte, not a verified live/complete reply. Never pad it into the
existing 16-byte capability decoder or infer unread MST bits.

## Wait Behavior

**UNBOUNDED_KERNEL_WAIT_POSSIBLE**, unchanged for length 1. There are two distinct
waits in the retained path:

1. Before firmware submission, AFKEPInterfaceV2::acquireCommand's block at
	`0xfffffe000928549c` waits while the eight-bit outstanding count at +145 is at
	least the limit at +144. It calls AFKWorkloop::sleep with deadline zero. A
	release can wake it, but no finite admission deadline is established.
2. After successful enqueue, DCPAV::performCommandGated at
	`0xfffffe000a018f40` selects command-gate slot +512 and passes THREAD_UNINT=0.
	This is IOCommandGate::commandSleep(void*,uint32_t) at
	`0xfffffe000bfe79ac`, not the deadline overload at +528. No one-byte condition
	changes that selection or adds a local deadline.

A missing reply or mismatched tag need not wake the outstanding context.
Conditional offline/error-response paths exist, but no universal finite recovery
bound is proved. One selector invocation also does not establish one physical
AUX transaction: firmware handling and internal retries remain unknown.

The read path can select BlockPower/ChangePower options from a live private field
at proxy+208; that value is not publicly observed. The M2F open-only result and
normal 22/99-microsecond open/close timings cannot bound this new submission or
its later close. No fault, HPD transition, forced wake or concurrent close was
induced to investigate these questions.

## Constant 500

**UNRESOLVED**. The exact instruction at `0xfffffe000a7ac694`, raw bytes
`843e8052`, loads w4=500; readDPCD stores its low 32 bits at message+96 at
`0xfffffe000a020740`. The examined host layers pass that payload through without
turning it into a deadline. No recovered, target-attributed firmware contract
establishes meaning or units. It cannot be called HARD_READ_TIMEOUT or even
LOWER_LAYER_TIMEOUT_WITH_UNBOUNDED_OUTER_WAIT without evidence of a lower timeout.
NOT_A_READ_TIMEOUT would also overstate what is known about firmware.

Linux's separately named AUX_RETRY_INTERVAL happens to equal 500 microseconds;
that independent constant is not evidence of Apple's field meaning. The retained
Asahi EPIC envelope matches do not define DP-device group 1/command 6's argument.
Even future proof of a firmware timeout would leave the pre-submission admission
wait and delivery/host-wake behavior independently unbounded in current evidence.

## Cancellation

**READ_CANCELLATION_UNRESOLVED**. The selected AFK abort slot +2192 resolves to
`0xfffffe0009279284`, whose complete eight-byte body is a landing hint and return
(`5f2403d5c0035fd6`). This hook does not cancel or drain an outstanding command.
It does not, by itself, prove OUTSTANDING_READ_NOT_CANCELLED for every possible
client-death path; nor does normal response cleanup establish
OUTSTANDING_READ_CANCELLED_ON_CLIENT_DEATH.

Normal delivery retains/releases callbacks and message references and wakes the
stack CommandContext before normal return. Callback retention is not ownership
of that stack storage. The no-op abort does not establish quiescence after an
abnormal early return. Endpoint list cleanup frees command storage without proving
every waiter receives a bounded response. Conditional createErrorResponses paths
must not be generalized into universal read cancellation.

The retained [dpdv-isolation-safety.md](dpdv-isolation-safety.md) distinguishes
rights destruction, client lifetime, provider completion and AFK/DCP cancellation:

| Action | Limit For An Outstanding Read |
| --- | --- |
| Same-thread IOServiceClose | Can occur only after the synchronous read returns; it cannot cancel its own blocked call |
| Concurrent IOServiceClose | Current close at 0xfffffe000c038688 takes an exclusive client IPC lock; external-method locking can serialize behind it, and driver gates/lifetimes add unresolved interactions. No supported concurrent-close cancellation contract is established |
| Port deallocation / process exit | Rights and ownership teardown are not proof of firmware completion or callback quiescence |
| SIGKILL | Cannot be caught by userspace, but pinned XNU thread termination does not give a finite bound for already-running THREAD_UNINT kernel work |
| Parent watchdog / waitpid | Bounds the parent's observation/attempted termination policy; even reaping is not evidence of DCP cancellation |
| CFRelease | Ordinary returned-operation cleanup only, not permission to destroy a wrapper concurrently with a read |

M2F validated immediate close with zero selectors, where an unused gate did not
have a submitted read to drain. That local proof is not transferable to close
after a blocked, interrupted or late-reply selector. No close thread is proposed
as a workaround.

## Constrained Future Contract

This is a design record only. It is not implemented, compiled, enabled or executed
as a read helper. Existing M2F helper/parent code remains open-only and the normal
CLI remains public-probe-only. The pure revision classifier has no transport.

Only after a separately approved readiness decision could a future implementation:

1. Recheck OS/kernel identity, committed source/binary hashes and a fresh public
	BEFORE capture; independently resolve the unique active External Unit 0 under
	DCPEXT0. Historical registry IDs are comparisons, never reusable service handles.
2. Preserve M2F-ATTEMPTED. Use a separate exclusive, persistent
	M2G-DPCD-READ-ATTEMPTED marker before any future private attempt. Do not create
	that marker in this milestone, reuse M2F's authorization, or retry after failure.
3. Spawn one isolated helper with bounded IPC, no inherited service/connection
	right and a parent observation deadline. Establish independently bounded read
	termination first; do not advertise the parent deadline as a kernel timeout.
4. Open one fresh DPDV connection, submit at most one selector-0 call using the
	exact fixed address/length contract, and never expose address/length/method
	options, a bulk read, fallback transport, preliminary probe or write path.
5. If the call returns, immediately attempt one same-thread close of the nonzero
	connection regardless of read status, before semantic processing or final
	reporting. Preserve scalar results/times locally first; no deliberate dwell.
	On open failure there is no selector call and no close of a null connection.
6. Report raw open/read/close results, byte/size/canaries, elapsed times, helper
	exit and reaping, and a public AFTER comparison. Never claim that missing AFTER
	evidence means no state change. A hang, denial, malformed report or unknown
	byte ends the attempt without another open/read/close sequence.

No firmware/NVRAM/security setting, display route, HPD state, link training or MST
payload is changed or requested as a prerequisite. The unresolved kernel wait
prevents this proposed sequence from being a complete safe execution contract.

## Readiness Matrix

PASS is scoped evidence, not permission to execute. CONTRACT_ONLY means a written
constraint without an implemented read helper. UNKNOWN is an unproved gate;
BLOCKED identifies a specific missing guarantee. All gates are evaluated for the
future fresh connection and one-byte selector, not inherited from open-only safety.

| Gate | State | Evidence / Limit |
| --- | --- | --- |
| DPDV open runtime validated | PASS, one observed context | One M2F open returned 0, nonzero port, 22 microseconds; no repeat |
| DPDV close runtime validated | PASS, zero-selector close only | One immediate close returned 0, 99 microseconds; not a pending-read close proof |
| External target selection | PASS historically; recheck required | Unique active External Unit 0/DCPEXT0 identified by helper and matching public captures |
| Selector ABI | PASS for retained native ABI; live route UNKNOWN | Exact wrapper/table/_readBytes/thunk; runtime open alone does not attest selected implementation |
| Selector read direction | PASS for native path | Selector 0/output and DP command 6; separate selector 1/write excluded; firmware effects remain unknown |
| Address fixed 0x000 | CONTRACT_ONLY | Immutable zero scalar in future design; no read helper exists |
| Length fixed 1 | CONTRACT_ONLY | One-byte output and size_t 1 in future design; no cap substitution or bulk request |
| Buffer memory safety | PARTIAL | Fixed arithmetic, initialized local copy and synthetic canaries; OOL misreport and abnormal callback lifetime not proved safe |
| Reply completeness | BLOCKED | Actual copied firmware size discarded; one-byte short-prefix counterexample |
| Semantic result validation | PASS, plausibility only | All 256 bytes classified; raw/error/size/sentinel policy documented; not freshness or completeness proof |
| Kernel wait bounded | BLOCKED | Pre-enqueue deadline zero and post-enqueue THREAD_UNINT/no-deadline wait |
| Read cancellation | UNKNOWN | Selected abort is no-op; universal bounded cancellation unresolved |
| Client death cleanup | UNKNOWN for in-flight read | Ordinary conditional lifecycle evidence does not prove final read/callback/firmware quiescence |
| No write path | PASS for M2G; CONTRACT_ONLY for future helper | Pure classifier/tests/docs only; future design excludes selector 1, structure input and other operations |
| Helper isolation | PASS for existing mocks/open-only helper; future read unimplemented | No parent IOKit transport or inherited connection; does not contain shared-kernel blocking |
| Parent watchdog | PASS as observation policy only | Existing mock/open parent is bounded; cannot guarantee kernel cancellation or prompt reaping of a blocked read |
| No retry | PASS for M2G; CONTRACT_ONLY for future read | No new private operations; consumed M2F marker intact, read marker absent; firmware-internal retries unknown |
| Public before/after observation | PASS for M2F; required anew for any future attempt | Hashed matching runtime captures, not evidence of unobservable firmware state |
| OS/kernel evidence still current | PASS for build identity | macOS 26.6.2/25G83, UUID 447D769E-1CB7-3086-A0B4-32226837B587 unchanged; not live route attestation |

## Decisions And Next Step

- Transport: **NO_TRANSPORT_READY**.
- Selector readiness: **NOT_READY_FOR_ONE_BYTE_DPCD_READ**.
- Wait: **UNBOUNDED_KERNEL_WAIT_POSSIBLE**.
- Constant 500: **UNRESOLVED**.
- Cancellation: **READ_CANCELLATION_UNRESOLVED**.
- Global gate: **NOT_READY_FOR_DPCD_TEST**.

The single smallest next blocker is **a target-attributed bounded, cancel-safe
termination contract for an in-flight one-byte read when its reply is lost**.
Existing evidence disproves relying on length 1, raw 500, same-thread close or a
userspace watchdog as that contract. A positive source/firmware guarantee must
cover admission, outstanding callback quiescence and final completion; another
unrelated call-graph expansion or open/close trial does not resolve it. Reply
completeness remains a separate gate even if termination is later established.

No DPCD byte was observed on hardware. M2G performs zero private opens, closes or
selectors; the historical one M2F open/close remains the entire authorized runtime
record. M2F-ATTEMPTED is retained and M2G-DPCD-READ-ATTEMPTED is not created.

## Provenance And Reproduction

Existing ABI-02/RPC-03/M2C evidence is reused without a fresh kernel extraction or
call graph. Preferred addresses below are file-image evidence, not callable live
addresses. The R3 container SHA-256 is
`b20d50fc8f445a5c578ac63bd974efeb6ae48a97116800301071891795fb26d9`.
Each listed server report records kernel UUID
`447D769E-1CB7-3086-A0B4-32226837B587`; the running UUID was rechecked in M2G.
For userland wrapper/call bindings, retain the exact ABI-02 evidence in
[iodpdevice-abi-02.md](iodpdevice-abi-02.md), not a reconstructed private header.

| Retained Report Under artifacts/probes | SHA-256 |
| --- | --- |
| R3: iodp-static-20260912T045748Z/iodp-static.json | `b80b5f6b1d9553ce1ee1b292f68102369d0c7e3d29cfdd6ab80ff3c9c199b263` |
| R4: iodp-static-20260912T095457Z/iodp-static.json | `1262f818b09a562b22c4649c97d94e77a5c865148268793cd2a9dc8d5c72ab1f` |
| R6: iodp-static-20260912T115506Z/iodp-static.json | `8e235935b12579787150b991c1c90db2f618312deab0e58594eb52b1d14843dd` |
| R7: iodp-static-20260912T115605Z/iodp-static.json | `e52a1db96cad564a3ea0cfebf0884942e8d2139bbc481a8580517b6697077102` |

The concatenated raw instruction bytes reproduce these retained full-body hashes;
declared function bounds and selected vtable targets remain those in the reports.

| Body / Preferred Address | Bytes | SHA-256 |
| --- | --- | --- |
| _readBytes, 0xfffffe000a7ac65c | 72 | `c3b94597539cfbb8cea1afea34515bfc11348ef800d09b53f224239b654e5078` |
| readDPCD, 0xfffffe000a020628 | 392 | `372d7a56d61721b28562b88c692f04840cbc7a61ff4672845ef5af46011ae10c` |
| handleResponse, 0xfffffe000a01908c | 184 | `1f742a141915f52fe31f893cfcaaa392ed3c594bfe9f247152d9e5ddd32c7cf7` |
| Response-taking block, 0xfffffe000a0090a4 | 64 | `9da8d72d6ee5e3dd42bfa1e1328b6c059975c0262ed1f6ee2759ae43ca600845` |
| performCommandGated, 0xfffffe000a018f40 | 332 | `98bf09b907fc17558a5f487ba143182ab3e613585f21ae6f8e30c63c153efee3` |
| acquireCommand block, 0xfffffe000928549c | 88 | `5f68446166f25ff3412c69a4126da0c0b45580669a6a506fda2610021c15b951` |
| Selected abortCommand, 0xfffffe0009279284 | 8 | `d33fdb74881bcff46b1cf4fc3e20479b1882e0e683789e80e6d650554066a1aa` |

Primary Linux files are retained locally under ignored artifacts/sources/m2g,
not committed or compiled. URLs are immutable by the full revisions above.

| Source | SHA-256 | Decisive Locations |
| --- | --- | --- |
| Linux v6.12 include/drm/display/drm_dp.h | `70ea7e2c08c2155450f998d30d53e147070443168f616f06584b671e2b37dfd2` | DP_DPCD_REV and five named encodings, line 107 onward |
| Linux current include/drm/display/drm_dp.h | `7f7958ee96e2dcd2329ef53422b1801eb2ba0a2f47febdc42cfb808a45754c5f` | Same address/encodings, line 107 onward |
| Linux current drivers/gpu/drm/display/drm_dp_helper.c | `e9f9869b034230c39766a1237ad7b96b3d88e8f3e8c5b315189a2a855ce7d155` | drm_dp_dpcd_access, drm_dp_dpcd_probe, drm_dp_dpcd_read, drm_dp_read_dpcd_caps |
| Installed macOS 26.5 SDK IOKit.framework/Headers/IOKitLib.h | `553869588e8c0b162b232e294dea2579cfd739d83e772a0b8a79e2be91a5816e` | IOConnectCallMethod declaration at line 825; size_t outputStructCnt is in/out |

Safe reproduction commands for the source/hash and focused synthetic checks:

```sh
sysctl -n kern.uuid
shasum -a 256 artifacts/probes/iodp-static-20260912T045748Z/iodp-static.json
shasum -a 256 artifacts/sources/m2g/linux-current/include/drm/display/drm_dp.h
shasum -a 256 artifacts/sources/m2g/linux-current/drivers/gpu/drm/display/drm_dp_helper.c
cmake --build build --target macmst_dpcd_tests
ctest --test-dir build -R '^dpcd_capabilities$' --output-on-failure
```

These commands do not submit a display request. A fresh clone lacks ignored raw
evidence and must not fabricate a hash match or automatically rerun a private
experiment to replace it. The current-image proof and pure model have separate
validation scopes; neither is a measured one-byte DPCD result.

## Validation

Executed on the same M5/macOS/toolchain on 2026-09-13 UTC. No private helper mode
was run, including no repeat of M2F's no-open helper selection or coordinator.
The dpdv_contract tests use mocks, static imports and a pre-existing temporary
marker with a nonexistent helper; they do not submit a real private operation.

| Check | Result | Verified Scope |
| --- | --- | --- |
| cmake --build build | PASS | Full strict warnings-as-errors build |
| ctest --test-dir build -L unit --output-on-failure | 9/9 PASS | Pure decoder, privacy, parser, CLI, process mocks and open-only contract guards |
| cmake --build build-sanitized | PASS | ASan/UBSan build |
| ctest --test-dir build-sanitized -L unit --output-on-failure | 9/9 PASS | Same deterministic suite under sanitizers; no private hardware call |
| python3 -m unittest discover -s tests -p 'test_iodp_static.py' | 60/60 PASS | Existing synthetic static/parser/public-inspector regressions |
| build/macmst_dpcd_tests | 324 checks, zero failures | All raw revision bytes, six short-prefix cases and existing receiver-block tests |
| ctest --test-dir build -L hardware --output-on-failure | 1/1 PASS | Existing public-only probe/JSON contract, not a DPCD transaction or new complete topology capture |
| Existing audit_binaries plus source comparison | PASS | Rebuilt helper still has one open/one close callsite and zero selector imports; parent has no display transport; helper/parent/coordinator/production source unchanged from the tag |
| Receipt/source/byte/marker and document checks | PASS | Historical receipts, four reports, seven raw bodies, pinned sources, 19 gates, links/fences/ledger and editor diagnostics |

The full build regenerated the experimental helper and parent binaries. Their
hashes changed despite unchanged sources; do not transfer the historical runtime
or signing observation to these rebuilt binaries. The production public probe is
byte-identical. No attempt is made to reproduce the old binary by running it or
to replace the consumed receipt/marker with a new result.

| Binary | Historical M2F SHA-256 | M2G Rebuilt SHA-256 |
| --- | --- | --- |
| Public macmst | `450832c50446d3a430cbed2bcab7c285cddf5f6b370b2339df2cd0a33aefd89a` | `450832c50446d3a430cbed2bcab7c285cddf5f6b370b2339df2cd0a33aefd89a` |
| macmst_dpdv_open_helper | `4ffc55f505364467f82cbd5685be3af976be8dc01990081dfaf240b2261535cc` | `d94b0a450e89daa697675d816e231994e37456ec61928fc72261ec500f153830` |
| macmst_dpdv_open_check parent | `834c856d7761e944055f5a1f6020a6d3ecd28834d69156430885df3de8e50a4b` | `f94db7e91ef670ce6c59ce73929016d2d36a5adb44fb9714f188932771b55e8b` |

M2G's generic library edits make a historical all-source receipt unsuitable for
any new execution as well. The old marker remains consumed regardless of source
or binary identity. Builds, sanitizer tests and a public-probe success are not
evidence of bounded kernel waits, DPCD reads, cancellation or M5 MST support.

## Git

The research branch is `research/selector0-one-byte-readiness`, based on runtime
merge `3f5f0cd887ed2ef5c8dbadc9abb278792c3150be`. Commit `8c8f226` records the
independently validated runtime reconciliation. Commit
`6e3bd0751c62e0277f444c9d176bc8e060a7df9a` adds only the portable classifier and
synthetic tests. The subsequent research commit records this completed assessment,
validation and navigation. Eight scoped text paths change from the runtime tag;
no raw capture, downloaded source, Apple binary, credential or build is published.

After the separately completed main/runtime-tag integration above, publication is
restricted to this research branch with an explicit non-force refspec and
push.followTags=false. Main, the runtime tag, both older tags, the completed M2F
branch and all historical research branches are preserved. M2G is not merged and
no pull request is opened.

```sh
git log --oneline dpdv-open-runtime-v0.3..HEAD
git rev-parse HEAD
git status --short --branch
git rev-list --left-right --count HEAD...@{upstream}
```

These identify the final report commit and verify a clean synchronized branch
without rewriting the immutable runtime receipts or either experiment marker.